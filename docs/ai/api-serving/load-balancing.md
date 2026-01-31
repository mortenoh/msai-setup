# Load Balancing

Distribute requests across multiple LLM backends for reliability and performance.

## Overview

Load balancing enables:

- **High availability** - Failover between backends
- **Model routing** - Different models for different tasks
- **Scaling** - Distribute load across multiple instances
- **A/B testing** - Compare model performance

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Requests                          │
│                    POST /v1/chat/completions                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Load Balancer                              │
│                   (Traefik / nginx)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Routing Rules:                                          │   │
│  │  - /v1/chat/*     → ollama-chat:11434                   │   │
│  │  - /v1/code/*     → ollama-code:11434                   │   │
│  │  - /v1/*          → round-robin all backends            │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  ollama-chat    │ │  ollama-code    │ │  llama-server   │
│  (70B general)  │ │  (code model)   │ │  (fast model)   │
│  :11434         │ │  :11435         │ │  :8080          │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Traefik Setup

### Basic Configuration

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    ports:
      - "8080:80"
      - "8081:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command:
      - --api.insecure=true
      - --providers.docker
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ollama.rule=PathPrefix(`/v1`)"
      - "traefik.http.routers.ollama.entrypoints=web"
      - "traefik.http.services.ollama.loadbalancer.server.port=11434"
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
```

### Multi-Backend Round Robin

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    command:
      - --api.insecure=true
      - --providers.docker
      - --entrypoints.web.address=:80
    ports:
      - "8080:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  ollama-1:
    image: ollama/ollama
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.llm.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llm.loadbalancer.server.port=11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]

  ollama-2:
    image: ollama/ollama
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.llm.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llm.loadbalancer.server.port=11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
```

### Model-Based Routing

Route to different backends based on request content:

```yaml
# traefik/dynamic.yml
http:
  routers:
    code-router:
      rule: "PathPrefix(`/v1/chat`) && HeaderRegexp(`Content-Type`, `.*code.*`)"
      service: code-backend
      entryPoints:
        - web

    chat-router:
      rule: "PathPrefix(`/v1`)"
      service: chat-backend
      entryPoints:
        - web

  services:
    chat-backend:
      loadBalancer:
        servers:
          - url: "http://ollama-chat:11434"

    code-backend:
      loadBalancer:
        servers:
          - url: "http://ollama-code:11434"
```

## nginx Setup

### Basic Reverse Proxy

```nginx
# /etc/nginx/conf.d/llm.conf
upstream llm_backends {
    server 127.0.0.1:11434 weight=5;
    server 127.0.0.1:11435 weight=3;
    server 127.0.0.1:8080 weight=2;

    keepalive 32;
}

server {
    listen 8000;

    location /v1/ {
        proxy_pass http://llm_backends/v1/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;

        # Streaming support
        proxy_buffering off;
        proxy_cache off;

        # Timeouts for long generations
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
```

### Health Check Based Routing

```nginx
upstream llm_backends {
    server 127.0.0.1:11434 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:11435 max_fails=3 fail_timeout=30s backup;
}
```

## Health Checks

### Traefik Health Checks

```yaml
services:
  ollama:
    labels:
      - "traefik.http.services.ollama.loadbalancer.healthcheck.path=/health"
      - "traefik.http.services.ollama.loadbalancer.healthcheck.interval=10s"
      - "traefik.http.services.ollama.loadbalancer.healthcheck.timeout=5s"
```

### Docker Health Checks

```yaml
services:
  ollama:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Custom Health Script

```bash
#!/bin/bash
# healthcheck.sh

# Check if API responds
if ! curl -sf http://localhost:11434/ > /dev/null; then
    exit 1
fi

# Check if model is loaded
if ! curl -sf http://localhost:11434/api/ps | grep -q "llama"; then
    exit 1
fi

exit 0
```

## Sticky Sessions

For conversation continuity:

### Traefik Sticky Sessions

```yaml
labels:
  - "traefik.http.services.llm.loadbalancer.sticky.cookie.name=llm_backend"
  - "traefik.http.services.llm.loadbalancer.sticky.cookie.secure=true"
```

### nginx Sticky Sessions

```nginx
upstream llm_backends {
    ip_hash;  # Route same client to same backend
    server 127.0.0.1:11434;
    server 127.0.0.1:11435;
}
```

## Rate Limiting

### Traefik Rate Limiting

```yaml
labels:
  - "traefik.http.middlewares.ratelimit.ratelimit.average=10"
  - "traefik.http.middlewares.ratelimit.ratelimit.burst=20"
  - "traefik.http.routers.ollama.middlewares=ratelimit"
```

### nginx Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=llm_limit:10m rate=10r/s;

server {
    location /v1/ {
        limit_req zone=llm_limit burst=20 nodelay;
        proxy_pass http://llm_backends/v1/;
    }
}
```

## Multi-Model Setup

### Specialized Backends

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    # ...

  # General chat - 70B model
  ollama-chat:
    image: ollama/ollama
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.chat.rule=PathPrefix(`/v1`) && HeaderRegexp(`X-Model`, `llama.*`)"
      - "traefik.http.services.chat.loadbalancer.server.port=11434"
    environment:
      - OLLAMA_KEEP_ALIVE=1h
    volumes:
      - /tank/ai/models/ollama-chat:/root/.ollama

  # Code assistance - DeepSeek
  ollama-code:
    image: ollama/ollama
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.code.rule=PathPrefix(`/v1`) && HeaderRegexp(`X-Model`, `deepseek.*|code.*`)"
      - "traefik.http.services.code.loadbalancer.server.port=11434"
    environment:
      - OLLAMA_KEEP_ALIVE=1h
    volumes:
      - /tank/ai/models/ollama-code:/root/.ollama

  # Fast responses - small model
  ollama-fast:
    image: ollama/ollama
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.fast.rule=PathPrefix(`/v1`) && Query(`fast=true`)"
      - "traefik.http.services.fast.loadbalancer.server.port=11434"
    volumes:
      - /tank/ai/models/ollama-fast:/root/.ollama
```

## Monitoring

### Traefik Metrics

```yaml
services:
  traefik:
    command:
      - --metrics.prometheus=true
      - --metrics.prometheus.addEntryPointsLabels=true
      - --metrics.prometheus.addServicesLabels=true
    ports:
      - "8082:8082"  # Metrics
```

### Access Logs

```yaml
command:
  - --accesslog=true
  - --accesslog.format=json
```

## Full Production Example

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    command:
      - --api.dashboard=true
      - --providers.docker
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --accesslog=true
      - --metrics.prometheus=true
    ports:
      - "8080:80"
      - "8081:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

  ollama-main:
    image: ollama/ollama
    container_name: ollama-main
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.llm.rule=PathPrefix(`/v1`)"
      - "traefik.http.services.llm.loadbalancer.server.port=11434"
      - "traefik.http.services.llm.loadbalancer.healthcheck.path=/"
      - "traefik.http.services.llm.loadbalancer.healthcheck.interval=30s"
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    environment:
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_KEEP_ALIVE=1h
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

networks:
  default:
    name: llm-network
```

## See Also

- [API Serving Index](index.md) - Overview
- [Container Deployment](../containers/index.md) - Docker setup
- [Remote Access](../remote-access/index.md) - External access
- [API Security](../remote-access/api-security.md) - Authentication
