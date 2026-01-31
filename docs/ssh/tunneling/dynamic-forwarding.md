# Dynamic Port Forwarding (SOCKS Proxy)

## Overview

Dynamic port forwarding creates a SOCKS proxy that routes all traffic through the SSH connection. Unlike local/remote forwarding (single destination), dynamic forwarding works for any destination.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Dynamic Port Forwarding (SOCKS)                       │
│                                                                           │
│   Your Machine            SSH Server              Internet                │
│   ┌───────────┐          ┌───────────┐          ┌───────────┐           │
│   │           │          │           │          │           │           │
│   │   SOCKS   │──────────┤   SSH     │──────────┤  Any Site │           │
│   │   :1080   │  SSH     │  Server   │  Normal  │           │           │
│   │           │  Tunnel  │           │  Traffic │           │           │
│   └───────────┘          └───────────┘          └───────────┘           │
│                                                                           │
│   Browser → SOCKS proxy → SSH → google.com, github.com, etc.            │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Use cases**: Browse internet as if from remote server, bypass geo-restrictions, secure browsing on untrusted networks.

## Basic Syntax

```bash
ssh -D [bind_address:]port user@ssh_server
```

## Basic Usage

### Create SOCKS Proxy

```bash
ssh -D 1080 user@server.example.com
```

Creates a SOCKS5 proxy on `localhost:1080`.

### Tunnel Only

```bash
ssh -D 1080 -N user@server.example.com
```

### Background

```bash
ssh -D 1080 -f -N user@server.example.com
```

## Browser Configuration

### Firefox

1. Settings → Network Settings → Settings
2. Manual proxy configuration
3. SOCKS Host: `127.0.0.1`, Port: `1080`
4. SOCKS v5
5. Check "Proxy DNS when using SOCKS v5"

### Chrome

Chrome uses system proxy, or launch with flags:

```bash
google-chrome --proxy-server="socks5://127.0.0.1:1080"
```

### System-Wide (macOS)

System Preferences → Network → Advanced → Proxies:
- Check "SOCKS Proxy"
- Server: 127.0.0.1:1080

### System-Wide (Linux)

```bash
export ALL_PROXY=socks5://127.0.0.1:1080
export HTTP_PROXY=socks5://127.0.0.1:1080
export HTTPS_PROXY=socks5://127.0.0.1:1080
```

## DNS Through SOCKS

### Problem

By default, DNS queries might not go through the proxy, leaking your real location.

### Browser Solution

Firefox: Enable "Proxy DNS when using SOCKS v5"

Chrome: Uses system DNS by default

### Command Line Tools

```bash
# curl (built-in SOCKS support with DNS)
curl --socks5-hostname 127.0.0.1:1080 https://ifconfig.me

# wget (doesn't support SOCKS natively, use proxychains)
proxychains wget https://example.com
```

## Proxychains

Route any program through the SOCKS proxy.

### Install

```bash
apt install proxychains-ng
```

### Configure

```bash
# /etc/proxychains4.conf
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 1080
```

### Usage

```bash
# Any command
proxychains curl https://ifconfig.me
proxychains nmap -sT -p 80 target.com
proxychains wget https://example.com
```

## SOCKS4 vs SOCKS5

| Feature | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| TCP | ✅ | ✅ |
| UDP | ❌ | ✅ |
| IPv6 | ❌ | ✅ |
| Authentication | ❌ | ✅ |
| DNS via proxy | ❌ | ✅ |

SSH creates a SOCKS5 proxy.

## SSH Config

```bash
# ~/.ssh/config
Host proxy
    HostName server.example.com
    User admin
    DynamicForward 1080
    Compression yes
```

Usage:

```bash
ssh proxy
# SOCKS proxy on :1080 while connected
```

## Multiple Proxies

### Multiple Servers

```bash
# Proxy 1
ssh -D 1080 user@server1.example.com

# Proxy 2 (different terminal)
ssh -D 1081 user@server2.example.com
```

### Chain Through Jump Host

```bash
ssh -J jumphost -D 1080 user@internal.example.com
```

## Common Use Cases

### Secure Browsing on Public WiFi

```bash
ssh -D 1080 -C user@home-server.example.com
# Configure browser to use SOCKS proxy
# All traffic encrypted to your home server
```

### Access Geo-Restricted Content

```bash
# Connect to server in desired country
ssh -D 1080 user@us-server.example.com
# Browse as if from that country
```

### Access Internal Resources

```bash
ssh -D 1080 user@office-server.example.com
# Browser can now access internal.company.com
```

### Scanning Through Proxy

```bash
ssh -D 1080 user@server.example.com

# In another terminal
proxychains nmap -sT -Pn -p 80,443 internal-target.com
```

### API Testing from Different IP

```bash
ssh -D 1080 user@server.example.com

curl --socks5-hostname 127.0.0.1:1080 https://api.example.com/endpoint
```

## Persistent SOCKS Proxy

### Using autossh

```bash
autossh -M 0 -f -N -D 1080 \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    user@server.example.com
```

### Systemd Service

```bash
# /etc/systemd/system/socks-proxy.service
[Unit]
Description=SOCKS Proxy via SSH
After=network.target

[Service]
User=youruser
ExecStart=/usr/bin/ssh -N -D 127.0.0.1:1080 \
    -o ServerAliveInterval=60 \
    -o ExitOnForwardFailure=yes \
    user@server.example.com
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Performance Options

### Enable Compression

```bash
ssh -D 1080 -C user@server.example.com
```

### Faster Cipher (If CPU-Limited)

```bash
ssh -D 1080 -c aes128-gcm@openssh.com user@server.example.com
```

## Verify Proxy is Working

### Check External IP

```bash
# Without proxy
curl https://ifconfig.me

# With proxy
curl --socks5-hostname 127.0.0.1:1080 https://ifconfig.me
```

### Check DNS

```bash
# Should show SSH server's DNS
curl --socks5-hostname 127.0.0.1:1080 https://dnsleaktest.com/
```

## Troubleshooting

### Proxy Not Working

```bash
# Check SSH tunnel is active
ss -tlnp | grep 1080

# Check you can connect to proxy
curl --socks5 127.0.0.1:1080 http://example.com
```

### Slow Performance

```bash
# Enable compression
ssh -D 1080 -C user@server.example.com

# Check server bandwidth
# Your speed is limited by the SSH server's connection
```

### DNS Leaking

```bash
# Ensure DNS goes through proxy
# Firefox: Enable "Proxy DNS"
# curl: Use --socks5-hostname not --socks5
```

### Connection Drops

```bash
# Add keep-alive
ssh -D 1080 -o ServerAliveInterval=60 user@server.example.com

# Use autossh for auto-reconnect
```

## Security Notes

1. **Traffic visible at exit**: The SSH server sees unencrypted HTTP traffic
2. **Server logs**: The server can log your browsing
3. **HTTPS recommended**: Use HTTPS sites for end-to-end encryption
4. **Trust your server**: Only use servers you control or trust
5. **Not a VPN**: Only TCP traffic, no system-wide routing

## Comparison

| Tool | Encryption | All Apps | Easy Setup | Speed |
|------|------------|----------|------------|-------|
| SSH SOCKS | ✅ | Manual | ✅ | Good |
| VPN | ✅ | ✅ | Medium | Good |
| Tor | ✅ | Manual | ✅ | Slow |
| Commercial proxy | Varies | Manual | ✅ | Varies |
