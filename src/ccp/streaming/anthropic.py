"""
Streaming response handler for Anthropic API.
"""

import json
import httpx
from ..models import MessagesRequest
from ..config import ANTHROPIC_API_KEY
from ..utils import get_logger

logger = get_logger(__name__)

async def handle_anthropic_streaming(anthropic_payload: dict, original_request: MessagesRequest):
    """Handle streaming responses from Anthropic API (mostly passthrough)."""
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                json=anthropic_payload,
                headers=headers,
                timeout=120.0
            ) as response:
                
                if response.status_code != 200:
                    error_data = {
                        "type": "error",
                        "error": {"type": "api_error", "message": f"Anthropic API error: {response.status_code}"}
                    }
                    yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                    return
                
                # For Anthropic streaming, we can mostly just pass through the events
                # since we're already using the Anthropic format
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # Pass through the SSE events as-is
                    yield f"{line}\n"

    except Exception as e:
        logger.error(f"Error in Anthropic streaming: {e}")
        error_data = {
            "type": "error",
            "error": {"type": "internal_server_error", "message": str(e)}
        }
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"