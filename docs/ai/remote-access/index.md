# Remote Access

Access your local LLM server from remote devices and networks.

## Overview

Remote access enables:

- **Mobile/laptop access** - Use local models from any device
- **Team sharing** - Multiple users accessing shared inference
- **Cross-network** - Tailscale for secure access anywhere
- **API integration** - Remote applications using your LLM

## Access Methods

```
┌─────────────────────────────────────────────────────────────────┐
│                     Remote Clients                              │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐   │
│  │   Laptop    │  │   Phone     │  │    Cloud App          │   │
│  │  (Tailnet)  │  │  (Tailnet)  │  │    (Funnel)           │   │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬───────────┘   │
│         │                │                     │                │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Access Layer                                │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │     Tailscale Serve     │  │     Tailscale Funnel        │  │
│  │  (Private - Tailnet)    │  │  (Public - Internet)        │  │
│  │   https://server:443    │  │   https://xxx.ts.net        │  │
│  └────────────┬────────────┘  └──────────────┬──────────────┘  │
│               │                              │                  │
│               └──────────────┬───────────────┘                  │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│                      LLM Server                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Ollama / llama.cpp                      │ │
│  │                    localhost:11434                         │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Method Comparison

| Method | Security | Setup | Use Case |
|--------|----------|-------|----------|
| Tailscale Serve | High | Easy | Personal/team access |
| Tailscale Funnel | Medium | Easy | Public API access |
| VPN | High | Medium | Enterprise |
| Port forwarding | Low | Easy | Development only |
| Reverse proxy | Medium | Medium | Self-hosted |

## Quick Start

### Tailscale Serve (Recommended)

Expose Ollama to your Tailnet:

```bash
# Start Ollama listening on localhost
ollama serve  # or docker start ollama

# Expose via Tailscale Serve
tailscale serve --bg https+insecure://localhost:11434

# Access from any Tailnet device
curl https://your-server.tail-abc123.ts.net/v1/models
```

### Tailscale Funnel (Public)

For internet access (use with caution):

```bash
# Expose to internet
tailscale funnel 11434

# Access via HTTPS
# https://your-server.tail-abc123.ts.net
```

### Direct Port (Development Only)

```bash
# Bind to all interfaces (NOT recommended for production)
docker run -p 0.0.0.0:11434:11434 ollama/ollama

# Or configure Ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## Security Considerations

### What to Expose

| Endpoint | Safe to Expose | Notes |
|----------|----------------|-------|
| `/v1/chat/completions` | Yes | Main API |
| `/v1/models` | Yes | List models |
| `/api/generate` | Yes | Native Ollama |
| `/api/pull` | No | Could fill disk |
| `/api/delete` | No | Model management |
| `/health` | Yes | Health checks |

### Recommended Setup

```
Remote Access → Tailscale Serve → Reverse Proxy → Ollama
                (encryption)       (rate limit)    (localhost)
```

## Topics

<div class="grid cards" markdown>

-   :material-cloud-lock: **Tailscale Integration**

    ---

    Secure remote access via Tailscale Serve and ACLs

    [:octicons-arrow-right-24: Tailscale setup](tailscale-integration.md)

-   :material-shield-lock: **API Security**

    ---

    Authentication, rate limiting, and access control

    [:octicons-arrow-right-24: Security setup](api-security.md)

</div>

## Common Configurations

### Personal Use (Single User)

```bash
# Simple Tailscale Serve
tailscale serve --bg 11434
```

### Team Access

```yaml
# Tailscale ACL for team
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:ai-team"],
      "dst": ["tag:llm-server:11434"]
    }
  ]
}
```

### Public API

```yaml
# With authentication proxy
services:
  caddy:
    image: caddy:latest
    ports:
      - "8080:8080"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
    # Add basic auth, rate limiting

  ollama:
    # localhost only
```

## Client Configuration

### From Remote Device

```bash
# Set API base URL
export OPENAI_API_BASE=https://your-server.tail-abc123.ts.net/v1
export OPENAI_API_KEY=not-needed

# Use with tools
aider --openai-api-base $OPENAI_API_BASE
```

### In Application Code

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-server.tail-abc123.ts.net/v1",
    api_key="not-needed"
)
```

## Monitoring Remote Access

### Access Logs

```bash
# Ollama logs
journalctl -u ollama -f

# Docker logs
docker logs -f ollama

# Tailscale connections
tailscale status
```

### Connection Tracking

```bash
# Active connections
ss -tuln | grep 11434

# Tailscale peers
tailscale netcheck
```

## See Also

- [Tailscale Integration](tailscale-integration.md) - Detailed setup
- [API Security](api-security.md) - Authentication
- [Tailscale Features](../../tailscale/features/funnel-serve.md) - Serve/Funnel reference
- [API Serving](../api-serving/index.md) - Local API setup
