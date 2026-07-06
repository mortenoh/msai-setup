# Windows LM Studio VM

Run LM Studio in a Windows 11 VM. On this build the default VM has **no GPU passthrough** — the iGPU stays with the host for ROCm.

!!! warning "Default: the host keeps the GPU (virtio-gpu VM)"
    This build's primary purpose is host ROCm inference, so the iGPU stays with the host and the Windows VM uses **virtio-gpu** (no passthrough). In the default setup LM Studio runs **CPU** inference in the VM, or — better — you point the VM's tools at the host's GPU-accelerated Ollama/llama.cpp API (see [API from VM](api-from-vm.md)). The GPU-passthrough path described in the "GPU Passthrough" section below is **opt-in** and mutually exclusive with host ROCm; it hands the single iGPU to the VM and gives up host inference. Only take it if that is a deliberate choice (see [GPU Passthrough](../../virtualization/gpu-passthrough.md) and [Windows 11 VM](../../virtualization/windows-vm.md)).

## Overview

Default (no passthrough) setup:

- Runs Windows 11 in KVM/QEMU with virtio-gpu
- Host retains the iGPU for ROCm
- LM Studio runs CPU inference in the VM, or the VM calls the host's Ollama/llama.cpp API for GPU-accelerated results
- Optionally exposes LM Studio's OpenAI-compatible API back to the host network

Opt-in passthrough setup (advanced): passes the iGPU directly to the VM for full GPU acceleration inside Windows, at the cost of host ROCm.

## Prerequisites

- Windows 11 VM (default: virtio-gpu, see [Windows 11 VM](../../virtualization/windows-vm.md))
- Sufficient RAM for host + VM + model
- Opt-in only: GPU passthrough configured, if you are deliberately handing the iGPU to the VM (see [GPU Passthrough](../../virtualization/gpu-passthrough.md)) — this disables host ROCm

## VM Configuration

### Resource Allocation

For 70B models, allocate generously:

```xml
<memory unit='GiB'>96</memory>
<vcpu>16</vcpu>
```

### GPU Passthrough (opt-in only)

!!! warning "Not the default — disables host ROCm"
    The `<hostdev>` block below applies **only** if you have deliberately chosen the opt-in passthrough path, which hands the single iGPU to the VM and gives up host ROCm inference. For the default virtio-gpu VM, **skip this section** — the VM has no GPU device and gets GPU-accelerated results by calling the host's Ollama/llama.cpp API instead (see [API from VM](api-from-vm.md)). Set up passthrough via [GPU Passthrough](../../virtualization/gpu-passthrough.md) before adding this.

If (and only if) you are on the passthrough path, pass the iGPU through:

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

### GPU Drivers (opt-in passthrough path only)

!!! note "Default VM has no passthrough GPU"
    These driver and GPU-verification steps apply only to the opt-in passthrough path. In the default virtio-gpu VM there is no AMD GPU to install drivers for — LM Studio uses CPU inference, or you call the host's Ollama/llama.cpp API (see [API from VM](api-from-vm.md)).

If you took the passthrough path, install AMD drivers in Windows (the MS-S1 MAX has an AMD Strix Halo iGPU):

- **AMD**: Download from [amd.com/support](https://amd.com/support)

### Verify GPU (passthrough path only)

In LM Studio (only if the iGPU is passed through):
- Check Settings -> Hardware
- The passed-through GPU should be detected with its full VRAM allocation

## Model Download

### In VM

1. Open LM Studio -> Search
2. Download models (e.g., Llama 3.3 70B Q4_K_M)
3. Models download to Windows storage

### Shared Storage (Optional)

For faster model access, share models from host:

```bash
# On host, create Samba share
sudo apt install samba
# Configure /etc/samba/smb.conf

# In Windows, map network drive
# \\host-ip\models -> Z:\
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

1. Windows Defender Firewall -> Advanced Settings
2. Inbound Rules -> New Rule
3. Port -> TCP 1234
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

- Check GPU is being used (Task Manager -> GPU)
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
