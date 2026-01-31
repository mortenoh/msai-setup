# Local Port Forwarding

## Overview

Local port forwarding makes a remote service accessible on your local machine. Traffic to a local port is forwarded through SSH to a destination.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Local Port Forwarding                              │
│                                                                           │
│   Your Machine            SSH Server              Destination             │
│   ┌───────────┐          ┌───────────┐          ┌───────────┐           │
│   │           │          │           │          │           │           │
│   │ localhost ├──────────┤   SSH     ├──────────┤  Service  │           │
│   │   :8080   │  SSH     │  Server   │  Direct  │   :80     │           │
│   │           │  Tunnel  │           │  Connect │           │           │
│   └───────────┘          └───────────┘          └───────────┘           │
│                                                                           │
│   Browser → localhost:8080 → SSH → webserver:80                         │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Use case**: Access remote services that aren't directly reachable (databases, internal web apps, admin panels).

## Basic Syntax

```bash
ssh -L [bind_address:]local_port:destination_host:destination_port user@ssh_server
```

## Examples

### Access Remote Web Server

```bash
ssh -L 8080:localhost:80 user@server.example.com
```

Now `http://localhost:8080` shows the web server running on `server.example.com`.

### Access Remote Database

```bash
# PostgreSQL
ssh -L 5432:localhost:5432 user@db.example.com

# MySQL
ssh -L 3306:localhost:3306 user@db.example.com

# Redis
ssh -L 6379:localhost:6379 user@redis.example.com
```

Connect with local tools:

```bash
psql -h localhost -p 5432 -U dbuser
mysql -h 127.0.0.1 -P 3306 -u dbuser -p
redis-cli -h localhost -p 6379
```

### Access Service on Different Host

Forward through SSH server to another host:

```bash
ssh -L 5432:database.internal:5432 user@bastion.example.com
```

```
Your Machine → Bastion → database.internal:5432
```

### Different Local Port

When local port is already in use:

```bash
ssh -L 15432:localhost:5432 user@db.example.com
# Connect to localhost:15432 instead
```

## Multiple Forwards

### Multiple -L Options

```bash
ssh -L 5432:localhost:5432 \
    -L 6379:localhost:6379 \
    -L 8080:localhost:80 \
    user@server.example.com
```

### In SSH Config

```bash
Host dev-server
    HostName dev.example.com
    User developer
    LocalForward 5432 localhost:5432
    LocalForward 6379 redis.internal:6379
    LocalForward 8080 localhost:80
```

## Tunnel Only (No Shell)

### Background Tunnel

```bash
ssh -f -N -L 8080:localhost:80 user@server.example.com
```

- `-f`: Fork to background after authentication
- `-N`: No remote command (tunnel only)

### Keep in Foreground

```bash
ssh -N -L 8080:localhost:80 user@server.example.com
# Ctrl+C to stop
```

## Bind Address

By default, forwards bind to localhost only.

### Allow Other Machines

```bash
ssh -L 0.0.0.0:8080:localhost:80 user@server.example.com
# or
ssh -L *:8080:localhost:80 user@server.example.com
```

Now other machines can connect to `your-ip:8080`.

### Specific Interface

```bash
ssh -L 192.168.1.100:8080:localhost:80 user@server.example.com
```

!!! warning "Security"
    Binding to 0.0.0.0 exposes the tunnel to your network. Ensure this is intentional.

## Common Use Cases

### Access Internal Jenkins

```bash
ssh -L 8080:jenkins.internal:8080 user@bastion.example.com
# Open http://localhost:8080
```

### Access RDP Through SSH

```bash
ssh -L 3389:windows-server.internal:3389 user@bastion.example.com
# Connect RDP client to localhost:3389
```

### Access Kubernetes Dashboard

```bash
ssh -L 8443:localhost:8443 user@k8s-master.example.com
# Open https://localhost:8443
```

### Access Jupyter Notebook

```bash
ssh -L 8888:localhost:8888 user@ml-server.example.com
# Open http://localhost:8888
```

### Access Elasticsearch

```bash
ssh -L 9200:localhost:9200 user@elk.example.com
curl http://localhost:9200
```

## With SSH Config

```bash
# ~/.ssh/config

Host db-tunnel
    HostName bastion.example.com
    User admin
    LocalForward 5432 database.internal:5432
    LocalForward 6379 redis.internal:6379

Host web-dev
    HostName dev.example.com
    User developer
    LocalForward 3000 localhost:3000
    LocalForward 5173 localhost:5173
```

Usage:

```bash
ssh db-tunnel
# Tunnels active until you exit
```

## Persistent Tunnels

### Using autossh

```bash
# Install
apt install autossh

# Create persistent tunnel
autossh -M 0 -f -N -L 5432:localhost:5432 user@server.example.com
```

- `-M 0`: Disable monitoring port (uses SSH keepalive instead)
- `-f`: Background

### Systemd Service

```bash
# /etc/systemd/system/ssh-tunnel.service
[Unit]
Description=SSH Tunnel to Database
After=network.target

[Service]
User=tunneluser
ExecStart=/usr/bin/ssh -N -L 5432:localhost:5432 -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes user@db.example.com
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable ssh-tunnel
systemctl start ssh-tunnel
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :5432
ss -tlnp | grep 5432

# Use different local port
ssh -L 15432:localhost:5432 user@server.example.com
```

### Connection Refused

```bash
# Check service is running on remote
ssh user@server "systemctl status postgresql"

# Check it's listening
ssh user@server "ss -tlnp | grep 5432"

# Check binding (localhost vs 0.0.0.0)
# Service might be on 127.0.0.1 only
```

### Tunnel Drops

```bash
# Add keep-alive
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 \
    -L 5432:localhost:5432 user@server.example.com

# Or use autossh
autossh -M 0 -f -N -L 5432:localhost:5432 user@server.example.com
```

### Permission Denied for Port

Ports below 1024 require root:

```bash
# This fails without root
ssh -L 80:localhost:80 user@server.example.com

# Use higher port instead
ssh -L 8080:localhost:80 user@server.example.com
```

## Security Considerations

1. **Tunnel scope**: Forward only what you need
2. **Bind address**: Keep localhost unless necessary
3. **Firewall**: Ensure local firewall allows traffic
4. **Server policy**: `AllowTcpForwarding` must be enabled on server
5. **Audit**: Log tunnel usage for compliance
