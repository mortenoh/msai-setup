# LocalAI

Full OpenAI API replacement with support for text, images, audio, and embeddings.

## Overview

LocalAI provides:

- **Drop-in replacement** - Complete OpenAI API compatibility
- **Multimodal** - Text, images, audio, embeddings
- **Multiple backends** - llama.cpp, transformers, diffusers
- **Gallery** - Pre-configured model downloads
- **LocalAGI** - Agent framework support

## Quick Start

### Docker (Recommended)

```bash
# CPU only
docker run -p 8080:8080 \
  -v /tank/ai/models/localai:/models \
  --name localai \
  localai/localai:latest

# With NVIDIA GPU
docker run --gpus all -p 8080:8080 \
  -v /tank/ai/models/localai:/models \
  --name localai \
  localai/localai:latest-gpu-nvidia-cuda-12
```

### Docker Compose

```yaml
version: '3.8'

services:
  localai:
    image: localai/localai:latest-gpu-nvidia-cuda-12
    container_name: localai
    ports:
      - "8080:8080"
    volumes:
      - /tank/ai/models/localai:/models
    environment:
      - THREADS=8
      - CONTEXT_SIZE=8192
      - DEBUG=false
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

### AMD ROCm

```yaml
services:
  localai:
    image: localai/localai:latest-gpu-hipblas
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
```

## Installing Models

### From Gallery

```bash
# List available models
curl http://localhost:8080/models/available

# Install a model
curl http://localhost:8080/models/apply \
  -H "Content-Type: application/json" \
  -d '{"id": "llama-3-8b-instruct"}'
```

### From GGUF Files

Create model configuration:

```yaml
# /tank/ai/models/localai/llama-3.3-70b.yaml
name: llama-3.3-70b
backend: llama-cpp
parameters:
  model: /models/gguf/llama-3.3-70b-q4_k_m.gguf
  context_size: 8192
  gpu_layers: 99
  threads: 8

template:
  chat: |
    {{- if .System }}<|start_header_id|>system<|end_header_id|>
    {{ .System }}<|eot_id|>{{- end }}
    {{- range .Messages }}<|start_header_id|>{{ .Role }}<|end_header_id|>
    {{ .Content }}<|eot_id|>
    {{- end }}<|start_header_id|>assistant<|end_header_id|>
```

Mount GGUF files:

```yaml
volumes:
  - /tank/ai/models/localai:/models
  - /tank/ai/models/gguf:/models/gguf:ro
```

### Multiple Models

```yaml
# /models/llama-3.3-70b.yaml - Chat model
# /models/deepseek-coder.yaml - Code model
# /models/nomic-embed.yaml - Embeddings

# All available at /v1/models
curl http://localhost:8080/v1/models
```

## API Usage

### Chat Completion

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain Docker in one sentence."}
    ]
  }'
```

### Embeddings

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "input": "The quick brown fox"
  }'
```

### Image Generation (Stable Diffusion)

```bash
curl http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A sunset over mountains",
    "model": "stable-diffusion",
    "size": "512x512"
  }'
```

### Transcription (Whisper)

```bash
curl http://localhost:8080/v1/audio/transcriptions \
  -F "file=@audio.mp3" \
  -F "model=whisper-1"
```

### Text-to-Speech

```bash
curl http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world!",
    "voice": "alloy"
  }' \
  --output speech.mp3
```

## Configuration

### Model Configuration File

```yaml
# model.yaml
name: my-model
backend: llama-cpp

parameters:
  model: /models/model.gguf
  context_size: 8192
  gpu_layers: 99
  threads: 8

  # Sampling parameters
  temperature: 0.7
  top_p: 0.95
  top_k: 40
  repeat_penalty: 1.1

# Chat template
template:
  chat: |
    {{- range .Messages }}
    {{ .Role }}: {{ .Content }}
    {{- end }}
    assistant:

# Stop tokens
stopwords:
  - "user:"
  - "<|eot_id|>"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `THREADS` | CPU threads | Auto |
| `CONTEXT_SIZE` | Default context | 512 |
| `DEBUG` | Debug logging | false |
| `MODELS_PATH` | Model directory | /models |
| `SINGLE_ACTIVE_BACKEND` | One model at a time | false |
| `PARALLEL_REQUESTS` | Concurrent requests | true |

### Memory Management

```yaml
environment:
  # Limit loaded models
  - SINGLE_ACTIVE_BACKEND=true

  # Or set keep-alive
  - WATCHDOG_IDLE=true
  - WATCHDOG_IDLE_TIMEOUT=300  # Unload after 5min idle
```

## Backends

LocalAI supports multiple inference backends:

| Backend | Models | Notes |
|---------|--------|-------|
| llama-cpp | GGUF | Primary for LLMs |
| transformers | Safetensors | HuggingFace models |
| diffusers | Stable Diffusion | Image generation |
| whisper | Whisper | Audio transcription |
| piper | TTS | Text-to-speech |
| bark | TTS | Neural TTS |

### Specify Backend

```yaml
# In model config
backend: llama-cpp  # or: transformers, diffusers, etc.
```

## Production Setup

### Full Stack

```yaml
version: '3.8'

services:
  localai:
    image: localai/localai:latest-gpu-nvidia-cuda-12
    container_name: localai
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - /tank/ai/models/localai:/models
      - /tank/ai/models/gguf:/models/gguf:ro
    environment:
      - THREADS=8
      - CONTEXT_SIZE=8192
      - DEBUG=false
      - WATCHDOG_IDLE=true
      - WATCHDOG_IDLE_TIMEOUT=600
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/readyz"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### With Reverse Proxy

```yaml
services:
  traefik:
    image: traefik:v3.0
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command:
      - --providers.docker
      - --entrypoints.web.address=:80

  localai:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.localai.rule=Host(`ai.example.com`)"
      - "traefik.http.services.localai.loadbalancer.server.port=8080"
```

## Monitoring

### Health Endpoints

```bash
# Readiness
curl http://localhost:8080/readyz

# Liveness
curl http://localhost:8080/healthz

# Metrics (Prometheus)
curl http://localhost:8080/metrics
```

### Debug Mode

```yaml
environment:
  - DEBUG=true
```

## Comparison with Alternatives

| Feature | LocalAI | Ollama | llama.cpp |
|---------|---------|--------|-----------|
| OpenAI API | Full | Partial | Partial |
| Model management | Gallery | Built-in | Manual |
| Multimodal | Yes | Limited | Limited |
| Image generation | Yes | No | No |
| Audio | Yes | No | No |
| Complexity | Medium | Low | Low |

## Troubleshooting

### Model Won't Load

```bash
# Check logs
docker logs localai

# Verify config
cat /tank/ai/models/localai/my-model.yaml

# Test model path
docker exec localai ls -la /models/gguf/
```

### GPU Not Used

```bash
# Verify GPU image
docker images | grep localai

# Check GPU in container
docker exec localai nvidia-smi

# Set GPU layers in config
parameters:
  gpu_layers: 99
```

### Out of Memory

```yaml
# Enable single backend mode
environment:
  - SINGLE_ACTIVE_BACKEND=true

# Reduce context
parameters:
  context_size: 4096
```

## See Also

- [API Serving Index](index.md) - Overview
- [OpenAI Compatible](openai-compatible.md) - API reference
- [Load Balancing](load-balancing.md) - Multi-backend setup
- [Container Deployment](../containers/index.md) - Docker setup
