# Hardware

## Minisforum MS-S1 MAX

The MS-S1 MAX is a compact mini-PC suitable for a home server with virtualization capabilities and local AI inference.

## Why This Hardware

The choice of an APU (Accelerated Processing Unit) over a discrete GPU setup is deliberate:

**Memory capacity over bandwidth**: Discrete GPUs like the RTX 4090 offer ~1 TB/s bandwidth but are limited to 24GB VRAM. For LLMs, model size matters more than raw speed - a 70B parameter model simply won't fit in 24GB regardless of bandwidth.

**Simplicity**: No PCIe passthrough complexity, no separate power requirements, no thermal challenges from a 300W+ GPU in a compact enclosure.

**Power efficiency**: The APU runs at 55-120W TDP versus 300-450W for high-end discrete GPUs. For a 24/7 home server, this translates to meaningful electricity savings.

**Cost effectiveness**: A single unified system versus coordinating a CPU, motherboard, and expensive discrete GPU.

## The Strix Point Advantage

The AMD Ryzen AI Max+ 395 represents AMD's most capable APU to date:

- **Zen 5 architecture**: Latest CPU cores with improved IPC
- **RDNA 3.5 graphics**: 40 compute units, same architecture as discrete RX 7000 series
- **Unified memory controller**: Both CPU and GPU access the same DDR5 pool
- **AI accelerator**: Dedicated XDNA 2 NPU (though less relevant for LLM inference)

This APU is essentially a laptop chip pushed to desktop power limits - the same silicon in high-end gaming laptops, but configured with maximum memory and thermal headroom.

For detailed architecture information, see [Hardware Architecture](hardware-architecture.md).

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

## Trade-offs

The APU approach involves a clear trade-off:

| Aspect | MS-S1 MAX (APU) | Discrete GPU (RTX 4090) |
|--------|-----------------|-------------------------|
| Memory capacity | 128GB | 24GB |
| Memory bandwidth | ~90 GB/s | ~1 TB/s |
| Tokens/second | Lower | Higher |
| Model size support | 70B+ at Q6/Q8 | 70B requires offloading |
| Power consumption | 55-120W | 300-450W |
| Setup complexity | Simple | PCIe passthrough needed |

**The practical impact**: Expect 5-15 tokens/second for large models versus 30-60 on discrete GPUs. But you can run models that discrete GPU users cannot run at all without CPU offloading (which makes them even slower).

For bandwidth calculations and deeper technical analysis, see [Hardware Architecture](hardware-architecture.md).

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
