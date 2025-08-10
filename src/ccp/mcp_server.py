import os
import sys
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import litellm

# Load environment variables from .env file
load_dotenv()

# --- Logging Setup ---
# Per MCP guidelines, log to stderr for stdio transport.
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(stream=sys.stderr, level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("ccp_mcp_server")


# --- MCP Server Setup ---
mcp = FastMCP("ccp", log_level=log_level_str)

# --- Environment Variable Validation ---
# The proxy server will validate these, but we can check for the port.
PORT = os.environ.get("PORT")
if not PORT:
    log.warning("PORT environment variable not set. Using default 8082.")

# --- MCP Tool Implementation ---
@mcp.tool(name="ccp")
async def run_ccp_proxy(prompt: str, model_alias: str = 'sonnet', system_prompt: str = None) -> str:
    """
    Offloads agentic work to a powerful LLM (like Claude) via the ccp proxy.

    Args:
        prompt: The main text prompt to send to the language model.
        model_alias: The model alias to use ('sonnet' for the big model, 'haiku' for the small model).
        system_prompt: An optional system message to guide the model's behavior.
    """
    try:
        # Get the port from environment variables, with a default
        port = os.environ.get("PORT", "8082")
        api_base = f"http://localhost:{port}"
        
        log.info(f"Offloading prompt to '{model_alias}' via proxy at {api_base}")

        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        # This call goes to the proxy server, which then maps the model
        response = await litellm.acompletion(
            model=model_alias,
            messages=messages,
            api_base=api_base,
            # The proxy needs an API key, but litellm sends a dummy one
            # if it's not set. The proxy should be configured to ignore it.
            api_key="dummy-key"
        )
        
        # Extract the response content
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        return "Error: No content in response."

    except Exception as e:
        log.error(f"Error running ccp proxy tool: {e}")
        return f"An error occurred: {str(e)}"

# --- Main Execution ---
if __name__ == "__main__":
    mcp.run()
