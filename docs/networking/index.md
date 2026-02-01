# Networking & Firewall

This section provides comprehensive coverage of Linux networking and firewall configuration, with particular focus on the complex interactions between UFW, Docker, KVM/libvirt, and LXC.

## Why This Matters

A home server running virtualization and containers creates a complex networking environment where multiple tools manipulate the same underlying systems. Without understanding these interactions, you risk:

- **Security holes** - Services exposed unintentionally
- **Broken connectivity** - VMs or containers unable to reach the network
- **Debugging nightmares** - Hours spent on issues caused by conflicting rules
- **False sense of security** - UFW enabled but not actually protecting anything

## Section Overview

### Fundamentals

- [Linux Networking Basics](fundamentals/linux-networking.md) - How packets flow through the kernel
- [Netfilter Architecture](fundamentals/netfilter.md) - The kernel's packet filtering framework
- [iptables Deep Dive](fundamentals/iptables.md) - Tables, chains, and rule processing
- [nftables Introduction](fundamentals/nftables.md) - The modern netfilter frontend
- [Network Namespaces](fundamentals/namespaces.md) - Container and VM network isolation

### UFW

- [UFW Fundamentals](ufw/fundamentals.md) - What UFW does and how it works
- [UFW Configuration](ufw/configuration.md) - Rules, policies, and files
- [UFW Advanced Usage](ufw/advanced.md) - Complex rules and custom chains
- [UFW Logging & Monitoring](ufw/logging.md) - Understanding and analyzing logs

### Docker Networking

- [Docker Network Overview](docker/overview.md) - Bridge, host, overlay networks
- [Docker and iptables](docker/iptables.md) - How Docker manipulates firewall rules
- [Docker UFW Conflict](docker/ufw-conflict.md) - The bypass problem explained
- [Docker UFW Solutions](docker/ufw-solutions.md) - Fixing the Docker/UFW issue
- [Docker Compose Networking](docker/compose.md) - Multi-container networking
- [Docker Network Security](docker/security.md) - Hardening container networks

### KVM/libvirt Networking

- [libvirt Network Overview](kvm/overview.md) - NAT, bridged, and isolated networks
- [KVM UFW Integration](kvm/ufw-integration.md) - Making UFW work with VMs
- [Bridged Networking](kvm/bridged.md) - VMs on the host network
- [VM Port Forwarding](kvm/port-forwarding.md) - Exposing VM services

### LXC/LXD Networking

- [LXD Network Overview](lxc/overview.md) - Container networking modes
- [LXD UFW Integration](lxc/ufw-integration.md) - Firewall considerations for LXC

### Integration & Conflicts

- [Multi-Technology Conflicts](integration/conflicts.md) - When Docker, KVM, and LXC collide

### External Access

- [External Access Guide](external-access/index.md) - Accessing services from outside your network

### Troubleshooting

- [Debugging Methodology](troubleshooting/methodology.md) - Systematic approach to network issues
- [Common Problems](troubleshooting/common-problems.md) - Frequent issues and solutions

### Reference

- [Complete before.rules](reference/before-rules.md) - Production-ready UFW configuration

## Quick Start

If you're setting up a new server, start with:

1. [UFW Fundamentals](ufw/fundamentals.md) - Basic firewall setup
2. [Docker UFW Conflict](docker/ufw-conflict.md) - Understand the problem
3. [Docker UFW Solutions](docker/ufw-solutions.md) - Fix it
4. [Complete before.rules](reference/before-rules.md) - Copy a working config

## Key Takeaways

!!! danger "Docker Bypasses UFW"
    By default, Docker published ports are accessible from anywhere, regardless of UFW rules. See [Docker UFW Conflict](docker/ufw-conflict.md).

!!! warning "Multiple Tools, One iptables"
    Docker, libvirt, and LXD all manipulate iptables. They can conflict. See [Multi-Technology Conflicts](integration/conflicts.md).

!!! tip "Use before.rules"
    Most integration issues are solved by properly configuring `/etc/ufw/before.rules`. See [Complete before.rules](reference/before-rules.md).
