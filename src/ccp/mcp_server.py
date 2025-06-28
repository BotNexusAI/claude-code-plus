import os
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import litellm

# Load environment variables from .env file
load_dotenv()

# --- MCP Server Setup ---
# Read and uppercase the log level to ensure it's valid.
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
mcp = FastMCP("claude-code-plus", log_level=log_level)

# --- Environment Variable Validation ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not OPENAI_API_KEY:
    mcp.log.error("FATAL: OPENAI_API_KEY environment variable not set.")
    sys.exit(1)
if not GEMINI_API_KEY:
    mcp.log.error("FATAL: GEMINI_API_KEY environment variable not set.")
    sys.exit(1)

# --- Model Mapping ---
PREFERRED_PROVIDER = os.environ.get("PREFERRED_PROVIDER", "openai").lower()
BIG_MODEL = os.environ.get("BIG_MODEL", "gpt-4.1")
SMALL_MODEL = os.environ.get("SMALL_MODEL", "gpt-4.1-mini")

def get_mapped_model(model_alias: str) -> str:
    """Maps an alias to a full model name based on provider preference."""
    if 'haiku' in model_alias.lower():
        return f"gemini/{SMALL_MODEL}" if PREFERRED_PROVIDER == "google" else f"openai/{SMALL_MODEL}"
    elif 'sonnet' in model_alias.lower():
        return f"gemini/{BIG_MODEL}" if PREFERRED_PROVIDER == "google" else f"openai/{BIG_MODEL}"
    # Default to the alias itself if no mapping is found
    return model_alias

# --- MCP Tool Implementation ---
@mcp.tool()
async def run_model(prompt: str, model_alias: str = 'sonnet', system_prompt: str = None) -> str:
    """
    Runs a prompt against a specified model alias ('sonnet' or 'haiku').

    Args:
        prompt: The main text prompt to send to the language model.
        model_alias: The model alias to use ('sonnet' for the big model, 'haiku' for the small model).
        system_prompt: An optional system message to guide the model's behavior.
    """
    try:
        model_name = get_mapped_model(model_alias)
        mcp.log.info(f"Running model '{model_name}' for alias '{model_alias}'")

        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        response = await litellm.acompletion(
            model=model_name,
            messages=messages,
        )
        
        # Extract the response content
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        return "Error: No content in response."

    except Exception as e:
        mcp.log.error(f"Error running model {model_alias}: {e}")
        return f"An error occurred: {str(e)}"

# --- Main Execution ---
if __name__ == "__main__":
    mcp.run()
