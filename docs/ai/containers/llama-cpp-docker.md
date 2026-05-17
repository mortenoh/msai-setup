# llama.cpp Docker

Deploy the llama.cpp inference server in Docker with GPU acceleration on
the MS-S1 MAX (AMD ROCm). CUDA images are noted only for reference and
are not used on this build.

## Official Images

Available from GitHub Container Registry:

| Image | Backend | Use case |
|-------|---------|----------|
| `ghcr.io/ggml-org/llama.cpp:server` | CPU only | Testing, fallback |
| `ghcr.io/ggml-org/llama.cpp:server-rocm` | AMD ROCm | **MS-S1 MAX (primary)** |
| `ghcr.io/ggml-org/llama.cpp:server-vulkan` | Vulkan | Portable GPU fallback |
| `ghcr.io/ggml-org/llama.cpp:server-cuda` | NVIDIA CUDA | Reference only — not used here |

## Quick start (AMD ROCm — MS-S1 MAX)

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -v /mnt/tank/ai/models/gguf:/models \
  -e HSA_OVERRIDE_GFX_VERSION=11.5.1 \
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

### Basic AMD ROCm setup

```yaml
services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    container_name: llama-server
    volumes:
      - /mnt/tank/ai/models/gguf:/models:ro
    ports:
      - "8080:8080"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    command: >
      -m /models/llama-3.3-70b-instruct-q4_k_m.gguf
      --host 0.0.0.0
      --port 8080
      -c 8192
      -ngl 99
    restart: unless-stopped
```

### Production configuration

```yaml
services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    container_name: llama-server
    volumes:
      - /mnt/tank/ai/models/gguf:/models:ro
      - /mnt/tank/ai/logs/llama:/logs
    ports:
      - "127.0.0.1:8080:8080"  # Local only, use reverse proxy
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
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

## Server parameters

### Essential options

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| `-m` | Model path | Required |
| `--host` | Listen address | `0.0.0.0` |
| `--port` | Listen port | `8080` |
| `-c` | Context length | `8192` - `32768` |
| `-ngl` | GPU layers | `99` (all) |

### Performance options

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| `--parallel` | Concurrent slots | `2` - `4` |
| `--cont-batching` | Continuous batching | Enable |
| `--flash-attn` | Flash attention | Enable if supported |
| `--threads` | CPU threads | Auto or core count |

### Monitoring options

| Parameter | Description |
|-----------|-------------|
| `--metrics` | Enable Prometheus metrics |
| `--log-file` | Log to file |
| `-v` | Verbose output |

## Multi-model deployment

The MS-S1 MAX has a single iGPU sharing the unified-memory pool, so
running two llama.cpp containers at the same time will fight for the
same GPU. The right pattern here is either:

1. One container, model swapped via an orchestrator (Ollama, LiteLLM).
2. Two containers, but only one with `-ngl 99` and the other CPU-only
   for embedding / lightweight tasks.

```yaml
services:
  llama-chat:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    ports:
      - "8081:8080"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    command: >
      -m /models/llama-3.3-70b-instruct-q4_k_m.gguf
      --host 0.0.0.0 -c 8192 -ngl 99
    volumes:
      - /mnt/tank/ai/models/gguf:/models:ro

  embedder-cpu:
    image: ghcr.io/ggml-org/llama.cpp:server
    ports:
      - "8082:8080"
    command: >
      -m /models/bge-large-en-v1.5-q8_0.gguf
      --host 0.0.0.0 -c 4096
    volumes:
      - /mnt/tank/ai/models/gguf:/models:ro
```

### With a load balancer

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

  llama-primary:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    labels:
      - "traefik.http.routers.llama.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llama.loadbalancer.server.port=8080"
    # ...devices, group_add, command as above

  llama-secondary-cpu:
    image: ghcr.io/ggml-org/llama.cpp:server
    labels:
      - "traefik.http.routers.llama.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llama.loadbalancer.server.port=8080"
    # ...
```

## API usage

### Test endpoint

```bash
# Health check
curl http://localhost:8080/health

# Model info
curl http://localhost:8080/v1/models
```

### Chat completion

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

### Prometheus metrics

```yaml
command: >
  -m /models/model.gguf
  --metrics
  --metrics-path /metrics
```

```bash
curl http://localhost:8080/metrics
```

Key metrics:

- `llamacpp_requests_total` — request count
- `llamacpp_tokens_generated_total` — tokens generated
- `llamacpp_prompt_tokens_total` — prompt tokens processed
- `llamacpp_kv_cache_usage_ratio` — KV cache utilisation

### Logs

```bash
docker logs -f llama-server
docker exec llama-server cat /logs/llama-server.log
```

## Troubleshooting

### Container won't start

```bash
docker logs llama-server

# Common causes:
# - Model file not found      -> check the volume mount
# - Out of memory             -> lower -ngl or pick a smaller model
# - GPU not available         -> check `rocm-smi` on the host
```

### GPU not detected

```bash
# Host first
rocm-smi

# Then in a container
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal rocminfo | head
```

### Slow performance

```bash
# Verify GPU layers are used
docker logs llama-server 2>&1 | grep -iE 'gpu|layer|rocm|hip'

# Check GPU utilisation
watch -n 1 rocm-smi

# Increase parallel slots for multi-client throughput
--parallel 4
```

### Memory issues

```bash
# Reduce context length
-c 4096  # instead of 8192

# Reduce GPU layers if VRAM-bound
-ngl 50

# Use a smaller quantization
# Q4_K_S instead of Q4_K_M
```

## Building a custom image

```dockerfile
# Dockerfile — extend the upstream ROCm server image
FROM ghcr.io/ggml-org/llama.cpp:server-rocm

COPY healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.sh

HEALTHCHECK CMD /usr/local/bin/healthcheck.sh
```

For a from-source build, see the upstream
[llama.cpp Docker docs](https://github.com/ggml-org/llama.cpp/tree/master/.devops)
and pick the `rocm` Dockerfile.

## See also

- [Container Deployment](index.md) — container overview
- [GPU Containers](gpu-containers.md) — GPU setup details
- [Model Volumes](model-volumes.md) — storage configuration
- [llama.cpp](../inference-engines/llama-cpp.md) — native installation
