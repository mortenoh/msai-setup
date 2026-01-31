# Container Deployment

Deploy LLM inference engines in Docker containers with persistent model storage.

## Overview

Containerized LLM deployment provides:

- **Isolation** - Separate engines, models, and configurations
- **Reproducibility** - Consistent environments across systems
- **Easy updates** - Pull new images without affecting data
- **ZFS integration** - Models stored on persistent datasets

## Container Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker/Podman Host                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Ollama    │  │ llama.cpp   │  │      Open WebUI         │  │
│  │  Container  │  │  Container  │  │       Container         │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
│         │                │                      │               │
│         └────────────────┴──────────────────────┘               │
│                          │                                      │
│              OpenAI-Compatible APIs                             │
│                          │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│                    Volume Mounts                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 /tank/ai/models                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │  │
│  │  │   ollama/   │  │    gguf/    │  │  huggingface/   │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## GPU Access in Containers

### NVIDIA GPUs

Excellent container support via nvidia-container-toolkit:

```yaml
services:
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### AMD GPUs (ROCm)

Good support on Linux with ROCm:

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
```

See [GPU Containers](gpu-containers.md) for detailed GPU setup.

## Container Comparison

| Feature | Ollama | llama.cpp | LocalAI |
|---------|--------|-----------|---------|
| Setup complexity | Easy | Medium | Medium |
| Model management | Built-in | Manual | Manual |
| GPU support | NVIDIA, AMD | NVIDIA, AMD, Vulkan | NVIDIA, AMD |
| OpenAI API | Yes | Yes | Yes |
| Multi-model | Yes | Per-instance | Yes |
| Official image | Yes | Yes | Yes |

## Quick Start

### Ollama (Recommended)

```bash
# Start Ollama container
docker run -d \
  --gpus all \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# Pull and run a model
docker exec ollama ollama run llama3.3
```

### llama.cpp

```bash
# Start llama.cpp server
docker run -d \
  --gpus all \
  -v /tank/ai/models/gguf:/models \
  -p 8080:8080 \
  --name llama-server \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/llama-3.3-70b-q4_k_m.gguf \
  -c 8192 -ngl 99
```

## Storage Layout

### ZFS Dataset Structure

```bash
# Create AI models dataset
zfs create tank/ai
zfs create -o recordsize=1M tank/ai/models
zfs create tank/ai/models/ollama
zfs create tank/ai/models/gguf
zfs create tank/ai/models/huggingface
```

### Volume Mounts

```yaml
volumes:
  - /tank/ai/models/ollama:/root/.ollama
  - /tank/ai/models/gguf:/models:ro
  - /tank/ai/models/huggingface:/root/.cache/huggingface:ro
```

## Network Configuration

### Internal Network

```yaml
networks:
  ai-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/24

services:
  ollama:
    networks:
      - ai-net
  webui:
    networks:
      - ai-net
    environment:
      - OLLAMA_API_BASE_URL=http://ollama:11434
```

### External Access

```yaml
services:
  ollama:
    ports:
      - "127.0.0.1:11434:11434"  # Local only
      # Or
      - "11434:11434"  # Network access (use with firewall)
```

## Topics

<div class="grid cards" markdown>

-   :material-llama: **llama.cpp Docker**

    ---

    Official llama.cpp container with GPU support

    [:octicons-arrow-right-24: Setup guide](llama-cpp-docker.md)

-   :material-cube: **Ollama Docker**

    ---

    Ollama container with model persistence

    [:octicons-arrow-right-24: Setup guide](ollama-docker.md)

-   :material-harddisk: **Model Volumes**

    ---

    ZFS dataset configuration for model storage

    [:octicons-arrow-right-24: Storage setup](model-volumes.md)

-   :material-gpu: **GPU Containers**

    ---

    GPU passthrough for NVIDIA and AMD

    [:octicons-arrow-right-24: GPU setup](gpu-containers.md)

</div>

## Common Patterns

### Development Stack

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
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

  webui:
    image: ghcr.io/open-webui/open-webui:main
    volumes:
      - /tank/ai/data/webui:/app/backend/data
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
```

### Multi-Backend

```yaml
services:
  ollama:
    # Fast model switching
    image: ollama/ollama
    # ...

  llama-server:
    # Specific model, fine-tuned config
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    # ...

  traefik:
    # Route requests to appropriate backend
    image: traefik:v3.0
    # ...
```

## See Also

- [Docker Setup](../../docker/setup.md) - Docker installation
- [ZFS Datasets](../../zfs/datasets.md) - Dataset configuration
- [Inference Engines](../inference-engines/index.md) - Engine comparison
- [API Serving](../api-serving/index.md) - API configuration
