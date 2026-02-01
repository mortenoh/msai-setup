# Bcachefs Features

## Compression

Bcachefs supports transparent compression of data at rest.

### Enabling Compression

```bash
# At format time
bcachefs format --compression=zstd /dev/sdb

# As mount option
mount -t bcachefs -o compression=zstd /dev/sdb /mnt/data
```

### Compression Algorithms

| Algorithm | Speed | Ratio | Use Case |
|-----------|-------|-------|----------|
| `lz4` | Very fast | Lower | General use, SSDs |
| `gzip` | Slow | Good | Archival |
| `zstd` | Fast | Better | Recommended default |
| `none` | N/A | None | Already compressed data |

### Background Compression

Set compression on an existing filesystem:

```bash
# Files written after this will be compressed
mount -o remount,compression=zstd /mnt/data
```

To compress existing data, copy files or use rebalance.

## Encryption

Bcachefs provides whole-filesystem encryption using ChaCha20/Poly1305.

### Creating an Encrypted Filesystem

```bash
# Interactive passphrase
bcachefs format --encrypted /dev/sdb

# With keyfile
bcachefs format --encrypted /dev/sdb
bcachefs unlock /dev/sdb < /path/to/keyfile
```

### Unlocking for Mount

```bash
# Interactive unlock
bcachefs unlock /dev/sdb
mount -t bcachefs /dev/sdb /mnt/data

# With keyfile
bcachefs unlock /dev/sdb < /path/to/keyfile
mount -t bcachefs /dev/sdb /mnt/data
```

### Key Management

```bash
# Add a new passphrase
bcachefs set-passphrase /dev/sdb

# Remove passphrase (must have another key)
bcachefs remove-passphrase /dev/sdb
```

### Encryption vs LUKS

| Aspect | Bcachefs Encryption | LUKS + Filesystem |
|--------|---------------------|-------------------|
| Setup | Single step | Two layers |
| Performance | Native integration | Extra layer |
| Key management | Built-in | dm-crypt |
| Compatibility | Bcachefs only | Any filesystem |

## SSD Caching

Use fast devices to cache frequently accessed data from slower devices.

### Tiered Storage Setup

```bash
bcachefs format \
    --label=hdd.hdd1 /dev/sda \
    --label=hdd.hdd2 /dev/sdb \
    --label=ssd.ssd1 /dev/nvme0n1p1 \
    --foreground_target=ssd \
    --promote_target=ssd \
    --background_target=hdd
```

Parameters:

| Parameter | Description |
|-----------|-------------|
| `foreground_target` | Where new writes initially go |
| `promote_target` | Where hot data is promoted to |
| `background_target` | Where cold data is demoted to |

### Cache Behavior

- New writes go to SSD (foreground)
- Frequently read data promoted to SSD
- Cold data migrated to HDD in background
- Transparent to applications

## Checksumming

All data and metadata is checksummed to detect corruption.

### Checksum Algorithms

```bash
# At format time
bcachefs format --data_checksum=crc32c --metadata_checksum=crc64 /dev/sdb
```

| Algorithm | Speed | Strength |
|-----------|-------|----------|
| `crc32c` | Fastest | Basic |
| `crc64` | Fast | Better |
| `xxhash` | Very fast | Good |
| `none` | N/A | No protection |

### Scrubbing

Verify all checksums and detect corruption:

```bash
bcachefs data scrub /mnt/data
```

With replication, corrupted data is automatically repaired from good copies.

## Snapshots and Subvolumes

### Subvolumes

Independent filesystem namespaces within a single bcachefs filesystem:

```bash
# Create subvolumes for different purposes
bcachefs subvolume create /mnt/data/documents
bcachefs subvolume create /mnt/data/photos
bcachefs subvolume create /mnt/data/backups
```

Benefits:

- Independent snapshot policies
- Can be mounted separately
- Logical organization

### Snapshots

Point-in-time copies sharing data blocks with the source:

```bash
# Create snapshot
bcachefs subvolume snapshot /mnt/data/documents /mnt/data/snapshots/documents-$(date +%Y%m%d)

# Read-only snapshot
bcachefs subvolume snapshot -r /mnt/data/documents /mnt/data/snapshots/documents-readonly
```

Snapshots are space-efficient - only changes consume additional space.

## Quotas (Planned)

Quota support is planned but not yet fully implemented. Track progress in the bcachefs development roadmap.

## Replication

### Data Replication

```bash
# Store 2 copies of all data
bcachefs format --replicas=2 /dev/sdb /dev/sdc
```

### Metadata Replication

Metadata can have higher replication than data:

```bash
bcachefs format \
    --replicas=1 \
    --metadata_replicas=2 \
    /dev/sdb /dev/sdc
```

### Degraded Mode

Mount with missing devices:

```bash
mount -t bcachefs -o degraded /dev/sdb /mnt/data
```

!!! warning
    Running degraded risks data loss if another device fails.

## Performance Tuning

### Discard/TRIM

Enable discard for SSDs:

```bash
mount -t bcachefs -o discard /dev/nvme0n1p1 /mnt/data
```

### Noatime

Reduce write overhead by not updating access times:

```bash
mount -t bcachefs -o noatime /dev/sdb /mnt/data
```

### Journal Location

Place journal on fast storage:

```bash
# Separate journal device (advanced)
bcachefs format --journal_dev=/dev/nvme0n1p2 /dev/sdb
```
