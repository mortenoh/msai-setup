# Bcachefs Concepts

## Terminology

| Term | Description |
|------|-------------|
| Filesystem | A bcachefs instance spanning one or more devices |
| Device | A block device (disk, partition, or loop device) in the filesystem |
| Subvolume | Independent namespace within a filesystem |
| Snapshot | Read-only point-in-time copy of a subvolume |
| Superblock | Metadata block describing the filesystem |

## Copy-on-Write Architecture

Like ZFS and Btrfs, bcachefs uses copy-on-write (COW):

1. New data is written to free space
2. Metadata pointers are updated atomically
3. Old blocks are freed (unless referenced by snapshots)

Benefits:

- Atomic updates prevent corruption
- Efficient snapshots
- Data integrity through checksums

## Comparison with ZFS

| Aspect | Bcachefs | ZFS |
|--------|----------|-----|
| License | GPL | CDDL |
| Kernel integration | External (DKMS) | External (DKMS/module) |
| Maturity | Experimental | Production-ready |
| Codebase size | ~117K lines | ~500K+ lines |
| Encryption | Built-in | Dataset-level |
| Compression | LZ4, gzip, zstd | LZ4, gzip, zstd, zle |
| RAID | Basic (RAID5/6 unstable) | Mature (RAIDZ1/2/3) |
| SSD caching | Native | L2ARC/SLOG |
| Community | Small | Large, established |

## Comparison with Btrfs

| Aspect | Bcachefs | Btrfs |
|--------|----------|-------|
| Kernel integration | External (DKMS) | In-kernel |
| Maturity | Experimental | Production (mostly) |
| RAID5/6 | Unstable | Unstable |
| Encryption | Built-in | None (use LUKS) |
| Scrubbing | Supported | Supported |
| Quotas | Planned | Supported |

## Device Roles

Bcachefs supports multiple device types in a single filesystem:

### Data Devices

Standard storage devices for filesystem data.

```bash
# Single device
bcachefs format /dev/sda

# Multiple devices (striped)
bcachefs format /dev/sda /dev/sdb
```

### Cache Devices

Fast devices (SSDs, NVMe) for caching hot data:

```bash
bcachefs format \
    --label=hdd.hdd1 /dev/sda \
    --label=ssd.ssd1 /dev/nvme0n1 \
    --foreground_target=ssd \
    --promote_target=ssd \
    --background_target=hdd
```

## Replication and Durability

### Data Replication

Control how many copies of data are stored:

```bash
# RAID1-style mirroring
bcachefs format --replicas=2 /dev/sda /dev/sdb
```

### Metadata Replication

Metadata can have different replication than data:

```bash
bcachefs format \
    --replicas=1 \
    --metadata_replicas=2 \
    /dev/sda /dev/sdb
```

## Checksumming

All data and metadata is checksummed by default:

| Algorithm | Description |
|-----------|-------------|
| crc32c | Fast, hardware-accelerated on modern CPUs |
| crc64 | Stronger than crc32c |
| xxhash | Very fast hash |
| none | Disable checksums (not recommended) |

Checksums enable:

- Detection of silent data corruption
- Automatic repair with replicated data
- Scrubbing to proactively find errors

## Allocator

Bcachefs uses a sophisticated allocator:

- **Buckets** - Fixed-size allocation units
- **Copygc** - Background garbage collection
- **Tiering** - Automatic data movement between device classes
