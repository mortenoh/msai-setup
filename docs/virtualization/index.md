# Virtualization

!!! note "VMs are managed through Incus on this build"
    This build no longer drives libvirt/`virt-install`/`virsh` directly on
    the host. Virtual machines are **[Incus](../incus/index.md) VM
    instances** — QEMU/KVM under the hood, managed with the `incus` CLI. The
    canonical current pages are [Incus VMs](../incus/vms.md) (the general VM
    model) and [Incus Windows 11 VM](../incus/windows-vm.md) (TPM 2.0 +
    Secure Boot + virtio + RDP). Read those for how to actually create and
    run a VM here.

    This section is kept as **background** — what KVM/QEMU/libvirt are, and
    how VM resource sizing works — because Incus is a thin management layer
    *over exactly this stack*. Understanding it explains what Incus is doing
    under the hood. Do **not** follow the bare `virt-install`/`virsh`
    commands here to set up the real VMs on this build; use the Incus pages.

This section covers the KVM/QEMU virtualization stack that sits under Incus
on the MS-S1 MAX. GPU passthrough is an opt-in trade-off, not the default:
by default the iGPU stays with the host for ROCm, and VMs use virtio-gpu.

## Overview

Virtualization stack (what Incus builds on):

- **KVM** - Kernel-based Virtual Machine (the hardware-virtualization layer)
- **QEMU** - Hardware emulation and the actual VM process
- **libvirt** - A management API over QEMU/KVM — used *directly* by the old
  design, now sitting behind Incus (Incus talks to QEMU/KVM itself rather
  than through libvirt, but the concepts map)
- **virt-manager** - GUI over libvirt — not used on this build; management is
  the `incus` CLI over SSH/Tailscale

## Key Principles (unchanged under Incus)

- VMs run on the host's KVM — Incus doesn't nest VMs inside anything, it
  manages them directly
- UEFI (OVMF) firmware with a Q35-class machine type — Incus configures this
  for you
- CPU mode passes host features through
- virtio paravirtualized devices for disk and network

## Sections

- [KVM Setup](kvm-setup.md) - background on the KVM/QEMU/libvirt stack Incus
  sits on (Incus supersedes the direct libvirt operation shown here)
- [VM Resources](vm-resources.md) - memory, vCPU, and I/O allocation
  concepts — the sizing guidance still applies; the libvirt XML is background
- [GPU Passthrough](gpu-passthrough.md) - the VM-level GPU passthrough
  trade-off (not the default; container passthrough is how this build reaches
  the GPU)
- [Windows 11 VM](windows-vm.md) - superseded by
  [Incus Windows 11 VM](../incus/windows-vm.md); kept as a short redirect
