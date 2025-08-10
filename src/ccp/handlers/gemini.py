"""
Handlers for direct Google GenAI requests.
"""

import time
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from google.api_core import exceptions as google_exceptions
from ..models import MessagesRequest
from ..conversions.genai import convert_anthropic_to_genai_payload, convert_genai_to_anthropic_response
from ..streaming.gemini import handle_gemini_streaming
from ..config import client
from ..utils import get_logger

logger = get_logger(__name__)

async def handle_gemini_request(request: MessagesRequest, raw_request: Request):
    """Handles requests targeted at Google Gemini models using the direct SDK."""
    try:
        logger.info(f"➡️ Handling direct Gemini request for model: {request.model}")
        
        # 1. Convert the incoming Anthropic request to a GenAI payload
        payload = convert_anthropic_to_genai_payload(request)
        
        # 2. Extract the actual model name (e.g., "gemini-1.5-pro-latest")
        model_name = request.model.replace("gemini/", "")

        # 3. Handle streaming or non-streaming requests
        if request.stream:
            # Use the streaming handler
            return StreamingResponse(
                handle_gemini_streaming(model_name, payload, request),
                media_type="text/event-stream"
            )
        else:
            # Use the standard generate_content method with the new SDK pattern
            start_time = time.time()
            
            # Make the API call using the async client
            genai_response = await client.aio.models.generate_content(
                model=model_name,
                contents=payload["contents"],
                generation_config=payload["generation_config"],
            )
            
            logger.info(f"✅ Gemini response received in {time.time() - start_time:.2f}s")
            
            # 4. Convert the GenAI response back to the Anthropic format
            anthropic_response = convert_genai_to_anthropic_response(genai_response, request)
            
            return anthropic_response

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        error_message = f"🔥 Error in handle_gemini_request: {str(e)}\n{error_traceback}"
        logger.error(error_message)

        status_code = 500
        detail = f"An unexpected error occurred: {str(e)}"

        if isinstance(e, google_exceptions.GoogleAPICallError):
            status_code = e.code or 500
            detail = f"Google API Error: {e.message}"
        elif isinstance(e, NotImplementedError):
             status_code = 501
             detail = "This feature is not yet implemented for Gemini direct integration."

        raise HTTPException(status_code=status_code, detail=detail)