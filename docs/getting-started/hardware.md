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
| RAM | 128GB LPDDR5X-8000 MT/s, quad-channel, soldered (~256 GB/s peak). ~121 GiB visible to the OS (`MemTotal`) with stock BIOS; the balance is the default UMA/VRAM carveout reserved for the iGPU, adjustable in BIOS (relevant for LLM work — see [GPU Memory Configuration](../ai/gpu/memory-configuration.md)). |
| ECC Memory | No |
| Internal NVMe (slot 1) | 4 TB Kingston KC3000 (`SKC3000D4096G`), PCIe 4.0 x4 (M.2 2280 slot supports up to 8 TB) |
| Secondary NVMe (slot 2) | 2 TB Crucial P310 (`CT2000P310SSD8`, DRAM-less), PCIe 4.0 **x1** (M.2 2280 slot supports up to 8 TB) |
| Networking | 2 x 10GbE (Realtek RTL8127) |
| Wireless | MediaTek MT7925 (Wi-Fi + Bluetooth combo) |
| Display | HDMI 2.1 FRL (up to 8K@60 / 4K@120) plus DisplayPort Alt Mode over all 4 USB4/USB4 V2 ports (same resolution ceiling) — up to 5 physical outputs, though this build runs headless over SSH |
| USB | Front: 1 x USB 3.2 Gen2, 2 x USB4 (40 Gbps), 2 x USB 2.0. Rear: 2 x USB4 V2 (80 Gbps), 1 x USB 3.2 Gen2 |
| Expansion | PCIe 4.0 x4 slot (full-length x16 connector) |
| Power | 320W external PSU (100-240V AC); ~160W peak / 130W sustained at the wall |
| BIOS Reset | Physical reset hole on the rear I/O (CMOS clear) — see [BIOS Setup](bios-setup.md#recovering-from-a-bad-bios-state) |

!!! note "Asymmetric NVMe slots — the 4 TB drive gets the fast slot"
    The second M.2 slot is only PCIe 4.0 **x1**, capping it at ~2 GB/s vs the ~8 GB/s available on slot 1. This build puts the **4 TB drive in slot 1** (fast) — ext4 root plus the `hot` pool (Incus storage, databases, model files) — and the **2 TB drive in slot 2** (slow) as `tank` — media, backups, cold data. Two independent pools, not one spanning both drives — see [Disk Partitioning](../ubuntu/installation/disk-partitioning.md).

!!! warning "Kernel `nvmeN` numbering does not match the physical slot"
    Linux enumerates NVMe devices by PCIe bus address, not by the slot label, and the ordering here is **reversed** from what you would expect: the fast 4 TB Kingston KC3000 (x4) comes up as `nvme1` (`65:00.0`) and the slow 2 TB Crucial P310 (x1) as `nvme0` (`64:00.0`). Physically swapping the drives between slots does **not** renumber them. Never assume `nvme0` is the primary/fast disk — a provisioning script that does will target the wrong drive. Always resolve the disk by model or by confirming link width before partitioning:

    ```bash
    # Confirm which device is the x4 (fast) drive before touching it
    for d in /sys/class/nvme/nvme*/device; do
      dev=$(basename "$(dirname "$d")")
      echo "$dev: $(cat /sys/class/nvme/$dev/model) width=x$(cat $d/current_link_width)"
    done
    ```

    Verified on this machine: `nvme1` = KINGSTON SKC3000D4096G width=x4 (fast), `nvme0` = CT2000P310SSD8 width=x1 (slow).

!!! info "Storage layout below is the target design, not the current state on every box"
    The `hot`/`tank` pool split describes the provisioned server. A fresh or experimental install (e.g. a plain Ubuntu desktop on this hardware) may have only an ext4 root on the 4 TB drive with the rest of both drives unpartitioned and no ZFS installed — in which case `msai doctor zfs` will correctly report the pools as absent until they are created.

!!! note "No ECC"
    This platform does not support ECC memory. That's not a reason to avoid ZFS here — see [ZFS Concepts -> "ZFS needs ECC RAM"](../zfs/concepts.md) for why that's mostly folklore — but it's worth knowing plainly rather than assuming it either way.

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

#### Internal NVMe (4 TB, PCIe 4.0 x4) — ext4 root + hot data (`hot`)

| Partition | Size | Filesystem | Mount |
|-----------|------|------------|-------|
| EFI | 512 MB | FAT32 | `/boot/efi` |
| Boot | 1 GB | ext4 | `/boot` |
| Root | 500 GB | ext4 | `/` |
| Pool member | ~3.4 TB | (ZFS) | `hot` |

The OS root, `/boot`, and `/home` are plain ext4; the leftover ~3.4 TB becomes the `hot` ZFS pool — Incus's storage backend, databases, and AI model files — everything stateful that benefits from the fast x4 link and ZFS snapshots.

#### Secondary NVMe (2 TB, PCIe 4.0 x1) — bulk cold data (`tank`)

Entire disk allocated as its own independent ZFS pool — not striped with `hot`. The x1 link is the bottleneck, so this drive holds media, backups, and other read-heavy or cold data that doesn't need the fast pool's bandwidth.

See [Disk Partitioning](../ubuntu/installation/disk-partitioning.md) for the full layout and creation commands.

### Why ext4 for Root?

- **Boring, well-understood recovery**: `e2fsck`, GRUB, and a stable separate `/boot` — no surprises on the critical boot path.
- **The host is disposable**: a broken OS is a quick reinstall; everything stateful lives on the ZFS pools with snapshots and off-host replication.
- **ZFS where it earns its keep**: containers, VMs, databases, and media get checksums, compression, and snapshots on `hot`/`tank`, without putting ZFS on the boot path.

Root-on-ZFS with ZFSBootMenu boot environments remains documented as an alternative if you want the OS layer snapshotted too — see [Disk Partitioning -> ZFS Root](../ubuntu/installation/disk-partitioning.md#zfs-root-documented-alternative) and the [ZFS Root (Alternative)](../ubuntu/installation/zfs-root-alternative.md) page.
