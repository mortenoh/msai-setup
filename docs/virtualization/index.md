# Virtualization

This section covers KVM/QEMU virtualization on the MS-S1 MAX. GPU passthrough is an opt-in trade-off, not the default: by default the iGPU stays with the host for ROCm, and VMs use virtio-gpu.

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
- [VM Resources](vm-resources.md) - Memory, vCPU, and I/O allocation
- [GPU Passthrough](gpu-passthrough.md) - Pass AMD GPU to VM
- [Windows 11 VM](windows-vm.md) - Create a Windows 11 admin/utility VM with virtio-gpu + RDP (no passthrough)
