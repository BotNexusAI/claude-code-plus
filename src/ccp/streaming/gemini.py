"""
Streaming response handler for Google GenAI.
"""

import json
import uuid
from ..models import MessagesRequest
from ..config import client
from ..utils import get_logger

logger = get_logger(__name__)

async def handle_gemini_streaming(model_name: str, payload: dict, original_request: MessagesRequest):
    """Handle streaming responses from Google GenAI and convert to Anthropic SSE format."""
    try:
        # Start the streaming call using the new SDK pattern
        response_generator = await client.aio.models.generate_content_stream(
            model=model_name,
            contents=payload["contents"],
            generation_config=payload["generation_config"],
        )

        # Send message_start event
        message_id = f"msg_gemini_{uuid.uuid4().hex[:24]}"
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

        content_block_index = 0
        current_tool_call_id = None
        
        async for chunk in response_generator:
            if not chunk.candidates:
                continue

            part = chunk.candidates[0].content.parts[0]

            if part.text:
                if content_block_index == 0: # Assuming first block is always text
                    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                
                delta = {'type': 'text_delta', 'text': part.text}
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': content_block_index, 'delta': delta})}\n\n"

            if part.function_call:
                if current_tool_call_id is None:
                    # First chunk of a tool call
                    content_block_index += 1
                    current_tool_call_id = f"toolu_{uuid.uuid4().hex[:24]}"
                    tool_use_block = {
                        'type': 'tool_use',
                        'id': current_tool_call_id,
                        'name': part.function_call.name,
                        'input': {}
                    }
                    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': content_block_index, 'content_block': tool_use_block})}\n\n"

                # Stream the arguments
                delta = {'type': 'input_json_delta', 'partial_json': json.dumps(part.function_call.args)}
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': content_block_index, 'delta': delta})}\n\n"

        # Stop events
        yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': content_block_index})}\n\n"
        
        # Final message delta with stop reason and usage
        # Note: Gemini streaming response does not provide usage data per chunk, so we estimate or leave it at 0
        usage_data = chunk.usage_metadata if hasattr(chunk, 'usage_metadata') else {'prompt_token_count': 0, 'candidates_token_count': 0}
        stop_reason = "end_turn" # Default stop reason
        if chunk.candidates[0].finish_reason:
             stop_reason = "tool_use" if str(chunk.candidates[0].finish_reason) in ["TOOL_CODE", "FUNCTION_CALL"] else "end_turn"

        message_delta = {
            'type': 'message_delta',
            'delta': {'stop_reason': stop_reason, 'stop_sequence': None},
            'usage': {'output_tokens': usage_data.candidates_token_count}
        }
        yield f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n"
        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

    except Exception as e:
        logger.error(f"Error in Gemini streaming: {e}")
        # Yield an error message to the client
        error_data = {
            "type": "error",
            "error": {"type": "internal_server_error", "message": str(e)}
        }
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"