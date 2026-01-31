# Funnel & Serve

## Overview

**Tailscale Serve** exposes local services to your tailnet.
**Tailscale Funnel** exposes services to the public internet.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Serve vs Funnel                                           │
│                                                                              │
│   Tailscale Serve                       Tailscale Funnel                    │
│   ─────────────────                     ────────────────                    │
│                                                                              │
│   Local Service                         Local Service                       │
│       │                                     │                                │
│       ▼                                     ▼                                │
│   tailscale serve                       tailscale funnel                    │
│       │                                     │                                │
│       ▼                                     ▼                                │
│   Your Tailnet                          Public Internet                     │
│   (private)                             (anyone can access)                 │
│                                                                              │
│   Access: my-server.tailnet.ts.net     Access: my-server.tailnet.ts.net    │
│           (Tailscale devices only)              (anyone with URL)           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Tailscale Serve

### Basic Usage

Expose a local port to your tailnet:

```bash
# Serve local port 3000
tailscale serve 3000

# Serve with HTTPS (automatic cert)
tailscale serve https / http://localhost:3000
```

### Serve Commands

```bash
# Start serving
tailscale serve [flags] {port|path|url}

# Show current configuration
tailscale serve status

# Stop serving
tailscale serve off

# Reset all serve config
tailscale serve reset
```

### Examples

```bash
# Serve a web app
tailscale serve 8080

# Serve static files
tailscale serve / /var/www/html

# Serve with path prefix
tailscale serve /api http://localhost:3000

# Serve TCP directly
tailscale serve tcp:5432 tcp://localhost:5432

# Serve multiple paths
tailscale serve /app http://localhost:3000
tailscale serve /api http://localhost:4000
```

### HTTPS Certificates

Tailscale automatically provisions TLS certificates:

```bash
# Serve with HTTPS
tailscale serve https / http://localhost:3000

# Access at:
# https://my-server.tailnet.ts.net
```

Certificates are:
- Automatically provisioned via Let's Encrypt
- Automatically renewed
- Valid for your Tailscale hostname

### Accessing Served Content

```bash
# From any device on your tailnet
curl https://my-server.tailnet.ts.net

# Or use MagicDNS short name
curl https://my-server
```

## Tailscale Funnel

Funnel exposes services to the public internet.

!!! warning "Public Access"
    Funnel makes your service accessible to anyone on the internet. Use with caution.

### Enable Funnel

```bash
# In admin console:
# DNS → Enable HTTPS Certificates
# Also enable Funnel in settings

# Then on device:
tailscale funnel 443
```

### Funnel Commands

```bash
# Start funnel
tailscale funnel {port|target}

# Show status
tailscale funnel status

# Stop funnel
tailscale funnel off

# Reset configuration
tailscale funnel reset
```

### Examples

```bash
# Funnel port 443 to local 3000
tailscale funnel 443

# Funnel with specific backend
tailscale funnel https / http://localhost:3000

# Funnel TCP (e.g., for SSH)
tailscale funnel tcp:22
```

### Accessing Funneled Services

```
https://my-server.tailnet.ts.net
```

This URL is accessible from anywhere on the internet.

## Configuration File

For complex setups, use a configuration file:

```json
// serve.json
{
  "TCP": {
    "443": {
      "HTTPS": true
    }
  },
  "Web": {
    "my-server.tailnet.ts.net:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:3000"
        },
        "/api": {
          "Proxy": "http://127.0.0.1:4000"
        },
        "/static": {
          "Path": "/var/www/static"
        }
      }
    }
  },
  "AllowFunnel": {
    "my-server.tailnet.ts.net:443": true
  }
}
```

Apply configuration:

```bash
tailscale serve --config=serve.json
```

### Configuration Options

| Field | Description |
|-------|-------------|
| `TCP` | TCP port configuration |
| `Web` | HTTP/HTTPS handlers |
| `Handlers` | Path-based routing |
| `Proxy` | Reverse proxy to local URL |
| `Path` | Serve static files |
| `AllowFunnel` | Enable public access |

## Use Cases

### Development Preview

Share a development server with teammates:

```bash
# Local dev server
npm run dev  # Running on localhost:3000

# Share via Tailscale
tailscale serve 3000

# Teammates access:
# https://dev-laptop.tailnet.ts.net
```

### Webhook Receiver

Expose a webhook endpoint publicly:

```bash
# Local webhook handler
python webhook_server.py  # Port 8000

# Expose via Funnel
tailscale funnel https /webhooks http://localhost:8000

# Give external service:
# https://my-server.tailnet.ts.net/webhooks
```

### Self-Hosted Services

Expose Nextcloud, Gitea, etc.:

```bash
# Nextcloud on port 80
tailscale serve https / http://localhost:80

# With Funnel for public access
tailscale funnel 443
```

### Quick File Sharing

Serve a directory temporarily:

```bash
# Python simple server
python3 -m http.server 8000 &

# Expose to tailnet
tailscale serve 8000
```

## Docker Integration

### Sidecar Pattern

```yaml
# docker-compose.yml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    hostname: my-app
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - ts-state:/var/lib/tailscale
      - ./serve.json:/config/serve.json
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_SERVE_CONFIG=/config/serve.json

  webapp:
    image: nginx:alpine
    network_mode: service:tailscale

volumes:
  ts-state:
```

```json
// serve.json
{
  "TCP": {"443": {"HTTPS": true}},
  "Web": {
    "my-app.tailnet.ts.net:443": {
      "Handlers": {
        "/": {"Proxy": "http://127.0.0.1:80"}
      }
    }
  }
}
```

## Security Considerations

### Serve (Tailnet Only)

- Only accessible by authenticated tailnet members
- Protected by Tailscale ACLs
- No public exposure

### Funnel (Public)

- **Accessible by anyone** with the URL
- No authentication by default
- Consider:
  - Adding authentication to your app
  - Rate limiting
  - Web Application Firewall
  - Monitoring access logs

### ACL for Serve

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:dev"],
      "dst": ["tag:devserver:443"]
    }
  ]
}
```

## Troubleshooting

### Serve Not Working

```bash
# Check serve status
tailscale serve status

# Check Tailscale is connected
tailscale status

# Verify local service is running
curl localhost:3000

# Check for port conflicts
ss -tlnp | grep :443
```

### HTTPS Certificate Issues

```bash
# Verify HTTPS is enabled in admin console
# DNS → Enable HTTPS Certificates

# Check certificate status
tailscale cert my-server.tailnet.ts.net

# Manual cert fetch
tailscale cert --cert-file=cert.pem --key-file=key.pem my-server.tailnet.ts.net
```

### Funnel Not Accessible

```bash
# Check Funnel is enabled in admin console
# Settings → Enable Funnel

# Verify funnel status
tailscale funnel status

# Test locally first via serve
tailscale serve status
```

### Connection Refused

```bash
# Verify local service is listening
curl -v localhost:3000

# Check firewall isn't blocking
sudo iptables -L -n | grep 3000

# Ensure serve config points to correct port
tailscale serve status
```

## Best Practices

1. **Start with Serve** before enabling Funnel
2. **Add authentication** for Funnel-exposed services
3. **Monitor access** to public endpoints
4. **Use HTTPS** always
5. **Review ACLs** for serve access control
6. **Limit Funnel scope** to necessary paths only
