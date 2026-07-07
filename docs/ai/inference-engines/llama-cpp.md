# llama.cpp

The foundational C/C++ inference engine for running LLMs efficiently on consumer hardware.

## Overview

llama.cpp provides:

- **Cross-platform support** - Linux (ROCm/HIP, CUDA, Vulkan), macOS (Metal), Windows
- **GGUF format** - Optimized quantized model format
- **llama-server** - OpenAI-compatible API server
- **Low dependencies** - Minimal runtime requirements
- **Active development** - Frequent updates and optimizations

## Installation

!!! tip "Backend choice on Strix Halo: Vulkan is faster for inference"
    Measured on this MS-S1 MAX (Radeon 8060S / `gfx1151`), llama.cpp's **Vulkan**
    backend beats **ROCm/HIP** for inference — most dramatically on prompt
    processing:

    | Backend | pp512 (prompt) | tg128 (generation) |
    |---------|---------------:|-------------------:|
    | **Vulkan (RADV)** | **756 t/s** | **28.7 t/s** |
    | ROCm/HIP          | 316 t/s     | 27.4 t/s          |

    (Gemma-4-12B Q4_0, `-ngl 99`, same build commit.) Token generation is
    memory-bandwidth-bound, so both sit near the same ~28 t/s ceiling; prompt
    processing is compute-bound, and RADV schedules the iGPU far better here
    (~2.4×). **Use Vulkan for llama.cpp inference.** Keep ROCm installed anyway —
    PyTorch, vLLM and fine-tuning need it and Vulkan cannot do those; the two are
    independent. `msai bootstrap llamacpp-vulkan` builds the Vulkan default on
    `PATH`; `llamacpp-hip` builds the ROCm variant under `/opt/llama.cpp-hip` for
    A/B testing.

    **One caveat — addressable memory.** The two backends expose different
    amounts of the unified pool: on this box `llama-cli --list-devices` reports
    the Vulkan (RADV) device at ~64 GiB but the ROCm device at ~116 GiB. For a
    model that fits under ~64 GiB, prefer Vulkan for speed; for a model too large
    for the Vulkan device, use the ROCm/HIP build, which can address the larger
    GTT pool. Always check `llama-cli --list-devices` for the backend you plan to
    run.

### Linux Vulkan (recommended for MS-S1 MAX inference)

The fastest llama.cpp backend on Strix Halo (see the benchmark above). Needs the
RADV driver (`mesa-vulkan-drivers`) plus the Vulkan/SPIR-V build tools
(`libvulkan-dev spirv-headers glslang-dev glslc glslang-tools spirv-tools`).

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build with the Vulkan backend
cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
# Binaries land in build/bin/ (llama-cli, llama-server, llama-bench, ...)
```

### Linux ROCm/HIP (for the compute stack / A/B)

Build with HIP when you want the ROCm path (or to benchmark it against Vulkan).
Requires ROCm 7.x installed first — see [ROCm Installation](../gpu/rocm-installation.md).
The distro ROCm lives in `/usr`, so point cmake at its clang via `hipconfig`.

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build with HIP, targeting Strix Halo (gfx1151).
# HIPCXX/HIP_PATH point cmake at the distro ROCm clang in /usr.
HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" cmake -B build \
    -DGGML_HIP=ON \
    -DAMDGPU_TARGETS=gfx1151 \
    -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)

# Binaries land in build/bin/
ls build/bin/
# llama-cli, llama-server, llama-bench, etc.
```

Runtime environment hints (add to `~/.bashrc` or a service unit):

```bash
export HIP_VISIBLE_DEVICES=0
export HSA_OVERRIDE_GFX_VERSION=11.5.1  # gfx1151 — only needed on older ROCm
```

### macOS (Metal)

For Apple Silicon laptops in the fleet. Build from source for best performance:

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build with Metal support
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j$(sysctl -n hw.ncpu)

ls build/bin/
```

### Linux (CUDA) — reference only, not used on the MS-S1 MAX

Documented for users on NVIDIA hardware; not applicable to this build.

```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)
```

### Pre-built Binaries

Download from [GitHub Releases](https://github.com/ggml-org/llama.cpp/releases):

```bash
# Example for macOS
curl -LO https://github.com/ggml-org/llama.cpp/releases/latest/download/llama-server-macos-arm64.zip
unzip llama-server-macos-arm64.zip
```

## llama-server

The OpenAI-compatible server for API access.

### Basic Usage

```bash
# Start server with a model
./llama-server \
  -m /path/to/model.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192  # context length
```

### Recommended Configuration

```bash
./llama-server \
  -m /mnt/tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -ngl 99 \           # GPU layers (99 = all)
  --threads 8 \       # CPU threads for any CPU work
  --parallel 2 \      # Concurrent requests
  --cont-batching \   # Enable continuous batching
  --metrics           # Prometheus metrics
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-m` | Model path | Required |
| `-c` | Context length | 2048 |
| `-ngl` | GPU layers (99 for all) | 0 (CPU) |
| `--threads` | CPU threads | Auto |
| `--parallel` | Concurrent slots | 1 |
| `--host` | Listen address | 127.0.0.1 |
| `--port` | Listen port | 8080 |
| `--cont-batching` | Continuous batching | Off |
| `--flash-attn` | Flash attention | Off |

### GPU Layer Allocation

Control memory usage with `-ngl`:

```bash
# Full GPU (128GB system, 70B Q4)
-ngl 99  # All layers on GPU

# Partial offload (limited memory)
-ngl 40  # 40 layers on GPU, rest on CPU

# CPU only
-ngl 0
```

### API Endpoints

```bash
# Chat completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain recursion."}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'

# Text completion
curl http://localhost:8080/v1/completions \
  -d '{"prompt": "The capital of France is", "max_tokens": 20}'

# List models
curl http://localhost:8080/v1/models

# Health check
curl http://localhost:8080/health
```

### Streaming

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

## Configuration File

Create a server config for complex setups:

```json
{
  "model": "/mnt/tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf",
  "host": "0.0.0.0",
  "port": 8080,
  "ctx_size": 8192,
  "n_gpu_layers": 99,
  "threads": 8,
  "parallel": 2,
  "cont_batching": true,
  "flash_attn": true
}
```

```bash
./llama-server --config config.json
```

## Performance Tuning

### Context Length vs Memory

| Context | Memory Impact | Use Case |
|---------|---------------|----------|
| 2048 | Baseline | Short prompts |
| 4096 | +~1GB | Standard chat |
| 8192 | +~2GB | Coding tasks |
| 32768 | +~8GB | Long documents |
| 131072 | +~32GB | Full context models |

### Flash Attention

Reduces memory usage for long contexts:

```bash
./llama-server -m model.gguf --flash-attn -c 32768
```

Requires compilation with Flash Attention support.

### Multi-Model Serving

Run multiple instances on different ports:

```bash
# Terminal 1 - Code model
./llama-server -m deepseek-coder-33b-q4.gguf --port 8081

# Terminal 2 - Chat model
./llama-server -m llama-3.3-70b-q4.gguf --port 8082
```

Use a reverse proxy to route requests. See [Load Balancing](../api-serving/load-balancing.md).

## Benchmarking

Use `llama-bench` to measure performance:

```bash
./llama-bench \
  -m model.gguf \
  -p 512 \      # Prompt tokens
  -n 128 \      # Generated tokens
  -ngl 99       # GPU layers

# Output shows tokens/sec for prompt processing and generation
```

See [Benchmarking](../performance/benchmarking.md) for methodology.

## systemd Service

Run llama-server as a service:

```ini
# /etc/systemd/system/llama-server.service
[Unit]
Description=llama.cpp Server
After=network.target

[Service]
Type=simple
User=llama
ExecStart=/opt/llama.cpp/build/bin/llama-server \
  -m /mnt/tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -ngl 99
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now llama-server
```

## Container Usage

See [llama.cpp Docker](../containers/llama-cpp-docker.md) for containerized deployment.

Quick start:

```bash
docker run --rm -p 8080:8080 \
  --device /dev/kfd --device /dev/dri \
  --group-add video --group-add render \
  -e HSA_OVERRIDE_GFX_VERSION=11.5.1 \
  -v /mnt/tank/ai/models:/models \
  ghcr.io/ggml-org/llama.cpp:server-rocm \
  -m /models/gguf/llama-3.3-70b-q4.gguf \
  -c 4096 -ngl 99
```

## Troubleshooting

### Model Won't Load

```bash
# Check available memory
free -h  # Linux
memory_pressure  # macOS

# Reduce GPU layers
-ngl 30  # Instead of 99

# Use smaller quantization
# Q4_K_M instead of Q6_K
```

### Slow Generation

```bash
# Verify GPU is being used
# Look for "llama_init_from_gpt_params" output showing GPU layers

# Check Metal is enabled (macOS)
./llama-server -m model.gguf --verbose 2>&1 | grep -i metal

# Reduce context if memory-bound
-c 4096  # Instead of 32768
```

### API Connection Refused

```bash
# Bind to all interfaces
--host 0.0.0.0

# Check firewall
sudo ufw allow 8080/tcp
```

## See Also

- [Inference Engines Index](index.md) - Engine comparison
- [llama.cpp Docker](../containers/llama-cpp-docker.md) - Container deployment
- [GGUF Formats](../models/gguf-formats.md) - Model format details
- [Benchmarking](../performance/benchmarking.md) - Performance testing
