# Hardware

## Minisforum MS-S1 MAX

The MS-S1 MAX is a compact mini-PC suitable for a home server with virtualization capabilities and local AI inference.

Authoritative spec sheet: [minisforum.com/products/ms-s1-max](https://www.minisforum.com/products/ms-s1-max).

## Why This Hardware

The choice of an APU (Accelerated Processing Unit) over a discrete GPU setup is deliberate:

**Memory capacity over bandwidth**: Discrete GPUs like the RTX 4090 offer ~1 TB/s bandwidth but are limited to 24GB VRAM. For LLMs, model size matters more than raw speed - a 70B parameter model simply won't fit in 24GB regardless of bandwidth.

**Simplicity**: No PCIe passthrough complexity, no separate power requirements, no thermal challenges from a 300W+ GPU in a compact enclosure.

**Power efficiency**: The platform peaks at ~160W and sustains around ~130W at the wall (320W PSU), versus 300-450W just for a high-end discrete GPU. For a 24/7 home server, this translates to meaningful electricity savings.

**Cost effectiveness**: A single unified system versus coordinating a CPU, motherboard, and expensive discrete GPU.

## The Strix Halo Advantage

The AMD Ryzen AI Max+ 395 (Strix Halo) represents AMD's most capable APU to date:

- **Zen 5 architecture**: Latest CPU cores with improved IPC
- **RDNA 3.5 graphics**: 40 compute units, same architecture family as discrete RX 7000 series
- **Quad-channel LPDDR5X-8000**: 256-bit memory bus delivers ~256 GB/s peak, ~3x a typical desktop DDR5 board
- **Unified memory controller**: Both CPU and GPU access the same memory pool
- **AI accelerator**: Dedicated XDNA 2 NPU (though less relevant for LLM inference)

This APU is essentially a workstation-class part in a mini-PC form factor — the same silicon in high-end mobile workstations, with maximum memory and thermal headroom.

For detailed architecture information, see [Hardware Architecture](hardware-architecture.md).

### Specifications

| Component | Specification |
|-----------|---------------|
| CPU | AMD Ryzen AI Max+ 395 (Strix Halo) |
| Cores/Threads | 16 cores / 32 threads (Zen 5) |
| GPU | AMD Radeon 8060S (RDNA 3.5, 40 CUs) |
| GPU ID | `gfx1151` |
| RAM | 128GB LPDDR5X-8000 MT/s, quad-channel, soldered (~256 GB/s peak) |
| Internal NVMe (slot 1) | 2 TB, PCIe 4.0 x4 |
| Secondary NVMe (slot 2) | 4 TB, PCIe 4.0 **x1** (slower; ~2 GB/s ceiling) |
| Networking | 2 x 10GbE (Realtek RTL8127) |
| Display | HDMI 2.1 FRL, single output (up to 8K@60 / 4K@120) |
| USB | Front: 1 x USB 3.2 Gen2, 2 x USB4 (40 Gbps), 2 x USB 2.0. Rear: 2 x USB4 V2 (80 Gbps), 1 x USB 3.2 Gen2 |
| Expansion | PCIe 4.0 x4 slot (full-length x16 connector) |
| Power | 320W external PSU; ~160W peak / 130W sustained at the wall |

!!! note "Asymmetric NVMe slots"
    The second M.2 slot is only PCIe 4.0 **x1**, capping it at ~2 GB/s vs the ~8 GB/s available on slot 1. This is fine for ZFS-backed media and cold data, but VM disks and hot databases should live on the primary 2 TB drive.

### APU for AI Workloads

The integrated RDNA 3.5 GPU shares system memory with the CPU, enabling:

- **Large model support**: 70B+ parameter models fit in 128GB RAM
- **No VRAM limitation**: Discrete GPUs typically max at 24GB
- **Simpler setup**: No PCIe passthrough configuration needed
- **Real memory bandwidth**: LPDDR5X-8000 quad-channel is in a different class than the dual-channel DDR5-5600 of typical desktop boards

## Trade-offs

The APU approach involves a clear trade-off:

| Aspect | MS-S1 MAX (APU) | Discrete GPU (RTX 4090) |
|--------|-----------------|-------------------------|
| Memory capacity | 128GB | 24GB |
| Memory bandwidth | ~256 GB/s (LPDDR5X-8000 quad-channel) | ~1 TB/s (GDDR6X) |
| Tokens/second | Moderate | Higher |
| Model size support | 70B+ at Q6/Q8, 405B at low quant | 70B requires CPU offloading |
| Power consumption | ~130W sustained system | 300-450W just for the GPU |
| Setup complexity | Simple | PCIe passthrough needed |

**The practical impact**: Expect ~6-9 tok/s on a 70B Q4 model, ~15-20 tok/s on a 32B Q4, and ~50-70 tok/s on an 8B Q4 with ROCm/HIP. Discrete GPUs are faster per token but can't run the larger models at all without CPU offloading (which is much slower than this box).

For bandwidth calculations and deeper technical analysis, see [Hardware Architecture](hardware-architecture.md).

See [BIOS Setup](bios-setup.md) for optimizing APU performance and [GPU Setup](../ai/gpu/index.md) for ROCm installation.

### Storage Layout

#### Internal NVMe (2 TB, PCIe 4.0 x4) — host OS + hot data

| Partition | Size | Filesystem | Mount |
|-----------|------|------------|-------|
| EFI | 512 MB | FAT32 | `/boot/efi` |
| Boot | 1 GB | ext4 | `/boot` |
| Root | 1 TB | ext4 | `/` |
| Free | ~1 TB | — | ZFS pool member |

#### Secondary NVMe (4 TB, PCIe 4.0 x1) — bulk ZFS data

Entire disk allocated as a second ZFS pool member. The x1 link is the bottleneck — use this drive for media, backups, model files, and other read-heavy or cold data; keep VM disks and hot databases on the primary drive.

### Why ext4 for Root?

- Extremely stable
- Excellent recovery tooling
- Zero operational surprises
- Root filesystem is infrastructure, not a feature

!!! note
    `/boot` lives on the same disk as `/` — not on ZFS, not on a separate drive.
