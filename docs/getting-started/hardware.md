# Hardware

## Minisforum MS-S1 MAX

The MS-S1 MAX is a compact mini-PC suitable for a home server with virtualization capabilities.

### Specifications

| Component | Specification |
|-----------|---------------|
| CPU | AMD Ryzen (integrated graphics) |
| Internal NVMe | 2 TB |
| Secondary NVMe | 4 TB |
| GPU | Integrated AMD (for passthrough) |
| Display | HDMI output to Samsung TV |

### Storage Layout

#### Internal NVMe (2 TB)

| Partition | Size | Filesystem | Mount |
|-----------|------|------------|-------|
| EFI | 512 MB | FAT32 | `/boot/efi` |
| Boot | 1 GB | ext4 | `/boot` |
| Root | 1 TB | ext4 | `/` |
| Free | ~1 TB | — | ZFS pool |

#### Secondary NVMe (4 TB)

Entire disk allocated to ZFS pool.

### Why ext4 for Root?

- Extremely stable
- Excellent recovery tooling
- Zero operational surprises
- Root filesystem is infrastructure, not a feature

!!! note
    `/boot` lives on the same disk as `/` — not on ZFS, not on a separate drive.
