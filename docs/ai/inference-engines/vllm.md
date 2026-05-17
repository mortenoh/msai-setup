# vLLM

!!! danger "Not currently usable on the MS-S1 MAX"
    vLLM's ROCm support targets CDNA/Instinct (`gfx9xx`) and a small set of RDNA3 dGPUs (`gfx1100`). The Strix Halo iGPU (`gfx1151`) is **not on the supported target list** as of ROCm 7.x — vLLM will either fail to build kernels for it or crash at model load. This page is kept as **reference only**; on this hardware use [llama.cpp HIP](llama-cpp.md#linux-rocmhip-recommended-for-ms-s1-max) or [Ollama](ollama.md). Re-evaluate vLLM if and when AMD ships official `gfx1151` kernels upstream.

High-throughput LLM serving engine with PagedAttention and continuous batching. Listed here so readers comparing engines understand what vLLM offers and why it isn't selected for this build.

## Overview

vLLM provides:

- **14-24x throughput** vs HuggingFace Transformers
- **PagedAttention** - Efficient KV cache memory management
- **Continuous batching** - Dynamic request scheduling
- **OpenAI-compatible API** - Drop-in replacement
- **Multi-GPU support** - Tensor and pipeline parallelism

## Hardware Support (reference only)

vLLM is GPU-first and primarily targets datacenter accelerators:

| Backend | Status | Notes |
|---------|--------|-------|
| AMD ROCm — CDNA / Instinct (`gfx9xx`) | Supported | MI200/MI300 class |
| AMD ROCm — RDNA3 dGPU (`gfx1100`) | Supported | RX 7900 XTX and similar |
| AMD ROCm — RDNA3.5 iGPU (`gfx1151`, Strix Halo) | **Not supported** | The MS-S1 MAX falls here |
| Apple Silicon (Metal / MLX) | Not supported | Use [MLX](mlx.md) or [llama.cpp](llama-cpp.md) instead |
| CPU-only | Experimental | Not a production path |

For the MS-S1 MAX specifically, the supported alternatives that cover the same use cases are:

- **High concurrency / OpenAI-compatible serving** -> [llama.cpp `llama-server`](llama-cpp.md) with `--cont-batching --parallel N`
- **Easy model management** -> [Ollama (ROCm image)](ollama.md)
- **Multimodal / extra endpoints** -> [LocalAI (`localai/localai:latest-gpu-hipblas`)](../api-serving/localai.md)

## Quick Start (reference)

The commands below show what vLLM usage looks like on supported hardware. They are **not expected to work on the MS-S1 MAX**.

### Command Line

```bash
# Start OpenAI-compatible server
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --host 0.0.0.0 \
  --port 8000
```

### Python API

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.3-70B-Instruct")
sampling_params = SamplingParams(temperature=0.7, max_tokens=100)
outputs = llm.generate(["What is machine learning?"], sampling_params)

for output in outputs:
    print(output.outputs[0].text)
```

### Key Server Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--model` | Model name or path | Required |
| `--host` | Listen address | `localhost` |
| `--port` | Listen port | `8000` |
| `--tensor-parallel-size` | GPUs for tensor parallelism | 1 |
| `--pipeline-parallel-size` | GPUs for pipeline parallelism | 1 |
| `--max-model-len` | Maximum context length | Model default |
| `--gpu-memory-utilization` | GPU memory fraction | 0.9 |
| `--quantization` | Quantization method | None |
| `--dtype` | Data type | `auto` |

## Concepts Worth Knowing

Even though vLLM isn't deployed on this build, two of its concepts are useful context for tuning llama.cpp's `llama-server`:

### Continuous Batching

vLLM popularized continuous batching — admit and retire requests at every decode step rather than waiting for a full batch to finish. `llama-server --cont-batching --parallel N` is llama.cpp's implementation of the same idea. See [API Serving](../api-serving/index.md).

### PagedAttention

Paged KV-cache allocation — store the per-request KV cache in fixed-size pages rather than one contiguous block. This is what makes vLLM's memory utilization so high. llama.cpp does not have a direct equivalent today; budget KV cache conservatively (see [Memory Management](../performance/memory-management.md)).

```
Traditional: Contiguous memory allocation
+-------------------------------------+
| Request 1 KV Cache (wasted space)   |
+-------------------------------------+
| Request 2 KV Cache                  |
+-------------------------------------+

PagedAttention: Paged memory blocks
+----+----+----+----+----+----+----+----+
| R1 | R2 | R1 | R3 | R2 | R1 | R3 | R2 |
+----+----+----+----+----+----+----+----+
```

## Comparison with Alternatives Used on the MS-S1 MAX

| Feature | vLLM (not used) | llama.cpp (HIP) | Ollama (ROCm) |
|---------|-----------------|-----------------|----------------|
| Runs on `gfx1151` today | No | Yes | Yes |
| Throughput on supported HW | Highest | Good | Good |
| Batching | Continuous + paged | Continuous | Continuous |
| GPU backends | ROCm (CDNA/gfx1100), CUDA | ROCm/HIP, Metal, Vulkan, CUDA | ROCm, Metal, CUDA |
| Setup | Medium | Easy | Easiest |
| Apple Silicon | No | Yes (Metal) | Yes (Metal) |

When `gfx1151` lands in vLLM upstream, the candidate path will be the official ROCm image with `devices: /dev/kfd, /dev/dri`, `group_add: [video, render]`, and the usual `HSA_OVERRIDE_GFX_VERSION=11.5.1` override if needed. Until then, do not deploy.

## See Also

- [Inference Engines Index](index.md) - Engine comparison
- [llama.cpp](llama-cpp.md) - Recommended engine for the MS-S1 MAX
- [Ollama](ollama.md) - Easiest path to serving on `gfx1151`
- [Load Balancing](../api-serving/load-balancing.md) - Multi-backend setup
- [Benchmarking](../performance/benchmarking.md) - Performance testing
