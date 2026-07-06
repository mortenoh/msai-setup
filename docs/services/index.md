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

## Port Map

Canonical host-port assignments for this build. Most services should be routed through the reverse proxy on 80/443 and **not** exposed on the LAN — services below that bind to a LAN port are either ones the reverse proxy can't proxy easily (DNS, BitTorrent peer port) or admin/legacy access points.

| Port | Service | Notes |
|---|---|---|
| 53/tcp, 53/udp | Pi-hole DNS | LAN |
| 80, 443 | Traefik / Caddy | LAN; everything else routes through here |
| 3000 | Grafana | bind `127.0.0.1` only |
| 3001 | Uptime Kuma | bind `127.0.0.1` only |
| 3030 | Homepage | bind `127.0.0.1` only (Grafana takes 3000) |
| 5432 | Postgres (Authentik, etc.) | bind `127.0.0.1` only |
| 7878 | Radarr | bind `127.0.0.1`; behind reverse proxy |
| 8080 | cAdvisor | bind `127.0.0.1`; metrics scrape only |
| 8096 | Jellyfin | LAN (local clients) |
| 8181 | Tautulli | bind `127.0.0.1` |
| 8989 | Sonarr | bind `127.0.0.1`; behind reverse proxy |
| 9000 | Authentik (HTTP) | bind `127.0.0.1`; behind reverse proxy on its own subdomain |
| 9002 | Portainer (if used) | bind `127.0.0.1`; **moved off 9000** to avoid colliding with Authentik |
| 9090 | Prometheus | bind `127.0.0.1` |
| 9091 | Transmission web UI | bind `127.0.0.1` (Authelia also defaults here — Authelia is behind the reverse proxy on its own subdomain) |
| 9443 | Authentik (HTTPS) | bind `127.0.0.1`; behind reverse proxy |
| 9696 | Prowlarr | bind `127.0.0.1` |
| 11434 | Ollama | LAN or Tailscale-only |
| 32400 | Plex | LAN |
| 51413/tcp, 51413/udp | Transmission peer | LAN/WAN as needed |

Bind sensitive services to `127.0.0.1` in compose like this:

```yaml
ports:
  - "127.0.0.1:3000:3000"
```

…and add the corresponding Traefik / Caddy route so users hit `grafana.example.com` via 80/443 instead of `:3000`.

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
