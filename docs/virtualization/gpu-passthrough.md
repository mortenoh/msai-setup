# GPU Passthrough (to a VM)

!!! warning "Not the default for this build — and this is VM-level passthrough, a different thing from how this build reaches the GPU"
    This build does **not** pass the iGPU through to a VM. The default is
    documented in [Incus Windows 11 VM](../incus/windows-vm.md): the host
    keeps the GPU for ROCm and the VM uses virtio-gpu + RDP. There is only
    one iGPU, so VM passthrough is mutually exclusive with host ROCm —
    enabling it means host ROCm / AI inference goes offline whenever the VM
    is running. Only follow this page if you have deliberately chosen that
    trade-off.

    **How this build actually reaches the GPU** is *container* passthrough,
    not VM passthrough: the host keeps the iGPU, and Incus hands `/dev/dri`
    + `/dev/kfd` to the containers that run ROCm inference. That is a
    different mechanism entirely (device passthrough into a shared-kernel
    container, no VFIO, no driver unbinding) and is the supported path — see
    [Incus GPU passthrough](../incus/gpu-passthrough.md). This page is only
    about the still-available-but-not-default option of giving the *whole
    GPU* to a VM.

!!! note "If you do choose VM passthrough, it's an Incus VM device now"
    The VFIO/IOMMU host preparation below (binding the GPU to `vfio-pci`,
    blacklisting `amdgpu`) is unchanged — it's a host-kernel concern. What
    changes is the last step: instead of attaching the PCI device in
    `virt-manager`/`virsh`, you attach it to an [Incus VM](../incus/vms.md)
    with a `gpu` device (`incus config device add <vm> gpu gpu
    pci=<addr>`). The "Attach GPU to VM" section below describes the old
    libvirt flow; treat it as background for the concept.

## Overview

Pass the AMD GPU directly to a VM for native graphics performance.

!!! info "Display Model"
    The GPU will be owned by the VM. The host is managed over SSH.

## Prerequisites

- IOMMU enabled in BIOS (AMD-Vi)
- GPU in its own IOMMU group
- No host drivers attached to GPU

## Enable IOMMU

Edit `/etc/default/grub`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amd_iommu=on iommu=pt"
```

Update GRUB:

```bash
sudo update-grub
sudo reboot
```

## Verify IOMMU

```bash
dmesg | grep -i iommu
```

Look for "AMD-Vi" or "IOMMU enabled".

## Find GPU IOMMU Group

```bash
#!/bin/bash
for d in /sys/kernel/iommu_groups/*/devices/*; do
    n=${d#*/iommu_groups/*}; n=${n%%/*}
    printf 'IOMMU Group %s ' "$n"
    lspci -nns "${d##*/}"
done | grep -i "vga\|audio"
```

Note the GPU and its audio device IDs (e.g., `1002:xxxx`).

## Bind GPU to VFIO

### Create VFIO Configuration

```bash
# /etc/modprobe.d/vfio.conf
options vfio-pci ids=1002:xxxx,1002:yyyy
```

Replace with your GPU and audio device IDs.

### Load VFIO Early

```bash
# /etc/modules-load.d/vfio.conf
vfio-pci
vfio
vfio_iommu_type1
```

### Blacklist AMD Drivers

```bash
# /etc/modprobe.d/blacklist-amd.conf
blacklist amdgpu
blacklist radeon
```

### Update Initramfs

```bash
sudo update-initramfs -u
sudo reboot
```

## Verify VFIO Binding

```bash
lspci -nnk | grep -A3 "VGA"
```

Should show `Kernel driver in use: vfio-pci`.

## Attach GPU to VM

In virt-manager or virsh:

1. Add PCI Host Device (GPU)
2. Add PCI Host Device (GPU Audio)
3. Remove virtual display (Spice/VNC)
4. Connect monitor to GPU HDMI

## Troubleshooting

### IOMMU Group Issues

If GPU shares a group with other devices:

- Try different PCIe slots
- Use ACS override patch (last resort)

### Reset Issues

Some GPUs don't reset properly:

```bash
# /etc/modprobe.d/vfio.conf
options vfio-pci ids=1002:xxxx disable_vga=1
```

### No Display After VM Start

- Verify monitor connected to GPU
- Check VM is using UEFI
- Ensure Q35 chipset selected
