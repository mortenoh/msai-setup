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

Start:

```bash
docker compose up -d
```

Access:
- Open WebUI: http://localhost:3000
- Ollama API: http://localhost:11434

## GPU Passthrough

### NVIDIA GPU

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

Prerequisites:
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

Verify:
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### AMD ROCm

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    # environment:
    #   - HSA_OVERRIDE_GFX_VERSION=10.3.0  # Only for ROCm 6.x
    restart: unless-stopped
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

### Load Balancing Multiple Ollama Instances

```yaml
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

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - ollama_data:/root/.ollama
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
      - openwebui_data:/app/backend/data
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

volumes:
  ollama_data:
  openwebui_data:
```

## Troubleshooting

### GPU Not Detected

```bash
# Verify NVIDIA runtime
docker info | grep -i runtime

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check Ollama logs
docker compose logs ollama
```

### Out of Memory

```bash
# Check GPU memory
nvidia-smi

# Use smaller model or quantized version
ollama pull llama3.2:8b-q4_K_M
```

### Slow Inference

- Ensure GPU is being used (check nvidia-smi during inference)
- Use quantized models for faster loading
- Increase GPU memory allocation

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
