# Anthropic API Proxy for Gemini & OpenAI Models (Fork) 🔄

**Use Anthropic clients (like Claude Code) with Gemini or OpenAI backends.** 🤝

This is a forked version of the original Anthropic API Proxy, with enhanced features for more flexible and powerful use. This proxy server lets you use Anthropic clients with Gemini or OpenAI models via LiteLLM. 🌉

![Anthropic API Proxy](pic.png)

## Key Features in This Fork ✨

*   **Advanced Model Mapping**: Automatically map Claude model names like `sonnet` and `haiku` to your preferred models from OpenAI (e.g., `gpt-4.1`) or Google (e.g., `gemini-2.5-pro-preview-06-25`).
*   **Enhanced Tool Support**: Full support for tool usage, with automatic schema cleaning for compatibility with Gemini models.
*   **Token Counting Endpoint**: A new `/v1/messages/count_tokens` endpoint to accurately count tokens for a given request.
*   **Interactive CLI**: A powerful command-line interface to initialize your configuration, start the server, and view your current setup.
*   **Robust Testing**: Includes a test suite to verify functionality.

## How It Works 🧩

This proxy works by:

1.  **Receiving requests** in Anthropic's API format 📥
2.  **Translating** the requests to the format of the target model (OpenAI or Gemini) via LiteLLM 🔄
3.  **Sending** the translated request to the target API 📤
4.  **Converting** the response back to Anthropic format 🔄
5.  **Returning** the formatted response to the client ✅

The proxy handles both streaming and non-streaming responses, maintaining compatibility with all Claude clients. 🌊

## Quick Start ⚡

### Prerequisites

- **Python**: Version 3.10 or higher.

### Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-fork-repo-url>
    cd <your-repo-directory>
    ```

2.  **Run the Initialization Wizard**:
    Use the interactive CLI to set up your configuration. This command will:
    - Prompt for your API keys (`OpenAI`, `Gemini`).
    - Ask for your preferred model provider and mappings.
    - Create a `.env` file to store your settings.
    - Offer to configure your shell (`.zshrc` or `.bashrc`) to make the proxy available automatically.

    ```bash
    python3 cli.py init
    ```

3.  **Start the Server**:
    Once initialization is complete, start the proxy server with a single command. This will handle creating a virtual environment, installing dependencies, and launching the server.

    ```bash
    python3 cli.py start
    ```
    The server will be running at `http://localhost:8082`.

### Using with Claude Code 🎮

1.  **Install Claude Code** (if you haven't already):
    ```bash
    npm install -g @anthropic-ai/claude-code
    ```

2.  **Connect to your proxy**:
    Point your Claude client to the local proxy server by setting the `ANTHROPIC_BASE_URL` environment variable.

    ```bash
    ANTHROPIC_BASE_URL=http://localhost:8082 claude
    ```

3.  **That's it!** Your Claude Code client will now communicate with your proxy, using the configured backend models. 🎯

## Configuration ⚙️

You can customize the proxy's behavior using environment variables, managed via the `cli.py init` command or by editing the `.env` file directly. Use `python3 cli.py config` to view your current setup.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | **(Required)** Your OpenAI API key. | - |
| `GEMINI_API_KEY` | **(Required)** Your Google AI Studio (Gemini) API key. | - |
| `PREFERRED_PROVIDER` | The primary backend for mapping models. Can be `openai` or `google`. | `openai` |
| `BIG_MODEL` | The model to map `sonnet` requests to. | `gpt-4.1` |
| `SMALL_MODEL` | The model to map `haiku` requests to. | `gpt-4.1-mini` |
| `ANTHROPIC_API_KEY`| Your Anthropic API key. Only needed if you intend to proxy requests *to* Anthropic models. | - |

**Example: Prefer Google Models**
```bash
export PREFERRED_PROVIDER="google"
export BIG_MODEL="gemini-2.5-pro-preview-06-25"
export SMALL_MODEL="gemini-2.0-flash"
```

## Running Tests 🧪

This project includes a test suite to ensure everything is working as expected. To run the tests, first make sure you have set up your `.env` file using `python3 cli.py init`. Then, run the following command:

```bash
python3 -m pytest
```

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request. 🎁
