# Windows LM Studio VM

Run LM Studio in a Windows 11 VM with GPU passthrough for local LLM inference.

## Overview

This setup:

- Runs Windows 11 in KVM/QEMU
- Passes GPU directly to VM
- Runs LM Studio with full GPU acceleration
- Exposes OpenAI-compatible API to host network

## Prerequisites

- GPU passthrough configured (see [GPU Passthrough](../../virtualization/gpu-passthrough.md))
- Windows 11 VM (see [Windows 11 VM](../../virtualization/windows-vm.md))
- 96GB+ RAM for VM (for 70B models)

## VM Configuration

### Resource Allocation

For 70B models, allocate generously:

```xml
<memory unit='GiB'>96</memory>
<vcpu>16</vcpu>
```

### GPU Passthrough

Ensure GPU is passed through:

```xml
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source>
    <address domain='0x0000' bus='0x01' slot='0x00' function='0x0'/>
  </source>
</hostdev>
```

### Network Configuration

Use bridged or NAT networking for API access:

```xml
<interface type='network'>
  <source network='default'/>
  <model type='virtio'/>
</interface>
```

Get VM IP:

```bash
virsh domifaddr win11
# Or in Windows: ipconfig
```

## LM Studio Installation

### In Windows VM

1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Run installer
3. Set storage location for models

### GPU Drivers

Install appropriate GPU drivers in Windows:

- **NVIDIA**: Download from [nvidia.com/drivers](https://nvidia.com/drivers)
- **AMD**: Download from [amd.com/support](https://amd.com/support)

### Verify GPU

In LM Studio:
- Check Settings → Hardware
- GPU should be detected with full VRAM

## Model Download

### In VM

1. Open LM Studio → Search
2. Download models (e.g., Llama 3.3 70B Q4_K_M)
3. Models download to Windows storage

### Shared Storage (Optional)

For faster model access, share models from host:

```bash
# On host, create Samba share
sudo apt install samba
# Configure /etc/samba/smb.conf

# In Windows, map network drive
# \\host-ip\models → Z:\
```

## API Server Configuration

### Start Server

1. Click **Local Server** tab
2. Select model
3. Configure settings:
   - Host: `0.0.0.0` (listen on all interfaces)
   - Port: `1234` (default)
4. Click **Start Server**

### Server Settings

| Setting | Recommended | Notes |
|---------|-------------|-------|
| Host | `0.0.0.0` | Accept external connections |
| Port | `1234` | Default LM Studio port |
| Context Length | `8192+` | Adjust per model |
| GPU Layers | Maximum | All on GPU |

### Verify Server

In Windows (PowerShell):

```powershell
curl http://localhost:1234/v1/models
```

## Access from Host

### Test Connection

```bash
# Get VM IP
virsh domifaddr win11
# Example: 192.168.122.10

# Test API
curl http://192.168.122.10:1234/v1/models
```

### Chat Completion

```bash
curl http://192.168.122.10:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Environment Setup

```bash
# For coding tools
export OPENAI_API_BASE=http://192.168.122.10:1234/v1
export OPENAI_API_KEY=not-needed

# Use with Aider
aider --openai-api-base http://192.168.122.10:1234/v1
```

## Docker Container Access

### From Containers

Containers can access VM API via host network:

```yaml
services:
  app:
    environment:
      - OPENAI_API_BASE=http://192.168.122.10:1234/v1
```

Or use `host.docker.internal` (on some Docker setups):

```yaml
environment:
  - OPENAI_API_BASE=http://host.docker.internal:1234/v1
```

## Auto-Start Configuration

### Windows Task Scheduler

Create task to start LM Studio on boot:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start LM Studio

### Start Server Automatically

LM Studio can be configured to start server on launch in settings.

## Firewall Configuration

### Windows Firewall

Allow inbound connections:

1. Windows Defender Firewall → Advanced Settings
2. Inbound Rules → New Rule
3. Port → TCP 1234
4. Allow connection
5. Apply to all profiles

### Host Firewall

If using UFW on host:

```bash
# Usually not needed for NAT network
# But for bridged:
sudo ufw allow from 192.168.122.0/24 to any port 1234
```

## Performance Optimization

### Memory Settings

Allocate most VM memory to Windows:

```xml
<memory unit='GiB'>96</memory>
<currentMemory unit='GiB'>96</currentMemory>
```

### CPU Pinning

Pin VM CPUs for consistent performance:

```xml
<cputune>
  <vcpupin vcpu='0' cpuset='8'/>
  <vcpupin vcpu='1' cpuset='9'/>
  <!-- ... continue for all vCPUs -->
</cputune>
```

### Huge Pages

Enable huge pages for better memory performance:

```bash
# On host
echo 49152 > /proc/sys/vm/nr_hugepages

# In VM config
<memoryBacking>
  <hugepages/>
</memoryBacking>
```

## Troubleshooting

### GPU Not Detected

- Verify GPU passthrough in VM config
- Check Windows Device Manager for GPU
- Update GPU drivers

### API Connection Refused

- Verify LM Studio server is started
- Check Windows Firewall allows port 1234
- Verify VM network is working: `ping <vm-ip>`

### Slow Performance

- Check GPU is being used (Task Manager → GPU)
- Verify all GPU layers are allocated
- Check for thermal throttling

### Model Loading Fails

- Check available memory in Task Manager
- Use smaller quantization (Q4 instead of Q6)
- Close other applications

## See Also

- [VM Integration Index](index.md) - Overview
- [API from VM](api-from-vm.md) - Detailed API access
- [GPU Passthrough](../../virtualization/gpu-passthrough.md) - GPU setup
- [Windows 11 VM](../../virtualization/windows-vm.md) - VM creation
