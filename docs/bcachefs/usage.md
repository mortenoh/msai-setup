# Bcachefs Usage

This guide covers creating, mounting, and managing bcachefs filesystems.

## Creating a Filesystem

### Single Device

```bash
# Format a single device
bcachefs format /dev/sdb

# With a label
bcachefs format --label=mydata /dev/sdb
```

### Multiple Devices (Striped)

```bash
# Stripe across multiple devices
bcachefs format /dev/sdb /dev/sdc /dev/sdd
```

### Replicated (RAID1)

```bash
# Mirror data across devices
bcachefs format --replicas=2 /dev/sdb /dev/sdc
```

### Mixed Configuration

```bash
# SSD cache with HDD storage
bcachefs format \
    --label=hdd.data1 /dev/sdb \
    --label=hdd.data2 /dev/sdc \
    --label=ssd.cache /dev/nvme0n1p1 \
    --foreground_target=ssd \
    --promote_target=ssd \
    --background_target=hdd
```

## Mounting

### Basic Mount

```bash
# Single device
mount -t bcachefs /dev/sdb /mnt/data

# Multiple devices (specify any member)
mount -t bcachefs /dev/sdb:/dev/sdc /mnt/data
```

### Mount Options

```bash
# With specific options
mount -t bcachefs -o noatime,compression=zstd /dev/sdb /mnt/data
```

Common mount options:

| Option | Description |
|--------|-------------|
| `noatime` | Don't update access times |
| `compression=<algo>` | Set compression (lz4, gzip, zstd) |
| `degraded` | Mount with missing devices |
| `verbose` | Increase logging verbosity |
| `norecovery` | Skip journal replay |

### Persistent Mounts (/etc/fstab)

```bash
# Get the filesystem UUID
bcachefs show-super /dev/sdb | grep uuid

# Add to /etc/fstab
UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx /mnt/data bcachefs defaults,noatime 0 0

# For multi-device
/dev/sdb:/dev/sdc /mnt/data bcachefs defaults,noatime 0 0
```

## Device Management

### Show Filesystem Info

```bash
# Display superblock info
bcachefs show-super /dev/sdb

# Show filesystem usage
bcachefs fs usage /mnt/data
```

### Adding Devices

```bash
# Add a new device to existing filesystem
bcachefs device add /mnt/data /dev/sdd
```

### Removing Devices

```bash
# Remove a device (data is migrated first)
bcachefs device remove /dev/sdd

# Or by path
bcachefs device remove /mnt/data /dev/sdd
```

### Device Evacuation

Before removing a device, evacuate its data:

```bash
bcachefs device evacuate /dev/sdd
```

## Filesystem Operations

### Check Filesystem

```bash
# Offline check (unmounted)
bcachefs fsck /dev/sdb

# With repair
bcachefs fsck -y /dev/sdb
```

### Online Scrub

```bash
# Verify all data checksums
bcachefs data scrub /mnt/data
```

### Filesystem Resize

```bash
# Resize after expanding underlying device
bcachefs device resize /dev/sdb
```

## Subvolumes

### Create Subvolume

```bash
# Create a subvolume
bcachefs subvolume create /mnt/data/mysubvol
```

### List Subvolumes

```bash
bcachefs subvolume list /mnt/data
```

### Delete Subvolume

```bash
bcachefs subvolume delete /mnt/data/mysubvol
```

## Snapshots

### Create Snapshot

```bash
# Snapshot a subvolume
bcachefs subvolume snapshot /mnt/data/mysubvol /mnt/data/mysubvol-snap
```

### Read-Only Snapshot

```bash
bcachefs subvolume snapshot -r /mnt/data/mysubvol /mnt/data/mysubvol-snap-ro
```

### Delete Snapshot

```bash
bcachefs subvolume delete /mnt/data/mysubvol-snap
```

## Monitoring

### Filesystem Statistics

```bash
# Show space usage
bcachefs fs usage /mnt/data

# Show device statistics
bcachefs device show /mnt/data
```

### Watching Activity

```bash
# Monitor filesystem activity
bcachefs fs top /mnt/data
```

## Unmounting

```bash
# Standard unmount
umount /mnt/data

# Force unmount if busy
umount -l /mnt/data
```

## Complete Example

Setting up a simple bcachefs filesystem:

```bash
# 1. Format the device
sudo bcachefs format --label=storage /dev/sdb

# 2. Create mount point
sudo mkdir -p /mnt/storage

# 3. Mount the filesystem
sudo mount -t bcachefs /dev/sdb /mnt/storage

# 4. Set permissions
sudo chown $USER:$USER /mnt/storage

# 5. Add to fstab for persistence
echo "UUID=$(bcachefs show-super /dev/sdb | grep 'External UUID' | awk '{print $3}') /mnt/storage bcachefs defaults,noatime 0 0" | sudo tee -a /etc/fstab

# 6. Test fstab entry
sudo umount /mnt/storage
sudo mount -a
```
