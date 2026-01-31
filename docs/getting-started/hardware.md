# Hardware

## Minisforum MS-S1 MAX

The MS-S1 MAX is a compact mini-PC suitable for a home server with virtualization capabilities and local AI inference.

### Specifications

| Component | Specification |
|-----------|---------------|
| CPU | AMD Ryzen AI Max+ 395 (Strix Point) |
| Cores/Threads | 16 cores / 32 threads (Zen 5) |
| GPU | AMD Radeon Graphics (RDNA 3.5, 40 CUs) |
| GPU ID | gfx1151 |
| RAM | 128GB DDR5-5600 (dual-channel) |
| Internal NVMe | 2 TB |
| Secondary NVMe | 4 TB |
| TDP | 55-120W configurable |
| Display | HDMI 2.1, DisplayPort 2.1, USB-C |

### APU for AI Workloads

The integrated RDNA 3.5 GPU shares system memory with the CPU, enabling:

- **Large model support**: 70B+ parameter models fit in 128GB RAM
- **No VRAM limitation**: Discrete GPUs typically max at 24GB
- **Simpler setup**: No PCIe passthrough configuration needed
- **Lower power**: ~65W vs 300W+ for high-end discrete GPUs

The tradeoff is lower memory bandwidth (~90 GB/s DDR5 vs ~1 TB/s GDDR6X), resulting in slower tokens/second but access to larger models.

See [BIOS Setup](bios-setup.md) for optimizing APU performance and [GPU Setup](../ai/gpu/index.md) for ROCm installation.

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
