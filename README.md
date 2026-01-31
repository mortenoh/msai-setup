# MS-S1 MAX Server Setup

Setup guide for the Minisforum MS-S1 MAX as a home server running Ubuntu, ZFS, KVM, Docker, and local LLMs.

## Hardware Overview

| Component | Specification |
|-----------|---------------|
| System | Minisforum MS-S1 MAX |
| CPU | AMD Ryzen AI Max+ 395 (16 cores / 32 threads, Zen 5) |
| GPU | AMD Radeon Graphics (RDNA 3.5, 40 CUs, integrated) |
| RAM | 128GB DDR5-5600 (unified, shared between CPU/GPU) |
| Storage | 2TB NVMe (system) + 4TB NVMe (ZFS pool) |
| TDP | 55-120W configurable |

The APU architecture enables running 70B+ parameter LLMs that wouldn't fit in discrete GPU VRAM (typically 24GB max).

## What's Covered

- **Ubuntu Server** - Installation, hardening, systemd configuration
- **ZFS** - Pool creation, datasets, snapshots, Docker integration
- **KVM/QEMU** - Virtualization, GPU passthrough, Windows 11 VM
- **Docker** - Container services, resource management
- **Networking** - Netplan, UFW, Tailscale, SSH
- **Local LLMs** - ROCm setup, llama.cpp, Ollama, inference optimization

## Viewing the Documentation

```bash
# Install dependencies
uv sync

# Start local server
uv run mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Project Structure

```
docs/
  getting-started/    # Hardware, BIOS, prerequisites
  ubuntu/             # Installation, security, systemd
  zfs/                # Storage configuration
  virtualization/     # KVM, GPU passthrough
  docker/             # Container services
  networking/         # Netplan
  netplan/            # Network configuration
  ssh/                # SSH configuration
  tailscale/          # Mesh VPN
  ai/                 # LLM setup and optimization
  operations/         # Backup, recovery, capacity planning
```

## Building Static Site

```bash
uv run mkdocs build
```

Output goes to `site/` directory.
