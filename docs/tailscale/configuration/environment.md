# Environment Variables

## Overview

Tailscale can be configured via environment variables, useful for containerized and automated deployments.

## Daemon Environment Variables

These are set for `tailscaled`:

### Authentication

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_AUTHKEY` | Auth key for automatic login | `tskey-auth-xxxxx` |
| `TS_AUTH_ONCE` | Only use auth key once | `true` |

### State Management

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_STATE_DIR` | State file directory | `/var/lib/tailscale` |
| `TS_SOCKET` | Unix socket path | `/var/run/tailscale/tailscaled.sock` |

### Network Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_ROUTES` | Subnet routes to advertise | `192.168.1.0/24,10.0.0.0/8` |
| `TS_EXTRA_ARGS` | Extra args for `tailscale up` | `--ssh --accept-routes` |
| `TS_ACCEPT_DNS` | Accept MagicDNS | `true` |
| `TS_HOSTNAME` | Override hostname | `my-server` |
| `TS_USERSPACE` | Run in userspace mode | `true` |

### Proxy Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_SOCKS5_SERVER` | SOCKS5 proxy address | `:1055` |
| `TS_OUTBOUND_HTTP_PROXY_LISTEN` | HTTP proxy address | `:1056` |
| `HTTP_PROXY` | Outbound HTTP proxy | `http://proxy:8080` |
| `HTTPS_PROXY` | Outbound HTTPS proxy | `http://proxy:8080` |
| `NO_PROXY` | Proxy bypass list | `localhost,127.0.0.1` |

### Exit Nodes

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_DEST_IP` | Exit node IP | `100.100.100.2` |

### Serve/Funnel

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_SERVE_CONFIG` | Serve configuration file | `/config/serve.json` |

## Container-Specific Variables

For Docker and Kubernetes:

### Docker

```yaml
# docker-compose.yml
services:
  tailscale:
    image: tailscale/tailscale:latest
    environment:
      - TS_AUTHKEY=tskey-auth-xxxxx
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_HOSTNAME=docker-app
      - TS_EXTRA_ARGS=--ssh --advertise-routes=172.17.0.0/16
      - TS_ACCEPT_DNS=true
      - TS_USERSPACE=false
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tailscale-env
type: Opaque
stringData:
  TS_AUTHKEY: "tskey-auth-xxxxx"
  TS_KUBE_SECRET: "tailscale-state"
  TS_HOSTNAME: "k8s-app"
```

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: tailscale
          image: tailscale/tailscale:latest
          envFrom:
            - secretRef:
                name: tailscale-env
```

## Kubernetes-Specific Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_KUBE_SECRET` | Kubernetes secret for state | `tailscale-state` |
| `TS_CERT_DOMAIN` | Domain for TLS cert | `my-app.example.com` |
| `TS_EXPERIMENTAL_VERSIONED_CONFIG_DIR` | Versioned config | `/config` |

## Debug Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_DEBUG_FIREWALL_MODE` | Firewall debug mode | `auto` |
| `TS_DEBUG_MTU` | Override MTU | `1280` |
| `TS_LOG_TARGET` | Log destination | `stderr` |
| `TS_DEBUG_USE_WIREGUARD_GO` | Use userspace WG | `true` |

## Setting Environment Variables

### systemd Service

```bash
# /etc/default/tailscaled (Debian/Ubuntu)
# or /etc/sysconfig/tailscaled (RHEL/Fedora)

FLAGS=""
PORT="41641"
```

Or use a drop-in:

```bash
# /etc/systemd/system/tailscaled.service.d/environment.conf
[Service]
Environment="TS_AUTHKEY=tskey-auth-xxxxx"
Environment="TS_HOSTNAME=my-server"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart tailscaled
```

### Docker

```bash
docker run -d \
  -e TS_AUTHKEY=tskey-auth-xxxxx \
  -e TS_STATE_DIR=/var/lib/tailscale \
  -e TS_EXTRA_ARGS="--ssh" \
  tailscale/tailscale:latest
```

### Shell Export

```bash
export TS_AUTHKEY=tskey-auth-xxxxx
sudo -E tailscaled
```

## Configuration Precedence

Configuration sources in order of precedence (highest first):

1. Command-line flags (`tailscale up --ssh`)
2. Environment variables (`TS_EXTRA_ARGS=--ssh`)
3. Configuration files
4. Default values

## Common Configurations

### Headless Server

```bash
# /etc/default/tailscaled
TS_AUTHKEY=tskey-auth-xxxxx
TS_HOSTNAME=prod-server-01
TS_EXTRA_ARGS="--ssh --advertise-tags=tag:server"
```

### Subnet Router

```bash
TS_AUTHKEY=tskey-auth-xxxxx
TS_ROUTES=192.168.1.0/24,192.168.2.0/24
TS_EXTRA_ARGS="--advertise-routes=${TS_ROUTES}"
```

### Exit Node

```bash
TS_AUTHKEY=tskey-auth-xxxxx
TS_EXTRA_ARGS="--advertise-exit-node --ssh"
```

### Container with Proxy

```bash
TS_AUTHKEY=tskey-auth-xxxxx
TS_USERSPACE=true
TS_SOCKS5_SERVER=:1055
TS_OUTBOUND_HTTP_PROXY_LISTEN=:1056
```

## Auth Key Best Practices

### Types of Auth Keys

| Type | Use Case | Expiry |
|------|----------|--------|
| One-time | Single device setup | After use |
| Reusable | Multiple devices | Configurable |
| Ephemeral | Temporary nodes | Short-lived |

### Generating Keys

In admin console at **Settings** → **Keys**:

1. Click **Generate auth key**
2. Configure options:
   - Reusable
   - Ephemeral
   - Pre-authorized
   - Tags
3. Copy and store securely

### Security Considerations

```bash
# DON'T commit auth keys to git
# Use secrets management:

# GitHub Actions
- name: Tailscale
  env:
    TS_AUTHKEY: ${{ secrets.TAILSCALE_AUTHKEY }}

# Kubernetes secrets
kubectl create secret generic tailscale-auth \
  --from-literal=authkey=tskey-auth-xxxxx

# Docker secrets
echo "tskey-auth-xxxxx" | docker secret create tailscale_authkey -
```

## Debugging Environment

```bash
# View current environment
sudo systemctl show tailscaled --property=Environment

# View all tailscaled settings
sudo tailscale debug prefs

# Check if env vars are applied
tailscale status --json | jq '.Self'
```
