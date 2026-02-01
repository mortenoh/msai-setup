# Self-Hosted Services

Containerized applications for your homelab infrastructure.

## Service Categories

### Infrastructure

| Service | Description |
|---------|-------------|
| [Reverse Proxy](reverse-proxy/index.md) | Route traffic to services (Traefik, Caddy) |
| [SSL/TLS Certificates](ssl-tls/index.md) | Certificate management and HTTPS |
| [Authentication](authentication/index.md) | SSO and identity management |
| [Pi-hole](pi-hole/index.md) | Network-wide ad blocking |

### Applications

| Service | Description |
|---------|-------------|
| [Media Stack](media-stack/index.md) | Jellyfin and *arr automation |
| [Homepage](homepage/index.md) | Homelab dashboard |

### Monitoring

| Service | Description |
|---------|-------------|
| [Uptime Kuma](uptime-kuma/index.md) | Status pages and monitoring |

## Deployment Patterns

### Recommended Stack

```
Internet
    │
    v
┌─────────────────┐
│  Reverse Proxy  │  (Traefik/Caddy)
│  + SSL/TLS      │
└─────────────────┘
    │
    ├──> Authentication (Authentik)
    │
    ├──> Applications
    │    ├── Jellyfin
    │    ├── Homepage
    │    └── Other services
    │
    └──> Monitoring
         ├── Uptime Kuma
         └── Prometheus/Grafana

DNS: Pi-hole (network-wide)
```

### Docker Network Setup

```yaml
# Create shared network
networks:
  proxy:
    external: true

# In each service's docker-compose.yml
services:
  myservice:
    networks:
      - proxy
      - default

networks:
  proxy:
    external: true
```

```bash
# Create network
docker network create proxy
```

## Common Configurations

### Environment Variables

```bash
# .env file template
DOMAIN=example.com
TZ=Europe/Oslo
PUID=1000
PGID=1000
```

### Volume Permissions

```yaml
services:
  app:
    environment:
      - PUID=1000
      - PGID=1000
    volumes:
      - ./config:/config
```

### Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

## Getting Started

1. Set up [Reverse Proxy](reverse-proxy/index.md) first
2. Configure [Authentication](authentication/index.md) for SSO
3. Deploy services as needed
4. Add [Homepage](homepage/index.md) dashboard
5. Set up [Uptime Kuma](uptime-kuma/index.md) monitoring

## See Also

- [Docker Setup](../docker/index.md)
- [Monitoring](../operations/monitoring.md)
- [Networking](../networking/index.md)
