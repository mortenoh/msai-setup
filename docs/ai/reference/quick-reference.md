# Quick Reference

Command cheat sheet for local LLM operations.

## Ollama

### Basic Commands

```bash
# Start server
ollama serve

# Run model (pulls if needed)
ollama run llama3.3:70b

# Pull model
ollama pull llama3.3:70b-instruct-q4_K_M

# List models
ollama list

# Show model info
ollama show llama3.3:70b

# Remove model
ollama rm llama3.3:70b

# Copy/rename model
ollama cp llama3.3:70b my-llama

# Running models
ollama ps

# Stop model
ollama stop llama3.3:70b
```

### API Calls

```bash
# Chat completion (OpenAI compatible)
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.3", "messages": [{"role": "user", "content": "Hello"}]}'

# Native generate
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3", "prompt": "Hello", "stream": false}'

# Embeddings
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "Hello world"}'

# List models
curl http://localhost:11434/v1/models
```

### Environment Variables

```bash
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MODELS=/tank/ai/models/ollama
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_KEEP_ALIVE=30m
```

## llama.cpp

### Build

```bash
# Clone
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build (CUDA)
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release

# Build (ROCm)
cmake -B build -DGGML_HIP=ON
cmake --build build --config Release

# Build (Metal - macOS)
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release
```

### Server

```bash
# Basic server
./llama-server \
  -m model.gguf \
  --host 0.0.0.0 \
  --port 8080

# Full options
./llama-server \
  -m model.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \          # Context length
  -ngl 99 \          # GPU layers
  --parallel 4 \     # Concurrent requests
  --cont-batching \  # Continuous batching
  --flash-attn \     # Flash attention
  --metrics          # Enable metrics
```

### Benchmarking

```bash
./llama-bench \
  -m model.gguf \
  -p 512 \    # Prompt tokens
  -n 128 \    # Generated tokens
  -ngl 99 \   # GPU layers
  -r 5        # Repetitions
```

### CLI Inference

```bash
./llama-cli \
  -m model.gguf \
  -p "Hello, how are you?" \
  -n 100 \
  -ngl 99
```

## Docker

### Ollama

```bash
# Start Ollama (NVIDIA)
docker run -d \
  --gpus all \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# Start Ollama (AMD)
docker run -d \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama:rocm

# Run command in container
docker exec ollama ollama pull llama3.3:70b
docker exec -it ollama ollama run llama3.3:70b
```

### llama.cpp

```bash
# Start server (NVIDIA)
docker run -d \
  --gpus all \
  -v /tank/ai/models/gguf:/models \
  -p 8080:8080 \
  --name llama-server \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/llama-3.3-70b-q4_k_m.gguf \
  --host 0.0.0.0 -c 8192 -ngl 99

# Start server (AMD)
docker run -d \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  -v /tank/ai/models/gguf:/models \
  -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server-rocm \
  -m /models/llama-3.3-70b-q4_k_m.gguf \
  --host 0.0.0.0 -c 8192 -ngl 99
```

### Open WebUI

```bash
docker run -d \
  -p 3000:8080 \
  -v /tank/ai/data/open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## Hugging Face

```bash
# Login
huggingface-cli login

# Download model
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct

# Download GGUF
huggingface-cli download bartowski/Llama-3.3-70B-Instruct-GGUF \
  --include "*.Q4_K_M.gguf" \
  --local-dir /tank/ai/models/gguf/

# Scan cache
huggingface-cli scan-cache

# Set cache location
export HF_HOME=/tank/ai/models/huggingface
```

## GPU Monitoring

### NVIDIA

```bash
# Basic status
nvidia-smi

# Continuous monitoring
nvidia-smi -l 1

# Memory only
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Watch utilization
watch -n 1 nvidia-smi
```

### AMD

```bash
# Basic status
rocm-smi

# Memory info
rocm-smi --showmeminfo vram

# Watch
watch -n 1 rocm-smi
```

## ZFS for Models

```bash
# Create dataset
zfs create -o recordsize=1M -o compression=off tank/ai/models

# Create subdatasets
zfs create tank/ai/models/ollama
zfs create tank/ai/models/gguf
zfs create tank/ai/models/huggingface

# Snapshot
zfs snapshot tank/ai/models@backup

# Check usage
zfs list -r tank/ai/models
```

## Tailscale

```bash
# Expose Ollama
tailscale serve --bg https+insecure://localhost:11434

# Check status
tailscale serve status

# Reset
tailscale serve reset
```

## Coding Tools

### Aider

```bash
# With Ollama
aider --model ollama/deepseek-coder-v2:16b

# With OpenAI-compatible
aider --openai-api-base http://localhost:8080/v1 --model llama3.3

# Add files
aider src/main.py tests/test_main.py
```

### Environment Setup

```bash
# For OpenAI-compatible tools
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=not-needed

# For Ollama-native tools
export OLLAMA_HOST=http://localhost:11434
```

## Testing

```bash
# Test Ollama
curl http://localhost:11434/

# Test llama.cpp
curl http://localhost:8080/health

# Test chat
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.3", "messages": [{"role": "user", "content": "Hi"}]}'

# List models
curl http://localhost:11434/v1/models
```
