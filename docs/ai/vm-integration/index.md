# VM Integration

Run Windows-only LLM tooling (e.g. LM Studio) in a VM alongside the host's ROCm inference.

!!! warning "The default on this build: the host keeps the GPU"
    On the MS-S1 MAX the iGPU stays with the **host** for ROCm inference — that is this build's primary purpose (see `START.md` and [Architecture Decisions](../fundamentals/architecture-decisions.md)). The default Windows VM uses **virtio-gpu** (no GPU passthrough) and reaches the GPU indirectly by calling the host's Ollama/llama.cpp API. iGPU passthrough is an **opt-in** path that is mutually exclusive with host ROCm; only pursue it if you deliberately hand the GPU to the VM and give up host inference (see [GPU Passthrough](../../virtualization/gpu-passthrough.md) and [Windows 11 VM](../../virtualization/windows-vm.md)).

## Overview

VM-based LLM deployment enables:

- **Windows tools** - LM Studio, specialized applications
- **Isolation** - Separate environment from host
- **API sharing** - the VM can call the host's Ollama/llama.cpp API (default), or serve its own API back to the host

For the default (no passthrough) setup, the realistic options are: run LM Studio's **CPU** inference inside the VM, or have the VM call the host's GPU-accelerated Ollama/llama.cpp API (see [API from VM](api-from-vm.md)). Direct GPU access in the VM requires the opt-in passthrough path below.

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
│  │  │  │           :1234 -> API endpoint                │  │ │   │
│  │  │  └───────────────────────────────────────────────┘  │ │   │
│  │  │  ┌───────────────────────────────────────────────┐  │ │   │
│  │  │  │      AMD GPU (opt-in passthrough only —        │  │ │   │
│  │  │  │      default VM uses virtio-gpu, no GPU)       │  │ │   │
│  │  │  └───────────────────────────────────────────────┘  │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                       192.168.122.10:1234                        │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐ │
│  │                       Clients                               │ │
│  │  - Host applications                                        │ │
│  │  - Docker containers (via host network)                     │ │
│  │  - Other VMs                                                │ │
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

- Windows VM (default: virtio-gpu, no passthrough — see [Windows 11 VM](../../virtualization/windows-vm.md))
- Sufficient RAM for host + VM + model
- Opt-in only: GPU passthrough configured, if you are deliberately handing the iGPU to the VM (see [GPU Passthrough](../../virtualization/gpu-passthrough.md)) — note this disables host ROCm

## Quick Start (default: no passthrough)

### 1. Install Windows VM

See [Windows 11 VM](../../virtualization/windows-vm.md). The default uses virtio-gpu, so the iGPU stays with the host for ROCm.

### 2. Install LM Studio in VM

Download from [lmstudio.ai](https://lmstudio.ai) in the Windows VM. Without passthrough, LM Studio runs **CPU** inference in the VM.

### 3. Choose how the VM gets inference

- **Recommended**: point tools in the VM at the host's GPU-accelerated Ollama/llama.cpp API instead of running heavy models in the VM (see [API from VM](api-from-vm.md)).
- **Or**: run LM Studio's own CPU inference in the VM for lighter models, then start its Local Server (`Local Server -> Start Server`) to expose an API.

### 4. Access from Host (if the VM serves an API)

```bash
# Test connection
curl http://192.168.122.10:1234/v1/models

# Use with tools
export OPENAI_API_BASE=http://192.168.122.10:1234/v1
```

!!! note "Opt-in GPU passthrough path"
    If you specifically need GPU acceleration *inside* the VM, follow [GPU Passthrough](../../virtualization/gpu-passthrough.md) first — but this hands the iGPU to the VM and disables host ROCm inference. It is not the default for this build.

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
| GPU access | Passthrough | ROCm devices (/dev/kfd, /dev/dri) |
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
