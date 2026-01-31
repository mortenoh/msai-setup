# API Serving

Expose local LLMs via OpenAI-compatible APIs for integration with tools and services.

## Overview

OpenAI-compatible APIs enable:

- **Tool compatibility** - Claude Code, Aider, Continue.dev work seamlessly
- **Standard interface** - Single API works with any backend
- **Flexibility** - Switch models without changing client code
- **Ecosystem** - Libraries, SDKs, and tools work out of the box

## API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Applications                        │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐   │
│  │ Claude Code │  │   Aider     │  │    Custom Apps        │   │
│  │ (OpenAI)    │  │  (OpenAI)   │  │    (OpenAI SDK)       │   │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬───────────┘   │
│         │                │                     │                │
│         └────────────────┴─────────────────────┘                │
│                          │                                      │
│              POST /v1/chat/completions                          │
│                          │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│                    API Gateway                                  │
│              (Optional: Traefik/nginx)                          │
│                          │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│                   Inference Backends                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Ollama    │  │ llama.cpp   │  │       LocalAI           │ │
│  │   :11434    │  │   :8080     │  │       :8080             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Standard Endpoints

All OpenAI-compatible servers provide these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/chat/completions` | POST | Chat/conversation |
| `/v1/completions` | POST | Text completion |
| `/v1/models` | GET | List available models |
| `/v1/embeddings` | POST | Generate embeddings |
| `/health` | GET | Health check |

## Backend Comparison

| Backend | Strengths | Endpoints | Notes |
|---------|-----------|-----------|-------|
| [Ollama](../inference-engines/ollama.md) | Easy setup, model management | All standard | Recommended start |
| [llama.cpp](../inference-engines/llama-cpp.md) | Performance, flexibility | All standard | Production |
| [LocalAI](localai.md) | Drop-in replacement, multimodal | Full OpenAI | Feature-rich |
| [vLLM](../inference-engines/vllm.md) | High throughput | All standard | Multi-GPU |

## Quick Start

### Test API

```bash
# List models
curl http://localhost:11434/v1/models

# Chat completion
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3:70b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### With Streaming

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3:70b",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'
```

## Client Configuration

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="not-needed"  # Required but not validated
)

response = client.chat.completions.create(
    model="llama3.3:70b",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'not-needed'
});

const response = await client.chat.completions.create({
  model: 'llama3.3:70b',
  messages: [{ role: 'user', content: 'Hello!' }]
});
```

### curl

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer not-needed" \
  -d '{"model": "llama3.3:70b", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Topics

<div class="grid cards" markdown>

-   :material-api: **OpenAI Compatible**

    ---

    Standard endpoints and request/response formats

    [:octicons-arrow-right-24: API reference](openai-compatible.md)

-   :material-swap-horizontal: **LocalAI**

    ---

    Full OpenAI replacement with multimodal support

    [:octicons-arrow-right-24: LocalAI setup](localai.md)

-   :material-scale-balance: **Load Balancing**

    ---

    Multiple backends with Traefik routing

    [:octicons-arrow-right-24: Load balancing](load-balancing.md)

</div>

## Environment Setup

### For Coding Tools

```bash
# Set environment variables
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=not-needed

# Or per-tool configuration
# See coding-tools section for specific tools
```

### Docker Network Access

```yaml
# Containers can access by service name
services:
  ollama:
    container_name: ollama
    # ...

  app:
    environment:
      - OPENAI_API_BASE=http://ollama:11434/v1
```

## Common Configurations

### Single Backend

```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
```

### Multi-Backend with Gateway

```yaml
services:
  traefik:
    image: traefik:v3.0
    ports:
      - "8080:80"
    # Routes to different backends

  ollama:
    # General models

  llama-code:
    # Code-specialized model
```

See [Load Balancing](load-balancing.md) for details.

## See Also

- [Inference Engines](../inference-engines/index.md) - Backend options
- [Container Deployment](../containers/index.md) - Docker setup
- [AI Coding Tools](../coding-tools/index.md) - Tool configuration
- [Remote Access](../remote-access/index.md) - External access
