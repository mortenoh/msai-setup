# Model Compatibility

Engine, model format, and feature compatibility reference.

## Format Compatibility

| Engine | GGUF | Safetensors | AWQ | GPTQ | PyTorch |
|--------|------|-------------|-----|------|---------|
| llama.cpp | Native | Convert | No | No | Convert |
| Ollama | Native | Convert | No | No | Convert |
| MLX | Convert | Native | No | No | No |
| vLLM | No | Native | Yes | Yes | Yes |
| LocalAI | Native | Via backend | No | No | No |
| LM Studio | Native | No | No | No | No |
| Jan.ai | Native | No | No | No | No |

## GPU Backend Support

| Engine | NVIDIA (CUDA) | AMD (ROCm) | Apple (Metal) | Vulkan |
|--------|---------------|------------|---------------|--------|
| llama.cpp | Yes | Yes | Yes | Yes |
| Ollama | Yes | Yes | Yes | Via llama.cpp |
| MLX | No | No | Yes (native) | No |
| vLLM | Yes | Experimental | No | No |
| LocalAI | Yes | Yes | Via llama.cpp | No |

## Model Family Support

### llama.cpp / Ollama

| Model Family | Supported | Notes |
|--------------|-----------|-------|
| Llama 2/3/3.1/3.2/3.3 | Yes | Full support |
| Qwen 2/2.5 | Yes | Full support |
| Mistral/Mixtral | Yes | Full support |
| DeepSeek Coder | Yes | Full support |
| DeepSeek V3 | Yes | MoE support |
| Gemma 2 | Yes | Full support |
| Phi-3/4 | Yes | Full support |
| CodeLlama | Yes | Full support |
| StarCoder | Yes | Full support |
| Falcon | Yes | Full support |
| Yi | Yes | Full support |

### vLLM

| Model Family | Supported | Notes |
|--------------|-----------|-------|
| Llama | Yes | Optimized |
| Qwen | Yes | Full support |
| Mistral/Mixtral | Yes | Full support |
| DeepSeek | Yes | MoE support |
| Gemma | Yes | Full support |
| Phi | Yes | Full support |
| Falcon | Yes | Full support |
| MPT | Yes | Full support |
| Baichuan | Yes | Full support |

### MLX

| Model Family | Supported | Notes |
|--------------|-----------|-------|
| Llama | Yes | Optimized |
| Qwen | Yes | Full support |
| Mistral | Yes | Full support |
| Gemma | Yes | Full support |
| Phi | Yes | Full support |
| DeepSeek | Yes | Full support |

## Quantization Support

### GGUF Quantizations

| Quantization | llama.cpp | Ollama | LM Studio | Jan.ai |
|--------------|-----------|--------|-----------|--------|
| F32 | Yes | Yes | Yes | Yes |
| F16 | Yes | Yes | Yes | Yes |
| Q8_0 | Yes | Yes | Yes | Yes |
| Q6_K | Yes | Yes | Yes | Yes |
| Q5_K_M | Yes | Yes | Yes | Yes |
| Q5_K_S | Yes | Yes | Yes | Yes |
| Q4_K_M | Yes | Yes | Yes | Yes |
| Q4_K_S | Yes | Yes | Yes | Yes |
| Q4_0 | Yes | Yes | Yes | Yes |
| Q3_K_M | Yes | Yes | Yes | Yes |
| Q2_K | Yes | Yes | Yes | Yes |
| IQ4_NL | Yes | Yes | Yes | Varies |
| IQ3_XS | Yes | Yes | Yes | Varies |
| IQ2_XXS | Yes | Yes | Yes | Varies |

### vLLM Quantizations

| Quantization | Supported | Notes |
|--------------|-----------|-------|
| FP16 | Yes | Default |
| BF16 | Yes | Better for training |
| FP8 | Yes | H100/RTX 40 series |
| AWQ | Yes | Recommended |
| GPTQ | Yes | Wide availability |
| SqueezeLLM | Yes | |
| Marlin | Yes | Fast |

## Feature Support

### Context Length

| Engine | Max Tested | Notes |
|--------|------------|-------|
| llama.cpp | 1M+ | With RoPE scaling |
| Ollama | 128K | Model dependent |
| MLX | 128K | Model dependent |
| vLLM | 128K+ | Model dependent |

### Speculative Decoding

| Engine | Supported | Notes |
|--------|-----------|-------|
| llama.cpp | Yes | Draft model |
| Ollama | No | |
| MLX | Yes | |
| vLLM | Yes | |

### Flash Attention

| Engine | Supported | Notes |
|--------|-----------|-------|
| llama.cpp | Yes | Compile flag |
| Ollama | Via llama.cpp | |
| MLX | Built-in | |
| vLLM | Yes | Default |

### Continuous Batching

| Engine | Supported | Notes |
|--------|-----------|-------|
| llama.cpp | Basic | `--cont-batching` |
| Ollama | Basic | |
| MLX | No | |
| vLLM | Yes | Advanced |

## API Compatibility

### OpenAI Endpoints

| Endpoint | llama.cpp | Ollama | MLX | vLLM | LocalAI |
|----------|-----------|--------|-----|------|---------|
| `/v1/chat/completions` | Yes | Yes | Via wrapper | Yes | Yes |
| `/v1/completions` | Yes | Yes | Via wrapper | Yes | Yes |
| `/v1/models` | Yes | Yes | Via wrapper | Yes | Yes |
| `/v1/embeddings` | Yes | Yes | Via wrapper | Yes | Yes |
| `/v1/images/generations` | No | No | No | No | Yes |
| `/v1/audio/transcriptions` | No | No | No | No | Yes |

### Streaming

All engines support Server-Sent Events (SSE) streaming.

## Memory Requirements

### 70B Models

| Quantization | Size | VRAM (8K ctx) | VRAM (32K ctx) |
|--------------|------|---------------|----------------|
| Q8_0 | 75GB | 79GB | 91GB |
| Q6_K | 57GB | 61GB | 73GB |
| Q5_K_M | 48GB | 52GB | 64GB |
| Q4_K_M | 43GB | 47GB | 59GB |
| Q3_K_M | 35GB | 39GB | 51GB |
| Q2_K | 28GB | 32GB | 44GB |

### 32-34B Models

| Quantization | Size | VRAM (8K ctx) | VRAM (32K ctx) |
|--------------|------|---------------|----------------|
| Q8_0 | 36GB | 39GB | 47GB |
| Q6_K | 28GB | 31GB | 39GB |
| Q5_K_M | 24GB | 27GB | 35GB |
| Q4_K_M | 21GB | 24GB | 32GB |

### 7-8B Models

| Quantization | Size | VRAM (8K ctx) | VRAM (32K ctx) |
|--------------|------|---------------|----------------|
| Q8_0 | 8GB | 10GB | 14GB |
| Q6_K | 6GB | 8GB | 12GB |
| Q4_K_M | 5GB | 7GB | 11GB |

## Docker Images

| Image | GPU | Size |
|-------|-----|------|
| `ollama/ollama` | NVIDIA | ~2GB |
| `ollama/ollama:rocm` | AMD | ~3GB |
| `ghcr.io/ggml-org/llama.cpp:server` | CPU | ~200MB |
| `ghcr.io/ggml-org/llama.cpp:server-cuda` | NVIDIA | ~3GB |
| `ghcr.io/ggml-org/llama.cpp:server-rocm` | AMD | ~3GB |
| `vllm/vllm-openai` | NVIDIA | ~5GB |
| `localai/localai:latest-gpu-nvidia-cuda-12` | NVIDIA | ~4GB |
| `ghcr.io/open-webui/open-webui` | N/A (UI) | ~500MB |

## See Also

- [Inference Engines](../inference-engines/index.md) - Engine details
- [Quantization](../models/quantization.md) - Quantization details
- [Choosing Models](../models/choosing-models.md) - Selection guide
