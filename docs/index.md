# MS-S1 MAX Server

Setup guide for the MS-S1 MAX mini-PC running Ubuntu Server with ZFS, KVM, and Docker.

## Project Goals

Build a clean, minimal Ubuntu Server host that:

- Uses **ZFS** for all important data
- Runs full desktop OSes (Windows 11, Linux) via **KVM/QEMU** with GPU passthrough
- Runs services (Nextcloud, Plex, etc.) via **Docker**
- Remains rebuildable, understandable, and low-maintenance

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
