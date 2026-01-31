# MS-S1 MAX Server

Setup guide for the MS-S1 MAX mini-PC running Ubuntu Server with ZFS, KVM, and Docker.

## Project Goals

Build a clean, minimal Ubuntu Server host that:

- Uses **ZFS** for all important data
- Runs full desktop OSes (Windows 11, Linux) via **KVM/QEMU** with GPU passthrough
- Runs services (Nextcloud, Plex, etc.) via **Docker**
- Remains rebuildable, understandable, and low-maintenance

## The Hardware

This guide is built around the **Minisforum MS-S1 MAX**, a mini-PC featuring AMD's Strix Point APU - a chip that combines CPU and GPU on a single die with access to all system memory.

```
AMD Ryzen AI Max+ 395 (Strix Point APU):
+--------------------------------------------------+
|                                                  |
|  +-------------+          +------------------+   |
|  |   Zen 5     |          |    RDNA 3.5      |   |
|  |   16 cores  |          |    40 CUs        |   |
|  |   32 threads|          |    (gfx1151)     |   |
|  +------+------+          +--------+---------+   |
|         |                          |             |
|         +------------+-------------+             |
|                      |                           |
|         +------------v-------------+             |
|         |   Unified Memory         |             |
|         |   128GB DDR5-5600        |             |
|         |   Shared CPU + GPU       |             |
|         +--------------------------+             |
|                                                  |
+--------------------------------------------------+
```

| Component | Specification | Why It Matters |
|-----------|---------------|----------------|
| CPU | Ryzen AI Max+ 395 (16 cores) | Fast prompt processing |
| GPU | RDNA 3.5 (40 CUs) | Accelerated inference |
| RAM | 128GB DDR5-5600 | Fits 70B+ models |
| Architecture | Unified memory | No VRAM bottleneck |

Unlike discrete GPUs limited to 24GB VRAM, the APU shares all 128GB with both CPU and GPU, enabling models that won't fit on any consumer graphics card.

[:octicons-arrow-right-24: Hardware details](getting-started/hardware.md){ .md-button }
[:octicons-arrow-right-24: Hardware architecture](getting-started/hardware-architecture.md){ .md-button .md-button--primary }

## Quick Links

<div class="grid cards" markdown>

-   :material-rocket-launch: **Getting Started**

    ---

    Hardware specs, architecture overview, and prerequisites

    [:octicons-arrow-right-24: Get started](getting-started/index.md)

-   :material-ubuntu: **Ubuntu Server**

    ---

    Installation, post-install config, networking, and firewall

    [:octicons-arrow-right-24: Ubuntu setup](ubuntu/index.md)

-   :material-harddisk: **ZFS Storage**

    ---

    Pool creation, datasets, and snapshot policies

    [:octicons-arrow-right-24: ZFS guide](zfs/index.md)

-   :material-server: **Virtualization**

    ---

    KVM setup, GPU passthrough, and Windows 11 VM

    [:octicons-arrow-right-24: VMs](virtualization/index.md)

-   :material-docker: **Docker Services**

    ---

    Nextcloud, Plex, and other containerized services

    [:octicons-arrow-right-24: Services](docker/index.md)

-   :material-tools: **Operations**

    ---

    Backup, recovery, and rebuild procedures

    [:octicons-arrow-right-24: Ops guide](operations/index.md)

-   :material-brain: **AI & Local LLMs**

    ---

    Run local LLMs with Ollama, llama.cpp, and AI coding tools

    [:octicons-arrow-right-24: AI guide](ai/index.md)

</div>

## Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| Host OS is boring | Ubuntu Server LTS, no desktop, SSH-only |
| Data lives outside containers | ZFS is the source of truth |
| VMs are first-class | KVM/QEMU with GPU passthrough |
| Services are containerized | Docker + Compose with bind mounts |
| Everything is recoverable | Reinstall host without touching data |

## What This Project Avoids

- ZFS on root
- Desktop environment on the host
- Manual iptables rules
- Docker volumes for critical data
- Nested virtualization
- "All-in-one" hypervisor distros
