# Ollama Docker

Deploy Ollama in Docker with persistent model storage and GPU
acceleration on the MS-S1 MAX (AMD ROCm).

## Official Images

| Image | Backend | Use case |
|-------|---------|----------|
| `ollama/ollama:rocm` | AMD ROCm | **MS-S1 MAX (primary)** |
| `ollama/ollama` | CPU / NVIDIA default | Reference only — not used here |
| `ollama/ollama:latest` | Same as default | Reference only |

> The default `ollama/ollama` image ships with the CUDA backend, which the
> MS-S1 MAX cannot use. Always pull the `:rocm` tag on this host.

## Quick start

### AMD GPU (ROCm) — MS-S1 MAX

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -v /mnt/tank/ai/models/ollama:/root/.ollama \
  -e HSA_OVERRIDE_GFX_VERSION=11.5.1 \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama:rocm

# Pull a model
docker exec ollama ollama pull llama3.3:70b

# Run model
docker exec -it ollama ollama run llama3.3:70b
```

### CPU only (fallback / lightweight workloads)

```bash
docker run -d \
  -v /mnt/tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama-cpu \
  ollama/ollama
```

## Docker Compose

### Basic AMD ROCm setup

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    volumes:
      - /mnt/tank/ai/models/ollama:/root/.ollama
    ports:
      - "11434:11434"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    restart: unless-stopped
```

### Production configuration

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    volumes:
      - /mnt/tank/ai/models/ollama:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"  # Local only — front with a reverse proxy
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      OLLAMA_HOST: "0.0.0.0"
      OLLAMA_NUM_PARALLEL: "2"
      OLLAMA_MAX_LOADED_MODELS: "2"
      OLLAMA_KEEP_ALIVE: "30m"
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    deploy:
      resources:
        limits:
          memory: 100G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/"]
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

## Environment variables

Configure Ollama behavior via environment:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Listen address:port | `127.0.0.1:11434` |
| `OLLAMA_MODELS` | Model storage path | `/root/.ollama` |
| `OLLAMA_NUM_PARALLEL` | Concurrent requests | `1` |
| `OLLAMA_MAX_LOADED_MODELS` | Models in memory | `1` |
| `OLLAMA_KEEP_ALIVE` | Model unload timeout | `5m` |
| `OLLAMA_DEBUG` | Debug logging | `false` |
| `HSA_OVERRIDE_GFX_VERSION` | ROCm GPU arch override (`11.5.1` for gfx1151 on older ROCm) | unset |

```yaml
environment:
  OLLAMA_HOST: "0.0.0.0:11434"
  OLLAMA_NUM_PARALLEL: "4"
  OLLAMA_MAX_LOADED_MODELS: "2"
  OLLAMA_KEEP_ALIVE: "1h"
  HSA_OVERRIDE_GFX_VERSION: "11.5.1"
```

## Model management

### Pull models

```bash
# From host
docker exec ollama ollama pull llama3.3:70b-instruct-q4_K_M
docker exec ollama ollama pull deepseek-coder-v2:16b
docker exec ollama ollama pull nomic-embed-text

# List models
docker exec ollama ollama list
```

### Pre-load on startup

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    volumes:
      - /mnt/tank/ai/models/ollama:/root/.ollama
      - ./init-models.sh:/init-models.sh:ro
    entrypoint: ["/bin/bash", "-c"]
    command:
      - |
        /bin/ollama serve &
        sleep 5
        /init-models.sh
        wait
```

```bash
#!/bin/bash
# init-models.sh
ollama pull llama3.3:70b-instruct-q4_K_M
ollama pull deepseek-coder-v2:16b
```

### Import GGUF models

```bash
# Create Modelfile
cat > /mnt/tank/ai/models/ollama/Modelfile << 'EOF'
FROM /models/gguf/custom-model.gguf

TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>
{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>
{{ .Response }}<|eot_id|>"""

PARAMETER stop "<|eot_id|>"
EOF

# Mount GGUF volume and create model
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  -v /mnt/tank/ai/models/ollama:/root/.ollama \
  -v /mnt/tank/ai/models/gguf:/models/gguf:ro \
  ollama/ollama:rocm create custom-model -f /root/.ollama/Modelfile
```

## With Open WebUI

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    volumes:
      - /mnt/tank/ai/models/ollama:/root/.ollama
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - /mnt/tank/ai/data/open-webui:/app/backend/data
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

networks:
  default:
    name: ai-network
```

## API usage

### Chat completion (OpenAI compatible)

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3:70b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is Docker?"}
    ]
  }'
```

### Native API

```bash
# Generate
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3.3:70b",
    "prompt": "Why is the sky blue?",
    "stream": false
  }'

# Chat
curl http://localhost:11434/api/chat \
  -d '{
    "model": "llama3.3:70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Model management API

```bash
# List models
curl http://localhost:11434/api/tags

# Show model info
curl http://localhost:11434/api/show -d '{"name": "llama3.3:70b"}'

# Pull model
curl http://localhost:11434/api/pull -d '{"name": "llama3.3:70b"}'

# Delete model
curl http://localhost:11434/api/delete -d '{"name": "old-model"}'
```

## Single-instance pattern (MS-S1 MAX)

The MS-S1 MAX has one iGPU sharing the unified-memory pool, so the
"two Ollama containers, one per GPU" pattern doesn't apply. Use a
single Ollama instance and configure it to keep multiple models
warm:

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      OLLAMA_MAX_LOADED_MODELS: "3"
      OLLAMA_KEEP_ALIVE: "1h"
      OLLAMA_NUM_PARALLEL: "2"
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    volumes:
      - /mnt/tank/ai/models/ollama:/root/.ollama
    ports:
      - "11434:11434"
```

Ollama will swap models in/out of GPU memory as requests come in, and
`OLLAMA_KEEP_ALIVE` prevents the most-used ones from being unloaded.

## Monitoring

### Health checks

```bash
# Check if running
curl http://localhost:11434/

# Check loaded models
docker exec ollama ollama ps
```

### Resource usage

```bash
# Container stats
docker stats ollama

# GPU usage (AMD ROCm)
rocm-smi
watch -n 1 rocm-smi
```

### Logs

```bash
# View logs
docker logs -f ollama

# With debug
docker run -e OLLAMA_DEBUG=1 ollama/ollama:rocm
```

## Storage persistence

### Volume structure

```
/mnt/tank/ai/models/ollama/
|-- models/
|   |-- blobs/        # Model weights (large files)
|   |   `-- sha256-xxx
|   `-- manifests/    # Model metadata
|       `-- registry.ollama.ai/
|           `-- library/
|               `-- llama3.3/
`-- history           # Chat history (optional)
```

### Backup models

```bash
# Models are in the blobs directory
# Backup manifests to remember which models
tar czf ollama-manifests.tar.gz /mnt/tank/ai/models/ollama/models/manifests

# Full backup (large)
zfs snapshot tank/ai/models/ollama@backup
```

## Troubleshooting

### Container won't start

```bash
docker logs ollama
ls -la /mnt/tank/ai/models/ollama
```

### GPU not available

```bash
# Host first
rocm-smi
rocminfo | head

# Then in a container
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal rocminfo | head
```

If `rocminfo` works on the host but not in the container, the most
common cause is missing `--device=` / `--group-add` flags.

### Model pull fails

```bash
df -h /mnt/tank/ai/models/ollama
docker exec ollama rm -rf /root/.ollama/models/blobs/*.partial
docker exec ollama ollama pull llama3.3:70b
```

### Out of memory

```bash
# Reduce concurrent models
OLLAMA_MAX_LOADED_MODELS=1

# Use smaller quantization
ollama pull llama3.3:70b-instruct-q4_K_S

# Check current memory
docker exec ollama ollama ps
```

### Slow response

```bash
# Verify GPU is being used
docker exec ollama ollama ps
# Should show "GPU" in the PROCESSOR column, not "CPU"

# Confirm the ROCm backend is active in logs
docker logs ollama 2>&1 | grep -iE 'rocm|hip|gpu'

# Increase parallel slots for concurrent requests
OLLAMA_NUM_PARALLEL=4
```

## See also

- [Container Deployment](index.md) — container overview
- [GPU Containers](gpu-containers.md) — GPU setup details
- [Model Volumes](model-volumes.md) — storage configuration
- [Ollama](../inference-engines/ollama.md) — Ollama reference
- [Open WebUI](../gui-tools/open-webui.md) — web interface
