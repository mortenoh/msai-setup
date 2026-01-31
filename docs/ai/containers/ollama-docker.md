# Ollama Docker

Deploy Ollama in Docker with persistent model storage and GPU acceleration.

## Official Images

| Image | GPU | Notes |
|-------|-----|-------|
| `ollama/ollama` | NVIDIA (default) | Most common |
| `ollama/ollama:rocm` | AMD | ROCm support |
| `ollama/ollama:latest` | NVIDIA | Same as default |

## Quick Start

### NVIDIA GPU

```bash
docker run -d \
  --gpus all \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# Pull a model
docker exec ollama ollama pull llama3.3:70b

# Run model
docker exec -it ollama ollama run llama3.3:70b
```

### AMD GPU (ROCm)

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama:rocm
```

### CPU Only

```bash
docker run -d \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

## Docker Compose

### Basic Setup (NVIDIA)

```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    container_name: ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    ports:
      - "11434:11434"
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
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    ports:
      - "11434:11434"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    restart: unless-stopped
```

### Production Configuration

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    container_name: ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"  # Local only
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_MAX_LOADED_MODELS=2
      - OLLAMA_KEEP_ALIVE=30m
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

## Environment Variables

Configure Ollama behavior via environment:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Listen address:port | `127.0.0.1:11434` |
| `OLLAMA_MODELS` | Model storage path | `/root/.ollama` |
| `OLLAMA_NUM_PARALLEL` | Concurrent requests | `1` |
| `OLLAMA_MAX_LOADED_MODELS` | Models in memory | `1` |
| `OLLAMA_KEEP_ALIVE` | Model unload timeout | `5m` |
| `OLLAMA_DEBUG` | Debug logging | `false` |

```yaml
environment:
  - OLLAMA_HOST=0.0.0.0:11434
  - OLLAMA_NUM_PARALLEL=4
  - OLLAMA_MAX_LOADED_MODELS=2
  - OLLAMA_KEEP_ALIVE=1h
```

## Model Management

### Pull Models

```bash
# From host
docker exec ollama ollama pull llama3.3:70b-instruct-q4_K_M
docker exec ollama ollama pull deepseek-coder-v2:16b
docker exec ollama ollama pull nomic-embed-text

# List models
docker exec ollama ollama list
```

### Pre-Load on Startup

Create a script to pull models on container start:

```yaml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
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

### Import GGUF Models

```bash
# Create Modelfile
cat > /tank/ai/models/ollama/Modelfile << 'EOF'
FROM /models/gguf/custom-model.gguf

TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>
{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>
{{ .Response }}<|eot_id|>"""

PARAMETER stop "<|eot_id|>"
EOF

# Mount GGUF volume and create model
docker run --rm \
  -v /tank/ai/models/ollama:/root/.ollama \
  -v /tank/ai/models/gguf:/models/gguf:ro \
  ollama/ollama create custom-model -f /root/.ollama/Modelfile
```

## With Open WebUI

### Combined Stack

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    container_name: ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - /tank/ai/data/open-webui:/app/backend/data
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

## API Usage

### Chat Completion (OpenAI Compatible)

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

### Model Management API

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

## Multi-Instance Deployment

### Different Models per Instance

```yaml
version: '3.8'

services:
  ollama-chat:
    image: ollama/ollama
    container_name: ollama-chat
    volumes:
      - /tank/ai/models/ollama-chat:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_KEEP_ALIVE=1h
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]

  ollama-code:
    image: ollama/ollama
    container_name: ollama-code
    volumes:
      - /tank/ai/models/ollama-code:/root/.ollama
    ports:
      - "11435:11434"
    environment:
      - OLLAMA_KEEP_ALIVE=1h
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
```

## Monitoring

### Health Checks

```bash
# Check if running
curl http://localhost:11434/

# Check loaded models
docker exec ollama ollama ps
```

### Resource Usage

```bash
# Container stats
docker stats ollama

# GPU usage (NVIDIA)
nvidia-smi

# GPU usage (AMD)
rocm-smi
```

### Logs

```bash
# View logs
docker logs -f ollama

# With debug
docker run -e OLLAMA_DEBUG=1 ollama/ollama
```

## Storage Persistence

### Volume Structure

```
/tank/ai/models/ollama/
├── models/
│   ├── blobs/        # Model weights (large files)
│   │   └── sha256-xxx
│   └── manifests/    # Model metadata
│       └── registry.ollama.ai/
│           └── library/
│               └── llama3.3/
└── history           # Chat history (optional)
```

### Backup Models

```bash
# Models are in the blobs directory
# Backup manifests to remember which models
tar czf ollama-manifests.tar.gz /tank/ai/models/ollama/models/manifests

# Full backup (large)
zfs snapshot tank/ai/models/ollama@backup
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs ollama

# Verify volume permissions
ls -la /tank/ai/models/ollama
```

### GPU Not Available

```bash
# NVIDIA: Check toolkit
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# AMD: Check ROCm
rocm-smi
docker run --rm --device=/dev/kfd --device=/dev/dri rocm/rocm-terminal rocminfo
```

### Model Pull Fails

```bash
# Check disk space
df -h /tank/ai/models/ollama

# Clean incomplete downloads
docker exec ollama rm -rf /root/.ollama/models/blobs/*.partial

# Retry
docker exec ollama ollama pull llama3.3:70b
```

### Out of Memory

```bash
# Reduce concurrent models
OLLAMA_MAX_LOADED_MODELS=1

# Use smaller quantization
ollama pull llama3.3:70b-instruct-q4_K_S

# Check current memory
docker exec ollama ollama ps
```

### Slow Response

```bash
# Verify GPU is being used
docker exec ollama ollama ps
# Should show "GPU" in PROCESSOR column

# Increase parallel slots for concurrent requests
OLLAMA_NUM_PARALLEL=4
```

## See Also

- [Container Deployment](index.md) - Container overview
- [GPU Containers](gpu-containers.md) - GPU setup details
- [Model Volumes](model-volumes.md) - Storage configuration
- [Ollama](../inference-engines/ollama.md) - Ollama reference
- [Open WebUI](../gui-tools/open-webui.md) - Web interface
