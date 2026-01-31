# GUI Tools

Visual interfaces for interacting with local LLMs.

## Overview

GUI tools provide:

- **User-friendly interface** - Chat without command line
- **Model management** - Download, switch, configure models
- **Conversation history** - Persistent chat sessions
- **Multi-backend** - Connect to various inference engines

## Tool Comparison

| Feature | LM Studio | Jan.ai | Open WebUI |
|---------|-----------|--------|------------|
| **Platform** | macOS, Windows, Linux | macOS, Windows, Linux | Web (any) |
| **Model source** | HuggingFace | HuggingFace | Any OpenAI-compatible |
| **Local server** | Yes | Yes | Connects to backends |
| **Offline** | Yes | Yes | Backend dependent |
| **Multi-user** | No | No | Yes |
| **RAG** | No | Extensions | Built-in |
| **Open source** | No | Yes | Yes |
| **Privacy** | Good | Excellent | Depends on setup |

## Feature Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Applications                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │      LM Studio      │    │       Jan.ai        │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ ✓ Model discovery   │    │ ✓ 100% offline      │             │
│  │ ✓ Built-in chat     │    │ ✓ No telemetry      │             │
│  │ ✓ OpenAI API server │    │ ✓ Extensions        │             │
│  │ ✓ Good for testing  │    │ ✓ Privacy-first     │             │
│  └─────────────────────┘    └─────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Web-Based Interface                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      Open WebUI                          │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ ✓ Connects to Ollama, OpenAI, any compatible API        │    │
│  │ ✓ Multi-user with authentication                        │    │
│  │ ✓ RAG (document upload and search)                      │    │
│  │ ✓ Model switching                                       │    │
│  │ ✓ Chat history                                          │    │
│  │ ✓ Self-hosted                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Recommendation by Use Case

| Use Case | Recommended Tool |
|----------|------------------|
| Quick model testing | LM Studio |
| Privacy-focused use | Jan.ai |
| Team/multi-user | Open WebUI |
| Server deployment | Open WebUI |
| Model discovery | LM Studio |
| Offline work | Jan.ai or LM Studio |

## Quick Start

### LM Studio

1. Download from [lmstudio.ai](https://lmstudio.ai)
2. Search and download a model
3. Start chatting or enable API server

### Jan.ai

1. Download from [jan.ai](https://jan.ai)
2. Download models from Hub
3. Chat offline

### Open WebUI

```bash
docker run -d \
  -p 3000:8080 \
  -v /tank/ai/data/open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## Topics

<div class="grid cards" markdown>

-   :material-application: **LM Studio**

    ---

    Desktop app with model discovery and local API server

    [:octicons-arrow-right-24: LM Studio guide](lm-studio.md)

-   :material-incognito: **Jan.ai**

    ---

    Privacy-first offline assistant

    [:octicons-arrow-right-24: Jan.ai guide](jan-ai.md)

-   :material-web: **Open WebUI**

    ---

    Multi-backend web interface with RAG and auth

    [:octicons-arrow-right-24: Open WebUI guide](open-webui.md)

</div>

## See Also

- [Inference Engines](../inference-engines/index.md) - Backend options
- [Ollama](../inference-engines/ollama.md) - Popular backend for GUIs
- [Container Deployment](../containers/index.md) - Docker setup
