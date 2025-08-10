"""
Main FastAPI server using modular handlers (no LiteLLM).
"""

from fastapi import FastAPI, Request
import uvicorn
import sys

from .models import MessagesRequest, TokenCountRequest
from .handlers.gemini import handle_gemini_request
from .handlers.openai import handle_openai_request, handle_openai_token_count_request
from .handlers.anthropic import handle_anthropic_request, handle_anthropic_token_count_request
from .utils import get_logger
from .config import setup_config

logger = get_logger(__name__)

app = FastAPI()

# Initialize configuration
setup_config()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Get request details
    method = request.method
    path = request.url.path
    
    # Log only basic request details at debug level
    logger.debug(f"Request: {method} {path}")
    
    # Process the request and get the response
    response = await call_next(request)
    
    return response

@app.post("/v1/messages")
async def create_message(
    request: MessagesRequest,
    raw_request: Request
):
    """Main endpoint for message creation - routes to appropriate handler."""
    try:
        # Route based on model prefix
        if request.model.startswith("gemini/"):
            return await handle_gemini_request(request, raw_request)
        elif request.model.startswith("openai/"):
            return await handle_openai_request(request, raw_request)
        elif request.model.startswith("anthropic/"):
            return await handle_anthropic_request(request, raw_request)
        else:
            # Default routing based on model name patterns
            # This handles cases where no prefix is provided
            logger.warning(f"No explicit provider prefix for model: {request.model}")
            
            # Try to infer provider from model name
            model_lower = request.model.lower()
            if any(name in model_lower for name in ["gpt", "o1", "chatgpt"]):
                logger.info(f"Routing {request.model} to OpenAI based on model name")
                return await handle_openai_request(request, raw_request)
            elif any(name in model_lower for name in ["gemini"]):
                logger.info(f"Routing {request.model} to Gemini based on model name")
                return await handle_gemini_request(request, raw_request)
            elif any(name in model_lower for name in ["claude", "haiku", "sonnet", "opus"]):
                logger.info(f"Routing {request.model} to Anthropic based on model name")
                return await handle_anthropic_request(request, raw_request)
            else:
                # Final fallback - use the mapped model's prefix
                if request.model.startswith("gemini/"):
                    return await handle_gemini_request(request, raw_request)
                elif request.model.startswith("openai/"):
                    return await handle_openai_request(request, raw_request)
                else:
                    # Default to Anthropic if we can't determine
                    logger.warning(f"Defaulting to Anthropic for unknown model: {request.model}")
                    return await handle_anthropic_request(request, raw_request)
                
    except Exception as e:
        logger.error(f"Error in create_message: {str(e)}")
        raise

@app.post("/v1/messages/count_tokens")
async def count_tokens(
    request: TokenCountRequest,
    raw_request: Request
):
    """Token counting endpoint - routes to appropriate handler."""
    try:
        # Route based on model prefix
        if request.model.startswith("gemini/"):
            # For now, use a simple estimation for Gemini
            # In production, you might want a dedicated Gemini token counter
            return await handle_openai_token_count_request(request, raw_request)
        elif request.model.startswith("openai/"):
            return await handle_openai_token_count_request(request, raw_request)
        elif request.model.startswith("anthropic/"):
            return await handle_anthropic_token_count_request(request, raw_request)
        else:
            # Default routing based on model name patterns
            model_lower = request.model.lower()
            if any(name in model_lower for name in ["gpt", "o1", "chatgpt", "gemini"]):
                return await handle_openai_token_count_request(request, raw_request)
            else:
                return await handle_anthropic_token_count_request(request, raw_request)
                
    except Exception as e:
        logger.error(f"Error in count_tokens: {str(e)}")
        raise

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Claude Code Plus: Direct API proxy for Anthropic, OpenAI & Gemini models (no LiteLLM).",
        "version": "2.0.0",
        "features": ["direct_apis", "no_litellm", "modular_handlers"]
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Run with: uvicorn server:app --reload --host 0.0.0.0 --port 8082")
        sys.exit(0)
    
    # Configure uvicorn to run with minimal logs
    uvicorn.run(app, host="0.0.0.0", port=8082, log_level="error")