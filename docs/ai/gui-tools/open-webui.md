# Open WebUI

Self-hosted web interface for LLMs with multi-backend support, RAG, and multi-user authentication.

## Overview

Open WebUI provides:

- **Backend agnostic** - Connect to Ollama, OpenAI, or any compatible API
- **Multi-user** - Authentication and user management
- **RAG** - Upload documents for context
- **Model switching** - Change models mid-conversation
- **Customizable** - Themes, prompts, settings

## Quick Start

### With Ollama

```bash
docker run -d \
  -p 3000:8080 \
  -v /tank/ai/data/open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

Access at `http://localhost:3000`

### Standalone

```bash
docker run -d \
  -p 3000:8080 \
  -v /tank/ai/data/open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## Docker Compose

### With Ollama Stack

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    container_name: ollama
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - /tank/ai/data/open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

networks:
  default:
    name: ai-network
```

### AMD ROCm Stack

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
    volumes:
      - /tank/ai/models/ollama:/root/.ollama

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - /tank/ai/data/open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |
| `OPENAI_API_BASE_URL` | OpenAI-compatible URL | - |
| `OPENAI_API_KEY` | API key for OpenAI | - |
| `WEBUI_AUTH` | Enable authentication | `True` |
| `WEBUI_SECRET_KEY` | Session encryption key | Random |
| `DEFAULT_MODELS` | Default model selection | - |
| `ENABLE_SIGNUP` | Allow user registration | `True` |

### Multiple Backends

```yaml
environment:
  # Ollama
  - OLLAMA_BASE_URL=http://ollama:11434

  # OpenAI-compatible (e.g., local llama.cpp)
  - OPENAI_API_BASE_URLS=http://llama-server:8080/v1

  # Cloud fallback
  - OPENAI_API_KEY=sk-xxx
```

### Production Configuration

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "127.0.0.1:3000:8080"  # Local only, use reverse proxy
    volumes:
      - /tank/ai/data/open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_AUTH=True
      - ENABLE_SIGNUP=False  # Disable public signup
      - WEBUI_SECRET_KEY=${WEBUI_SECRET}
      - DEFAULT_MODELS=llama3.3:70b
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

## User Management

### First User

The first user to sign up becomes admin.

### Disable Signup

After creating admin account:

```yaml
environment:
  - ENABLE_SIGNUP=False
```

Or in Admin Settings → General → Disable Signup

### User Roles

| Role | Capabilities |
|------|--------------|
| Admin | Full access, user management |
| User | Chat, model access |
| Pending | Awaiting admin approval |

## RAG (Document Chat)

### Upload Documents

1. Click **+** in chat
2. Select **Upload Files**
3. Upload PDF, TXT, MD, etc.
4. Documents become part of context

### Supported Formats

- PDF
- Text files (.txt, .md)
- Word documents
- Code files
- And more

### Collection Management

Create document collections:

1. **Workspace** → **Documents**
2. Create collection
3. Upload documents
4. Reference in chats with `#collection-name`

## Model Management

### Switch Models

- Select model from dropdown in chat
- Models from all connected backends appear

### Model Settings

Per-model configuration:

1. **Workspace** → **Models**
2. Select model
3. Configure:
   - System prompt
   - Temperature
   - Max tokens
   - Context length

### Custom Models

Add model aliases:

```json
{
  "name": "coding-assistant",
  "base_model": "deepseek-coder-v2:16b",
  "system_prompt": "You are a senior software engineer..."
}
```

## Features

### Chat Features

- **Markdown rendering** - Code blocks, tables
- **Code execution** - Python code blocks (with extension)
- **Image understanding** - Vision models
- **Voice input** - Speech-to-text
- **Voice output** - Text-to-speech

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+O` | New chat |
| `Ctrl+Shift+S` | Toggle sidebar |
| `Ctrl+Shift+Backspace` | Delete chat |
| `Enter` | Send message |
| `Shift+Enter` | New line |

### Themes

1. **Settings** → **Interface**
2. Choose theme (Light, Dark, System)
3. Custom CSS available

## Integration

### Tailscale Access

Expose Open WebUI via Tailscale:

```bash
tailscale serve --bg https+insecure://localhost:3000
```

Access via `https://server.tailnet.ts.net`

### Reverse Proxy (Caddy)

```caddyfile
webui.example.com {
    reverse_proxy localhost:3000
}
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 443 ssl;
    server_name webui.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Data Persistence

### Volume Structure

```
/tank/ai/data/open-webui/
├── webui.db          # SQLite database
├── uploads/          # Uploaded files
├── cache/            # Temporary cache
└── docs/             # RAG documents
```

### Backup

```bash
# Snapshot ZFS dataset
zfs snapshot tank/ai/data/open-webui@backup

# Or copy files
cp -r /tank/ai/data/open-webui /backup/
```

## Troubleshooting

### Can't Connect to Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/

# In Docker, use correct URL
OLLAMA_BASE_URL=http://host.docker.internal:11434  # macOS/Windows
OLLAMA_BASE_URL=http://172.17.0.1:11434           # Linux (Docker bridge)
```

### Login Loop

```bash
# Clear cookies in browser
# Or reset session
docker exec open-webui rm -rf /app/backend/data/webui.db
```

### Slow Response

- Check Ollama logs: `docker logs ollama`
- Verify model is loaded: `ollama ps`
- Ensure GPU is being used

### WebSocket Errors

```nginx
# Ensure WebSocket upgrade in proxy
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## API Access

Open WebUI also provides an API:

```bash
# Get API key from Settings → Account → API Keys

curl http://localhost:3000/api/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3:70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## See Also

- [GUI Tools Index](index.md) - Tool comparison
- [Ollama Docker](../containers/ollama-docker.md) - Ollama setup
- [Container Deployment](../containers/index.md) - Docker configuration
- [Remote Access](../remote-access/index.md) - External access
