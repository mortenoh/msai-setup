# Tailscale Integration

Secure remote access to local LLMs via Tailscale Serve and MagicDNS.

## Overview

Tailscale provides:

- **Zero-config VPN** - Mesh network with WireGuard
- **MagicDNS** - Automatic DNS for all devices
- **Tailscale Serve** - HTTPS proxy for local services
- **ACLs** - Fine-grained access control
- **Funnel** - Optional public internet access

## Prerequisites

- Tailscale installed on server and clients
- Tailnet configured
- LLM server running on localhost

See [Tailscale Installation](../../tailscale/installation/linux.md) for setup.

## Tailscale Serve

### Basic Setup

Expose Ollama to your Tailnet:

```bash
# Expose port 11434 as HTTPS
tailscale serve --bg https+insecure://localhost:11434

# Check status
tailscale serve status
```

The service is now available at `https://your-hostname.your-tailnet.ts.net`

### With Custom Path

```bash
# Expose under /api path
tailscale serve --bg --set-path /api https+insecure://localhost:11434
```

### Multiple Services

```bash
# Ollama on /ollama
tailscale serve --bg --set-path /ollama https+insecure://localhost:11434

# llama.cpp on /llama
tailscale serve --bg --set-path /llama https+insecure://localhost:8080

# Open WebUI on root
tailscale serve --bg https+insecure://localhost:3000
```

### Persistent Configuration

Using `tailscale serve` config file:

```bash
# Show current config
tailscale serve status --json

# Reset config
tailscale serve reset
```

The configuration persists across reboots when using `--bg`.

## DNS Names

### MagicDNS

Access via MagicDNS name:

```bash
# Format: hostname.tailnet-name.ts.net
curl https://server.tail12345.ts.net/v1/models

# Or just hostname within tailnet
curl https://server/v1/models
```

### Find Your Hostname

```bash
# Show tailscale status
tailscale status

# Your device shows as:
# 100.x.x.x    server    your-email@   linux   -
```

## Access Control Lists (ACLs)

### Basic ACL

Restrict access to specific users:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["user1@gmail.com", "user2@gmail.com"],
      "dst": ["server:*"]
    }
  ]
}
```

### Tag-Based Access

```json
{
  "tagOwners": {
    "tag:llm-server": ["autogroup:admin"],
    "tag:ai-user": ["autogroup:admin"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["tag:ai-user"],
      "dst": ["tag:llm-server:11434"]
    }
  ]
}
```

Apply tag to server:

```bash
tailscale set --advertise-tags=tag:llm-server
```

### Group-Based Access

```json
{
  "groups": {
    "group:developers": ["dev1@example.com", "dev2@example.com"],
    "group:ai-team": ["ai1@example.com", "ai2@example.com"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:ai-team"],
      "dst": ["tag:llm-server:*"]
    }
  ]
}
```

## Tailscale Funnel

For public internet access (use carefully):

### Enable Funnel

```bash
# Expose to internet
tailscale funnel 11434

# With background mode
tailscale funnel --bg 11434
```

### Funnel Considerations

| Aspect | Consideration |
|--------|---------------|
| Security | Add authentication layer |
| Cost | No bandwidth limits but consider model costs |
| Abuse | Rate limiting essential |
| Privacy | Requests come from internet |

### Recommended Funnel Setup

```bash
# Put reverse proxy with auth in front
tailscale funnel 8080  # Proxy port, not direct Ollama

# Proxy handles auth, rate limiting
```

## Client Configuration

### Environment Variables

```bash
# For tools expecting OpenAI API
export OPENAI_API_BASE=https://server.tail12345.ts.net/v1
export OPENAI_API_KEY=not-needed

# Or Ollama-specific
export OLLAMA_HOST=https://server.tail12345.ts.net
```

### Tool Configuration

```bash
# Aider
aider --openai-api-base https://server.tail12345.ts.net/v1

# Continue.dev (config.json)
{
  "models": [{
    "apiBase": "https://server.tail12345.ts.net/v1"
  }]
}
```

### Python Client

```python
from openai import OpenAI

# Use Tailscale DNS name
client = OpenAI(
    base_url="https://server.tail12345.ts.net/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="llama3.3:70b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Docker Integration

### Tailscale Sidecar

```yaml
version: '3.8'

services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale
    hostname: llm-server
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_SERVE_CONFIG=/config/serve.json
    volumes:
      - tailscale-state:/var/lib/tailscale
      - ./serve.json:/config/serve.json:ro
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    network_mode: service:tailscale
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    depends_on:
      - tailscale
```

```json
// serve.json
{
  "TCP": {
    "443": {
      "HTTPS": true
    }
  },
  "Web": {
    "${TS_CERT_DOMAIN}:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:11434"
        }
      }
    }
  }
}
```

## Troubleshooting

### Can't Connect

```bash
# Check Tailscale is running
tailscale status

# Check Serve is configured
tailscale serve status

# Test local connection first
curl http://localhost:11434/

# Test Tailscale connection
curl https://your-server.tail12345.ts.net/
```

### Certificate Errors

```bash
# Tailscale Serve handles certs automatically
# If issues, check:
tailscale cert your-server.tail12345.ts.net

# Verify HTTPS
curl -v https://your-server.tail12345.ts.net/
```

### ACL Blocking Access

```bash
# Check ACL status
tailscale debug acl

# Verify your identity
tailscale whois $(tailscale ip -4)
```

### Slow Connection

```bash
# Check for direct connection
tailscale netcheck

# Verify not relaying
tailscale status
# Should show "direct" not "relay"
```

## Monitoring

### Access Logs

```bash
# Tailscale doesn't log by default
# Monitor Ollama logs instead
journalctl -u ollama -f

# Or Docker
docker logs -f ollama
```

### Connection Status

```bash
# Active peers
tailscale status

# Network quality
tailscale ping server
```

## Security Best Practices

1. **Use ACLs** - Don't allow unrestricted access
2. **Avoid Funnel for LLMs** - Keep private unless needed
3. **Monitor usage** - Check logs for unusual patterns
4. **Limit endpoints** - Only expose what's needed
5. **Use tags** - Easier to manage than user lists

## See Also

- [Remote Access Index](index.md) - Overview
- [API Security](api-security.md) - Authentication
- [Tailscale Serve](../../tailscale/features/funnel-serve.md) - Full reference
- [Tailscale ACLs](../../tailscale/administration/acls.md) - Access control
