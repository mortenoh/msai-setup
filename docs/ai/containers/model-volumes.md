# Model Volumes

Configure ZFS storage for LLM model files with optimal settings.

## Overview

LLM models require careful storage configuration:

- **Large files** - 40-180GB per model
- **Sequential reads** - Model loading reads entire file
- **Minimal writes** - Models rarely change after download
- **Shared access** - Multiple containers may read same models

## ZFS Dataset Structure

### Create Datasets

```bash
# Parent dataset for AI workloads
zfs create tank/ai

# Models dataset with optimized settings
zfs create -o recordsize=1M \
           -o compression=off \
           -o atime=off \
           -o xattr=sa \
           tank/ai/models

# Subdatasets for different formats
zfs create tank/ai/models/ollama
zfs create tank/ai/models/gguf
zfs create tank/ai/models/huggingface

# Application data (different requirements)
zfs create -o recordsize=128K \
           -o compression=zstd \
           tank/ai/data
```

### Dataset Layout

```
tank/ai/
├── models/              # recordsize=1M, compression=off
│   ├── ollama/          # Ollama model storage
│   ├── gguf/            # GGUF files for llama.cpp
│   └── huggingface/     # HuggingFace cache
└── data/                # recordsize=128K, compression=zstd
    ├── open-webui/      # Open WebUI data
    └── embeddings/      # Vector databases
```

## Dataset Properties

### For Model Files

| Property | Value | Reason |
|----------|-------|--------|
| `recordsize` | `1M` | Large sequential reads |
| `compression` | `off` | Models already compressed |
| `atime` | `off` | No access time updates |
| `xattr` | `sa` | Extended attributes in inode |
| `sync` | `standard` | Default durability |

```bash
# Apply settings
zfs set recordsize=1M tank/ai/models
zfs set compression=off tank/ai/models
zfs set atime=off tank/ai/models
zfs set xattr=sa tank/ai/models
```

### For Application Data

| Property | Value | Reason |
|----------|-------|--------|
| `recordsize` | `128K` | Mixed I/O patterns |
| `compression` | `zstd` | Good compression for databases |
| `atime` | `off` | Performance |

```bash
zfs set recordsize=128K tank/ai/data
zfs set compression=zstd tank/ai/data
zfs set atime=off tank/ai/data
```

## Storage Sizing

### Model Size Reference

| Model | Quantization | Size | Notes |
|-------|--------------|------|-------|
| Llama 3.2 8B | Q8_0 | ~10GB | Small model |
| Qwen 2.5 32B | Q5_K_M | ~25GB | Medium |
| Llama 3.3 70B | Q4_K_M | ~43GB | Large |
| Llama 3.3 70B | Q6_K | ~58GB | High quality |
| Llama 3.1 405B | Q4_K_M | ~180GB | Very large |

### Capacity Planning

```
Recommended minimum for 128GB RAM system:

Basic setup (2-3 models):
  tank/ai/models: 200GB

Comfortable (5-10 models):
  tank/ai/models: 500GB

Power user (many quants/versions):
  tank/ai/models: 1TB+
```

## Docker Volume Mounts

### Read-Only Model Access

For containers that only read models:

```yaml
services:
  llama-server:
    volumes:
      - /tank/ai/models/gguf:/models:ro  # Read-only
```

### Read-Write for Ollama

Ollama needs write access to download/manage models:

```yaml
services:
  ollama:
    volumes:
      - /tank/ai/models/ollama:/root/.ollama  # Read-write
```

### Shared Access Pattern

```yaml
version: '3.8'

services:
  ollama:
    volumes:
      - /tank/ai/models/ollama:/root/.ollama

  llama-server:
    volumes:
      - /tank/ai/models/gguf:/models:ro
      # Or share Ollama's blobs
      - /tank/ai/models/ollama/models/blobs:/blobs:ro

  open-webui:
    volumes:
      - /tank/ai/data/open-webui:/app/backend/data
```

## Directory Organization

### GGUF Models

```
/tank/ai/models/gguf/
├── llama/
│   ├── llama-3.3-70b-instruct-q4_k_m.gguf
│   ├── llama-3.3-70b-instruct-q5_k_m.gguf
│   └── llama-3.2-8b-instruct-q8_0.gguf
├── qwen/
│   ├── qwen2.5-72b-instruct-q4_k_m.gguf
│   └── qwen2.5-coder-32b-instruct-q5_k_m.gguf
├── deepseek/
│   └── deepseek-coder-v2-16b-q8_0.gguf
└── mistral/
    └── mistral-large-2-q4_k_m.gguf
```

### Hugging Face Cache

```
/tank/ai/models/huggingface/
└── hub/
    ├── models--meta-llama--Llama-3.3-70B-Instruct/
    │   ├── refs/
    │   ├── blobs/
    │   └── snapshots/
    └── models--Qwen--Qwen2.5-72B-Instruct/
```

### Ollama Storage

```
/tank/ai/models/ollama/
└── models/
    ├── blobs/
    │   └── sha256-xxxxx  # Actual model files
    └── manifests/
        └── registry.ollama.ai/
            └── library/
                ├── llama3.3/
                └── deepseek-coder-v2/
```

## Environment Variables

Configure applications to use mounted paths:

```yaml
services:
  ollama:
    environment:
      - OLLAMA_MODELS=/root/.ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama

  vllm:
    environment:
      - HF_HOME=/root/.cache/huggingface
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    volumes:
      - /tank/ai/models/huggingface:/root/.cache/huggingface
```

## Snapshots and Backup

### Create Snapshots

```bash
# Snapshot before major changes
zfs snapshot tank/ai/models@before-update

# Snapshot with date
zfs snapshot tank/ai/models@$(date +%Y-%m-%d)
```

### Rollback

```bash
# If model download corrupted
zfs rollback tank/ai/models@before-update
```

### List Snapshots

```bash
zfs list -t snapshot -r tank/ai
```

### Space Efficiency

Models are mostly static, so snapshots are space-efficient:

```bash
# Check snapshot space usage
zfs list -o name,used,refer -t snapshot -r tank/ai/models
```

## Performance Tuning

### Memory Caching

ZFS ARC (cache) helps with repeated model loads:

```bash
# Check ARC stats
arc_summary

# Models benefit from ARC for faster subsequent loads
# Especially important for small/medium models
```

### Read Prefetch

Large sequential reads benefit from prefetch:

```bash
# Verify prefetch is enabled (default)
cat /sys/module/zfs/parameters/zfs_prefetch_disable
# Should be 0

# Tune for large files
echo 67108864 > /sys/module/zfs/parameters/zfs_read_chunk_size
```

### SSD vs HDD

| Storage | Model Load Time | Notes |
|---------|----------------|-------|
| NVMe SSD | 5-30 seconds | Recommended |
| SATA SSD | 15-60 seconds | Acceptable |
| HDD | 60-300 seconds | Slow but works |

## Monitoring

### Space Usage

```bash
# Dataset usage
zfs list -o name,used,avail,refer tank/ai/models

# Directory sizes
du -sh /tank/ai/models/*/
```

### I/O Statistics

```bash
# ZFS I/O stats
zpool iostat -v 1

# During model load
iostat -x 1
```

## Troubleshooting

### Container Can't Read Models

```bash
# Check mount
docker exec container ls -la /models

# Verify permissions
ls -la /tank/ai/models/gguf/

# Check SELinux/AppArmor if applicable
```

### Slow Model Loading

```bash
# Check for disk I/O bottleneck
iostat -x 1

# Verify recordsize
zfs get recordsize tank/ai/models
# Should be 1M

# Check ARC hit rate
arc_summary | grep -A5 "ARC Size"
```

### Disk Full

```bash
# Find large files
du -sh /tank/ai/models/*/* | sort -h

# Remove old models
rm /tank/ai/models/gguf/old-model.gguf

# Or through Ollama
docker exec ollama ollama rm old-model
```

## See Also

- [ZFS Datasets](../../zfs/datasets.md) - ZFS configuration
- [Container Deployment](index.md) - Container overview
- [Hugging Face](../models/huggingface.md) - Model downloads
- [GGUF Formats](../models/gguf-formats.md) - File format details
