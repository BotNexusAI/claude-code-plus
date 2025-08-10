# GenAI Proxy Server Documentation

## Overview

This server acts as a proxy to enable the use of OpenAI and Google Gemini models through an API that is compatible with Anthropic's Messages API format. It allows you to send requests in a familiar format and have them automatically routed to the appropriate backend service, with request and response bodies translated as needed.

The primary goals of this proxy are:
- To provide a unified API interface for multiple AI providers.
- To simplify model selection by using abstract names that map to concrete models.
- To handle the complexities of tool use (function calling) translation between different provider schemas.

## Configuration

The server is configured using environment variables. Create a `.env` file in the root of the project with the following variables:

### Required Variables

- `OPENAI_API_KEY`: Your API key for OpenAI.
- `GEMINI_API_KEY`: Your API key for Google Gemini.

### Optional Variables

- `PREFERRED_PROVIDER`: Sets the default provider for abstract models. Can be `openai` or `google`. Defaults to `openai`.
- `BIG_MODEL`: The model to use when a request specifies a "big" abstract model (e.g., `claude-3-sonnet`). Defaults to `gpt-4.1`.
- `SMALL_MODEL`: The model to use when a request specifies a "small" abstract model (e.g., `claude-3-haiku`). Defaults to `gpt-4.1-mini`.

## API Endpoints

### `POST /v1/messages`

This is the main endpoint for generating content from a model. It accepts requests in the Anthropic Messages API format.

**Request Body:**

The request body should follow the structure of the Anthropic Messages API. See the `MessagesRequest` Pydantic model in [`server.py`](src/ccp/server.py:204) for the full schema.

**Example Request:**
```json
{
  "model": "claude-3-haiku-20240307",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "Hello, what is the weather in San Francisco?"
    }
  ],
  "stream": false
}
```

**Streaming:**

To receive a streaming response, set `"stream": true` in your request. The response will be a server-sent event (SSE) stream.

### `POST /v1/messages/count_tokens`

This endpoint calculates the number of tokens for a given set of messages for a specified model.

**Request Body:**

The request body is similar to the `/v1/messages` endpoint but does not require all parameters. See the `TokenCountRequest` model in [`server.py`](src/ccp/server.py:281).

**Example Request:**
```json
{
  "model": "claude-3-sonnet-20240229",
  "messages": [
    {
      "role": "user",
      "content": "How many tokens are in this message?"
    }
  ]
}
```

**Example Response:**
```json
{
  "input_tokens": 8
}
```

## Model Mapping

The proxy provides a flexible model mapping system to abstract away the specific model names of different providers.

- **Abstract Models**: You can use Anthropic model names like `claude-3-haiku-20240307` or `claude-3-sonnet-20240229`.
  - `haiku` models are mapped to the `SMALL_MODEL` environment variable.
  - `sonnet` models are mapped to the `BIG_MODEL` environment variable.
- **Provider Preference**: The `PREFERRED_PROVIDER` environment variable determines whether to use the OpenAI or Google Gemini equivalent for the abstract models.
- **Provider Prefixes**: You can also specify a provider directly by prefixing the model name:
  - `openai/gpt-4o`
  - `gemini/gemini-2.0-flash`

If no mapping rule applies and no prefix is provided, the server will attempt to use the model name as is, which may result in an error if the model is not recognized by the default provider.

## Function Calling (Tool Use)

The server supports function calling and translates the tool definitions between the Anthropic format and the format required by the target provider (OpenAI or Gemini).

When defining tools in your request, use the Anthropic format. The server will handle the conversion.

**Example Tool Definition in Request:**
```json
{
  "model": "claude-3-sonnet-20240229",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "What is the weather in London?"}],
  "tools": [
    {
      "name": "get_weather",
      "description": "Get the current weather for a specified location.",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g., San Francisco, CA"
          }
        },
        "required": ["location"]
      }
    }
  ]
}
```

The server will translate this to the appropriate format for the downstream model and will also translate the model's `tool_use` response back into the Anthropic format.

## Google Gemini Direct Integration

For models prefixed with `gemini/`, the server uses a direct integration with the `google-generativeai` Python SDK instead of relying on LiteLLM. This allows for more direct control and access to Gemini-specific features.

### Schema Cleaning

The Gemini API has stricter requirements for tool schemas than OpenAI. The proxy automatically cleans the `input_schema` for tools when targeting a Gemini model. The `clean_gemini_schema` function in [`server.py`](src/ccp/server.py:139) performs the following adjustments:
- Removes unsupported fields like `additionalProperties`, `default`, and `$schema`.
- Removes empty `description` fields.
- Removes unsupported `format` values for string types.

This ensures that tool definitions that work with Anthropic or OpenAI are compatible with Gemini.

## Running the Server

To run the server, use the following command:
```bash
uvicorn src.ccp.server:app --reload --host 0.0.0.0 --port 8082