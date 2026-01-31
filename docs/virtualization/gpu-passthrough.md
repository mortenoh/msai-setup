# GPU Passthrough

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
