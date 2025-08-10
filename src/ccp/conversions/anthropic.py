"""
Conversion functions for Anthropic format (mostly passthrough, but useful for validation).
"""

from ..models import MessagesRequest, MessagesResponse
from ..utils import get_logger

logger = get_logger(__name__)

def convert_anthropic_to_anthropic(anthropic_request: MessagesRequest) -> dict:
    """Convert internal Anthropic request to official Anthropic API format."""
    # This is mostly a passthrough since we're already using Anthropic format
    # But we can clean up and validate the request here
    
    payload = {
        "model": anthropic_request.model.replace("anthropic/", ""),  # Remove prefix
        "max_tokens": anthropic_request.max_tokens,
        "messages": [],
        "stream": anthropic_request.stream,
    }
    
    # Add system message if present
    if anthropic_request.system:
        payload["system"] = anthropic_request.system
    
    # Convert messages
    for msg in anthropic_request.messages:
        message = {
            "role": msg.role,
            "content": msg.content
        }
        payload["messages"].append(message)
    
    # Add optional parameters
    if anthropic_request.temperature is not None:
        payload["temperature"] = anthropic_request.temperature
    if anthropic_request.top_p is not None:
        payload["top_p"] = anthropic_request.top_p
    if anthropic_request.top_k is not None:
        payload["top_k"] = anthropic_request.top_k
    if anthropic_request.stop_sequences:
        payload["stop_sequences"] = anthropic_request.stop_sequences
    if anthropic_request.tools:
        payload["tools"] = [tool.model_dump() if hasattr(tool, 'model_dump') else tool for tool in anthropic_request.tools]
    if anthropic_request.tool_choice:
        payload["tool_choice"] = anthropic_request.tool_choice
    if anthropic_request.metadata:
        payload["metadata"] = anthropic_request.metadata
    
    return payload

def convert_anthropic_to_anthropic_response(anthropic_response: dict, 
                                          original_request: MessagesRequest) -> MessagesResponse:
    """Convert official Anthropic API response to our internal format."""
    # This is also mostly a passthrough
    return MessagesResponse(**anthropic_response)