# Inference Engines

Compare and choose the right inference engine for your local LLM deployment on the MS-S1 MAX.

## Recommendation for this hardware

For Strix Halo (AMD `gfx1151`) the practical choices are **llama.cpp built with HIP** and **Ollama** (which uses llama.cpp under the hood). Everything else either doesn't run on this GPU or doesn't run on Linux:

| Engine | Strix Halo / gfx1151 | Notes |
|---|---|---|
| **[llama.cpp (HIP)](llama-cpp.md)** | **Yes — recommended** | Build with `cmake -DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1151`. Best perf and most flexibility. |
| **[Ollama](ollama.md)** | **Yes — recommended** | Auto-detects ROCm on install. Easiest UX. |
| [MLX](mlx.md) | No — Apple Silicon only | Reference for Mac clients only. |
| [vLLM](vllm.md) | No — `gfx1151` not in supported targets | Re-evaluate when AMD ships official kernels. |

## Engine Comparison

| Engine | Best For | GPU support (this site) | API | Speed |
|--------|----------|--------------------------|-----|-------|
| [llama.cpp](llama-cpp.md) | Flexibility, max perf on Strix Halo | HIP/ROCm + Vulkan + Metal (Mac) | OpenAI-compat | Good |
| [Ollama](ollama.md) | Ease of use, model library | ROCm (Linux) + Metal (Mac) | OpenAI-compat | Good |
| [MLX](mlx.md) | Apple Silicon only | Metal only | Python/REST | Excellent (on Mac) |
| [vLLM](vllm.md) | High-throughput when supported | ROCm CDNA / `gfx1100` only — not `gfx1151` | OpenAI-compat | Excellent (when supported) |

## Feature Matrix

| Feature | llama.cpp | Ollama | MLX | vLLM |
|---------|-----------|--------|-----|------|
| Runs on MS-S1 MAX | Yes | Yes | No | No |
| OpenAI API | Yes | Yes | Via wrapper | Yes |
| Streaming | Yes | Yes | Yes | Yes |
| Batching | Basic / `--parallel` | Basic | Basic | Advanced |
| GGUF support | Native | Native | Via convert | No |
| Safetensors | Via convert | Via convert | Native | Native |
| Model library / pull | Manual | Built-in | Manual | Manual |
| GPU memory mgmt | Manual | Auto | Auto | Auto |
| Multi-model | Yes (multiple server instances) | Yes (LRU swap) | Yes | Yes |
| Speculative decode | Yes | No | Yes | Yes |
| Continuous batching | No | No | No | Yes |

## Performance — Strix Halo (single-stream, ROCm/HIP)

Approximate tokens/sec on the MS-S1 MAX after `amd-ttm --set 108`:

| Model / quant | llama-server | Ollama |
|---|---|---|
| 8B Q4_K_M | ~55-70 | ~50-65 |
| 32B Q4_K_M | ~16-22 | ~15-20 |
| 70B Q4_K_M | ~7-9 | ~6-8 |
| 70B Q6_K | ~4-6 | ~4-5 |
| 70B Q8_0 | ~3-5 | ~3-4 |
| 405B IQ2 | ~1-2 | ~1-2 |

Ollama runs ~5-15% slower than a direct `llama-server` build because it ships its own llama.cpp binary and adds a small abstraction layer. Worth it for the model-pull/swap UX unless you're squeezing every token.

## Reference numbers from other platforms

| Platform | Engine | Llama 3.3 70B Q4 |
|---|---|---|
| Apple M4 Max 128GB | MLX | ~30-45 tok/s |
| Apple M4 Max 128GB | llama.cpp (Metal) | ~25-35 tok/s |
| **MS-S1 MAX (gfx1151)** | **llama.cpp (HIP)** | **~7-9 tok/s** |

The MS-S1 MAX is slower per token on small models but can run far larger
models without offloading because of its 128GB unified-memory pool. For
context, discrete-GPU rigs with ~24GB of VRAM (RTX 4090 class) typically
hit ~45-50 tok/s on a 70B Q4 — much faster on small models, but unable
to fit larger weights at all without spilling to system RAM.

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
    # vLLM does not support the MS-S1 MAX (gfx1151) today.
    # Listed here for reference only — works on ROCm CDNA / gfx1100 or
    # other supported GPUs. Re-evaluate when AMD ships official gfx1151
    # kernels.
    pip install vllm
    vllm serve meta-llama/Llama-3.3-70B-Instruct
    ```

## Container Availability

| Engine | Official image (this build) | Notes |
|--------|------------------------------|-------|
| llama.cpp | `ghcr.io/ggml-org/llama.cpp:server-rocm` | ROCm variant for MS-S1 MAX; `:server-vulkan` as fallback |
| Ollama | `ollama/ollama:rocm` | ROCm variant; default `:latest` is CUDA and unused here |
| MLX | N/A (native only) | Metal — run natively on Mac |
| vLLM | `vllm/vllm-openai` | Not used — does not support gfx1151 today |

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

**Recommended on the MS-S1 MAX: llama.cpp (HIP) behind Ollama or a thin proxy**
- Best stability + flexibility on `gfx1151`
- Use `--parallel` to allow concurrent slots

### Maximum Performance

**MS-S1 MAX: llama.cpp (HIP) tuned with `--flash-attn --cont-batching`**
**Apple Silicon laptop: MLX**
- Pick the engine that matches the hardware; cross-platform comparisons
  rarely beat the platform-native option.

### Container Deployment

**Recommended: Ollama or llama.cpp**
- Good Docker support
- GPU passthrough options

## See Also

- [llama.cpp](llama-cpp.md) - Detailed setup guide
- [Ollama](ollama.md) - Docker-like LLM runner
- [MLX](mlx.md) - Apple Silicon optimization
- [vLLM](vllm.md) - High-throughput serving
