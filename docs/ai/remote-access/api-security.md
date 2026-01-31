# API Security

Protect your LLM API with authentication, rate limiting, and access control.

## Overview

Security measures for exposed LLM APIs:

- **Authentication** - Verify client identity
- **Rate limiting** - Prevent abuse and overload
- **Access control** - Restrict endpoints and models
- **Logging** - Audit access patterns
- **Encryption** - Protect data in transit

## Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| Unauthorized access | High | Authentication |
| Resource exhaustion | High | Rate limiting |
| Data exfiltration | Medium | Logging, access control |
| Prompt injection | Medium | Input validation |
| Model theft | Low | Endpoint restrictions |

## Authentication

### API Key Authentication

Using Caddy as reverse proxy:

```caddyfile
# Caddyfile
:8080 {
    @valid_key header Authorization "Bearer {$API_KEY}"

    handle @valid_key {
        reverse_proxy localhost:11434
    }

    handle {
        respond "Unauthorized" 401
    }
}
```

```bash
# Set environment variable
export API_KEY=your-secret-key

# Start Caddy
caddy run --config Caddyfile
```

### Basic Authentication

```caddyfile
:8080 {
    basicauth {
        user1 $2a$14$...  # bcrypt hash
        user2 $2a$14$...
    }
    reverse_proxy localhost:11434
}
```

Generate password hash:

```bash
caddy hash-password
# Enter password when prompted
```

### nginx Basic Auth

```nginx
# /etc/nginx/conf.d/llm.conf
server {
    listen 8080;

    auth_basic "LLM API";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:11434;
    }
}
```

```bash
# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd user1
```

## Rate Limiting

### Caddy Rate Limiting

Using rate_limit plugin:

```caddyfile
{
    order rate_limit before reverse_proxy
}

:8080 {
    rate_limit {
        zone dynamic {
            key {remote_host}
            events 60
            window 1m
        }
    }

    reverse_proxy localhost:11434
}
```

### nginx Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=llm_limit:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=llm_conn:10m;

server {
    listen 8080;

    # Rate limit requests
    limit_req zone=llm_limit burst=20 nodelay;

    # Limit concurrent connections
    limit_conn llm_conn 5;

    location / {
        proxy_pass http://localhost:11434;
    }
}
```

### Traefik Rate Limiting

```yaml
labels:
  - "traefik.http.middlewares.ratelimit.ratelimit.average=10"
  - "traefik.http.middlewares.ratelimit.ratelimit.burst=20"
  - "traefik.http.middlewares.ratelimit.ratelimit.period=1s"
  - "traefik.http.routers.ollama.middlewares=ratelimit"
```

## Endpoint Restrictions

### Allow Only Read Endpoints

```nginx
server {
    listen 8080;

    # Allow chat/completion endpoints
    location ~ ^/v1/(chat/completions|completions|models|embeddings)$ {
        proxy_pass http://localhost:11434;
    }

    # Allow health checks
    location /health {
        proxy_pass http://localhost:11434;
    }

    # Block everything else
    location / {
        return 403;
    }
}
```

### Block Administrative Endpoints

```nginx
# Block Ollama management endpoints
location ~ ^/api/(pull|push|delete|copy|create)$ {
    return 403;
}
```

### Caddy Endpoint Filtering

```caddyfile
:8080 {
    @allowed {
        path /v1/chat/completions
        path /v1/completions
        path /v1/models
        path /v1/embeddings
        path /health
    }

    handle @allowed {
        reverse_proxy localhost:11434
    }

    handle {
        respond "Forbidden" 403
    }
}
```

## Request Validation

### Size Limits

```nginx
# Limit request body size
client_max_body_size 1m;

# Limit header size
large_client_header_buffers 4 16k;
```

### Timeout Protection

```nginx
# Prevent long-running requests from blocking
proxy_read_timeout 120s;
proxy_connect_timeout 10s;
proxy_send_timeout 60s;
```

## Logging

### nginx Access Logs

```nginx
log_format llm_json escape=json '{'
    '"time":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"request":"$request",'
    '"status":"$status",'
    '"body_bytes_sent":"$body_bytes_sent",'
    '"request_time":"$request_time",'
    '"user":"$remote_user"'
'}';

access_log /var/log/nginx/llm_access.log llm_json;
```

### Caddy Logging

```caddyfile
:8080 {
    log {
        output file /var/log/caddy/llm_access.log
        format json
    }

    reverse_proxy localhost:11434
}
```

### Log Analysis

```bash
# Recent requests
tail -f /var/log/nginx/llm_access.log | jq .

# Top users
jq -r '.remote_addr' /var/log/nginx/llm_access.log | sort | uniq -c | sort -rn

# Failed requests
jq 'select(.status != "200")' /var/log/nginx/llm_access.log
```

## Full Secure Setup

### Docker Compose with Caddy

```yaml
version: '3.8'

services:
  caddy:
    image: caddy:latest
    container_name: caddy
    ports:
      - "8080:8080"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    environment:
      - API_KEY=${API_KEY}
    restart: unless-stopped

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

volumes:
  caddy_data:
```

```caddyfile
# Caddyfile
:8080 {
    # Logging
    log {
        output file /data/access.log
        format json
    }

    # API Key authentication
    @valid_key header Authorization "Bearer {$API_KEY}"

    # Rate limiting per IP
    @rate_exceeded expression {http.rate_limit.exceeded}

    handle @rate_exceeded {
        respond "Too Many Requests" 429
    }

    handle @valid_key {
        # Only allow safe endpoints
        @allowed {
            path /v1/chat/completions
            path /v1/completions
            path /v1/models
            path /v1/embeddings
            path /health
            path /
        }

        handle @allowed {
            reverse_proxy ollama:11434
        }

        handle {
            respond "Forbidden" 403
        }
    }

    handle {
        respond "Unauthorized" 401
    }
}
```

### nginx Full Configuration

```nginx
# /etc/nginx/conf.d/llm-secure.conf

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=llm_burst:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=llm_conn:10m;

# Upstream
upstream ollama {
    server 127.0.0.1:11434;
    keepalive 32;
}

server {
    listen 8080;
    server_name _;

    # Logging
    access_log /var/log/nginx/llm_access.log;
    error_log /var/log/nginx/llm_error.log;

    # Rate limiting
    limit_req zone=llm_burst burst=20 nodelay;
    limit_conn llm_conn 10;

    # Size limits
    client_max_body_size 1m;

    # Timeouts
    proxy_read_timeout 120s;
    proxy_connect_timeout 10s;

    # Basic auth
    auth_basic "LLM API";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # Allowed endpoints
    location ~ ^/v1/(chat/completions|completions|models|embeddings)$ {
        proxy_pass http://ollama;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_buffering off;  # For streaming
    }

    location /health {
        auth_basic off;  # Allow unauthenticated health checks
        proxy_pass http://ollama;
    }

    location / {
        return 403;
    }
}
```

## Testing Security

### Test Authentication

```bash
# Without auth (should fail)
curl -I http://localhost:8080/v1/models
# Expect: 401 Unauthorized

# With auth
curl -H "Authorization: Bearer your-key" http://localhost:8080/v1/models
# Expect: 200 OK
```

### Test Rate Limiting

```bash
# Send many requests
for i in {1..50}; do
    curl -s -o /dev/null -w "%{http_code}\n" \
         -H "Authorization: Bearer your-key" \
         http://localhost:8080/v1/models
done
# Should see 429 responses after limit
```

### Test Endpoint Restrictions

```bash
# Try blocked endpoint
curl -H "Authorization: Bearer your-key" \
     -X POST http://localhost:8080/api/pull \
     -d '{"name": "malicious-model"}'
# Expect: 403 Forbidden
```

## Monitoring

### Failed Auth Attempts

```bash
# grep for 401 responses
grep '"status":"401"' /var/log/nginx/llm_access.log | wc -l
```

### Rate Limited Requests

```bash
# grep for 429 responses
grep '"status":"429"' /var/log/nginx/llm_access.log
```

### Unusual Patterns

```bash
# Large request counts from single IP
awk '{print $1}' /var/log/nginx/llm_access.log | \
    sort | uniq -c | sort -rn | head -20
```

## See Also

- [Remote Access Index](index.md) - Overview
- [Tailscale Integration](tailscale-integration.md) - Secure access
- [Load Balancing](../api-serving/load-balancing.md) - Proxy configuration
- [UFW Configuration](../../networking/ufw/configuration.md) - Firewall rules
