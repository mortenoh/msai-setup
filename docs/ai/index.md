# AI & Local LLMs

Run large language models locally on a 128GB unified memory system for privacy, cost savings, and low latency.

## Why Local LLMs?

| Benefit | Description |
|---------|-------------|
| **Privacy** | Data never leaves your machine |
| **Cost** | No API fees after hardware investment |
| **Latency** | Sub-100ms first token for local inference |
| **Offline** | Works without internet connection |
| **Control** | Choose models, tune parameters, no rate limits |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Claude Code │  │   Aider     │  │  Cline / Continue.dev   │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
│                   OpenAI-Compatible API                          │
│                          │                                       │
├──────────────────────────┼───────────────────────────────────────┤
│                    Inference Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Ollama    │  │ llama.cpp   │  │     MLX     │   Native    │
│  │  (Docker)   │  │  (Docker)   │  │   (Native)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
├─────────┴────────────────┴────────────────┴──────────────────────┤
│                     Storage Layer                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              tank/ai/models (ZFS Dataset)                  │  │
│  │     recordsize=1M │ compression=zstd │ ~500GB capacity     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start Paths

### Path 1: Fastest Setup (GUI)

1. Install [LM Studio](gui-tools/lm-studio.md) - download and run
2. Download a model (Llama 3.3 70B Q4)
3. Start local server, connect coding tools

### Path 2: Server/Container Setup

1. [Create ZFS dataset](containers/model-volumes.md) for model storage
2. [Deploy Ollama container](containers/ollama-docker.md)
3. Pull models and expose OpenAI-compatible API

### Path 3: Maximum Performance

1. Install [MLX](inference-engines/mlx.md) for Apple Silicon
2. Download GGUF models from Hugging Face
3. Run inference with Metal acceleration

## What You Can Run on 128GB

| Model Size | Quantization | VRAM Usage | Example Models |
|------------|--------------|------------|----------------|
| 7-8B | Q8_0 | ~10GB | Llama 3.2, Mistral 7B |
| 32-34B | Q5_K_M | ~25GB | Qwen 2.5 32B, DeepSeek Coder 33B |
| 70B | Q4_K_M | ~43GB | Llama 3.3 70B, Qwen 2.5 72B |
| 70B | Q6_K | ~58GB | Higher quality 70B |
| 405B | Q2_K | ~95GB | Llama 3.1 405B (limited context) |

The 75% VRAM rule: Reserve 25% of unified memory for system overhead. On 128GB, target ~96GB for models.

## Section Overview

<div class="grid cards" markdown>

-   :material-brain: **Fundamentals**

    ---

    Why local LLMs, unified memory advantages, architecture decisions

    [:octicons-arrow-right-24: Learn basics](fundamentals/why-local-llms.md)

-   :material-cpu-64-bit: **Inference Engines**

    ---

    llama.cpp, Ollama, MLX, vLLM - when to use each

    [:octicons-arrow-right-24: Compare engines](inference-engines/index.md)

-   :material-application: **GUI Tools**

    ---

    LM Studio, Jan.ai, Open WebUI - visual interfaces

    [:octicons-arrow-right-24: GUI options](gui-tools/index.md)

-   :material-docker: **Container Deployment**

    ---

    Docker setups for Ollama and llama.cpp with ZFS storage

    [:octicons-arrow-right-24: Containers](containers/index.md)

-   :material-api: **API Serving**

    ---

    OpenAI-compatible endpoints, LocalAI, load balancing

    [:octicons-arrow-right-24: API setup](api-serving/index.md)

-   :material-desktop-tower: **VM Integration**

    ---

    LM Studio in Windows VM with GPU passthrough

    [:octicons-arrow-right-24: VM setup](vm-integration/index.md)

-   :material-code-braces: **AI Coding Tools**

    ---

    Claude Code, Aider, Cline, Continue.dev configuration

    [:octicons-arrow-right-24: Coding tools](coding-tools/index.md)

-   :material-cube-outline: **Model Management**

    ---

    Choosing models, quantization, Hugging Face downloads

    [:octicons-arrow-right-24: Models](models/index.md)

-   :material-speedometer: **Performance**

    ---

    Benchmarking, context optimization, memory management

    [:octicons-arrow-right-24: Performance](performance/index.md)

-   :material-remote-desktop: **Remote Access**

    ---

    Tailscale integration, API security, remote inference

    [:octicons-arrow-right-24: Remote access](remote-access/index.md)

</div>

## Related Documentation

- [Docker Setup](../docker/setup.md) - Container runtime configuration
- [ZFS Datasets](../zfs/datasets.md) - Storage configuration
- [GPU Passthrough](../virtualization/gpu-passthrough.md) - VM GPU access
- [Tailscale Serve](../tailscale/features/funnel-serve.md) - Remote access
