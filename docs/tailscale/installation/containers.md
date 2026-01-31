# Container Installation

## Docker

### Official Tailscale Container

```bash
docker run -d \
  --name=tailscale \
  --hostname=docker-tailscale \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  -v /dev/net/tun:/dev/net/tun \
  -v tailscale-state:/var/lib/tailscale \
  -e TS_AUTHKEY=tskey-auth-xxxxx \
  -e TS_STATE_DIR=/var/lib/tailscale \
  tailscale/tailscale:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale
    hostname: docker-host
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - tailscale-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=tskey-auth-xxxxx
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_EXTRA_ARGS=--ssh
    restart: unless-stopped

volumes:
  tailscale-state:
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_AUTHKEY` | Auth key for automated login | `tskey-auth-xxxxx` |
| `TS_STATE_DIR` | State directory location | `/var/lib/tailscale` |
| `TS_EXTRA_ARGS` | Additional tailscale up args | `--ssh --advertise-routes=10.0.0.0/24` |
| `TS_HOSTNAME` | Override hostname | `my-container` |
| `TS_ROUTES` | Subnet routes to advertise | `10.0.0.0/24,192.168.1.0/24` |
| `TS_ACCEPT_DNS` | Accept MagicDNS | `true` |
| `TS_USERSPACE` | Run in userspace mode | `true` |

### Sidecar Pattern

Run Tailscale as a sidecar to provide network access to other containers:

```yaml
# docker-compose.yml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale-sidecar
    hostname: app-server
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - tailscale-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
    network_mode: host  # Or create shared network

  myapp:
    image: myapp:latest
    network_mode: service:tailscale  # Share Tailscale's network
    depends_on:
      - tailscale

volumes:
  tailscale-state:
```

### Exposing Services

```yaml
version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /dev/net/tun:/dev/net/tun
      - tailscale-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_SERVE_CONFIG=/config/serve.json
    volumes:
      - ./serve.json:/config/serve.json

  nginx:
    image: nginx:alpine
    network_mode: service:tailscale

volumes:
  tailscale-state:
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
    "example.com:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:80"
        }
      }
    }
  }
}
```

### Subnet Router in Docker

```yaml
version: "3.8"

services:
  tailscale-router:
    image: tailscale/tailscale:latest
    container_name: tailscale-router
    hostname: docker-router
    cap_add:
      - NET_ADMIN
      - NET_RAW
      - SYS_MODULE
    volumes:
      - /dev/net/tun:/dev/net/tun
      - tailscale-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_EXTRA_ARGS=--advertise-routes=172.17.0.0/16 --accept-routes
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv6.conf.all.forwarding=1
    network_mode: host
    restart: unless-stopped

volumes:
  tailscale-state:
```

## Kubernetes

### Tailscale Operator

The recommended way to run Tailscale on Kubernetes:

```bash
# Add Helm repository
helm repo add tailscale https://pkgs.tailscale.com/helmcharts
helm repo update

# Install operator
helm upgrade --install tailscale-operator tailscale/tailscale-operator \
  --namespace=tailscale \
  --create-namespace \
  --set oauth.clientId="${OAUTH_CLIENT_ID}" \
  --set oauth.clientSecret="${OAUTH_CLIENT_SECRET}"
```

### OAuth Credentials

Create OAuth credentials in the Tailscale admin console:

1. Go to **Settings** → **OAuth clients**
2. Create new OAuth client with appropriate scopes
3. Use the client ID and secret in the Helm install

### Exposing Services

```yaml
# Expose a service via Tailscale
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    tailscale.com/expose: "true"
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

### Ingress Class

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: tailscale
  rules:
    - host: my-app.tailnet.ts.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
```

### Subnet Router (Kubernetes)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: tailscale-router
  namespace: tailscale
spec:
  selector:
    matchLabels:
      app: tailscale-router
  template:
    metadata:
      labels:
        app: tailscale-router
    spec:
      hostNetwork: true
      serviceAccountName: tailscale
      containers:
        - name: tailscale
          image: tailscale/tailscale:latest
          securityContext:
            capabilities:
              add:
                - NET_ADMIN
                - NET_RAW
          env:
            - name: TS_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: tailscale-auth
                  key: authkey
            - name: TS_KUBE_SECRET
              value: "tailscale-state"
            - name: TS_EXTRA_ARGS
              value: "--advertise-routes=10.96.0.0/12,10.244.0.0/16"
          volumeMounts:
            - name: tun
              mountPath: /dev/net/tun
      volumes:
        - name: tun
          hostPath:
            path: /dev/net/tun
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tailscale-auth
  namespace: tailscale
type: Opaque
stringData:
  authkey: tskey-auth-xxxxx
```

## LXC/LXD

### Privileged Container

```bash
# Create container
lxc launch ubuntu:22.04 tailscale-container

# Install Tailscale
lxc exec tailscale-container -- bash -c "curl -fsSL https://tailscale.com/install.sh | sh"

# Start Tailscale
lxc exec tailscale-container -- tailscale up
```

### Unprivileged with TUN

```bash
# Add TUN device
lxc config device add tailscale-container tun unix-char path=/dev/net/tun

# Set security options
lxc config set tailscale-container security.nesting true

# May need additional permissions
lxc config set tailscale-container raw.lxc "lxc.cgroup.devices.allow = c 10:200 rwm"
```

### LXD Profile

```yaml
# tailscale-profile.yaml
config:
  security.nesting: "true"
  linux.kernel_modules: tun
devices:
  tun:
    path: /dev/net/tun
    type: unix-char
```

```bash
# Create and apply profile
lxc profile create tailscale
lxc profile edit tailscale < tailscale-profile.yaml

# Launch with profile
lxc launch ubuntu:22.04 my-container --profile default --profile tailscale
```

## Proxmox LXC

### Preparation

```bash
# On Proxmox host, edit container config
# /etc/pve/lxc/<CTID>.conf

# Add these lines:
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```

### Inside Container

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start with userspace networking if needed
tailscale up --accept-dns=false
```

## Userspace Mode

For environments without TUN device access:

```bash
# Docker with userspace networking
docker run -d \
  --name=tailscale-userspace \
  -e TS_AUTHKEY=tskey-auth-xxxxx \
  -e TS_USERSPACE=true \
  -e TS_SOCKS5_SERVER=:1055 \
  -p 1055:1055 \
  tailscale/tailscale:latest
```

Use the SOCKS5 proxy to access the tailnet:

```bash
curl --proxy socks5://localhost:1055 http://my-server.tailnet.ts.net
```

## Troubleshooting Containers

### No TUN Device

```bash
# Check if TUN is available
ls -la /dev/net/tun

# Create if missing (on host)
mkdir -p /dev/net
mknod /dev/net/tun c 10 200
chmod 666 /dev/net/tun
```

### Permission Denied

```bash
# Ensure container has NET_ADMIN
docker inspect tailscale | grep -A5 CapAdd

# Run container with required caps
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW ...
```

### DNS Not Working

```bash
# Check if DNS is configured
cat /etc/resolv.conf

# In container, may need
TS_ACCEPT_DNS=false
# And configure DNS manually
```

### State Persistence

```bash
# Ensure state volume is mounted
docker volume inspect tailscale-state

# If losing auth on restart, check:
# - Volume mount is correct
# - TS_STATE_DIR matches mount path
```
