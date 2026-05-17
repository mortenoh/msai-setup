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
│  +-------------+  +-------------+  +---------------------+      │
│  |   Ollama    |  | llama-server|  |   Native build       |     │
│  | (ROCm)      |  | (ROCm/HIP)  |  | (cmake -DGGML_HIP=ON)|     │
│  +------+------+  +------+------+  +----------+-----------+     │
│         |                |                    |                  │
├─────────┴────────────────┴────────────────────┴──────────────────┤
│                     Storage Layer                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            tank/ai/models (ZFS Dataset)                    │  │
│  │  recordsize=1M │ compression=off (models already compressed)│  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

!!! note "Engine choices for Strix Halo / gfx1151"
    On this hardware the practical engines are **llama.cpp (HIP build)** and **Ollama** (which uses llama.cpp under the hood). **MLX is Apple-Silicon-only**, and **vLLM does not currently ship a working build for `gfx1151`** — keep both off the recommended path until that changes. See [Inference Engines](inference-engines/index.md) for details.

## Quick Start Paths

### Path 1: Web UI in front of Ollama (easiest)

1. [Install ROCm](gpu/quick-start.md) and verify `gfx1151` is detected.
2. [Install Ollama natively](inference-engines/ollama.md) (it auto-detects ROCm).
3. Deploy [Open WebUI](gui-tools/open-webui.md) as a Docker container; point it at the host Ollama.
4. Pull a 70B Q4 model and chat from any browser.

### Path 2: Container stack (compose-managed)

1. [Create the ZFS dataset](containers/model-volumes.md) for model files.
2. [Deploy the Ollama container](containers/ollama-docker.md) with `/dev/kfd` + `/dev/dri` device mounts.
3. Expose Ollama's OpenAI-compatible endpoint on the LAN (or only via Tailscale).

### Path 3: Maximum performance (native HIP build)

1. [Install ROCm 7.x](gpu/rocm-installation.md).
2. Build [llama.cpp with HIP for `gfx1151`](inference-engines/llama-cpp.md#linux-rocmhip--recommended-for-ms-s1-max).
3. Run `llama-server` directly under systemd; tune `--parallel`, `-ngl 99`, KV-cache quantization.

## What You Can Run on 128GB

Assuming GTT is sized to ~108 GB (see [Memory Configuration](gpu/memory-configuration.md)), with ~20 GB reserved for the OS / ARC / VMs:

| Model Size | Quantization | Memory | Example Models |
|------------|--------------|--------|----------------|
| 7-8B | Q8_0 | ~10 GB | Llama 3.x 8B, Mistral 7B, Qwen3 8B |
| 32-34B | Q4_K_M | ~20 GB | Qwen3 32B, DeepSeek Coder, Codestral |
| 70B | Q4_K_M | ~40 GB | Llama 3.3 70B, Qwen3 72B |
| 70B | Q6_K | ~55 GB | Higher-quality 70B with long context |
| 70B | Q8_0 | ~75 GB | Near-fp16 quality 70B |
| 120-200B MoE | Q4/Q8 | 60-110 GB | DeepSeek-V3-class, GPT-OSS-120B-MXFP4 |
| 405B | IQ2/IQ1 | ~100 GB | Llama 3.1 405B, very tight context |

Real-world tok/s on this box (ROCm/HIP, single-stream):

| Model | Tokens/sec (gen) |
|---|---|
| 8B Q4 | ~50-70 |
| 32B Q4 | ~15-20 |
| 70B Q4 | ~6-9 |
| 70B Q6 | ~4-6 |
| 405B IQ2 | ~1-2 |

Model recommendations rot fast — verify on [ollama.com](https://ollama.com/library) or [huggingface.co/models](https://huggingface.co/models) on the day you set this up.

## Section Overview

<div class="grid cards" markdown>

-   :material-brain: **Fundamentals**

    ---

    Why local LLMs, unified memory advantages, architecture decisions

    [:octicons-arrow-right-24: Learn basics](fundamentals/why-local-llms.md)

-   :material-cpu-64-bit: **Inference Engines**

    ---

    llama.cpp (HIP) and Ollama on Strix Halo; MLX/vLLM noted but not for this box

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

    Call the host's Ollama API from VMs (the host owns the iGPU)

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
