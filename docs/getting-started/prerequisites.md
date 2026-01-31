# Prerequisites

## Before You Begin

### Required

- [ ] MS-S1 MAX or similar mini-PC with:
    - AMD CPU with IOMMU support
    - GPU capable of passthrough
    - At least 32 GB RAM recommended
- [ ] Ubuntu Server 24.04 LTS ISO
- [ ] USB drive for installation
- [ ] Network connection (Ethernet preferred)
- [ ] SSH client on another machine

### Recommended

- [ ] Second machine for SSH management during setup
- [ ] Basic familiarity with:
    - Linux command line
    - systemd services
    - Docker and Compose
    - ZFS concepts

## Knowledge Requirements

This guide assumes you understand:

- Partitioning and filesystems
- Basic networking (IP, DHCP, DNS)
- SSH key authentication
- YAML configuration files

## Network Planning

Before installation, determine:

- Static IP or DHCP reservation for the server
- Network interface name (check with `ip link`)
- DNS servers to use
- Any VLANs if applicable

## Backup Strategy

Have a plan for:

- Where ZFS snapshots will be sent
- Off-site backup destination
- Recovery testing schedule
