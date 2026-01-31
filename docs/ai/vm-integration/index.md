# VM Integration

Run LLM inference in virtual machines with GPU passthrough.

## Overview

VM-based LLM deployment enables:

- **Windows tools** - LM Studio, specialized applications
- **Isolation** - Separate environment from host
- **GPU passthrough** - Direct GPU access in VM
- **API sharing** - Host and containers access VM-hosted models

## When to Use VMs

| Scenario | VM Benefit |
|----------|------------|
| Windows-only software | Run LM Studio Windows |
| Testing different OSes | Separate environments |
| Strong isolation | Security boundaries |
| GPU-specific drivers | Match driver to application |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Linux Host (Ubuntu)                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  QEMU/KVM Hypervisor                      │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │                Windows 11 VM                         │ │   │
│  │  │  ┌───────────────────────────────────────────────┐  │ │   │
│  │  │  │              LM Studio                         │  │ │   │
│  │  │  │         (OpenAI-compatible API)               │  │ │   │
│  │  │  │           :1234 → API endpoint                │  │ │   │
│  │  │  └───────────────────────────────────────────────┘  │ │   │
│  │  │  ┌───────────────────────────────────────────────┐  │ │   │
│  │  │  │         AMD/NVIDIA GPU (Passthrough)          │  │ │   │
│  │  │  └───────────────────────────────────────────────┘  │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                       192.168.122.10:1234                        │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐ │
│  │                       Clients                               │ │
│  │  • Host applications                                        │ │
│  │  • Docker containers (via host network)                     │ │
│  │  • Other VMs                                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Topics

<div class="grid cards" markdown>

-   :material-microsoft-windows: **Windows LM Studio**

    ---

    LM Studio in Windows VM with GPU passthrough

    [:octicons-arrow-right-24: Windows setup](windows-lm-studio.md)

-   :material-api: **API from VM**

    ---

    Access VM-hosted LLM APIs from host and containers

    [:octicons-arrow-right-24: API access](api-from-vm.md)

</div>

## Prerequisites

- GPU passthrough configured (see [GPU Passthrough](../../virtualization/gpu-passthrough.md))
- Windows VM with GPU drivers
- Sufficient RAM for host + VM + model

## Quick Start

### 1. Configure GPU Passthrough

Follow [GPU Passthrough](../../virtualization/gpu-passthrough.md) guide.

### 2. Install Windows VM

See [Windows 11 VM](../../virtualization/windows-vm.md).

### 3. Install LM Studio in VM

Download from [lmstudio.ai](https://lmstudio.ai) in the Windows VM.

### 4. Start API Server

In LM Studio: Local Server → Start Server

### 5. Access from Host

```bash
# Test connection
curl http://192.168.122.10:1234/v1/models

# Use with tools
export OPENAI_API_BASE=http://192.168.122.10:1234/v1
```

## Resource Allocation

### Memory Planning

For 128GB system running LLM in VM:

| Component | Memory | Notes |
|-----------|--------|-------|
| Host reserved | 16-32GB | OS, containers, cache |
| VM | 96-112GB | Most for VM |
| Model in VM | ~43GB | 70B Q4 |
| VM overhead | ~4GB | Windows, apps |

### CPU Allocation

```xml
<!-- VM config -->
<vcpu>16</vcpu>
<cpu mode='host-passthrough'>
  <topology sockets='1' cores='8' threads='2'/>
</cpu>
```

## Comparison: VM vs Container

| Aspect | VM | Container |
|--------|-----|-----------|
| Overhead | Higher | Lower |
| Isolation | Full | Process-level |
| GPU access | Passthrough | NVIDIA/ROCm toolkit |
| Windows support | Yes | WSL only |
| Setup complexity | Higher | Lower |
| Startup time | Minutes | Seconds |

## Recommendation

- **Use containers** when possible (Linux, GPU toolkit available)
- **Use VMs** for Windows-only tools or strong isolation requirements

## See Also

- [GPU Passthrough](../../virtualization/gpu-passthrough.md) - GPU configuration
- [Windows 11 VM](../../virtualization/windows-vm.md) - VM setup
- [Container Deployment](../containers/index.md) - Alternative approach
