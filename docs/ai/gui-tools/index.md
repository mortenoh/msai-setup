# GUI Tools

Visual interfaces for interacting with local LLMs.

## Overview

GUI tools provide:

- **User-friendly interface** - Chat without command line
- **Model management** - Download, switch, configure models
- **Conversation history** - Persistent chat sessions
- **Multi-backend** - Connect to various inference engines

## Tool Comparison

| Feature | LM Studio | Jan.ai | Open WebUI | ComfyUI |
|---------|-----------|--------|------------|---------|
| **Platform** | macOS, Windows, Linux | macOS, Windows, Linux | Web (any) | Web (any) |
| **Primary use** | LLM chat | LLM chat | LLM chat | Image/video/audio/3D generation |
| **Model source** | HuggingFace | HuggingFace | Any OpenAI-compatible | HuggingFace, Civitai |
| **Local server** | Yes | Yes | Connects to backends | Yes (built-in) |
| **Offline** | Yes | Yes | Backend dependent | Yes |
| **Multi-user** | No | No | Yes | No |
| **RAG** | No | Extensions | Built-in | N/A |
| **Open source** | No | Yes | Yes | Yes (GPL-3.0) |
| **Privacy** | Good | Excellent | Depends on setup | Excellent |

## Feature Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Applications                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │      LM Studio      │    │       Jan.ai        │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ [x] Model discovery   │    │ [x] 100% offline      │             │
│  │ [x] Built-in chat     │    │ [x] No telemetry      │             │
│  │ [x] OpenAI API server │    │ [x] Extensions        │             │
│  │ [x] Good for testing  │    │ [x] Privacy-first     │             │
│  └─────────────────────┘    └─────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Web-Based Interfaces                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      Open WebUI                          │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ [x] Connects to Ollama, OpenAI, any compatible API        │    │
│  │ [x] Multi-user with authentication                        │    │
│  │ [x] RAG (document upload and search)                      │    │
│  │ [x] Model switching                                       │    │
│  │ [x] Chat history                                          │    │
│  │ [x] Self-hosted                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                       ComfyUI                            │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ [x] Node-based workflow editor                            │    │
│  │ [x] Image, video, audio/music, 3D generation              │    │
│  │ [x] Native AMD ROCm support                               │    │
│  │ [x] Thousands of custom nodes                             │    │
│  │ [x] API-driven (every workflow is JSON)                   │    │
│  │ [x] Self-hosted, open source (GPL-3.0)                    │    │
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
| Image generation | ComfyUI |
| Video generation | ComfyUI |
| Audio/music generation | ComfyUI |
| 3D model generation | ComfyUI |
| Node-based workflows | ComfyUI |

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
  -v /mnt/tank/ai/data/open-webui:/app/backend/data \
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

-   :material-lan: **ComfyUI**

    ---

    Node-based workbench for image, video, audio, and 3D generation

    [:octicons-arrow-right-24: ComfyUI guide](comfyui.md)

</div>

## See Also

- [Inference Engines](../inference-engines/index.md) - Backend options
- [Ollama](../inference-engines/ollama.md) - Popular backend for GUIs
- [Container Deployment](../containers/index.md) - Docker setup
