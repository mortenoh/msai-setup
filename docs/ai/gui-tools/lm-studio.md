# LM Studio

Desktop application for running local LLMs with built-in model discovery and API server.

## Overview

LM Studio provides:

- **Model discovery** - Browse and download from HuggingFace
- **Chat interface** - Built-in conversation UI
- **Local server** - OpenAI-compatible API
- **Model configuration** - GPU layers, context, parameters
- **Cross-platform** - macOS, Windows, Linux

## Installation

### Download

Get LM Studio from [lmstudio.ai](https://lmstudio.ai):

- **macOS**: `.dmg` installer (Apple Silicon or Intel)
- **Windows**: `.exe` installer
- **Linux**: `.AppImage`

### Linux Installation

```bash
# Download AppImage
wget https://releases.lmstudio.ai/linux/x86/LM-Studio-x.x.x.AppImage

# Make executable
chmod +x LM-Studio-*.AppImage

# Run
./LM-Studio-*.AppImage

# Or install system-wide
sudo mv LM-Studio-*.AppImage /opt/lm-studio
sudo ln -s /opt/lm-studio /usr/local/bin/lm-studio
```

### First Run

1. Launch LM Studio
2. Sign in (optional, enables cloud sync)
3. Select model storage location
4. Browse and download a model

## Model Management

### Downloading Models

1. Click **Search** (magnifying glass)
2. Search for model (e.g., "llama 3.3")
3. Select quantization (Q4_K_M recommended for 128GB)
4. Click **Download**

### Recommended Models for 128GB

| Model | Quantization | Size | Use Case |
|-------|--------------|------|----------|
| Llama 3.3 70B | Q4_K_M | ~43GB | General |
| Qwen 2.5 72B | Q4_K_M | ~45GB | Multilingual |
| DeepSeek Coder V2 | Q4_K_M | Varies | Coding |
| Mistral 7B | Q8_0 | ~8GB | Fast |

### Model Settings

Configure per-model settings:

| Setting | Description | Recommended |
|---------|-------------|-------------|
| GPU Layers | Layers offloaded to GPU | Max (all) |
| Context Length | Max tokens in context | 8192+ |
| CPU Threads | Threads for CPU work | Auto |
| Batch Size | Tokens processed together | 512 |

## Chat Interface

### Basic Usage

1. Select model from dropdown
2. Type message and press Enter
3. View streaming response

### System Prompt

Set a system prompt in the chat settings:

```
You are a helpful coding assistant. Focus on Python and TypeScript.
Provide concise, well-documented code examples.
```

### Chat Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Temperature | Randomness | 0.7 |
| Top P | Nucleus sampling | 0.95 |
| Max Tokens | Response length | 2048 |
| Repeat Penalty | Reduce repetition | 1.1 |

## Local Server

### Enable Server

1. Click **Local Server** tab
2. Select model to serve
3. Click **Start Server**

Default: `http://localhost:1234`

### Server Configuration

| Setting | Default | Notes |
|---------|---------|-------|
| Port | 1234 | Can be changed |
| Host | localhost | Change to 0.0.0.0 for network |
| CORS | Enabled | For browser clients |

### API Usage

```bash
# List models
curl http://localhost:1234/v1/models

# Chat completion
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "loaded-model",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### With Coding Tools

```bash
# Set environment for tools
export OPENAI_API_BASE=http://localhost:1234/v1
export OPENAI_API_KEY=not-needed

# Use with Aider
aider --openai-api-base http://localhost:1234/v1
```

## Performance Tips

### Memory Settings

For 128GB systems:

- **GPU Layers**: Maximum (all layers on GPU)
- **Context**: 16384 or higher
- **Leave headroom**: ~20-30GB for system

### GPU Utilization

Check GPU usage:

```bash
# NVIDIA
nvidia-smi -l 1

# AMD
rocm-smi
```

### Model Loading

- First load takes time (disk → memory)
- Keep frequently used models loaded
- Use smaller quantizations for faster switching

## Running in VM

For Windows VM with GPU passthrough:

### Requirements

- GPU passthrough configured (see [GPU Passthrough](../../virtualization/gpu-passthrough.md))
- Windows VM with GPU drivers
- LM Studio Windows version

### Setup

1. Install LM Studio in Windows VM
2. Download models (or use shared storage)
3. Start local server
4. Configure VM networking for API access

### Accessing from Host

```bash
# VM IP (example: 192.168.122.10)
export OPENAI_API_BASE=http://192.168.122.10:1234/v1

# Test connection
curl http://192.168.122.10:1234/v1/models
```

## CLI Mode

LM Studio has limited CLI support:

```bash
# Start server from CLI (if supported)
lm-studio server start --model "model-name"
```

For full CLI usage, consider [Ollama](../inference-engines/ollama.md) instead.

## Storage Location

### Default Locations

| Platform | Path |
|----------|------|
| macOS | `~/.cache/lm-studio` |
| Windows | `C:\Users\<user>\.cache\lm-studio` |
| Linux | `~/.cache/lm-studio` |

### Custom Location

Change in Settings → Storage to use ZFS dataset:

```
/tank/ai/models/lm-studio
```

## Comparison with Alternatives

| Feature | LM Studio | Ollama | Jan.ai |
|---------|-----------|--------|--------|
| GUI | Full | None | Full |
| Model discovery | Built-in | Library | Built-in |
| CLI | Limited | Full | Limited |
| Server | Yes | Yes | Yes |
| Container | No | Yes | No |

## Troubleshooting

### Model Won't Load

- Check available memory (70B Q4 needs ~45GB)
- Reduce GPU layers if memory limited
- Try smaller quantization

### Slow Generation

- Verify GPU layers are maxed
- Check GPU utilization
- Reduce context length if needed

### Server Connection Refused

- Verify server is started
- Check port isn't blocked
- For network access, change host to 0.0.0.0

### GPU Not Detected

- Update GPU drivers
- Reinstall LM Studio
- Check GPU compatibility

## See Also

- [GUI Tools Index](index.md) - Tool comparison
- [Choosing Models](../models/choosing-models.md) - Model selection
- [VM Integration](../vm-integration/index.md) - Windows VM setup
- [Ollama](../inference-engines/ollama.md) - CLI alternative
