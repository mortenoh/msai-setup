# Ollama Stack

Docker-based local AI setup with Ollama and Open WebUI.

## Overview

This stack provides:

- **Ollama** - Local LLM inference server
- **Open WebUI** - ChatGPT-like web interface
- **GPU support** - NVIDIA and AMD ROCm
- **Model persistence** - Volume-based storage
- **API access** - OpenAI-compatible endpoints

## Quick Start

### Basic Setup (CPU)

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - openwebui_data:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama_data:
  openwebui_data:
```

!!! note "Named volumes here are for the CPU quick-start only"
    This basic block uses Docker named volumes so it runs anywhere. On the
    MS-S1 MAX build, real data lives on ZFS: the
    [Complete Production Stack](#complete-production-stack) below bind-mounts
    into `/mnt/tank/...` datasets instead (see
    [Docker vs LXC](docker-vs-lxc.md)). Prefer that pattern for anything you
    keep.

Start:

```bash
docker compose up -d
```

Access:
- Open WebUI: http://localhost:3000
- Ollama API: http://localhost:11434

## GPU Passthrough

### AMD ROCm (this build)

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - /mnt/tank/ai/ollama:/root/.ollama
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    # environment:
    #   - HSA_OVERRIDE_GFX_VERSION=11.5.1  # Strix Halo (gfx1151) on older ROCm
    restart: unless-stopped
```

Prerequisites: ROCm 7.x installed on the host (see [ROCm Installation](../ai/gpu/rocm-installation.md)). The user running Docker needs to be in the `render` and `video` groups so the container can use `/dev/kfd`/`/dev/dri`.

Verify the GPU is visible inside the container:

```bash
docker exec ollama rocminfo | grep gfx
# Should show gfx1151 on Strix Halo
```

### NVIDIA GPU (not used on the MS-S1 MAX — reference only)

For users repurposing this guide on NVIDIA hardware:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - /mnt/tank/ai/ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

Needs the NVIDIA Container Toolkit installed on the host:

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list \
    | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

!!! note "HSA_OVERRIDE_GFX_VERSION"
    For ROCm 7.x with gfx1151 (Strix Halo), this variable is **not needed** -- native support is included. Only set it for older AMD GPUs on ROCm 6.x:

    | GPU | Version |
    |-----|---------|
    | RX 6700 XT | 10.3.0 |
    | RX 6800/6900 | 10.3.0 |
    | RX 7900 XTX | 11.0.0 |

## Model Management

### Pull Models

```bash
# Pull via CLI
docker compose exec ollama ollama pull llama3.3

# Pull via API
curl http://localhost:11434/api/pull -d '{"name": "llama3.3"}'
```

### List Models

```bash
docker compose exec ollama ollama list
```

### Pre-Pull Models on Startup

Create `init-models.sh`:

```bash
#!/bin/bash
models=(
    "llama3.3"
    "deepseek-coder-v2:16b"
    "qwen2.5-coder:32b"
)

for model in "${models[@]}"; do
    echo "Pulling $model..."
    ollama pull "$model"
done
```

Add to compose:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
      - ./init-models.sh:/init-models.sh
    # Run init script after container starts

  init-models:
    image: ollama/ollama:latest
    depends_on:
      - ollama
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        sleep 5
        ollama pull llama3.3
        ollama pull deepseek-coder-v2:16b
    environment:
      - OLLAMA_HOST=http://ollama:11434
    restart: "no"
```

## Model Persistence

### Volume Configuration

```yaml
services:
  ollama:
    volumes:
      # Models persist here
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
    driver: local
    driver_opts:
      type: none
      device: /data/ollama  # Custom path
      o: bind
```

### Backup Models

```bash
# Backup
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/ollama-backup.tar.gz /data

# Restore
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/ollama-backup.tar.gz -C /
```

## Open WebUI Configuration

### Full Configuration

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - openwebui_data:/app/backend/data
    environment:
      # Ollama connection
      - OLLAMA_BASE_URL=http://ollama:11434

      # Authentication
      - WEBUI_AUTH=true
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}

      # Default model
      - DEFAULT_MODELS=llama3.3

      # Features
      - ENABLE_RAG_WEB_SEARCH=true
      - ENABLE_IMAGE_GENERATION=false

      # UI customization
      - WEBUI_NAME=Local AI
```

### Without Authentication (Local Only)

```yaml
environment:
  - WEBUI_AUTH=false
```

### With External Authentication

```yaml
environment:
  - WEBUI_AUTH=true
  - OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID}
  - OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}
```

## API Proxy Configuration

### Expose API Securely

```yaml
services:
  ollama:
    # Internal only
    expose:
      - "11434"

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - ollama
```

`nginx.conf`:

```nginx
events {}

http {
    upstream ollama {
        server ollama:11434;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://ollama;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }
}
```

### With API Key Authentication

```nginx
server {
    listen 80;

    location / {
        if ($http_authorization != "Bearer ${API_KEY}") {
            return 401;
        }

        proxy_pass http://ollama;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

## Multi-Model Orchestration

### Multiple Ollama Instances

For single-GPU systems like the MS-S1 MAX, you don't shard across GPUs — instead let one Ollama instance hold multiple models and swap them in/out. Ollama's default behaviour does this; control retention via `OLLAMA_KEEP_ALIVE` and `OLLAMA_MAX_LOADED_MODELS`:

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    devices: [/dev/kfd, /dev/dri]
    group_add: [video, render]
    environment:
      - OLLAMA_KEEP_ALIVE=24h           # keep loaded models around
      - OLLAMA_MAX_LOADED_MODELS=2      # don't OOM the GPU
    volumes:
      - /mnt/tank/ai/ollama:/root/.ollama
```

For multi-GPU hosts (not the MS-S1 MAX — reference only), you can shard across cards with NVIDIA:

```yaml
# Reference: NOT used on MS-S1 MAX (single iGPU)
services:
  ollama-1:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0"]
              capabilities: [gpu]
    volumes:
      - ollama_data_1:/root/.ollama

  ollama-2:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["1"]
              capabilities: [gpu]
    volumes:
      - ollama_data_2:/root/.ollama

  nginx:
    image: nginx:alpine
    ports:
      - "11434:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf:ro
```

`nginx-lb.conf`:

```nginx
events {}

http {
    upstream ollama_cluster {
        least_conn;
        server ollama-1:11434;
        server ollama-2:11434;
    }

    server {
        listen 80;
        location / {
            proxy_pass http://ollama_cluster;
            proxy_http_version 1.1;
            proxy_read_timeout 300s;
        }
    }
}
```

## Integration with Coding Tools

### Aider

```bash
# Use Ollama container from Aider
aider --model ollama/llama3.3 --ollama-host http://localhost:11434
```

### Continue.dev

```json
{
  "models": [
    {
      "title": "Ollama Docker",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "apiBase": "http://localhost:11434"
    }
  ]
}
```

### Cline

In VS Code settings:

```json
{
  "cline.apiProvider": "ollama",
  "cline.ollamaBaseUrl": "http://localhost:11434",
  "cline.ollamaModelId": "qwen2.5-coder:32b"
}
```

## Complete Production Stack

ROCm version for the MS-S1 MAX (this build's default):

```yaml
# docker-compose.yml
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
    volumes:
      - /mnt/tank/ai/ollama:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - ai_network

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - /mnt/tank/containers/open-webui:/app/backend/data  # bind to ZFS dataset
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_AUTH=true
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
      - DEFAULT_MODELS=llama3.3
    depends_on:
      ollama:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - ai_network

  # Optional: API gateway
  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - ai_network

networks:
  ai_network:
    driver: bridge
```

## Troubleshooting

### GPU Not Detected

```bash
# Verify ROCm devices are present on the host
ls -l /dev/kfd /dev/dri

# Test GPU access from a container
docker run --rm --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal:latest rocminfo | head

# Check Ollama logs
docker compose logs ollama
```

### Out of Memory

```bash
# Check GPU/VRAM usage
rocm-smi

# Use smaller model or quantized version
ollama pull llama3.2:8b-q4_K_M
```

### Slow Inference

- Ensure the GPU is being used (`rocm-smi` should show utilization during inference)
- On ROCm 7.x with gfx1151 (Strix Halo) do **not** set `HSA_OVERRIDE_GFX_VERSION` — native support is included and the override can force the wrong code path. It is only needed for older AMD GPUs on ROCm 6.x (see the note above).
- Use quantized models for faster loading
- Increase GPU memory allocation if running other ROCm workloads

### Connection Refused

```bash
# Check Ollama is running
curl http://localhost:11434/

# Check container logs
docker compose logs ollama

# Verify port mapping
docker compose ps
```

## See Also

- [Ollama](../ai/inference-engines/ollama.md) - Ollama reference
- [Docker Compose](compose.md) - Compose reference
- [AI Coding Tools](../ai/coding-tools/index.md) - Integration with coding tools
- [GPU Containers](../ai/containers/gpu-containers.md) - GPU setup
