"""
Conversion functions between Anthropic and OpenAI formats (direct, no LiteLLM).
"""

import json
import uuid
from typing import Dict, Any
from ..models import MessagesRequest, MessagesResponse, Usage, ContentBlockText, ContentBlockToolUse
from ..utils import parse_tool_result_content, get_logger

logger = get_logger(__name__)

def convert_anthropic_to_openai(anthropic_request: MessagesRequest) -> Dict[str, Any]:
    """Convert Anthropic API request format to OpenAI format (direct API calls)."""
    
    messages = []
    
    # Add system message if present
    if anthropic_request.system:
        if isinstance(anthropic_request.system, str):
            messages.append({"role": "system", "content": anthropic_request.system})
        elif isinstance(anthropic_request.system, list):
            system_text = ""
            for block in anthropic_request.system:
                if hasattr(block, 'type') and block.type == "text":
                    system_text += block.text + "\n\n"
                elif isinstance(block, dict) and block.get("type") == "text":
                    system_text += block.get("text", "") + "\n\n"
            
            if system_text:
                messages.append({"role": "system", "content": system_text.strip()})
    
    # Add conversation messages
    for msg in anthropic_request.messages:
        content = msg.content
        
        # Case 1: Simple string content
        if isinstance(content, str):
            messages.append({"role": msg.role, "content": content})
            continue

        # Case 2: List of content blocks (complex content)
        if msg.role == "assistant":
            tool_calls = []
            assistant_text_content = ""
            for block in content:
                if block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input)
                        }
                    })
                elif block.type == "text":
                    assistant_text_content += block.text + "\n"
            
            assistant_message = {"role": "assistant", "content": assistant_text_content.strip()}
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            messages.append(assistant_message)

        elif msg.role == "user":
            user_text_content = ""
            # Separate tool results from text content
            for block in content:
                if block.type == "tool_result":
                    # Each tool result becomes a separate message with role 'tool'
                    messages.append({
                        "role": "tool",
                        "tool_call_id": block.tool_use_id,
                        "content": parse_tool_result_content(block.content)
                    })
                elif block.type == "text":
                    user_text_content += block.text + "\n"
                elif block.type == "image":
                    user_text_content += "[Image Content]\n"
            
            # If there was any text content, add it as a separate user message
            if user_text_content.strip():
                messages.append({"role": "user", "content": user_text_content.strip()})
    
    # Create OpenAI request dict
    openai_request = {
        "model": anthropic_request.model.replace("openai/", ""),  # Remove prefix
        "messages": messages,
        "max_tokens": anthropic_request.max_tokens,
        "temperature": anthropic_request.temperature,
        "stream": anthropic_request.stream,
    }
    
    # Add optional parameters if present
    if anthropic_request.stop_sequences:
        openai_request["stop"] = anthropic_request.stop_sequences
    
    if anthropic_request.top_p:
        openai_request["top_p"] = anthropic_request.top_p
    
    # Convert tools to OpenAI format
    if anthropic_request.tools:
        openai_tools = []
        for tool in anthropic_request.tools:
            tool_dict = tool.model_dump() if hasattr(tool, 'model_dump') else tool
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_dict["name"],
                    "description": tool_dict.get("description", ""),
                    "parameters": tool_dict.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)
        openai_request["tools"] = openai_tools
    
    # Convert tool_choice to OpenAI format if present
    if anthropic_request.tool_choice:
        tool_choice_dict = anthropic_request.tool_choice
        choice_type = tool_choice_dict.get("type")
        if choice_type == "auto":
            openai_request["tool_choice"] = "auto"
        elif choice_type == "any":
            openai_request["tool_choice"] = "required"
        elif choice_type == "tool" and "name" in tool_choice_dict:
            openai_request["tool_choice"] = {
                "type": "function",
                "function": {"name": tool_choice_dict["name"]}
            }
        else:
            openai_request["tool_choice"] = "auto"
    
    return openai_request

def convert_openai_to_anthropic(openai_response: Dict[str, Any], 
                                original_request: MessagesRequest) -> MessagesResponse:
    """Convert OpenAI response to Anthropic API response format."""
    
    try:
        # Extract the content from the response
        choices = openai_response.get("choices", [{}])
        message = choices[0].get("message", {}) if choices and len(choices) > 0 else {}
        content_text = message.get("content", "")
        tool_calls = message.get("tool_calls", None)
        finish_reason = choices[0].get("finish_reason", "stop") if choices and len(choices) > 0 else "stop"
        usage_info = openai_response.get("usage", {})
        response_id = openai_response.get("id", f"msg_{uuid.uuid4()}")
        
        # Create content list for Anthropic format
        content = []
        
        # Add text content block if present
        if content_text is not None and content_text != "":
            content.append(ContentBlockText(type="text", text=content_text))
        
        # Add tool calls if present
        if tool_calls:
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_id = tool_call.get("id", f"tool_{uuid.uuid4()}")
                name = function.get("name", "")
                arguments = function.get("arguments", "{}")
                
                # Convert string arguments to dict if needed
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments as JSON: {arguments}")
                        arguments = {"raw": arguments}
                
                content.append(ContentBlockToolUse(
                    type="tool_use",
                    id=tool_id,
                    name=name,
                    input=arguments
                ))
        
        # Get usage information
        prompt_tokens = usage_info.get("prompt_tokens", 0)
        completion_tokens = usage_info.get("completion_tokens", 0)
        
        # Map OpenAI finish_reason to Anthropic stop_reason
        stop_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use"
        }
        stop_reason = stop_reason_map.get(finish_reason, "end_turn")
        
        # Make sure content is never empty
        if not content:
            content.append(ContentBlockText(type="text", text=""))
        
        # Create Anthropic-style response
        anthropic_response = MessagesResponse(
            id=response_id,
            model=original_request.original_model or original_request.model,
            role="assistant",
            content=content,
            stop_reason=stop_reason,
            stop_sequence=None,
            usage=Usage(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens
            )
        )
        
        return anthropic_response
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"Error converting OpenAI response: {str(e)}\n\nFull traceback:\n{error_traceback}"
        logger.error(error_message)
        
        # In case of any error, create a fallback response
        return MessagesResponse(
            id=f"msg_{uuid.uuid4()}",
            model=original_request.model,
            role="assistant",
            content=[ContentBlockText(type="text", text=f"Error converting response: {str(e)}. Please check server logs.")],
            stop_reason="end_turn",
            usage=Usage(input_tokens=0, output_tokens=0)
        )