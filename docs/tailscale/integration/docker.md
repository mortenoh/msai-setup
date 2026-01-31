# Docker Integration

## Overview

Tailscale can integrate with Docker in several ways:

1. **Host-level Tailscale**: Docker containers use host's Tailscale connection
2. **Sidecar container**: Tailscale container provides network for others
3. **Per-container Tailscale**: Each container has its own Tailscale identity

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Docker + Tailscale Patterns                               │
│                                                                              │
│   1. Host Network                 2. Sidecar                3. Per-Container │
│   ──────────────                  ────────                  ───────────────  │
│                                                                              │
│   ┌───────────┐               ┌───────────────┐           ┌─────────────┐  │
│   │ Container │               │ TS │ App      │           │ App + TS    │  │
│   └─────┬─────┘               │    │ Container│           │ Container   │  │
│         │                     └──┬─┴──────────┘           └──────┬──────┘  │
│   ┌─────┴─────┐                  │                               │         │
│   │   Host    │                  │                         ┌─────┴─────┐   │
│   │ Tailscale │               shared                       │ Tailscale │   │
│   └───────────┘               network                      │  (in app) │   │
│                                                            └───────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Host Network Mode

Simplest approach - containers use host's Tailscale:

```yaml
# docker-compose.yml
version: "3.8"

services:
  webapp:
    image: nginx:alpine
    network_mode: host
```

Containers can:
- Access Tailscale DNS (MagicDNS)
- Connect to other Tailscale devices
- Be accessed via host's Tailscale IP

**Limitations**:
- Loses Docker network isolation
- Port conflicts possible
- All containers share Tailscale identity

## Sidecar Pattern

Tailscale container provides network for application containers:

```yaml
# docker-compose.yml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: ts-sidecar
    hostname: docker-app
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - ts-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_EXTRA_ARGS=--ssh
    restart: unless-stopped

  webapp:
    image: nginx:alpine
    network_mode: service:tailscale
    depends_on:
      - tailscale

  api:
    image: myapi:latest
    network_mode: service:tailscale
    depends_on:
      - tailscale

volumes:
  ts-state:
```

Services sharing network can:
- Communicate via `localhost`
- All appear as one Tailscale device
- Be accessed at same Tailscale IP

## Per-Container Tailscale

Each container has its own Tailscale identity:

```yaml
version: "3.8"

services:
  app1:
    image: tailscale/tailscale:latest
    hostname: app1
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - app1-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_HOSTNAME=docker-app1

  app2:
    image: tailscale/tailscale:latest
    hostname: app2
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - app2-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_HOSTNAME=docker-app2

volumes:
  app1-state:
  app2-state:
```

## Subnet Router in Docker

Expose Docker networks to Tailscale:

```yaml
version: "3.8"

services:
  tailscale-router:
    image: tailscale/tailscale:latest
    container_name: ts-router
    hostname: docker-router
    cap_add:
      - NET_ADMIN
      - NET_RAW
      - SYS_MODULE
    volumes:
      - /dev/net/tun:/dev/net/tun
      - ts-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_EXTRA_ARGS=--advertise-routes=172.18.0.0/16
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv6.conf.all.forwarding=1
    networks:
      - app-network

  webapp:
    image: nginx:alpine
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/16

volumes:
  ts-state:
```

Then approve the route in the admin console.

## Exit Node in Docker

Run a Tailscale exit node:

```yaml
version: "3.8"

services:
  tailscale-exit:
    image: tailscale/tailscale:latest
    container_name: ts-exit
    hostname: docker-exit
    cap_add:
      - NET_ADMIN
      - NET_RAW
      - SYS_MODULE
    volumes:
      - /dev/net/tun:/dev/net/tun
      - ts-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_EXTRA_ARGS=--advertise-exit-node
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv6.conf.all.forwarding=1
    network_mode: host
    restart: unless-stopped

volumes:
  ts-state:
```

## Serve/Funnel with Docker

Expose containerized services via Tailscale Serve:

```yaml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    hostname: web-server
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - ts-state:/var/lib/tailscale
      - ./serve.json:/config/serve.json:ro
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_SERVE_CONFIG=/config/serve.json

  nginx:
    image: nginx:alpine
    network_mode: service:tailscale

volumes:
  ts-state:
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
    "web-server.tailnet.ts.net:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:80"
        }
      }
    }
  }
}
```

## Userspace Mode

For environments without TUN device:

```yaml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    hostname: userspace-ts
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_USERSPACE=true
      - TS_SOCKS5_SERVER=:1055
    ports:
      - "1055:1055"
    volumes:
      - ts-state:/var/lib/tailscale

volumes:
  ts-state:
```

Access Tailscale via SOCKS5 proxy:

```bash
curl --proxy socks5://localhost:1055 http://my-server.tailnet.ts.net
```

## Docker DNS with MagicDNS

Configure containers to use Tailscale DNS:

```yaml
version: "3.8"

services:
  webapp:
    image: nginx:alpine
    dns:
      - 100.100.100.100
    dns_search:
      - tailnet.ts.net
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TS_AUTHKEY` | Auth key for login |
| `TS_STATE_DIR` | State directory |
| `TS_HOSTNAME` | Device hostname |
| `TS_EXTRA_ARGS` | Additional `tailscale up` args |
| `TS_SERVE_CONFIG` | Serve config file path |
| `TS_USERSPACE` | Enable userspace mode |
| `TS_SOCKS5_SERVER` | SOCKS5 proxy address |
| `TS_ROUTES` | Subnet routes |
| `TS_ACCEPT_DNS` | Accept MagicDNS |

## Docker Swarm

Tailscale with Docker Swarm:

```yaml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
    secrets:
      - tailscale_authkey
    environment:
      - TS_AUTHKEY_FILE=/run/secrets/tailscale_authkey

secrets:
  tailscale_authkey:
    external: true
```

## Troubleshooting

### TUN Device Not Available

```bash
# Check TUN exists on host
ls -la /dev/net/tun

# Create if missing
sudo mkdir -p /dev/net
sudo mknod /dev/net/tun c 10 200
sudo chmod 666 /dev/net/tun
```

### Permission Denied

```bash
# Ensure caps are set
docker inspect container_name | grep -A5 CapAdd

# Run with required caps
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW ...
```

### State Not Persisting

```bash
# Check volume mount
docker volume inspect ts-state

# Verify TS_STATE_DIR matches mount
docker exec tailscale ls -la /var/lib/tailscale
```

### DNS Not Working in Container

```bash
# Check container DNS
docker exec webapp cat /etc/resolv.conf

# Add explicit DNS
docker run --dns=100.100.100.100 ...
```

## Best Practices

1. **Use named volumes** for state persistence
2. **Use auth keys** for automated deployment
3. **Set hostname** explicitly for clarity
4. **Use sidecar pattern** for multi-container apps
5. **Consider userspace mode** for restricted environments
6. **Monitor container health** and Tailscale status
