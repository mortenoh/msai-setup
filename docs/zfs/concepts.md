# ZFS Concepts

## Terminology

| Term | Description |
|------|-------------|
| Pool | Collection of storage devices (vdevs) |
| vdev | Virtual device (single disk, mirror, raidz) |
| Dataset | Filesystem or volume within a pool |
| Snapshot | Read-only point-in-time copy |
| Clone | Writable copy of a snapshot |

## Pool Topologies

### Single Disk (No Redundancy)

```
tank
└── disk1
```

- Maximum usable space
- No protection against disk failure
- Suitable when using snapshots + backups

### Mirror

```
tank
└── mirror-0
    ├── disk1
    └── disk2
```

- 50% usable space
- Survives single disk failure

### RAIDZ1

```
tank
└── raidz1-0
    ├── disk1
    ├── disk2
    └── disk3
```

- ~67% usable space (with 3 disks)
- Survives single disk failure

## Key Properties

### Compression

```bash
zfs set compression=lz4 tank
```

- `lz4` - Fast, good compression (recommended)
- `zstd` - Better compression, more CPU
- `off` - No compression

### Record Size

```bash
zfs set recordsize=1M tank/media
zfs set recordsize=16K tank/db
```

- Large files (media): 1M
- Databases: 16K-128K
- General use: 128K (default)

### Quota

```bash
zfs set quota=500G tank/nextcloud-data
```

Limits maximum space a dataset can consume.

### Reservation

```bash
zfs set reservation=100G tank/db
```

Guarantees minimum space for a dataset.

## Copy-on-Write

ZFS never overwrites data in place:

1. New data written to free blocks
2. Metadata updated to point to new blocks
3. Old blocks freed (unless referenced by snapshot)

This enables:

- Atomic updates
- Consistent snapshots
- Self-healing with checksums
