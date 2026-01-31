# Ollama

Docker-like simplicity for running local LLMs with built-in model management.

## Overview

Ollama provides:

- **Simple CLI** - `ollama run llama3.3` to get started
- **Model library** - Built-in discovery and downloads
- **OpenAI-compatible API** - Drop-in replacement
- **Modelfiles** - Customize models like Dockerfiles
- **Cross-platform** - macOS, Linux, Windows

## Installation

### macOS

```bash
# Homebrew
brew install ollama

# Or download from ollama.com
curl -fsSL https://ollama.com/download/mac -o ollama.pkg
open ollama.pkg
```

### Linux

```bash
# Install script
curl -fsSL https://ollama.com/install.sh | sh

# Starts service automatically
systemctl status ollama
```

### Manual Service Setup

```bash
# Create service user
sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama

# Service file
sudo tee /etc/systemd/system/ollama.service <<EOF
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_MODELS=/tank/ai/models/ollama"

[Install]
WantedBy=default.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ollama
```

## Basic Usage

### Running Models

```bash
# Start chat with a model (downloads if needed)
ollama run llama3.3

# Specific version/quantization
ollama run llama3.3:70b-instruct-q4_K_M

# Exit chat
/bye
```

### Model Management

```bash
# List installed models
ollama list

# Pull a model
ollama pull deepseek-coder-v2:16b

# Show model info
ollama show llama3.3

# Remove a model
ollama rm llama3.3:latest

# Copy/rename model
ollama cp llama3.3 my-llama
```

### Check Status

```bash
# Running models
ollama ps

# Output:
# NAME              ID              SIZE     PROCESSOR  UNTIL
# llama3.3:70b      abc123def456    43 GB    GPU        4 minutes from now
```

## Popular Models

| Model | Size | Use Case | Command |
|-------|------|----------|---------|
| Llama 3.3 70B | ~43GB Q4 | General, coding | `ollama run llama3.3:70b` |
| Qwen 2.5 72B | ~45GB Q4 | Multilingual | `ollama run qwen2.5:72b` |
| DeepSeek Coder V2 | ~9GB | Coding | `ollama run deepseek-coder-v2` |
| Mistral Large 2 | ~75GB Q4 | General | `ollama run mistral-large` |
| Llama 3.2 8B | ~5GB | Fast, mobile | `ollama run llama3.2` |

For 128GB systems, 70B models at Q4 quantization work well.

## API Usage

### Chat Completion (OpenAI-compatible)

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain Docker in one paragraph."}
    ]
  }'
```

### Native API

```bash
# Generate (completion)
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3", "prompt": "Why is the sky blue?"}'

# Chat
curl http://localhost:11434/api/chat \
  -d '{
    "model": "llama3.3",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming (default)
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3", "prompt": "Tell me a story", "stream": true}'
```

### Embeddings

```bash
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "Hello world"}'
```

## Environment Variables

Configure via environment:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Listen address | `127.0.0.1:11434` |
| `OLLAMA_MODELS` | Model storage path | `~/.ollama/models` |
| `OLLAMA_NUM_PARALLEL` | Concurrent requests | 1 |
| `OLLAMA_MAX_LOADED_MODELS` | Models in memory | 1 |
| `OLLAMA_KEEP_ALIVE` | Model unload timeout | `5m` |
| `OLLAMA_DEBUG` | Debug logging | false |

Example configuration:

```bash
# In /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_MODELS=/tank/ai/models/ollama"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_KEEP_ALIVE=30m"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

## Modelfiles

Customize models with Dockerile-like syntax:

### Basic Modelfile

```dockerfile
# Modelfile
FROM llama3.3:70b

# Set system prompt
SYSTEM """
You are a senior software engineer. Write clean, efficient code.
Focus on Python and TypeScript.
"""

# Adjust parameters
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
```

### Build Custom Model

```bash
# Create model from Modelfile
ollama create coding-assistant -f Modelfile

# Run it
ollama run coding-assistant
```

### Import GGUF

```dockerfile
# Modelfile for GGUF import
FROM /tank/ai/models/gguf/custom-model.gguf

TEMPLATE """{{ if .System }}{{ .System }}

{{ end }}{{ if .Prompt }}User: {{ .Prompt }}
{{ end }}Assistant: """

PARAMETER stop "User:"
```

### Modelfile Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `FROM` | Base model or path | `llama3.3:70b` |
| `SYSTEM` | System prompt | `"You are..."` |
| `TEMPLATE` | Prompt template | Custom format |
| `PARAMETER temperature` | Randomness | `0.7` |
| `PARAMETER num_ctx` | Context length | `8192` |
| `PARAMETER num_gpu` | GPU layers | `99` |
| `PARAMETER stop` | Stop sequences | `["User:"]` |

## Multi-Model Setup

### Keep Multiple Models Loaded

```bash
# Allow 2 models in memory
export OLLAMA_MAX_LOADED_MODELS=2

# Load models
ollama run llama3.3
# In another terminal
ollama run deepseek-coder-v2
```

### Model Switching

```bash
# Check loaded models
ollama ps

# Unload a model
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3", "keep_alive": 0}'
```

## Integration Examples

### Python

```python
import ollama

response = ollama.chat(
    model='llama3.3',
    messages=[
        {'role': 'user', 'content': 'Explain Kubernetes briefly'}
    ]
)
print(response['message']['content'])
```

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'  # Required but ignored
)

response = client.chat.completions.create(
    model='llama3.3',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
```

### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'ollama'
});

const response = await client.chat.completions.create({
  model: 'llama3.3',
  messages: [{ role: 'user', content: 'Hello!' }]
});
```

## Performance

### GPU Memory Usage

```bash
# Check GPU allocation
ollama ps

# For 70B Q4 on 128GB Mac:
# - ~43GB for model weights
# - ~2GB for 8K context KV cache
# - Leaves ~80GB for system + other models
```

### Speed Comparison

On M4 Max (128GB), Llama 3.3 70B Q4:

| Metric | Value |
|--------|-------|
| Tokens/sec | ~35 |
| Time to first token | ~200ms |
| Context processing | ~500 tok/sec |

## Troubleshooting

### Model Download Fails

```bash
# Check disk space
df -h ~/.ollama

# Resume interrupted download
ollama pull llama3.3:70b

# Clear corrupted download
rm -rf ~/.ollama/models/blobs/sha256-<partial>
ollama pull llama3.3:70b
```

### Out of Memory

```bash
# Use smaller quantization
ollama run llama3.3:70b-instruct-q4_K_S  # Instead of Q4_K_M

# Reduce context
curl -d '{"model": "llama3.3", "options": {"num_ctx": 4096}}' \
  http://localhost:11434/api/generate
```

### Slow Startup

```bash
# Pre-load model on service start
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3", "keep_alive": "24h"}'
```

### API Connection Refused

```bash
# Bind to all interfaces
export OLLAMA_HOST=0.0.0.0
ollama serve

# Or in service file
Environment="OLLAMA_HOST=0.0.0.0"
```

## See Also

- [Inference Engines Index](index.md) - Engine comparison
- [Ollama Docker](../containers/ollama-docker.md) - Container deployment
- [OpenAI Compatible](../api-serving/openai-compatible.md) - API details
- [Model Volumes](../containers/model-volumes.md) - ZFS storage for models
