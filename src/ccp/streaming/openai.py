"""
Streaming response handler for OpenAI API.
"""

import json
import uuid
import httpx
from ..models import MessagesRequest
from ..config import OPENAI_API_KEY
from ..utils import get_logger

logger = get_logger(__name__)

async def handle_openai_streaming(openai_payload: dict, original_request: MessagesRequest):
    """Handle streaming responses from OpenAI and convert to Anthropic SSE format."""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Send message_start event
        message_id = f"msg_openai_{uuid.uuid4().hex[:24]}"
        message_data = {
            'type': 'message_start',
            'message': {
                'id': message_id,
                'type': 'message',
                'role': 'assistant',
                'model': original_request.original_model or original_request.model,
                'content': [], 'stop_reason': None, 'stop_sequence': None,
                'usage': {'input_tokens': 0, 'output_tokens': 0}
            }
        }
        yield f"event: message_start\ndata: {json.dumps(message_data)}\n\n"
        yield f"event: ping\ndata: {json.dumps({'type': 'ping'})}\n\n"

        # Start text content block
        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

        content_block_index = 0
        current_tool_call_id = None
        text_sent = False
        text_block_closed = False
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                json=openai_payload,
                headers=headers,
                timeout=120.0
            ) as response:
                
                if response.status_code != 200:
                    error_data = {
                        "type": "error",
                        "error": {"type": "api_error", "message": f"OpenAI API error: {response.status_code}"}
                    }
                    yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                    return
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                                
                            delta = choices[0].get("delta", {})
                            finish_reason = choices[0].get("finish_reason")
                            
                            # Handle text content
                            if "content" in delta and delta["content"]:
                                text_sent = True
                                delta_text = {'type': 'text_delta', 'text': delta["content"]}
                                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': delta_text})}\n\n"
                            
                            # Handle tool calls
                            if "tool_calls" in delta and delta["tool_calls"]:
                                # Close text block if needed
                                if not text_block_closed:
                                    text_block_closed = True
                                    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
                                
                                for tool_call in delta["tool_calls"]:
                                    if current_tool_call_id is None:
                                        # Start new tool call
                                        content_block_index += 1
                                        current_tool_call_id = tool_call.get("id", f"toolu_{uuid.uuid4().hex[:24]}")
                                        tool_use_block = {
                                            'type': 'tool_use',
                                            'id': current_tool_call_id,
                                            'name': tool_call.get("function", {}).get("name", ""),
                                            'input': {}
                                        }
                                        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': content_block_index, 'content_block': tool_use_block})}\n\n"
                                    
                                    # Stream function arguments
                                    if "function" in tool_call and "arguments" in tool_call["function"]:
                                        args = tool_call["function"]["arguments"]
                                        delta_args = {'type': 'input_json_delta', 'partial_json': args}
                                        yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': content_block_index, 'delta': delta_args})}\n\n"
                            
                            # Handle finish reason
                            if finish_reason:
                                # Close any open blocks
                                if not text_block_closed:
                                    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
                                if current_tool_call_id:
                                    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': content_block_index})}\n\n"
                                
                                # Map finish reason
                                stop_reason = "end_turn"
                                if finish_reason == "length":
                                    stop_reason = "max_tokens"
                                elif finish_reason == "tool_calls":
                                    stop_reason = "tool_use"
                                
                                # Get usage if available
                                usage = chunk.get("usage", {})
                                usage_data = {'output_tokens': usage.get("completion_tokens", 0)}
                                
                                message_delta = {
                                    'type': 'message_delta',
                                    'delta': {'stop_reason': stop_reason, 'stop_sequence': None},
                                    'usage': usage_data
                                }
                                yield f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n"
                                yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
                                return
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing OpenAI streaming chunk: {e}")
                            continue

    except Exception as e:
        logger.error(f"Error in OpenAI streaming: {e}")
        error_data = {
            "type": "error",
            "error": {"type": "internal_server_error", "message": str(e)}
        }
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"