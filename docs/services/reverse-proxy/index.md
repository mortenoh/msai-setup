# Reverse Proxy

A reverse proxy routes incoming traffic to the appropriate backend services, handling SSL/TLS termination and load balancing.

## Why Use a Reverse Proxy?

- **Single entry point** - One port (443) for all services
- **SSL/TLS termination** - Automatic HTTPS for all services
- **Domain routing** - `app1.domain.com`, `app2.domain.com`
- **Security** - Hide internal network structure
- **Load balancing** - Distribute traffic across instances

```
Internet
    │
    ▼ (443)
┌────────────────┐
│ Reverse Proxy  │
│   SSL/TLS      │
└────────────────┘
    │
    ├──► app1:8080
    ├──► app2:3000
    └──► app3:5000
```

## Options Comparison

| Feature | Traefik | Caddy | Nginx Proxy Manager |
|---------|---------|-------|---------------------|
| Auto SSL | Yes (ACME) | Yes (ACME) | Yes (ACME) |
| Docker integration | Excellent | Good | Good |
| Configuration | Labels/YAML | Caddyfile | Web UI |
| Learning curve | Medium | Low | Low |
| Performance | Good | Good | Excellent |
| Middleware | Built-in | Plugins | Limited |

## In This Section

| Document | Description |
|----------|-------------|
| [Traefik](traefik.md) | Docker-native reverse proxy |
| [Caddy](caddy.md) | Simple, automatic HTTPS |

## Quick Decision

- **Traefik** - Best for Docker environments, auto-discovery
- **Caddy** - Simplest configuration, great for beginners
- **Nginx Proxy Manager** - Web UI for management

## Basic Concepts

### SSL/TLS Certificates

Automatic certificate management via ACME (Let's Encrypt):

```
Request → Let's Encrypt → Certificate → Auto-renewal
```

Requirements:
- Public domain name
- Port 80 or 443 accessible (or DNS challenge)
- Valid DNS records

### Routing Methods

**Host-based:**
```
app1.domain.com → service1
app2.domain.com → service2
```

**Path-based:**
```
domain.com/app1 → service1
domain.com/app2 → service2
```

### Docker Labels (Traefik)

```yaml
services:
  myapp:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.domain.com`)"
      - "traefik.http.services.myapp.loadbalancer.server.port=8080"
```

### Caddyfile (Caddy)

```
myapp.domain.com {
    reverse_proxy myapp:8080
}
```

## See Also

- [Traefik Setup](traefik.md)
- [Caddy Setup](caddy.md)
- [Authentication](../authentication/index.md)
- [Docker Networking](../../docker/networking.md)
