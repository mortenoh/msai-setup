# Windows 11 VM

## Overview

Create a Windows 11 admin/utility VM on the MS-S1 MAX with emulated GPU (virtio-gpu/Spice) over RDP — **without** GPU passthrough.

!!! warning "GPU passthrough on this hardware"
    The Strix Halo iGPU is the only GPU in the system. Passing it through to the Windows VM means the host has no GPU for ROCm-based local LLM inference (the primary purpose of this build). This guide assumes the **host keeps the GPU**; the VM uses virtio-gpu and is accessed via RDP. If you want to flip that trade-off, see [GPU Passthrough](gpu-passthrough.md) — but understand it disables host AI workloads.

## Prerequisites

- [KVM Setup](kvm-setup.md) completed (including `swtpm swtpm-tools`)
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

!!! note "Verify the URL is live"
    `fedorapeople.org` has been the historical canonical source for virtio-win. Red Hat occasionally moves distribution points; if the `wget` fails, check the [KVM-on-Windows wiki](https://github.com/virtio-win/virtio-win-pkg-scripts) for the current URL.

## Create VM

### Using virt-install

Windows 11 requires TPM 2.0 and ideally Secure Boot. The `--tpm` flag wires up `swtpm` for an emulated TPM 2.0 device, and `loader=…OVMF_CODE.secboot.fd` selects the Secure-Boot variant of OVMF.

```bash
virt-install \
    --name win11 \
    --memory 16384 \
    --vcpus 8 \
    --cpu host-passthrough \
    --machine q35 \
    --boot loader=/usr/share/OVMF/OVMF_CODE.secboot.fd,loader_ro=yes,loader_type=pflash,loader_secure=yes,nvram_template=/usr/share/OVMF/OVMF_VARS.secboot.fd \
    --features smm=on \
    --tpm backend.type=emulator,model=tpm-crb,backend.version=2.0 \
    --disk path=/mnt/tank/vm/win11.qcow2,size=200,bus=virtio,cache=writeback,discard=unmap \
    --cdrom /var/lib/libvirt/images/Win11.iso \
    --disk path=/var/lib/libvirt/images/virtio-win.iso,device=cdrom \
    --network network=default,model=virtio \
    --graphics spice \
    --video virtio \
    --osinfo win11
```

The `--graphics spice` + `--video virtio` combo gives you a usable console for the install. Once Windows is up and RDP is configured, you can keep Spice or remove it.

### Using virt-manager

1. Create new VM
2. Select Windows 11 ISO
3. Set memory (16 GB+) and CPUs (8+)
4. Create disk on ZFS pool (200 GB+) — keep VM disks on the **primary 2 TB NVMe**, not the slow x1 slot
5. Customize before install:
    - Firmware: UEFI with Secure Boot (`OVMF_CODE.secboot.fd`)
    - Chipset: Q35
    - CPU: host-passthrough
    - Add TPM device (CRB, version 2.0, emulator backend)
    - Add VirtIO ISO as CDROM
    - Video: virtio
    - Display: Spice (for install) or remove later in favour of RDP only

## Windows Installation

1. Boot from Windows ISO
2. At disk selection, load VirtIO drivers:
    - Browse to VirtIO CD
    - Select `amd64/win11`
    - Install storage driver
3. Complete Windows installation
4. Install remaining VirtIO drivers from Device Manager

## Post-Install

### Enable Remote Desktop

Primary access path for this headless-host build:

1. Settings > System > Remote Desktop
2. Enable Remote Desktop
3. Add the user to the Remote Desktop Users group
4. Note the VM's IP (via libvirt NAT or bridge), connect via RDP from your Mac/PC

### Performance tuning (no GPU passthrough)

Without GPU passthrough this VM is fine for admin/utility/Office-class workloads. For 3D-accelerated workloads or gaming, you have two options:

- **Re-evaluate the trade-off**: enable [GPU Passthrough](gpu-passthrough.md) and accept that host ROCm goes offline whenever the VM runs.
- **Stream from another machine**: keep the iGPU on the host, run any GPU-heavy work on a separate workstation, and use RDP/Parsec/Moonlight from the Windows VM as a thin client.

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
