# Windows 11 VM

## Overview

Create a Windows 11 VM with GPU passthrough for gaming.

## Prerequisites

- [KVM Setup](kvm-setup.md) completed
- [GPU Passthrough](gpu-passthrough.md) configured
- Windows 11 ISO
- VirtIO drivers ISO

## Download Required Files

### Windows 11 ISO

Download from Microsoft's official site.

### VirtIO Drivers

```bash
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso
sudo mv virtio-win.iso /var/lib/libvirt/images/
```

## Create VM

### Using virt-install

```bash
virt-install \
    --name win11 \
    --memory 16384 \
    --vcpus 8 \
    --cpu host-passthrough \
    --machine q35 \
    --boot uefi \
    --disk path=/mnt/tank/vm/win11.qcow2,size=200,bus=virtio \
    --cdrom /var/lib/libvirt/images/Win11.iso \
    --disk path=/var/lib/libvirt/images/virtio-win.iso,device=cdrom \
    --network network=default,model=virtio \
    --graphics none \
    --hostdev <GPU_PCI_ADDRESS> \
    --hostdev <GPU_AUDIO_PCI_ADDRESS>
```

### Using virt-manager

1. Create new VM
2. Select Windows 11 ISO
3. Set memory (16 GB+) and CPUs (8+)
4. Create disk on ZFS pool (200 GB+)
5. Customize before install:
    - Firmware: UEFI
    - Chipset: Q35
    - CPU: host-passthrough
    - Add VirtIO ISO as CDROM
    - Add GPU PCI devices
    - Remove Spice/VNC display

## Windows Installation

1. Boot from Windows ISO
2. At disk selection, load VirtIO drivers:
    - Browse to VirtIO CD
    - Select `amd64/win11`
    - Install storage driver
3. Complete Windows installation
4. Install remaining VirtIO drivers from Device Manager

## Post-Install

### Install GPU Drivers

Download and install AMD drivers from AMD's website.

### Enable Remote Desktop

For admin access when GPU is busy:

1. Settings > System > Remote Desktop
2. Enable Remote Desktop
3. Note the IP address

### Install Parsec/Moonlight (Optional)

For game streaming when away from monitor.

## Performance Tuning

### CPU Pinning

Edit VM XML:

```xml
<vcpu placement='static'>8</vcpu>
<cputune>
    <vcpupin vcpu='0' cpuset='0'/>
    <vcpupin vcpu='1' cpuset='1'/>
    <!-- etc -->
</cputune>
```

### Huge Pages

```bash
# /etc/sysctl.d/hugepages.conf
vm.nr_hugepages = 8192
```

### Disk I/O

Use `writeback` cache for better performance:

```xml
<driver name='qemu' type='qcow2' cache='writeback'/>
```

## VM Management

```bash
# Start VM
virsh start win11

# Stop VM gracefully
virsh shutdown win11

# Force stop
virsh destroy win11

# Autostart on boot
virsh autostart win11
```
