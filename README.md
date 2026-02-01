# MS-S1 MAX Server Setup

[![Documentation](https://img.shields.io/badge/docs-live-blue)](https://mortenoh.github.io/msai-setup/)
[![AI Generated](https://img.shields.io/badge/AI%20Generated-Claude-blueviolet)](https://claude.ai)
[![MkDocs](https://img.shields.io/badge/built%20with-MkDocs%20Material-blue)](https://squidfunk.github.io/mkdocs-material/)

> **This documentation is 100% AI-generated using Claude.** All 290+ pages of guides, tutorials, and reference material were created through conversations with Claude (Anthropic). This serves as both practical documentation and a demonstration of AI-assisted technical writing.

> [!CAUTION]
> **Not Verified or Tested**: This documentation has not been manually verified or tested. Commands, configurations, and procedures may contain errors, omissions, or may not work as described. Always review commands before executing them, especially those requiring root/sudo privileges. Use at your own risk.

**[View Live Documentation](https://mortenoh.github.io/msai-setup/)**

---

Comprehensive setup guide for the Minisforum MS-S1 MAX as a home server running Ubuntu, ZFS, KVM, Docker, and local LLMs.

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

## Documentation Sections

| Section | Description | Link |
|---------|-------------|------|
| **Getting Started** | Hardware overview, BIOS setup, prerequisites | [View](https://mortenoh.github.io/msai-setup/getting-started/) |
| **Ubuntu Server** | Installation, security hardening, systemd, logging | [View](https://mortenoh.github.io/msai-setup/ubuntu/) |
| **ZFS Storage** | Pool creation, datasets, snapshots, Docker integration | [View](https://mortenoh.github.io/msai-setup/zfs/) |
| **Bcachefs** | Next-gen COW filesystem, DKMS setup, encryption, caching | [View](https://mortenoh.github.io/msai-setup/bcachefs/) |
| **Virtualization** | KVM setup, GPU passthrough, Windows 11 VM | [View](https://mortenoh.github.io/msai-setup/virtualization/) |
| **Docker** | Compose, development stacks, Ollama, monitoring, Nextcloud, Plex | [View](https://mortenoh.github.io/msai-setup/docker/) |
| **Netplan** | Network configuration, bridges, bonds, VLANs | [View](https://mortenoh.github.io/msai-setup/netplan/) |
| **Firewall & Security** | UFW, iptables, nftables, Docker/KVM networking | [View](https://mortenoh.github.io/msai-setup/networking/) |
| **SSH** | Client/server config, tunneling, file transfer | [View](https://mortenoh.github.io/msai-setup/ssh/) |
| **Tailscale** | Mesh VPN, MagicDNS, exit nodes, Docker integration | [View](https://mortenoh.github.io/msai-setup/tailscale/) |
| **Bash** | Shell fundamentals, scripting, tools, chezmoi, direnv, Starship | [View](https://mortenoh.github.io/msai-setup/bash/) |
| **AI & Local LLMs** | ROCm, llama.cpp, Ollama, AI coding tools (Claude Code, Aider, Cline) | [View](https://mortenoh.github.io/msai-setup/ai/) |
| **Operations** | Monitoring, backup, recovery, secrets management | [View](https://mortenoh.github.io/msai-setup/operations/) |

## Key Topics

- **Ubuntu Server** - Installation, CIS hardening, AppArmor, Fail2ban, auditd
- **ZFS** - Pool creation, datasets, snapshots, Docker integration
- **Bcachefs** - Next-gen filesystem, encryption, compression, SSD caching
- **KVM/QEMU** - Virtualization, GPU passthrough, Windows 11 VM
- **Docker** - Compose, development stacks, Ollama stack, monitoring, container services
- **Networking** - Netplan, UFW, iptables/nftables, namespaces
- **SSH** - Keys, agent forwarding, tunneling, jump hosts
- **Tailscale** - WireGuard mesh VPN, ACLs, subnet routing
- **Bash** - Scripting, chezmoi, direnv, 1Password CLI, modern CLI tools, Starship
- **Local LLMs** - ROCm setup, llama.cpp, Ollama, AI coding tools (Claude Code, Aider, Cline, Continue)

## Local Development

```bash
# Clone repository
git clone https://github.com/mortenoh/msai-setup.git
cd msai-setup

# Install dependencies (requires uv)
uv sync

# Start local server
uv run mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Building Static Site

```bash
uv run mkdocs build
```

Output goes to `site/` directory.

## Project Structure

```
docs/
  getting-started/    # Hardware, BIOS, prerequisites
  ubuntu/             # Installation, security, systemd, logging
  zfs/                # Pool creation, datasets, snapshots
  bcachefs/           # Next-gen COW filesystem documentation
  virtualization/     # KVM, GPU passthrough, Windows VM
  docker/             # Container setup, Nextcloud, Plex
  netplan/            # Network configuration
  networking/         # Firewall, UFW, Docker/KVM networking
  ssh/                # Client, server, tunneling, file transfer
  tailscale/          # Mesh VPN, features, integration
  bash/               # Fundamentals, scripting, tools, Starship
  ai/                 # GPU setup, inference engines, models
  operations/         # Monitoring, backup, recovery
```

## License

This documentation is provided as-is for educational purposes.

## Acknowledgments

- Generated entirely by [Claude](https://claude.ai) (Anthropic)
- Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- Deployed via [GitHub Pages](https://pages.github.com/)
