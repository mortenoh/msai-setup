# Netplan Network Configuration

This section provides comprehensive coverage of Netplan, Ubuntu's network configuration abstraction layer. Understanding Netplan is essential for configuring complex network setups involving bridges, bonds, VLANs, and integration with virtualization technologies.

## What is Netplan?

Netplan is a utility for network configuration on Linux systems using YAML files. It acts as an abstraction layer between you and the underlying network configuration systems.

```
┌─────────────────────────────────────────────────────────────┐
│                    YAML Configuration                        │
│                  /etc/netplan/*.yaml                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        Netplan                               │
│              Parses YAML, generates config                   │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    systemd-networkd     │   │    NetworkManager       │
│   (Server default)      │   │   (Desktop default)     │
└─────────────────────────┘   └─────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Linux Kernel                              │
│              Network interfaces configured                   │
└─────────────────────────────────────────────────────────────┘
```

## Why Netplan?

### Before Netplan

Different tools for different scenarios:
- `/etc/network/interfaces` (ifupdown)
- NetworkManager connection files
- systemd-networkd `.network` files
- Distribution-specific tools

### With Netplan

- **Single configuration format** (YAML)
- **Backend-agnostic** - same config works with networkd or NetworkManager
- **Declarative** - describe desired state, not commands
- **Cloud-ready** - integrates with cloud-init
- **Validation** - catches errors before applying

## Section Overview

### Fundamentals

- [Netplan Basics](fundamentals/basics.md) - Configuration files, syntax, commands
- [Renderers](fundamentals/renderers.md) - systemd-networkd vs NetworkManager
- [YAML Syntax](fundamentals/yaml-syntax.md) - Complete reference for Netplan YAML
- [Configuration Workflow](fundamentals/workflow.md) - Try, apply, debug

### Interface Types

- [Ethernet](interfaces/ethernet.md) - Physical interfaces, DHCP, static IP
- [Bridges](interfaces/bridges.md) - Software switches for VMs and containers
- [Bonds](interfaces/bonds.md) - Link aggregation for redundancy/performance
- [VLANs](interfaces/vlans.md) - Virtual LANs for network segmentation
- [Wireless](interfaces/wireless.md) - WiFi configuration
- [Virtual Interfaces](interfaces/virtual.md) - Dummy, VXLAN, tunnels

### Routing & DNS

- [Static Routes](routing/static-routes.md) - Custom routing tables
- [Policy Routing](routing/policy-routing.md) - Source-based routing
- [DNS Configuration](routing/dns.md) - systemd-resolved integration
- [IPv6](routing/ipv6.md) - Dual-stack and IPv6-only setups

### Advanced Topics

- [Multiple Addresses](advanced/multiple-addresses.md) - Secondary IPs, aliases
- [Wake-on-LAN](advanced/wake-on-lan.md) - Remote power management
- [Network Dispatcher](advanced/dispatcher.md) - Hooks and scripts
- [Performance Tuning](advanced/performance.md) - MTU, offloading, buffers

### Integration

- [Docker Integration](integration/docker.md) - Bridge networks for containers
- [KVM/libvirt Integration](integration/kvm.md) - VM networking with Netplan
- [LXD Integration](integration/lxd.md) - Container host networking

### Troubleshooting

- [Common Issues](troubleshooting/common-issues.md) - Frequent problems and solutions
- [Debugging Tools](troubleshooting/debugging.md) - networkctl, ip, ss
- [Migration Guide](troubleshooting/migration.md) - From interfaces file to Netplan

### Reference

- [Complete Examples](reference/examples.md) - Full configuration files
- [Property Reference](reference/properties.md) - All Netplan options
- [Network Diagrams](reference/diagrams.md) - Visual architecture examples

## Quick Start

### Minimal Server Configuration

```yaml
# /etc/netplan/00-config.yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

### Static IP Configuration

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
```

### Apply Configuration

```bash
# Test without applying
sudo netplan try

# Apply configuration
sudo netplan apply

# Generate and show backend config
sudo netplan generate
```

## Key Concepts

!!! info "Declarative Configuration"
    Netplan uses declarative YAML - you describe the desired end state, not the steps to get there.

!!! tip "Always Use netplan try"
    The `netplan try` command applies changes with an automatic rollback timer. Essential for remote administration.

!!! warning "File Naming Matters"
    Files are processed in alphabetical order. Use numbered prefixes (00-, 01-) to control order.
