# OpenAI Compatible API

Standard API endpoints and formats for local LLM inference.

## Why OpenAI Compatibility?

- **Ecosystem support** - Thousands of tools and libraries work automatically
- **No code changes** - Switch between providers by changing base URL
- **Familiar interface** - Well-documented, widely understood API
- **Future-proof** - Industry standard for LLM APIs

## Endpoint Reference

### Chat Completions

Primary endpoint for conversational AI:

```
POST /v1/chat/completions
```

#### Request

```json
{
  "model": "llama3.3:70b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "stream": false
}
```

#### Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1706789012,
  "model": "llama3.3:70b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

### Completions (Legacy)

Text completion without chat format:

```
POST /v1/completions
```

#### Request

```json
{
  "model": "llama3.3:70b",
  "prompt": "The capital of France is",
  "max_tokens": 20,
  "temperature": 0.3
}
```

### List Models

```
GET /v1/models
```

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama3.3:70b",
      "object": "model",
      "created": 1706789012,
      "owned_by": "library"
    }
  ]
}
```

### Embeddings

```
POST /v1/embeddings
```

#### Request

```json
{
  "model": "nomic-embed-text",
  "input": "The quick brown fox"
}
```

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.123, -0.456, ...],
      "index": 0
    }
  ],
  "model": "nomic-embed-text",
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5
  }
}
```

## Request Parameters

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | Required | Model identifier |
| `temperature` | float | 0.7 | Randomness (0-2) |
| `max_tokens` | int | varies | Maximum response length |
| `top_p` | float | 1.0 | Nucleus sampling |
| `stream` | bool | false | Enable streaming |
| `stop` | array | null | Stop sequences |

### Chat-Specific Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `messages` | array | Conversation history |
| `presence_penalty` | float | Reduce repetition |
| `frequency_penalty` | float | Reduce common tokens |

### Message Format

```json
{
  "messages": [
    {"role": "system", "content": "System prompt..."},
    {"role": "user", "content": "User message..."},
    {"role": "assistant", "content": "Previous response..."},
    {"role": "user", "content": "Follow-up..."}
  ]
}
```

Roles:
- `system` - Instructions for the model
- `user` - Human input
- `assistant` - Model responses (for context)

## Streaming

### Enable Streaming

```json
{
  "model": "llama3.3:70b",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}
```

### Response Format (SSE)

```
data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"},"index":0}]}

data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"delta":{"content":"!"},"index":0}]}

data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"delta":{},"finish_reason":"stop","index":0}]}

data: [DONE]
```

### Python Streaming Example

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="x")

stream = client.chat.completions.create(
    model="llama3.3:70b",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Backend-Specific Extensions

### Ollama Extensions

Ollama's native API at `/api/*`:

```bash
# Pull model
curl -X POST http://localhost:11434/api/pull \
  -d '{"name": "llama3.3:70b"}'

# Show model info
curl -X POST http://localhost:11434/api/show \
  -d '{"name": "llama3.3:70b"}'

# Running models
curl http://localhost:11434/api/ps
```

### llama.cpp Extensions

Additional endpoints:

```bash
# Health check
curl http://localhost:8080/health

# Server props
curl http://localhost:8080/props

# Tokenize
curl -X POST http://localhost:8080/tokenize \
  -d '{"content": "Hello world"}'
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Model not found",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

### Common Errors

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad request | Check request format |
| 401 | Unauthorized | Add API key (even if ignored) |
| 404 | Model not found | Pull model first |
| 503 | Model loading | Wait and retry |

### Retry Logic

```python
from openai import OpenAI
from tenacity import retry, wait_exponential

client = OpenAI(base_url="http://localhost:11434/v1", api_key="x")

@retry(wait=wait_exponential(min=1, max=10))
def chat(messages):
    return client.chat.completions.create(
        model="llama3.3:70b",
        messages=messages
    )
```

## Rate Limiting

Local servers typically don't enforce rate limits, but consider:

```yaml
# Ollama: Control concurrent requests
environment:
  - OLLAMA_NUM_PARALLEL=4  # Max concurrent

# llama.cpp: Control slots
command: --parallel 4  # Max concurrent
```

## Best Practices

### Model Naming

Use consistent model names:

```python
# Good - matches Ollama naming
model="llama3.3:70b-instruct-q4_K_M"

# Works - Ollama finds closest match
model="llama3.3"
```

### Context Management

Keep context within limits:

```python
def truncate_messages(messages, max_tokens=4000):
    """Keep most recent messages within limit."""
    # Implement token counting and truncation
    pass
```

### Error Handling

```python
try:
    response = client.chat.completions.create(...)
except openai.APIConnectionError:
    print("Server not reachable")
except openai.APIStatusError as e:
    print(f"API error: {e.status_code}")
```

## Testing Compatibility

### Basic Test Script

```python
#!/usr/bin/env python3
"""Test OpenAI API compatibility."""

from openai import OpenAI

BASE_URL = "http://localhost:11434/v1"

client = OpenAI(base_url=BASE_URL, api_key="test")

# Test: List models
print("Models:", [m.id for m in client.models.list().data])

# Test: Chat completion
response = client.chat.completions.create(
    model="llama3.3:70b",
    messages=[{"role": "user", "content": "Say hello"}],
    max_tokens=10
)
print("Response:", response.choices[0].message.content)

# Test: Streaming
print("Stream: ", end="")
stream = client.chat.completions.create(
    model="llama3.3:70b",
    messages=[{"role": "user", "content": "Count to 3"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()
```

## See Also

- [API Serving Index](index.md) - Overview
- [Ollama](../inference-engines/ollama.md) - Ollama setup
- [llama.cpp](../inference-engines/llama-cpp.md) - llama.cpp setup
- [AI Coding Tools](../coding-tools/index.md) - Client configuration
