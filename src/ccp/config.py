"""
Configuration and environment setup.
"""

import os
import sys
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Model Configuration
PREFERRED_PROVIDER = os.environ.get("PREFERRED_PROVIDER", "openai").lower()
BIG_MODEL = os.environ.get("BIG_MODEL", "gpt-4.1")
SMALL_MODEL = os.environ.get("SMALL_MODEL", "gpt-4.1-mini")

# Global client instance for Google GenAI
client = None

def validate_api_keys():
    """Validate that required API keys are set."""
    from .utils import get_logger
    logger = get_logger(__name__)
    
    if not OPENAI_API_KEY:
        logger.error("FATAL: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)
    if not GEMINI_API_KEY:
        logger.error("FATAL: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

def initialize_genai_client():
    """Initialize the Google GenAI client."""
    global client
    from .utils import get_logger
    logger = get_logger(__name__)
    
    try:
        # The client automatically uses the API key from the environment variables.
        client = genai.Client()
        logger.info("✅ Google GenAI client configured successfully.")
    except Exception as e:
        logger.error(f"🔥 Failed to configure Google GenAI client: {e}")
        sys.exit(1)

def setup_config():
    """Initialize configuration and validate setup."""
    validate_api_keys()
    initialize_genai_client()

# Configuration will be initialized explicitly by server.py