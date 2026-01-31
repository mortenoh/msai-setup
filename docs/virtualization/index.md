# Virtualization

This section covers KVM/QEMU virtualization and GPU passthrough for the MS-S1 MAX.

## Overview

Virtualization stack:

- **KVM** - Kernel-based Virtual Machine
- **QEMU** - Hardware emulation
- **libvirt** - Management API
- **virt-manager** - GUI (used remotely over SSH)

## Key Principles

- VMs run directly on the host
- No containers around KVM/libvirt
- UEFI (OVMF) with Q35 chipset
- CPU mode: host-passthrough

## Sections

- [KVM Setup](kvm-setup.md) - Install and configure KVM/QEMU/libvirt
- [GPU Passthrough](gpu-passthrough.md) - Pass AMD GPU to VM
- [Windows 11 VM](windows-vm.md) - Create Windows 11 gaming VM
