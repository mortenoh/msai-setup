# llama.cpp

The foundational C/C++ inference engine for running LLMs efficiently on consumer hardware.

## Overview

llama.cpp provides:

- **Cross-platform support** - macOS (Metal), Linux (CUDA, Vulkan), Windows
- **GGUF format** - Optimized quantized model format
- **llama-server** - OpenAI-compatible API server
- **Low dependencies** - Minimal runtime requirements
- **Active development** - Frequent updates and optimizations

## Installation

### macOS (Metal)

Build from source for best performance:

```bash
# Clone repository
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build with Metal support
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j$(sysctl -n hw.ncpu)

# Binaries in build/bin/
ls build/bin/
# llama-cli, llama-server, llama-bench, etc.
```

### Linux (CUDA)

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build with CUDA
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)
```

### Linux (Vulkan)

For AMD GPUs or cross-platform:

```bash
cmake -B build -DGGML_VULKAN=ON
cmake --build build --config Release
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
  -m /tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf \
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
  "model": "/tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf",
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
  -m /tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf \
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
docker run -p 8080:8080 \
  -v /tank/ai/models:/models \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
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
