"""
Direct OpenAI API handlers (no LiteLLM).
"""

import time
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from ..models import MessagesRequest, TokenCountRequest, TokenCountResponse
from ..conversions.openai import convert_anthropic_to_openai, convert_openai_to_anthropic
from ..streaming.openai import handle_openai_streaming
from ..config import OPENAI_API_KEY
from ..utils import get_logger, log_request_beautifully

logger = get_logger(__name__)

async def handle_openai_request(request: MessagesRequest, raw_request: Request):
    """Handle requests for OpenAI models using direct API calls."""
    try:
        logger.info(f"➡️ Handling direct OpenAI request for model: {request.model}")
        
        # Convert the request to OpenAI format
        openai_payload = convert_anthropic_to_openai(request)
        
        # Get original model for display
        original_model = request.original_model or request.model
        display_model = original_model.split("/")[-1] if "/" in original_model else original_model
        
        # Log the request
        num_tools = len(request.tools) if request.tools else 0
        log_request_beautifully(
            "POST", 
            raw_request.url.path, 
            display_model, 
            openai_payload["model"],
            len(openai_payload["messages"]),
            num_tools,
            200
        )
        
        if request.stream:
            # Handle streaming
            return StreamingResponse(
                handle_openai_streaming(openai_payload, request),
                media_type="text/event-stream"
            )
        else:
            # Handle non-streaming
            start_time = time.time()
            
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=openai_payload,
                    headers=headers,
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenAI API error: {response.text}"
                    )
                
                openai_response = response.json()
            
            logger.info(f"✅ OpenAI response received in {time.time() - start_time:.2f}s")
            
            # Convert back to Anthropic format
            anthropic_response = convert_openai_to_anthropic(openai_response, request)
            
            return anthropic_response

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"🔥 Error in handle_openai_request: {str(e)}\n{error_traceback}"
        logger.error(error_message)

        status_code = 500
        detail = f"An unexpected error occurred: {str(e)}"

        if isinstance(e, httpx.HTTPError):
            status_code = 502
            detail = f"OpenAI API connection error: {str(e)}"

        raise HTTPException(status_code=status_code, detail=detail)

async def handle_openai_token_count_request(request: TokenCountRequest, raw_request: Request):
    """Handle token counting for OpenAI models."""
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
        
        # Convert to OpenAI format
        openai_payload = convert_anthropic_to_openai(full_request)
        
        # Get original model for display
        original_model = request.original_model or request.model
        display_model = original_model.split("/")[-1] if "/" in original_model else original_model
        
        # Log the request
        num_tools = len(request.tools) if request.tools else 0
        log_request_beautifully(
            "POST",
            raw_request.url.path,
            display_model,
            openai_payload["model"],
            len(openai_payload["messages"]),
            num_tools,
            200
        )
        
        # For now, provide a simple estimation
        # In a production system, you might want to use tiktoken or similar
        total_chars = sum(
            len(str(msg.get("content", ""))) for msg in openai_payload["messages"]
        )
        estimated_tokens = total_chars // 4  # Rough estimation: 4 chars per token
        
        return TokenCountResponse(input_tokens=estimated_tokens)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error counting tokens for OpenAI: {str(e)}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error counting tokens: {str(e)}")