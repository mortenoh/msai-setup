# Inference Engines

Compare and choose the right inference engine for your local LLM deployment.

## Engine Comparison

| Engine | Best For | GPU Support | API | Speed |
|--------|----------|-------------|-----|-------|
| [llama.cpp](llama-cpp.md) | Flexibility, wide model support | Metal, CUDA, Vulkan | OpenAI-compat | Good |
| [Ollama](ollama.md) | Ease of use, container deployment | Metal, CUDA | OpenAI-compat | Good |
| [MLX](mlx.md) | Apple Silicon maximum performance | Metal only | Python/REST | Excellent |
| [vLLM](vllm.md) | High-throughput serving | CUDA (NVIDIA) | OpenAI-compat | Excellent |

## Quick Selection Guide

```
┌────────────────────────────────────────────────────────────┐
│                    Choose Your Engine                       │
└────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │Apple Silicon│     │   NVIDIA    │     │   Server    │
   │   Desktop   │     │     GPU     │     │  (Multi-GPU)│
   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
          │                   │                   │
          ▼                   ▼                   ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │    MLX      │     │ llama.cpp   │     │    vLLM     │
   │  (fastest)  │     │   or Ollama │     │  (batched)  │
   └─────────────┘     └─────────────┘     └─────────────┘
          │                   │
          ▼                   ▼
   ┌─────────────┐
   │   Ollama    │     Want Docker-like UX? → Ollama
   │  (easy UX)  │     Need max flexibility? → llama.cpp
   └─────────────┘
```

## Feature Matrix

| Feature | llama.cpp | Ollama | MLX | vLLM |
|---------|-----------|--------|-----|------|
| OpenAI API | Yes | Yes | Via wrapper | Yes |
| Streaming | Yes | Yes | Yes | Yes |
| Batching | Basic | Basic | Basic | Advanced |
| GGUF support | Native | Native | Via convert | No |
| Safetensors | Via convert | Via convert | Native | Native |
| Model discovery | Manual | Built-in | Manual | Manual |
| GPU memory mgmt | Manual | Auto | Auto | Auto |
| Multi-model | Yes | Yes | Yes | Yes |
| Speculative decode | Yes | No | Yes | Yes |
| Continuous batching | No | No | No | Yes |

## Performance Comparison

Benchmark on Apple Silicon M4 Max (128GB), Llama 3.3 70B Q4:

| Engine | Tokens/sec | Time to First Token | Notes |
|--------|------------|---------------------|-------|
| MLX | ~45 | ~100ms | Apple Silicon optimized |
| llama.cpp (Metal) | ~35 | ~150ms | Good all-rounder |
| Ollama | ~35 | ~200ms | Overhead for convenience |

Benchmark on NVIDIA RTX 4090, Llama 3.3 70B Q4:

| Engine | Tokens/sec | Notes |
|--------|------------|-------|
| vLLM | ~80+ | Batched requests |
| llama.cpp (CUDA) | ~50 | Single request |
| Ollama | ~48 | Single request |

## API Compatibility

All engines provide OpenAI-compatible endpoints:

```bash
# Works with any engine
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Standard endpoints:
- `POST /v1/chat/completions` - Chat completion
- `POST /v1/completions` - Text completion
- `GET /v1/models` - List models
- `POST /v1/embeddings` - Generate embeddings (some engines)

## Installation Summary

=== "llama.cpp"

    ```bash
    # Build from source (macOS)
    git clone https://github.com/ggml-org/llama.cpp
    cd llama.cpp
    cmake -B build -DGGML_METAL=ON
    cmake --build build --config Release

    # Run server
    ./build/bin/llama-server -m model.gguf -c 4096
    ```

=== "Ollama"

    ```bash
    # macOS
    brew install ollama

    # Linux
    curl -fsSL https://ollama.com/install.sh | sh

    # Start and run
    ollama serve
    ollama run llama3.3
    ```

=== "MLX"

    ```bash
    # Requires Apple Silicon
    pip install mlx-lm

    # Run inference
    mlx_lm.generate --model mlx-community/Llama-3.3-70B-Instruct-4bit
    ```

=== "vLLM"

    ```bash
    # Requires NVIDIA GPU
    pip install vllm

    # Start server
    vllm serve meta-llama/Llama-3.3-70B-Instruct
    ```

## Container Availability

| Engine | Official Image | GPU Support |
|--------|----------------|-------------|
| llama.cpp | `ghcr.io/ggml-org/llama.cpp:server` | CUDA, ROCm |
| Ollama | `ollama/ollama` | CUDA, ROCm |
| MLX | N/A (native only) | Metal (native) |
| vLLM | `vllm/vllm-openai` | CUDA |

See [Container Deployment](../containers/index.md) for detailed Docker setups.

## Memory Requirements

Same model, different engines (70B Q4):

| Engine | Base Memory | With 8K Context | Notes |
|--------|-------------|------------------|-------|
| MLX | ~40GB | ~42GB | Efficient |
| llama.cpp | ~43GB | ~45GB | Slightly higher |
| Ollama | ~43GB | ~45GB | Uses llama.cpp |
| vLLM | ~50GB+ | ~55GB+ | Higher for features |

## Choosing Based on Use Case

### Local Development

**Recommended: Ollama**
- Easy model management
- Quick to get started
- Good enough performance

### Production API

**Recommended: vLLM (NVIDIA) or llama.cpp (Apple Silicon)**
- vLLM for high throughput
- llama.cpp for stability and flexibility

### Maximum Performance

**Recommended: MLX (Apple Silicon) or vLLM (NVIDIA)**
- Best tokens/sec
- Optimized for their platforms

### Container Deployment

**Recommended: Ollama or llama.cpp**
- Good Docker support
- GPU passthrough options

## See Also

- [llama.cpp](llama-cpp.md) - Detailed setup guide
- [Ollama](ollama.md) - Docker-like LLM runner
- [MLX](mlx.md) - Apple Silicon optimization
- [vLLM](vllm.md) - High-throughput serving
