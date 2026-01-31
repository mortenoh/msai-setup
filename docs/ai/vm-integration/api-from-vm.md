# API from VM

Access LLM APIs hosted in virtual machines from the host system and containers.

## Overview

When running LLM inference in a VM (e.g., LM Studio in Windows), you need to:

- Configure VM networking for API access
- Set up host environment variables
- Configure containers to reach VM
- Handle cross-network scenarios (Tailscale)

## Network Configurations

### NAT Network (Default)

VM has private IP accessible from host:

```
┌─────────────────────────────────────────┐
│              Linux Host                  │
│                                          │
│  Host IP: 192.168.1.100                 │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │         virbr0 (NAT)               │ │
│  │         192.168.122.1              │ │
│  │              │                      │ │
│  │              ▼                      │ │
│  │  ┌─────────────────────────────┐   │ │
│  │  │      Windows VM             │   │ │
│  │  │   192.168.122.10:1234       │   │ │
│  │  └─────────────────────────────┘   │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

Host accesses: http://192.168.122.10:1234
```

### Bridged Network

VM has IP on same network as host:

```
┌─────────────────────────────────────────┐
│              Network                     │
│           192.168.1.0/24                │
│                                          │
│  ┌─────────────┐    ┌─────────────────┐ │
│  │ Linux Host  │    │   Windows VM    │ │
│  │ 192.168.1.100│   │ 192.168.1.101   │ │
│  └─────────────┘    └─────────────────┘ │
└─────────────────────────────────────────┘

Host accesses: http://192.168.1.101:1234
```

## Finding VM IP

### From Host

```bash
# For NAT network
virsh domifaddr win11

# Or scan network
nmap -sn 192.168.122.0/24
```

### In Windows VM

```powershell
ipconfig
# Look for IPv4 Address
```

## Host Configuration

### Environment Variables

```bash
# Set for current session
export OPENAI_API_BASE=http://192.168.122.10:1234/v1
export OPENAI_API_KEY=not-needed

# Add to shell profile
echo 'export OPENAI_API_BASE=http://192.168.122.10:1234/v1' >> ~/.bashrc
echo 'export OPENAI_API_KEY=not-needed' >> ~/.bashrc
```

### Test Connection

```bash
# List models
curl http://192.168.122.10:1234/v1/models

# Chat completion
curl http://192.168.122.10:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "loaded-model",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Container Configuration

### Docker Network Access

Containers need to reach VM IP:

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - OPENAI_API_BASE=http://192.168.122.10:1234/v1
      - OPENAI_API_KEY=not-needed
```

### Using Host Network

```yaml
services:
  app:
    network_mode: host
    # Can now use VM IP directly
```

### Bridge Network with Extra Host

```yaml
services:
  app:
    extra_hosts:
      - "llm-vm:192.168.122.10"
    environment:
      - OPENAI_API_BASE=http://llm-vm:1234/v1
```

## With Tailscale

### VM on Tailnet

If Windows VM has Tailscale installed:

```bash
# VM Tailscale IP (e.g., 100.64.0.10)
tailscale ip win11-vm

# Access via Tailscale
export OPENAI_API_BASE=http://100.64.0.10:1234/v1
```

### Benefits

- Access from any Tailnet device
- Encrypted traffic
- Works across networks

### Configuration

In Windows VM:
1. Install Tailscale
2. Login to tailnet
3. Note Tailscale IP

From any tailnet device:
```bash
curl http://win11-vm.tail12345.ts.net:1234/v1/models
```

## Static IP Configuration

### Set Static VM IP

In Windows VM:
1. Network Settings → Ethernet → Edit
2. IP assignment: Manual
3. Set IP: 192.168.122.10
4. Gateway: 192.168.122.1
5. DNS: 192.168.122.1

### libvirt DHCP Reservation

```xml
<!-- Add to network config -->
<dhcp>
  <range start='192.168.122.2' end='192.168.122.254'/>
  <host mac='52:54:00:xx:xx:xx' ip='192.168.122.10'/>
</dhcp>
```

```bash
virsh net-edit default
virsh net-destroy default
virsh net-start default
```

## Load Balancing

### Multiple VMs

For high availability:

```yaml
# Traefik configuration
services:
  traefik:
    labels:
      - "traefik.http.services.llm.loadbalancer.healthcheck.path=/v1/models"

  # Route to VMs
  llm-backend:
    # Traefik routes to VM IPs
```

### nginx Proxy

```nginx
upstream llm_vms {
    server 192.168.122.10:1234;
    server 192.168.122.11:1234 backup;
}

server {
    listen 8080;
    location / {
        proxy_pass http://llm_vms;
    }
}
```

## Application Configuration

### Aider

```bash
aider --openai-api-base http://192.168.122.10:1234/v1
```

### Continue.dev

```json
{
  "models": [
    {
      "title": "VM LM Studio",
      "provider": "openai",
      "model": "loaded-model",
      "apiBase": "http://192.168.122.10:1234/v1",
      "apiKey": "not-needed"
    }
  ]
}
```

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.122.10:1234/v1",
    api_key="not-needed"
)
```

## Troubleshooting

### Connection Refused

```bash
# Check VM is running
virsh list

# Check LM Studio server is started
# In VM, should show server running

# Check Windows Firewall
# Ensure port 1234 is allowed

# Test from host
ping 192.168.122.10
telnet 192.168.122.10 1234
```

### Connection Timeout

```bash
# Check routing
ip route

# Check VM network
virsh domiflist win11
virsh net-info default

# Restart VM networking
virsh net-destroy default
virsh net-start default
```

### Container Can't Reach VM

```bash
# Test from container
docker run --rm alpine ping 192.168.122.10

# If fails, check Docker network
docker network inspect bridge

# Use host network as workaround
docker run --network host ...
```

### Slow API Response

- Check model is fully loaded in LM Studio
- Verify GPU is being used (Windows Task Manager)
- Check network latency: `ping -c 10 192.168.122.10`

## Security Considerations

### API Exposure

By default, VM API is accessible from host network only. For additional security:

```bash
# On host, use UFW
sudo ufw deny from any to 192.168.122.10 port 1234
sudo ufw allow from 127.0.0.1 to 192.168.122.10 port 1234
```

### With Proxy

Route through authenticated proxy:

```yaml
services:
  caddy:
    ports:
      - "8080:8080"
    # Add authentication
```

## See Also

- [VM Integration Index](index.md) - Overview
- [Windows LM Studio](windows-lm-studio.md) - VM setup
- [Tailscale Integration](../remote-access/tailscale-integration.md) - Remote access
- [Load Balancing](../api-serving/load-balancing.md) - Multi-backend
