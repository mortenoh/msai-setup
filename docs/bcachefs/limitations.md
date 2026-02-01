# Bcachefs Limitations

Understanding current limitations is essential before using bcachefs.

## Experimental Status

!!! danger "Not Production Ready"
    Bcachefs is explicitly marked as experimental by its developers. Data loss bugs have occurred and may occur again.

### What This Means

- Filesystem format may change between versions
- Upgrade paths are not guaranteed
- Recovery tools are less mature than ZFS/ext4
- Limited testing compared to established filesystems

### Recommended Precautions

1. **Always maintain backups** - on a different filesystem type
2. **Test upgrades** - in non-production environments first
3. **Monitor for errors** - check `dmesg` and logs regularly
4. **Keep snapshots** - for quick recovery from corruption

## Known Issues

### RAID5/6 - DO NOT USE

!!! danger "Data Loss Risk"
    RAID5 and RAID6 modes are explicitly marked "DO NOT USE YET" by bcachefs developers. They contain known bugs that can cause data loss.

Use RAID1 (mirroring) instead:

```bash
# Safe: RAID1 mirroring
bcachefs format --replicas=2 /dev/sda /dev/sdb

# UNSAFE: RAID5/6
# bcachefs format --data_checksum=... --erasure_code  # DON'T DO THIS
```

### No Swap File Support

Swap files on bcachefs are not supported:

```bash
# This will NOT work
fallocate -l 8G /mnt/bcachefs/swapfile
mkswap /mnt/bcachefs/swapfile
swapon /mnt/bcachefs/swapfile  # Fails
```

**Workarounds:**

- Use a swap partition on a different filesystem
- Use zram for swap
- Use a swap file on ext4/xfs

### 32-bit Systems

Bcachefs has limited testing on 32-bit systems. Some features may not work correctly or may have reduced limits.

### Large Filesystem Limits

While bcachefs theoretically supports very large filesystems, real-world testing at extreme scales is limited.

## DKMS Requirements

Since bcachefs is now external to the kernel:

### Build Requirements

- Kernel headers must be installed
- Build tools (gcc, make) must be available
- Recompilation needed after kernel updates

```bash
# After kernel update
sudo dkms autoinstall
```

### Boot Issues

If the DKMS module fails to build:

1. System may not mount bcachefs filesystems at boot
2. Root on bcachefs requires initramfs with the module
3. Secure Boot adds signing complexity

### Compatibility

- May break with kernel updates
- Development kernel features sometimes required
- Not available on all distributions

## Missing Features

### Compared to ZFS

| Feature | ZFS | Bcachefs |
|---------|-----|----------|
| Send/Receive | Full support | Basic/Partial |
| Deduplication | Supported | Not yet |
| Quotas | Full support | Planned |
| Native encryption | Dataset-level | Whole filesystem |
| Pool expansion | Add vdevs | Add devices |
| Stable RAID | Yes | RAID1 only |
| Boot support | Well tested | Limited |

### Compared to Btrfs

| Feature | Btrfs | Bcachefs |
|---------|-------|----------|
| In-kernel | Yes | No (DKMS) |
| Send/Receive | Full support | Basic |
| Quotas | Supported | Planned |
| Stable RAID | RAID1/10 | RAID1 only |
| Defragmentation | Supported | Limited |

## Recovery Limitations

### Fsck Maturity

The `bcachefs fsck` tool is less mature than ext4's `e2fsck` or ZFS's `zpool scrub`:

```bash
# May not recover all corruption scenarios
bcachefs fsck -y /dev/sdb
```

### Data Recovery Tools

Third-party recovery tools (TestDisk, PhotoRec) have limited bcachefs support.

### Forensics

Forensic tools and documentation for bcachefs are minimal.

## Performance Considerations

### Write Amplification

Copy-on-write can cause write amplification with certain workloads:

- Random small writes
- Database workloads
- Journaling applications on top of bcachefs

### Fragmentation

Over time, bcachefs can become fragmented:

- No mature defragmentation tool yet
- Rebalancing helps but has limits
- May need to copy data off and back for severe fragmentation

## When NOT to Use Bcachefs

| Scenario | Recommendation |
|----------|----------------|
| Production server | Use ZFS or ext4 |
| Root filesystem | Use ext4 or XFS |
| Database storage | Use XFS or ZFS |
| Critical data (only copy) | Use ZFS with replication |
| NAS appliance | Use ZFS |
| Enterprise deployment | Wait for maturity |

## Safe Use Cases

| Scenario | Notes |
|----------|-------|
| Secondary data with backups | Safe to experiment |
| Development/testing | Good for learning |
| Media storage (with backup) | Compression useful |
| Non-critical archives | Checksums valuable |

## Monitoring for Problems

Watch for issues:

```bash
# Check kernel logs
dmesg | grep -i bcachefs

# Monitor filesystem status
bcachefs fs usage /mnt/data

# Run periodic scrubs
bcachefs data scrub /mnt/data
```

Set up alerts for:

- Checksum errors
- Device failures
- Unusual space consumption
- Kernel warnings
