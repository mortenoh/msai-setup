# Remote Port Forwarding

## Overview

Remote port forwarding exposes a local service to the remote network. Traffic to a port on the SSH server is forwarded back to your local machine.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Remote Port Forwarding                              │
│                                                                           │
│   Your Machine            SSH Server              Remote User             │
│   ┌───────────┐          ┌───────────┐          ┌───────────┐           │
│   │           │          │           │          │           │           │
│   │  Service  │◀─────────┤   SSH     │◀─────────┤   User    │           │
│   │   :3000   │  SSH     │  :8080    │  Connect │           │           │
│   │           │  Tunnel  │           │          │           │           │
│   └───────────┘          └───────────┘          └───────────┘           │
│                                                                           │
│   Remote User → ssh-server:8080 → SSH → your-localhost:3000             │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Use case**: Share local development server, expose service behind NAT, remote support.

## Basic Syntax

```bash
ssh -R [bind_address:]remote_port:destination_host:destination_port user@ssh_server
```

## Examples

### Expose Local Web Server

```bash
ssh -R 8080:localhost:3000 user@server.example.com
```

Now anyone who can reach `server.example.com:8080` sees your local `:3000`.

### Expose Local SSH

```bash
ssh -R 2222:localhost:22 user@server.example.com
```

Remote users can SSH to your machine:

```bash
# From server or anywhere reaching server
ssh -p 2222 localhost  # on the server
ssh -p 2222 server.example.com  # if GatewayPorts enabled
```

### Expose to Specific Address

```bash
ssh -R 192.168.1.100:8080:localhost:3000 user@server.example.com
```

## GatewayPorts

By default, remote forwards only bind to localhost on the server. To allow external access:

### Server Configuration

```bash
# /etc/ssh/sshd_config
GatewayPorts yes           # Allow binding to all interfaces
# or
GatewayPorts clientspecified  # Client chooses bind address
```

### Client Binding

With `GatewayPorts clientspecified`:

```bash
# Bind to all interfaces
ssh -R 0.0.0.0:8080:localhost:3000 user@server.example.com

# Bind to specific interface
ssh -R 192.168.1.100:8080:localhost:3000 user@server.example.com
```

## Multiple Forwards

```bash
ssh -R 8080:localhost:3000 \
    -R 8081:localhost:3001 \
    -R 2222:localhost:22 \
    user@server.example.com
```

## Tunnel Only

### Background Tunnel

```bash
ssh -f -N -R 8080:localhost:3000 user@server.example.com
```

### Foreground (For Debugging)

```bash
ssh -N -R 8080:localhost:3000 user@server.example.com
```

## Common Use Cases

### Share Development Server

```bash
# Local dev server on :3000
npm run dev

# In another terminal, expose it
ssh -R 8080:localhost:3000 user@server.example.com

# Colleague visits: http://server.example.com:8080
```

### Remote Support (Reverse Shell)

Your machine behind NAT/firewall:

```bash
ssh -R 2222:localhost:22 user@public-server.example.com
```

Support person connects:

```bash
ssh -p 2222 youruser@public-server.example.com
```

### Expose Local Database

```bash
ssh -R 5432:localhost:5432 user@server.example.com

# Remote app connects to localhost:5432 on server
```

### Webhook Testing

```bash
# Local webhook listener on :9000
ssh -R 80:localhost:9000 user@webhook.example.com

# External service sends to http://webhook.example.com
# You receive it locally
```

## Persistent Remote Tunnels

### Using autossh

```bash
autossh -M 0 -f -N \
    -o "ServerAliveInterval 30" \
    -o "ServerAliveCountMax 3" \
    -R 8080:localhost:3000 \
    user@server.example.com
```

### Systemd Service

```bash
# /etc/systemd/system/reverse-tunnel.service
[Unit]
Description=Reverse SSH Tunnel
After=network.target

[Service]
User=tunnel
ExecStart=/usr/bin/ssh -N -R 2222:localhost:22 \
    -o ServerAliveInterval=60 \
    -o ExitOnForwardFailure=yes \
    tunnel@server.example.com
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### With SSH Config

```bash
# ~/.ssh/config
Host reverse-tunnel
    HostName server.example.com
    User tunnel
    RemoteForward 8080 localhost:3000
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

## Security Considerations

### Restrict Access

On the server, create a restricted user:

```bash
# Create user
useradd -m -s /usr/sbin/nologin tunneluser

# In /etc/ssh/sshd_config
Match User tunneluser
    AllowTcpForwarding remote
    GatewayPorts no
    X11Forwarding no
    PermitTTY no
    ForceCommand /bin/false
```

### Authorized Keys Restrictions

```bash
# ~/.ssh/authorized_keys on server
command="/bin/false",no-pty,no-agent-forwarding,no-X11-forwarding ssh-ed25519 AAAAC3... tunnel-key
```

### Port Restrictions

```bash
# /etc/ssh/sshd_config
Match User tunneluser
    PermitOpen localhost:8080 localhost:8081
```

## Comparison: Local vs Remote

| Aspect | Local (-L) | Remote (-R) |
|--------|-----------|-------------|
| Direction | Pull remote to local | Push local to remote |
| Initiation | You access remote service | Others access your service |
| Bind location | Your machine | SSH server |
| Use case | Access remote DB | Share local dev server |
| NAT traversal | No | Yes (your machine can be behind NAT) |

## Troubleshooting

### Port Not Accessible Externally

```bash
# Check GatewayPorts setting
grep GatewayPorts /etc/ssh/sshd_config

# Check binding
ssh user@server "ss -tlnp | grep 8080"
# Should show 0.0.0.0:8080 not 127.0.0.1:8080
```

### Connection Refused

```bash
# Check local service is running
curl localhost:3000

# Check tunnel is established
ssh user@server "curl -s localhost:8080"
```

### Tunnel Dies

```bash
# Add keep-alive
ssh -o ServerAliveInterval=60 -R 8080:localhost:3000 user@server

# Or use autossh for auto-reconnect
```

### Permission Denied

```bash
# Check AllowTcpForwarding
grep AllowTcpForwarding /etc/ssh/sshd_config
# Must be 'yes' or 'remote'

# Privileged ports need root
# Use port > 1024
```

## Alternative: ngrok/Cloudflare Tunnel

For production-quality tunneling:

```bash
# ngrok
ngrok http 3000

# Cloudflare Tunnel
cloudflared tunnel --url localhost:3000
```

These provide:
- Stable URLs
- SSL termination
- Access control
- Logging

SSH remote forwarding is great for ad-hoc sharing but consider these tools for frequent use.
