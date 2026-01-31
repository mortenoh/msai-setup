# VM Storage

## Overview

ZFS provides two approaches for VM disk storage:

| Approach | Use Case | Pros | Cons |
|----------|----------|------|------|
| Directory pool | Simple setups, qcow2 images | Easy management, flexible | Extra filesystem layer |
| Zvols | Performance, Windows VMs | Direct block device, better I/O | Less flexible |

## Directory-Based Storage

The simpler approach uses a ZFS dataset as a libvirt storage pool. VM images (qcow2) are stored as files.

This is already configured in [KVM Setup](../virtualization/kvm-setup.md):

```bash
virsh pool-define-as vm-pool dir - - - - /mnt/tank/vm
virsh pool-start vm-pool
virsh pool-autostart vm-pool
```

## Zvol-Based Storage

Zvols are block devices backed by ZFS. VMs access them directly without a filesystem layer.

### Create a Zvol

```bash
sudo zfs create -V 100G tank/vm/win11
```

The `-V` flag creates a volume (zvol) instead of a filesystem dataset.

### Zvol Properties

Set properties at creation time:

```bash
sudo zfs create -V 100G \
    -o volblocksize=64K \
    -o compression=lz4 \
    tank/vm/win11
```

| Property | Recommended | Notes |
|----------|-------------|-------|
| volblocksize | 64K | Balance between performance and space efficiency |
| compression | lz4 | Good for most workloads |
| sync | standard | Use `disabled` only for non-critical VMs |

!!! warning "volblocksize is immutable"
    Once set, volblocksize cannot be changed. Choose carefully based on workload.

### Access Zvol

Zvols appear as block devices:

```bash
ls -la /dev/zvol/tank/vm/
```

Output:

```
win11 -> /dev/zd0
```

## libvirt Integration

### Define Zvol Storage Pool

Create a pool for zvols:

```xml
<!-- zvol-pool.xml -->
<pool type='zfs'>
  <name>zvol-pool</name>
  <source>
    <name>tank/vm</name>
  </source>
</pool>
```

```bash
virsh pool-define zvol-pool.xml
virsh pool-start zvol-pool
virsh pool-autostart zvol-pool
```

### Create VM with Zvol

Using `virt-install`:

```bash
virt-install \
    --name win11 \
    --ram 16384 \
    --vcpus 8 \
    --os-variant win11 \
    --disk path=/dev/zvol/tank/vm/win11,bus=virtio \
    --cdrom /path/to/win11.iso \
    --network network=default \
    --graphics spice \
    --boot uefi
```

### Attach Zvol to Existing VM

```bash
virsh attach-disk win11 /dev/zvol/tank/vm/win11-data vdb --persistent
```

## Snapshots

### Snapshot Before Changes

Before Windows updates or risky changes:

```bash
sudo zfs snapshot tank/vm/win11@before-update
```

### List Snapshots

```bash
zfs list -t snapshot -r tank/vm
```

### Rollback

!!! warning "VM must be stopped"
    Always shut down the VM before rolling back.

```bash
virsh shutdown win11
sudo zfs rollback tank/vm/win11@before-update
virsh start win11
```

### Clone VM

Create a copy of a VM disk:

```bash
sudo zfs snapshot tank/vm/win11@clone-base
sudo zfs clone tank/vm/win11@clone-base tank/vm/win11-test
```

## Performance Considerations

### When to Use Zvols

- Windows VMs (better compatibility with NTFS)
- Database VMs requiring consistent I/O
- Performance-critical workloads

### When to Use Directory Pool

- Linux VMs with qcow2
- VMs needing thin provisioning features
- Simpler management requirements

### Tuning

For database VMs:

```bash
sudo zfs create -V 50G \
    -o volblocksize=16K \
    -o compression=lz4 \
    -o primarycache=metadata \
    tank/vm/postgres
```

For general VMs:

```bash
sudo zfs create -V 100G \
    -o volblocksize=64K \
    -o compression=lz4 \
    tank/vm/ubuntu-server
```

## Management Commands

```bash
# List zvols
zfs list -t volume

# Check zvol usage
zfs list -o name,volsize,used,refer -t volume

# Resize zvol (grow only recommended)
sudo zfs set volsize=150G tank/vm/win11

# Destroy zvol (VM must be removed first)
sudo zfs destroy tank/vm/win11
```
