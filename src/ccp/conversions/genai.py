"""
Conversion functions between Anthropic and Google GenAI formats.
"""

import json
import uuid
from typing import Dict, Any
from google.genai import types
from ..models import MessagesRequest, MessagesResponse, Usage, ContentBlockText, ContentBlockToolUse
from ..utils import parse_tool_result_content, clean_gemini_schema, get_logger

logger = get_logger(__name__)

def convert_anthropic_to_genai_payload(request: MessagesRequest) -> dict:
    """Converts an Anthropic MessagesRequest to a Google GenAI API payload."""
    contents = []
    system_prompt = None

    # Create a map of tool_use_id to function name for later lookup
    tool_use_id_to_name = {}
    for message in request.messages:
        if message.role == "assistant" and isinstance(message.content, list):
            for block in message.content:
                if block.type == "tool_use":
                    tool_use_id_to_name[block.id] = block.name

    # Extract system prompt
    if request.system:
        if isinstance(request.system, str):
            system_prompt = request.system
        elif isinstance(request.system, list):
            system_text = ""
            for block in request.system:
                if hasattr(block, 'text'):
                    system_text += block.text + "\n\n"
            system_prompt = system_text.strip()

    # Process messages
    for message in request.messages:
        role = "user" if message.role == "user" else "model"
        
        if isinstance(message.content, str):
            parts = [types.Part(text=message.content)]
        else:
            parts = []
            for block in message.content:
                if block.type == "text":
                    parts.append(types.Part(text=block.text))
                elif block.type == "tool_use":
                    # This is an assistant message with a tool call
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=block.name,
                            args=block.input
                        )
                    ))
                elif block.type == "tool_result":
                    # This is a user message with a tool result
                    parts.append(types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_use_id_to_name.get(block.tool_use_id, "unknown_function"),
                            response={'result': parse_tool_result_content(block.content)}
                        )
                    ))

        contents.append(types.Content(role=role, parts=parts))

    # Gemini handles system prompts as the first part of the 'contents'
    if system_prompt:
        # Check if the first message is from a user
        if contents and contents[0].role == 'user':
            # Prepend system prompt text to the first user message
            original_text = contents[0].parts[0].text
            contents[0].parts[0].text = f"{system_prompt}\n\n{original_text}"
        else:
            # If no user message is first, insert a new one
            contents.insert(0, types.Content(role="user", parts=[types.Part(text=system_prompt)]))
            # We need a model response to follow
            if len(contents) < 2 or contents[1].role != 'model':
                 contents.insert(1, types.Content(role="model", parts=[types.Part(text="OK.")]))


    # Convert tools
    genai_tools = []
    if request.tools:
        function_declarations = []
        for tool in request.tools:
            # The schema cleaning is still relevant
            cleaned_schema = clean_gemini_schema(tool.input_schema)
            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=cleaned_schema,
                )
            )
        genai_tools.append(types.Tool(function_declarations=function_declarations))

    # Convert tool_choice to tool_config
    tool_config = None
    if request.tool_choice:
        choice_type = request.tool_choice.get("type")
        if choice_type == "any":
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode=types.FunctionCallingConfig.Mode.ANY)
            )
        elif choice_type == "auto":
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode=types.FunctionCallingConfig.Mode.AUTO)
            )
        elif choice_type == "tool":
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfig.Mode.ANY,
                    allowed_function_names=[request.tool_choice.get("name")]
                )
            )

    # Store parameters that will be used to build GenerateContentConfig
    # Filter out None values to avoid API issues
    config_params = {}
    
    if request.max_tokens is not None:
        # Gemini might have issues with very low token limits, set a minimum of 10
        config_params["max_output_tokens"] = max(request.max_tokens, 10)
    if request.temperature is not None:
        config_params["temperature"] = request.temperature
    if request.top_p is not None:
        config_params["top_p"] = request.top_p
    if request.top_k is not None:
        config_params["top_k"] = request.top_k
    if request.stop_sequences is not None:
        config_params["stop_sequences"] = request.stop_sequences
    
    # Only add tool_config if it exists
    if tool_config:
        config_params["tool_config"] = tool_config
    
    # Add tools if they exist
    if genai_tools:
        config_params["tools"] = genai_tools

    payload = {
        "contents": contents,
        "config_params": config_params,
    }
    
    # Debug logging
    logger.info(f"🔍 Converted payload - Contents: {len(contents)} messages")
    logger.info(f"🔍 Config params: {config_params}")
    
    return payload

def convert_genai_to_anthropic_response(
    genai_response: types.GenerateContentResponse,
    original_request: MessagesRequest
) -> MessagesResponse:
    """Converts a Google GenAI response to an Anthropic MessagesResponse."""
    content = []
    stop_reason = "end_turn"
    
    response_id = f"msg_gemini_{uuid.uuid4()}"
    
    # The response from Gemini is in `candidates`
    if genai_response.candidates:
        candidate = genai_response.candidates[0]
        
        # Map finish reason
        finish_reason_map = {
            "STOP": "end_turn",
            "MAX_TOKENS": "max_tokens",
            "TOOL_CODE": "tool_use", # Note: Gemini uses TOOL_CODE or FUNCTION_CALL
            "FUNCTION_CALL": "tool_use",
            "SAFETY": "end_turn", # Or could be mapped to an error
            "RECITATION": "end_turn",
        }
        stop_reason = finish_reason_map.get(str(candidate.finish_reason), "end_turn")

        # Process content parts - check if content exists
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text:
                    content.append(ContentBlockText(type="text", text=part.text))
                
                if part.function_call:
                    # Generate a unique ID for the tool call for Anthropic
                    tool_call_id = f"toolu_{uuid.uuid4().hex[:24]}"
                    content.append(ContentBlockToolUse(
                        type="tool_use",
                        id=tool_call_id,
                        name=part.function_call.name,
                        input=part.function_call.args
                    ))

    # If no content was generated (e.g. safety settings), add an empty text block
    if not content:
        content.append(ContentBlockText(type="text", text=""))

    # Get usage data
    input_tokens = 0
    output_tokens = 0
    if genai_response.usage_metadata:
        input_tokens = genai_response.usage_metadata.prompt_token_count or 0
        output_tokens = genai_response.usage_metadata.candidates_token_count or 0

    usage = Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )

    return MessagesResponse(
        id=response_id,
        model=original_request.original_model or original_request.model,
        role="assistant",
        content=content,
        type="message",
        stop_reason=stop_reason,
        usage=usage,
    )