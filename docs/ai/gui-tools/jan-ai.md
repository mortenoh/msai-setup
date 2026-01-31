# Jan.ai

Privacy-first, 100% offline AI assistant with no telemetry.

## Overview

Jan.ai provides:

- **Complete offline operation** - No internet required after download
- **Zero telemetry** - No data collection
- **ChatGPT-style UI** - Familiar interface
- **Extensions** - Extend functionality
- **Open source** - Full transparency

## Installation

### Download

Get Jan from [jan.ai](https://jan.ai):

- **macOS**: `.dmg` (Apple Silicon and Intel)
- **Windows**: `.exe` installer
- **Linux**: `.deb` or `.AppImage`

### Linux Installation

```bash
# Debian/Ubuntu
wget https://github.com/janhq/jan/releases/latest/download/jan-linux-amd64.deb
sudo dpkg -i jan-linux-amd64.deb

# Or AppImage
wget https://github.com/janhq/jan/releases/latest/download/jan-linux-x86_64.AppImage
chmod +x jan-linux-x86_64.AppImage
./jan-linux-x86_64.AppImage
```

### Verify Installation

Launch Jan and verify:
- App opens successfully
- No network connections made (check with network monitor)

## Privacy Features

| Feature | Implementation |
|---------|----------------|
| Offline mode | Works without internet |
| No telemetry | No usage data sent |
| Local models | Models stored locally |
| No accounts | No sign-in required |
| Open source | Auditable code |

## Model Management

### Built-in Hub

1. Click **Hub** in sidebar
2. Browse available models
3. Click **Download**

### Recommended Models

| Model | Size | Use Case |
|-------|------|----------|
| Llama 3.3 70B | ~43GB | General |
| Qwen 2.5 | Various | Multilingual |
| Mistral 7B | ~5GB | Fast responses |
| DeepSeek Coder | Various | Coding |

### Import Custom Models

Place GGUF files in Jan's models directory:

```bash
# Find Jan data directory
# Linux: ~/.jan
# macOS: ~/Library/Application Support/Jan
# Windows: %APPDATA%\Jan

# Copy model
cp /tank/ai/models/gguf/model.gguf ~/.jan/models/
```

Create model configuration:

```json
// ~/.jan/models/my-model/model.json
{
  "id": "my-model",
  "name": "My Custom Model",
  "version": "1.0",
  "description": "Custom imported model",
  "format": "gguf",
  "settings": {
    "ctx_len": 8192,
    "ngl": 99
  },
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.95
  },
  "engine": "nitro"
}
```

## Chat Interface

### Creating Conversations

1. Click **New Thread**
2. Select model from dropdown
3. Start chatting

### Thread Features

- **Named threads** - Organize conversations
- **Search** - Find past conversations
- **Export** - Save conversation as file
- **System prompts** - Set per-thread

### Model Settings

Adjust per-conversation:

| Setting | Description |
|---------|-------------|
| Temperature | Response randomness |
| Top P | Token sampling |
| Max Tokens | Response length |
| Context Length | Conversation memory |

## Local Server

### Enable API Server

1. Settings → Advanced
2. Enable **Local API Server**
3. Configure port (default: 1337)

### API Usage

```bash
# List models
curl http://localhost:1337/v1/models

# Chat completion
curl http://localhost:1337/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Extensions

### Available Extensions

| Extension | Purpose |
|-----------|---------|
| Inference Engine | Core model running |
| Monitoring | System metrics |
| Conversational | Chat features |

### Managing Extensions

1. Settings → Extensions
2. Browse available extensions
3. Install/update as needed

## Configuration

### Data Directory

Change storage location:

1. Settings → Advanced
2. Set **Data Folder** path

For ZFS:

```
/tank/ai/jan
```

### Model Settings

Global defaults in Settings → Models:

| Setting | Description | Default |
|---------|-------------|---------|
| Default model | Auto-load model | None |
| Context length | Default context | 4096 |
| GPU layers | Offload to GPU | Auto |

## Resource Usage

### Memory Management

Jan uses llama.cpp backend:

- Models load into RAM/VRAM
- Context grows with conversation
- Close unused models to free memory

### GPU Utilization

Check GPU settings:

1. Settings → Models
2. Set GPU layers (higher = more VRAM)

## Comparison with Alternatives

| Feature | Jan.ai | LM Studio | Open WebUI |
|---------|--------|-----------|------------|
| Offline | 100% | Yes | Backend dependent |
| Telemetry | None | Some | None |
| Open source | Yes | No | Yes |
| Model hub | Built-in | Built-in | External |
| Extensions | Yes | No | Limited |
| Multi-user | No | No | Yes |

## Troubleshooting

### Model Won't Download

- Check disk space
- Verify internet connection (for download only)
- Try alternative download source

### Slow Generation

- Increase GPU layers
- Reduce context length
- Use smaller model

### Jan Won't Start

```bash
# Linux: Check for missing dependencies
ldd /usr/bin/jan

# Clear settings
rm -rf ~/.jan
```

### GPU Not Detected

- Update GPU drivers
- Check Vulkan support:
  ```bash
  vulkaninfo
  ```

## Data Locations

| Platform | Data Directory |
|----------|---------------|
| Linux | `~/.jan` |
| macOS | `~/Library/Application Support/Jan` |
| Windows | `%APPDATA%\Jan` |

### Structure

```
~/.jan/
├── models/          # Downloaded models
├── threads/         # Conversation history
├── assistants/      # Custom assistants
└── extensions/      # Installed extensions
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New thread |
| `Ctrl+Shift+N` | New assistant |
| `Enter` | Send message |
| `Shift+Enter` | New line |
| `Ctrl+/` | Toggle sidebar |

## See Also

- [GUI Tools Index](index.md) - Tool comparison
- [Choosing Models](../models/choosing-models.md) - Model selection
- [GGUF Formats](../models/gguf-formats.md) - Custom model import
- [Ollama](../inference-engines/ollama.md) - CLI alternative
