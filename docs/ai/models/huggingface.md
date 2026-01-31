# Hugging Face

Download and manage models from the Hugging Face Hub.

## Overview

Hugging Face Hub is the primary source for:

- Open-weights models (Llama, Qwen, Mistral, etc.)
- GGUF quantized models (via TheBloke, bartowski, mlx-community)
- Model cards and documentation
- Datasets and tools

## Installation

### CLI Setup

```bash
# Install huggingface_hub
pip install huggingface_hub

# Or with uv
uv pip install huggingface_hub

# Verify installation
huggingface-cli --help
```

### Authentication

Required for gated models (Llama, etc.):

```bash
# Login (opens browser)
huggingface-cli login

# Or with token directly
huggingface-cli login --token hf_xxxxx

# Verify login
huggingface-cli whoami
```

Get tokens at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

## Downloading Models

### Basic Download

```bash
# Download entire model
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct

# Download to specific directory
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct \
  --local-dir /tank/ai/models/huggingface/Llama-3.3-70B-Instruct
```

### Download GGUF Files

```bash
# Download specific GGUF file
huggingface-cli download bartowski/Llama-3.3-70B-Instruct-GGUF \
  --include "Llama-3.3-70B-Instruct-Q4_K_M.gguf" \
  --local-dir /tank/ai/models/gguf/

# Download multiple quants
huggingface-cli download bartowski/Llama-3.3-70B-Instruct-GGUF \
  --include "*.Q4_K_M.gguf" "*.Q5_K_M.gguf" \
  --local-dir /tank/ai/models/gguf/
```

### Split Files

Large models are often split:

```bash
# Download split GGUF (auto-combines in llama.cpp)
huggingface-cli download bartowski/Llama-3.1-405B-Instruct-GGUF \
  --include "*Q4_K_M*" \
  --local-dir /tank/ai/models/gguf/

# Results in:
# Llama-3.1-405B-Instruct-Q4_K_M-00001-of-00004.gguf
# Llama-3.1-405B-Instruct-Q4_K_M-00002-of-00004.gguf
# ...
```

### Resume Downloads

Downloads automatically resume:

```bash
# Interrupted download - just run again
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct
# Resumes from where it left off
```

## Cache Management

### Default Cache Location

```bash
# Default: ~/.cache/huggingface
echo $HF_HOME

# View cache contents
huggingface-cli scan-cache
```

### Custom Cache Directory

```bash
# Set custom cache (ZFS dataset)
export HF_HOME=/tank/ai/models/huggingface

# Add to shell profile
echo 'export HF_HOME=/tank/ai/models/huggingface' >> ~/.bashrc
```

### Cache Structure

```
$HF_HOME/
└── hub/
    └── models--meta-llama--Llama-3.3-70B-Instruct/
        ├── refs/
        │   └── main
        ├── blobs/
        │   └── <sha256 hashes>
        └── snapshots/
            └── <commit hash>/
                ├── config.json
                ├── model-00001-of-00016.safetensors
                └── ...
```

### Clear Cache

```bash
# Show cache usage
huggingface-cli scan-cache

# Delete specific model
huggingface-cli delete-cache --pattern "*Llama-2*"

# Interactive deletion
huggingface-cli delete-cache
```

## Gated Models

Some models require accepting a license:

### Accessing Gated Models

1. Visit model page (e.g., [meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct))
2. Click "Access repository" and accept license
3. Wait for approval (usually instant for Llama)
4. Download with authenticated CLI

```bash
# After accepting license
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct
```

### Common Gated Models

| Model Family | License | Approval |
|--------------|---------|----------|
| Llama 2/3 | Meta License | Instant |
| Mistral | Apache 2.0 | None needed |
| Qwen | Tongyi License | Instant |
| Gemma | Google Terms | Instant |

## Popular Model Sources

### GGUF Models

| Source | Specialty | Example |
|--------|-----------|---------|
| bartowski | High quality quants | `bartowski/Llama-3.3-70B-Instruct-GGUF` |
| TheBloke | Wide selection | `TheBloke/Llama-2-70B-Chat-GGUF` |
| QuantFactory | Various quants | `QuantFactory/Qwen2.5-72B-Instruct-GGUF` |
| mlx-community | MLX format | `mlx-community/Llama-3.3-70B-Instruct-4bit` |

### Safetensors Models

| Source | Models |
|--------|--------|
| meta-llama | Llama 2, 3, 3.1, 3.2, 3.3 |
| Qwen | Qwen 2, 2.5 |
| mistralai | Mistral, Mixtral |
| google | Gemma 2 |
| deepseek-ai | DeepSeek Coder, V3 |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_HOME` | Cache directory | `~/.cache/huggingface` |
| `HF_TOKEN` | Auth token | None |
| `HF_HUB_OFFLINE` | Offline mode | `0` |
| `HF_HUB_ENABLE_HF_TRANSFER` | Fast downloads | `0` |

### Fast Downloads

Enable hf_transfer for faster downloads:

```bash
# Install
pip install hf_transfer

# Enable
export HF_HUB_ENABLE_HF_TRANSFER=1

# Download with faster transfer
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct
```

## Python API

### Basic Usage

```python
from huggingface_hub import hf_hub_download, snapshot_download

# Download single file
model_path = hf_hub_download(
    repo_id="bartowski/Llama-3.3-70B-Instruct-GGUF",
    filename="Llama-3.3-70B-Instruct-Q4_K_M.gguf",
    local_dir="/tank/ai/models/gguf"
)

# Download entire repo
snapshot_download(
    repo_id="meta-llama/Llama-3.3-70B-Instruct",
    local_dir="/tank/ai/models/huggingface/Llama-3.3-70B"
)
```

### With Filtering

```python
from huggingface_hub import snapshot_download

# Only safetensors and config
snapshot_download(
    repo_id="meta-llama/Llama-3.3-70B-Instruct",
    allow_patterns=["*.safetensors", "*.json"],
    ignore_patterns=["*.bin", "*.h5"]
)
```

## Mounting in Containers

### Docker Volume Mount

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - /tank/ai/models/huggingface:/root/.cache/huggingface:ro
      - /tank/ai/models/ollama:/root/.ollama
```

### Pass Token to Container

```yaml
services:
  vllm:
    image: vllm/vllm-openai
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    volumes:
      - /tank/ai/models/huggingface:/root/.cache/huggingface
```

## Troubleshooting

### Download Fails

```bash
# Check network
curl -I https://huggingface.co

# Clear partial downloads
rm -rf ~/.cache/huggingface/hub/models--<model>/blobs/*.incomplete

# Retry with resume
huggingface-cli download <model>
```

### Permission Denied (Gated Model)

```bash
# Verify login
huggingface-cli whoami

# Re-login
huggingface-cli login

# Check license acceptance on web
# Visit model page, ensure "Access granted"
```

### Disk Space

```bash
# Check cache size
huggingface-cli scan-cache

# Use separate ZFS dataset
zfs create -o recordsize=1M tank/ai/models/huggingface

# Point HF_HOME there
export HF_HOME=/tank/ai/models/huggingface
```

## See Also

- [Model Volumes](../containers/model-volumes.md) - ZFS storage for models
- [GGUF Formats](gguf-formats.md) - GGUF file details
- [Choosing Models](choosing-models.md) - Model selection guide
- [Ollama](../inference-engines/ollama.md) - Using models with Ollama
