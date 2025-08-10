# Migration Plan: From LiteLLM to Direct Google GenAI SDK

This document provides a comprehensive plan for refactoring the Claude Code Plus proxy. The primary goal is to replace the LiteLLM abstraction for Google Gemini models with a direct integration using the official `google-genai` Python SDK. This will enhance stability, improve debuggability, and give us fine-grained control over the API interactions.

LiteLLM will be retained as a compatibility layer for handling requests to OpenAI models.

---

## Phase 1: Setup and Configuration

### 1.1. Dependency Management (`pyproject.toml`)

The first step is to update the project's dependencies to include the necessary Google GenAI library.

-   **Action:** Modify the `dependencies` list in `pyproject.toml`.
-   **Remove:** `google-generativeai` (if present from previous incorrect attempts).
-   **Add:** `google-genai`
-   **Rationale:** The `google-genai` package provides the `google.genai` module, which is the current, supported SDK for the Gemini API.

**Example `pyproject.toml` change:**
```toml
[project]
# ...
dependencies = [
    "fastapi[standard]>=0.115.11",
    "uvicorn>=0.34.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "litellm (>=1.75.5.post1,<2.0.0)",
    "google-genai", # Correct package
    "typer[all]>=0.9.0",
    "python-dotenv>=1.0.0",
    "mcp[cli]>=0.4.0",
]
# ...
```

### 1.2. Install New Dependencies

After updating `pyproject.toml`, the new dependency must be installed in the local environment.

-   **Action:** Run the installation command.
-   **Command:** `pip install -e .`
-   **Verification:** Ensure the command completes successfully and the `google-genai` package is available in the virtual environment.

### 1.3. SDK Initialization (`src/ccp/server.py`)

The `google.genai` client must be configured and initialized at application startup.

-   **Action:** Add initialization logic to `src/ccp/server.py`.
-   **Details:**
    -   Import the required modules: `from google import genai` and `from google.genai import types`.
    -   After loading environment variables, configure the `genai` module with the `GEMINI_API_KEY`.
    -   Create a global `client` instance to be used for making API calls.
    -   Include robust error handling in case the key is missing or invalid.

**Example `src/ccp/server.py` change:**
```python
# ... other imports
from google import genai
from google.genai import types
# ...

# Global client instance
client = None

# After loading environment variables
if not GEMINI_API_KEY:
    logger.error("FATAL: GEMINI_API_KEY environment variable not set.")
    sys.exit(1)
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        client = genai.Client()
        logger.info("✅ Google GenAI client configured successfully.")
    except Exception as e:
        logger.error(f"🔥 Failed to configure Google GenAI client: {e}")
        sys.exit(1)
```

---

## Phase 2: Refactoring the Core Application Logic

### 2.1. Main Request Routing (`create_message` in `src/ccp/server.py`)

The core `create_message` endpoint needs to be refactored to delegate requests to the appropriate handler based on the model provider.

-   **Action:** Introduce a branching logic at the beginning of the `create_message` function.
-   **Logic:**
    -   If `request.model.startswith("gemini/")`, call a new `handle_gemini_request(request, raw_request)` function and return its result.
    -   Otherwise (for `openai/` or `anthropic/` models), proceed with the existing LiteLLM-based workflow.

**Example `create_message` structure:**
```python
@app.post("/v1/messages")
async def create_message(request: MessagesRequest, raw_request: Request):
    try:
        # New branching logic
        if request.model.startswith("gemini/"):
            return await handle_gemini_request(request, raw_request)

        # --- Existing LiteLLM logic for OpenAI/Anthropic follows ---
        # ...
        litellm_request = convert_anthropic_to_litellm(request)
        # ...
    except Exception as e:
        # ...
```

### 2.2. Placeholder for New Gemini Handler

-   **Action:** Create the placeholder async function `handle_gemini_request` to avoid `NameError`. This function will be fully implemented in the next phase.

**Example placeholder:**
```python
async def handle_gemini_request(request: MessagesRequest, raw_request: Request):
    # TODO: Implement the full Gemini request lifecycle
    raise NotImplementedError("Gemini direct integration is not yet fully implemented.")
```

---

## Phase 3: Implementing the Gemini Direct Integration

This is the most intensive phase, involving the creation of new conversion and handling functions specifically for the `google-genai` SDK.

### 3.1. Anthropic-to-GenAI Request Conversion

-   **Action:** Create a new function `convert_anthropic_to_genai_payload(request: MessagesRequest) -> dict`.
-   **Responsibilities:**
    -   **`contents`:** Translate the `messages` list from the Anthropic request into the `contents` list required by the `google.genai` SDK.
        -   Map roles: `user` -> `user`, `assistant` -> `model`.
        -   The Anthropic `system` prompt should be inserted as the first message in the `contents` list. The Gemini API uses the first `user` message as a system instruction if it's followed by a `model` message.
        -   Handle complex content blocks. An assistant message with `tool_use` blocks must be converted into a `model` role part containing `tool_call` objects. A user message with `tool_result` blocks must be converted into a `user` role part containing `function_response` objects.
    -   **`tools`:** Convert the Anthropic `tools` schema into a list of `types.Tool` objects. This requires careful mapping of the JSON schema for each function declaration.
    -   **`tool_config`:** Translate Anthropic's `tool_choice` parameter into Gemini's `tool_config`. For example, `{"type": "any"}` becomes `{"function_calling_config": {"mode": "ANY"}}`.
    -   **`generation_config`:** Map parameters like `max_tokens`, `temperature`, `top_p`, `top_k`, and `stop_sequences` into a `types.GenerateContentConfig` object. This same object will also hold the `tool_config` and `tools` list.

### 3.2. GenAI-to-Anthropic Response Conversion

-   **Action:** Create a new function `convert_genai_to_anthropic_response(genai_response, original_request: MessagesRequest) -> MessagesResponse`.
-   **Responsibilities:**
    -   **`content`:** Extract the response content.
        -   If the response contains text, create a `text` content block.
        -   If the response contains a `function_call` in its parts, translate it into an Anthropic `tool_use` content block. The `function_call.name` and `function_call.args` must be mapped correctly.
    -   **`stop_reason`:** Map Gemini's `finish_reason` (e.g., `TOOL_CALL`, `MAX_TOKENS`) to the corresponding Anthropic `stop_reason`.
    -   **`usage`:** Extract token counts from `genai_response.usage_metadata` (`prompt_token_count`, `candidates_token_count`) and map them to the Anthropic `usage` object.

### 3.3. Streaming Handler for Gemini

-   **Action:** Create a new async generator `handle_gemini_streaming(model_name: str, payload: dict, original_request: MessagesRequest)`.
-   **Responsibilities:**
    -   Use the global `client` to call `client.models.generate_content_stream(model=model_name, contents=payload["contents"], ...)`.
    -   Iterate over the streamed chunks from the SDK.
    -   Translate each chunk into the correct Anthropic Server-Sent Event (SSE) format. This requires handling different chunk types:
        -   Text deltas -> `content_block_delta` with `text_delta`.
        -   Function call deltas -> `content_block_delta` with `input_json_delta`.
        -   Start of content/tool blocks -> `content_block_start`.
        -   End of content/tool blocks -> `content_block_stop`.
    -   Send the final `message_stop` event with usage data.

### 3.4. Final Implementation of `handle_gemini_request`

-   **Action:** Fully implement the `handle_gemini_request` function.
-   **Logic:**
    1.  Log the incoming request details.
    2.  Call `convert_anthropic_to_genai_payload` to get the correctly formatted payload dictionary.
    3.  Extract the model name from the request, e.g., `model_name = request.model.replace("gemini/", "")`.
    4.  Check if `request.stream` is `True`.
        -   If streaming, `await` and `return` a `StreamingResponse` using the `handle_gemini_streaming` generator. The generator will call `client.models.generate_content_stream(model=model_name, ...)`.
        -   If not streaming, call `await client.models.generate_content(model=model_name, ...)` directly, pass the result to `convert_genai_to_anthropic_response`, and return the final `MessagesResponse`.
    5.  Wrap the entire process in robust `try...except` blocks to catch and log specific `google.api_core.exceptions` and return appropriate HTTP error responses.

---

By following this detailed plan, we can systematically replace the LiteLLM layer for Gemini with a direct, more reliable SDK integration, addressing the root cause of the instability while maintaining support for other model providers.
