# llama.cpp Docker

Deploy llama.cpp inference server in Docker with GPU acceleration.

## Official Images

Available from GitHub Container Registry:

| Image | GPU | Use Case |
|-------|-----|----------|
| `ghcr.io/ggml-org/llama.cpp:server` | CPU only | Testing, fallback |
| `ghcr.io/ggml-org/llama.cpp:server-cuda` | NVIDIA | Production |
| `ghcr.io/ggml-org/llama.cpp:server-rocm` | AMD | ROCm systems |
| `ghcr.io/ggml-org/llama.cpp:server-vulkan` | Vulkan | Cross-platform GPU |

## Quick Start

### NVIDIA GPU

```bash
docker run -d \
  --gpus all \
  -v /tank/ai/models/gguf:/models \
  -p 8080:8080 \
  --name llama-server \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/llama-3.3-70b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -ngl 99
```

### AMD GPU (ROCm)

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -v /tank/ai/models/gguf:/models \
  -p 8080:8080 \
  --name llama-server \
  ghcr.io/ggml-org/llama.cpp:server-rocm \
  -m /models/llama-3.3-70b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -ngl 99
```

## Docker Compose

### Basic Setup (NVIDIA)

```yaml
# docker-compose.yml
version: '3.8'

services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    container_name: llama-server
    volumes:
      - /tank/ai/models/gguf:/models:ro
    ports:
      - "8080:8080"
    command: >
      -m /models/llama-3.3-70b-instruct-q4_k_m.gguf
      --host 0.0.0.0
      --port 8080
      -c 8192
      -ngl 99
      --parallel 2
      --cont-batching
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

### AMD ROCm Setup

```yaml
version: '3.8'

services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    container_name: llama-server
    volumes:
      - /tank/ai/models/gguf:/models:ro
    ports:
      - "8080:8080"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    command: >
      -m /models/llama-3.3-70b-instruct-q4_k_m.gguf
      --host 0.0.0.0
      --port 8080
      -c 8192
      -ngl 99
    restart: unless-stopped
```

### Production Configuration

```yaml
version: '3.8'

services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    container_name: llama-server
    volumes:
      - /tank/ai/models/gguf:/models:ro
      - /tank/ai/logs/llama:/logs
    ports:
      - "127.0.0.1:8080:8080"  # Local only, use reverse proxy
    command: >
      -m /models/llama-3.3-70b-instruct-q4_k_m.gguf
      --host 0.0.0.0
      --port 8080
      -c 16384
      -ngl 99
      --parallel 4
      --cont-batching
      --flash-attn
      --metrics
      --log-file /logs/llama-server.log
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
        limits:
          memory: 100G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## Server Parameters

### Essential Options

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| `-m` | Model path | Required |
| `--host` | Listen address | `0.0.0.0` |
| `--port` | Listen port | `8080` |
| `-c` | Context length | `8192` - `32768` |
| `-ngl` | GPU layers | `99` (all) |

### Performance Options

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| `--parallel` | Concurrent slots | `2` - `4` |
| `--cont-batching` | Continuous batching | Enable |
| `--flash-attn` | Flash attention | Enable if supported |
| `--threads` | CPU threads | Auto or core count |

### Monitoring Options

| Parameter | Description |
|-----------|-------------|
| `--metrics` | Enable Prometheus metrics |
| `--log-file` | Log to file |
| `-v` | Verbose output |

## Multi-Model Deployment

### Separate Containers

```yaml
version: '3.8'

services:
  llama-chat:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    ports:
      - "8081:8080"
    command: >
      -m /models/llama-3.3-70b-instruct-q4_k_m.gguf
      --host 0.0.0.0 -c 8192 -ngl 99
    volumes:
      - /tank/ai/models/gguf:/models:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]

  deepseek-code:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    ports:
      - "8082:8080"
    command: >
      -m /models/deepseek-coder-v2-16b-q5_k_m.gguf
      --host 0.0.0.0 -c 16384 -ngl 99
    volumes:
      - /tank/ai/models/gguf:/models:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
```

### With Load Balancer

```yaml
services:
  traefik:
    image: traefik:v3.0
    ports:
      - "8080:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command:
      - --providers.docker
      - --entrypoints.web.address=:80

  llama-1:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    labels:
      - "traefik.http.routers.llama.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llama.loadbalancer.server.port=8080"
    # ...

  llama-2:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    labels:
      - "traefik.http.routers.llama.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llama.loadbalancer.server.port=8080"
    # ...
```

## API Usage

### Test Endpoint

```bash
# Health check
curl http://localhost:8080/health

# Model info
curl http://localhost:8080/v1/models
```

### Chat Completion

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain Docker in one sentence."}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### Streaming

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

## Monitoring

### Prometheus Metrics

```yaml
# Enable metrics in compose
command: >
  -m /models/model.gguf
  --metrics
  --metrics-path /metrics
```

```bash
# Scrape metrics
curl http://localhost:8080/metrics
```

Key metrics:

- `llamacpp_requests_total` - Request count
- `llamacpp_tokens_generated_total` - Tokens generated
- `llamacpp_prompt_tokens_total` - Prompt tokens processed
- `llamacpp_kv_cache_usage_ratio` - KV cache utilization

### Logs

```bash
# View container logs
docker logs -f llama-server

# With log file
docker exec llama-server cat /logs/llama-server.log
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs llama-server

# Common issues:
# - Model file not found → check volume mount
# - Out of memory → reduce -ngl or use smaller model
# - GPU not available → check nvidia-smi or rocm-smi
```

### GPU Not Detected

```bash
# NVIDIA: Verify nvidia-container-toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# AMD: Verify ROCm
docker run --rm --device=/dev/kfd --device=/dev/dri rocm/rocm-terminal rocminfo
```

### Slow Performance

```bash
# Verify GPU layers are used
docker logs llama-server 2>&1 | grep -i "gpu\|layer"

# Check GPU utilization
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# Increase parallel slots for multiple requests
--parallel 4
```

### Memory Issues

```bash
# Reduce context length
-c 4096  # Instead of 8192

# Reduce GPU layers if GPU memory limited
-ngl 50  # Instead of 99

# Use smaller quantization
# Q4_K_S instead of Q4_K_M
```

## Building Custom Image

### With Custom Configuration

```dockerfile
# Dockerfile
FROM ghcr.io/ggml-org/llama.cpp:server-cuda

# Add health check script
COPY healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.sh

HEALTHCHECK CMD /usr/local/bin/healthcheck.sh
```

### From Source

```dockerfile
FROM nvidia/cuda:12.1-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y \
    git cmake build-essential

WORKDIR /app
RUN git clone https://github.com/ggml-org/llama.cpp.git
WORKDIR /app/llama.cpp

RUN cmake -B build -DGGML_CUDA=ON && \
    cmake --build build --config Release -j

FROM nvidia/cuda:12.1-runtime-ubuntu22.04
COPY --from=builder /app/llama.cpp/build/bin/llama-server /usr/local/bin/

ENTRYPOINT ["llama-server"]
```

## See Also

- [Container Deployment](index.md) - Container overview
- [GPU Containers](gpu-containers.md) - GPU setup details
- [Model Volumes](model-volumes.md) - Storage configuration
- [llama.cpp](../inference-engines/llama-cpp.md) - Native installation
