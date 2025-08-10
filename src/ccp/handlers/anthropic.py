"""
Direct Anthropic API handlers.
"""

import time
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from ..models import MessagesRequest, TokenCountRequest, TokenCountResponse
from ..conversions.anthropic import convert_anthropic_to_anthropic, convert_anthropic_to_anthropic_response
from ..streaming.anthropic import handle_anthropic_streaming
from ..config import ANTHROPIC_API_KEY
from ..utils import get_logger, log_request_beautifully

logger = get_logger(__name__)

async def handle_anthropic_request(request: MessagesRequest, raw_request: Request):
    """Handle requests for Anthropic models using direct API calls."""
    try:
        logger.info(f"➡️ Handling direct Anthropic request for model: {request.model}")
        
        # Convert the request to official Anthropic format
        anthropic_payload = convert_anthropic_to_anthropic(request)
        
        # Get original model for display
        original_model = request.original_model or request.model
        display_model = original_model.split("/")[-1] if "/" in original_model else original_model
        
        # Log the request
        num_tools = len(request.tools) if request.tools else 0
        log_request_beautifully(
            "POST", 
            raw_request.url.path, 
            display_model, 
            anthropic_payload["model"],
            len(anthropic_payload["messages"]),
            num_tools,
            200
        )
        
        if request.stream:
            # Handle streaming
            return StreamingResponse(
                handle_anthropic_streaming(anthropic_payload, request),
                media_type="text/event-stream"
            )
        else:
            # Handle non-streaming
            start_time = time.time()
            
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=anthropic_payload,
                    headers=headers,
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Anthropic API error: {response.text}"
                    )
                
                anthropic_response = response.json()
            
            logger.info(f"✅ Anthropic response received in {time.time() - start_time:.2f}s")
            
            # Convert back to our internal format (mostly passthrough)
            response_obj = convert_anthropic_to_anthropic_response(anthropic_response, request)
            
            return response_obj

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"🔥 Error in handle_anthropic_request: {str(e)}\n{error_traceback}"
        logger.error(error_message)

        status_code = 500
        detail = f"An unexpected error occurred: {str(e)}"

        if isinstance(e, httpx.HTTPError):
            status_code = 502
            detail = f"Anthropic API connection error: {str(e)}"

        raise HTTPException(status_code=status_code, detail=detail)

async def handle_anthropic_token_count_request(request: TokenCountRequest, raw_request: Request):
    """Handle token counting for Anthropic models."""
    try:
        # Convert to a full MessagesRequest for processing
        full_request = MessagesRequest(
            model=request.model,
            max_tokens=100,  # Arbitrary value not used for token counting
            messages=request.messages,
            system=request.system,
            tools=request.tools,
            tool_choice=request.tool_choice,
            thinking=request.thinking
        )
        
        # Convert to Anthropic format
        anthropic_payload = convert_anthropic_to_anthropic(full_request)
        
        # Get original model for display
        original_model = request.original_model or request.model
        display_model = original_model.split("/")[-1] if "/" in original_model else original_model
        
        # Log the request
        num_tools = len(request.tools) if request.tools else 0
        log_request_beautifully(
            "POST",
            raw_request.url.path,
            display_model,
            anthropic_payload["model"],
            len(anthropic_payload["messages"]),
            num_tools,
            200
        )
        
        # Use the official Anthropic token counting endpoint if available
        # For now, provide a simple estimation
        total_chars = 0
        for msg in anthropic_payload["messages"]:
            if isinstance(msg.get("content"), str):
                total_chars += len(msg["content"])
            elif isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        total_chars += len(block.get("text", ""))
        
        if anthropic_payload.get("system"):
            if isinstance(anthropic_payload["system"], str):
                total_chars += len(anthropic_payload["system"])
        
        estimated_tokens = total_chars // 4  # Rough estimation: 4 chars per token
        
        return TokenCountResponse(input_tokens=estimated_tokens)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error counting tokens for Anthropic: {str(e)}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error counting tokens: {str(e)}")