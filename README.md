# 🚀 Claude Code Plus: Use Any Model with Your Favorite Anthropic Tools

**Unlock the full potential of your development workflow. Use Anthropic clients like Claude Code with any backend model from OpenAI, Google, or Anthropic using direct API integrations (no LiteLLM dependency).**

[![Test Suite](https://img.shields.io/badge/tests-passing-green.svg)](https://github.com/BotNexusAI/claude-code-plus)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## ✨ Why Use Claude Code Plus?

Claude Code Plus acts as a high-performance, modular translation proxy, allowing you to:

- **Break Vendor Lock-in:** Use your favorite Anthropic-compatible clients (like the Claude Code CLI) with more powerful or cost-effective models from OpenAI, Google, and Anthropic.
- **Access the Best Models:** Seamlessly switch to the latest models like GPT-4.1, Gemini 2.5 Pro, or Claude 3.5 Sonnet without changing your client-side workflow.
- **Native Performance:** Direct API integrations eliminate middleware overhead for faster responses and native streaming.
- **Modular Architecture:** Clean, maintainable codebase with separated concerns for each provider.
- **Full Tool Support:** Enhanced compatibility for tool usage, including automatic schema cleaning for Gemini models.
- **Easy Setup:** Get started in minutes with an interactive command-line wizard.

---

## 🧩 How It Works

The modular proxy server intercepts requests from your Anthropic client, routes them to specialized handlers for direct API communication, and translates responses back into the Anthropic format.

```mermaid
graph TD
    A[Anthropic Client e.g., Claude Code] -- Anthropic API Request --> B{Claude Code Plus Proxy};
    B -- Gemini Request --> C[Google GenAI SDK];
    B -- OpenAI Request --> D[OpenAI API];
    B -- Anthropic Request --> E[Anthropic API];
    C -- Gemini Response --> B;
    D -- OpenAI Response --> B;
    E -- Anthropic Response --> B;
    B -- Anthropic API Response --> A;

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#4285f4,stroke:#333,stroke-width:2px
    style D fill:#00d4aa,stroke:#333,stroke-width:2px
    style E fill:#d97706,stroke:#333,stroke-width:2px
```

### 🏗️ **Architecture Highlights**
- **Direct APIs:** No middleware dependencies - direct communication with each provider
- **Modular Design:** Separate handlers for Gemini, OpenAI, and Anthropic
- **Provider-Specific Optimizations:** Each handler leverages native API features
- **Unified Interface:** All providers appear as Anthropic-compatible endpoints

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+

### Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/BotNexusAI/claude-code-plus.git
    cd claude-code-plus
    ```

2.  **Install Dependencies:**
    This will also make the `ccp` command available in your shell.
    ```bash
    pip install -e .
    ```

3.  **Run the Initialization Wizard:**
    This interactive command sets up your API keys and model preferences in a `.env` file.
    ```bash
    ccp init
    ```

4.  **Start the Server:**
    By default, the server runs in the background.
    ```bash
    ccp start
    ```
    Your proxy is now running at `http://localhost:PORT` (e.g., `http://localhost:8082` by default).

---

## 🎮 Using with Claude Code

1.  **Install Claude Code:**
    ```bash
    npm install -g @anthropic-ai/claude-code
    ```

2.  **Connect to Your Proxy:**
    The `ccp init` command (Step 3 in Quick Start) will offer to automatically add the `ANTHROPIC_BASE_URL` to your shell configuration file (`.zshrc` or `.bashrc`). **This is the recommended method.**

    If you choose to set it manually, you can do so with the following command:
    ```bash
    export ANTHROPIC_BASE_URL=http://localhost:PORT
    ```
    (Replace `PORT` with the port you configured during `ccp init`.)
    *Tip: If you set this manually, add the line to your `.zshrc` or `.bashrc` file to make the setting permanent.*

3.  **Done!**
    After restarting your shell (or running `source ~/.zshrc`), you can use Claude Code as you normally would, and it will route requests through your configured backend model.
    ```bash
    claude "Hello, world!"
    ```

---

## 💻 CLI Commands

Manage the proxy with these simple commands:

| Command | Description |
| :--- | :--- |
| `ccp init` | 🧙‍♂️ Run the interactive wizard to set up API keys and model preferences. |
| `ccp start` | ▶️ Start the server. Use `-f` or `--foreground` to run in the foreground. |
| `ccp stop` | ⏹️ Stop the background server process. |
| `ccp logs` | 📄 Tail the log file (`.ccp.log`) for the background server. |
| `ccp config`| ⚙️ Display the current configuration from your `.env` file. |

---

## 🛠️ Configuration & Model Mapping

Customize the proxy's behavior by editing the `.env` file created by `ccp init`.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | **(Required)** Your OpenAI API key. | - |
| `GEMINI_API_KEY` | **(Required)** Your Google AI Studio (Gemini) API key. | - |
| `PORT` | The port for the proxy server to run on. | `8082` |
| `PREFERRED_PROVIDER`| The primary backend for mapping models (`openai` or `google`). | `openai` |
| `BIG_MODEL` | The model to map `sonnet` requests to. | `gpt-4.1` |
| `SMALL_MODEL` | The model to map `haiku` requests to. | `gpt-4.1-mini` |
| `ANTHROPIC_API_KEY`| Your Anthropic API key (only if proxying *to* Anthropic). | - |

**Example: Prefer Google Models**
```bash
# .env file
PREFERRED_PROVIDER="google"
BIG_MODEL="gemini-2.5-pro"
SMALL_MODEL="gemini-2.5-flash"
```

The proxy automatically prefixes models with `openai/`, `gemini/`, or `anthropic/` based on your `PREFERRED_PROVIDER`.

---

## 🧪 Running Tests

To run the test suite, first set up your `.env` file with `ccp init`, then run:

```bash
pytest
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
