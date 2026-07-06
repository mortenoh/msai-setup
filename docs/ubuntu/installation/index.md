# Installation Overview

This section provides comprehensive guidance for installing Ubuntu Server 26.04 LTS ("Resolute Raccoon") on the MS-S1 MAX with the canonical architecture: plain ext4 root (500 GB) on the primary 4 TB NVMe, with the leftover ~3.4 TB and the entire 2 TB secondary NVMe as two independent ZFS pools (`hot` and `tank`). Root itself is deliberately not on ZFS — see [Disk Partitioning](disk-partitioning.md); the [ZFS Root (Alternative)](zfs-root-alternative.md) documents the boot-environment path for those who want it.

## Installation Philosophy

A secure system begins with a secure installation. The choices made during installation — partition layout, boot configuration, initial hardening — establish the foundation for everything that follows.

### Key Principles

- **Minimal attack surface** - Install only what's needed; no desktop environment
- **Boring foundations** - Plain ext4 root + GRUB, no LVM, no LUKS on this build
- **Data lives outside the OS** - ZFS pools are the source of truth, host is rebuildable
- **Defense in depth at the network layer** - UFW + Tailscale for management, not boot-time integrity

## Section Contents

| Page | Description |
|------|-------------|
| [Preparation](preparation.md) | Pre-installation planning, hardware verification, download verification |
| [Secure Boot](secure-boot.md) | UEFI Secure Boot — disabled on this build, kept here for reference |
| [Disk Partitioning](disk-partitioning.md) | Canonical ext4 root + two ZFS pools; encrypted alternative |
| [Installation Walkthrough](installation-walkthrough.md) | Step-by-step guided-installer guide |
| [ZFS Root (Alternative)](zfs-root-alternative.md) | Root-on-ZFS via ZFSBootMenu — documented alternative |
| [Post-Install Checklist](post-install-checklist.md) | First boot essentials and initial hardening |

## Quick Path

For experienced administrators:

1. [Download and verify ISO](preparation.md#download-and-verify)
2. Confirm BIOS settings ([BIOS Setup](../../getting-started/bios-setup.md)) — Secure Boot off, IOMMU on
3. [Partition the primary: ext4 root, leftover for ZFS](disk-partitioning.md#canonical-layout-ext4-root-two-independent-zfs-pools)
4. [Run through the guided install](installation-walkthrough.md)
5. [Complete post-install checklist](post-install-checklist.md)

## Installation Types

### Minimal Server (Recommended)

The minimal installation provides:

- Base system packages only
- SSH server (optional during install)
- No graphical environment
- ~2 GB disk footprint

This is the recommended approach for production servers.

### Standard Server

Includes additional packages for common server tasks:

- Network utilities
- Basic system monitoring
- Additional shells and editors

### Cloud Image

Pre-built images for cloud deployments:

- cloud-init enabled
- Smaller footprint
- Optimized for virtual environments

!!! note "This Guide's Focus"
    This guide focuses on **physical server installation** with custom partitioning (plain ext4 root via the guided installer, no LUKS by default — see [Disk Partitioning](disk-partitioning.md) for the optional encrypted alternative). For cloud deployments, see [Ubuntu Cloud Images](https://cloud-images.ubuntu.com/).

## Hardware

This guide is specifically targeted at the [Minisforum MS-S1 MAX](https://www.minisforum.com/products/ms-s1-max):

| Component | Specification |
|-----------|---------------|
| CPU | AMD Ryzen AI Max+ 395 (Strix Halo, 16C / 32T) |
| GPU | Radeon 8060S (RDNA 3.5, integrated, `gfx1151`) |
| RAM | 128GB LPDDR5X-8000, quad-channel (soldered) |
| Storage | 2 x M.2 NVMe (PCIe 4.0 x4 + x1); 4 TB primary + 2 TB secondary |
| Networking | 2 x 10GbE (Realtek RTL8127) |

See [Hardware](../../getting-started/hardware.md) for the full spec and design rationale.

## Pre-Installation Decisions

Before starting the installer, confirm:

1. **Disk layout** — canonical for this build is ext4 root + two ZFS data pools (`hot`, `tank`); see [Disk Partitioning](disk-partitioning.md). Root-on-ZFS is a [documented alternative](zfs-root-alternative.md)
2. **Encryption** — not used on this build (private network, headless box); ZFS native encryption / LUKS documented as alternatives
3. **Secure Boot** — disabled to keep amdgpu/ROCm/ZFS DKMS simple
4. **Network** — DHCP during install, switch to static via Netplan post-install
5. **Hostname** — pick now and use it consistently in `/etc/hosts`, Tailscale, reverse-proxy configs
6. **User account** — initial administrator username (same as previous install simplifies the rebuild path)

## Next Step

Begin with [Preparation](preparation.md) to verify hardware compatibility and download the installation media.
