# Hardware Architecture

Deep dive into the AMD Strix Halo APU architecture and why it's well-suited for local AI inference.

Authoritative spec sheet for the Minisforum MS-S1 MAX: [minisforum.com/products/ms-s1-max](https://www.minisforum.com/products/ms-s1-max).

## APU Overview

An APU (Accelerated Processing Unit) combines CPU and GPU on a single die, sharing a unified memory pool. Unlike discrete GPU systems where the GPU has dedicated VRAM accessed over PCIe, the APU's integrated graphics directly accesses system RAM.

```
Traditional Discrete GPU Setup:
+-------------+     PCIe x16      +------------------+
|    CPU      |<----------------->|    GPU           |
|  (System)   |    ~32 GB/s       |  (Discrete)      |
+------+------+                   +--------+---------+
       |                                   |
       v                                   v
+-------------+                   +------------------+
| System RAM  |                   |   VRAM (GDDR6X)  |
|   64-128GB  |                   |     24GB max     |
|  ~90 GB/s   |                   |    ~1 TB/s       |
+-------------+                   +------------------+

APU Architecture (Strix Halo):
+--------------------------------------------------+
|           AMD Ryzen AI Max+ 395                  |
|  +-------------+          +------------------+   |
|  |   Zen 5     |          |    RDNA 3.5      |   |
|  |   CPU       |          |    GPU           |   |
|  |   16 cores  |          |    40 CUs        |   |
|  +------+------+          +--------+---------+   |
|         |    On-die Infinity Fabric    |         |
|         +------------+-------------+             |
|                      |                           |
|         +------------v-------------+             |
|         |   Memory Controller      |             |
|         |   256-bit bus            |             |
|         +--------------------------+             |
+--------------------------------------------------+
                       |
                       v
          +-------------------------------+
          |  LPDDR5X-8000 (128GB)         |
          |  Quad-channel, soldered       |
          |  ~256 GB/s peak bandwidth     |
          +-------------------------------+
```

## Strix Halo Architecture

The Ryzen AI Max+ 395 is built on the Strix Halo platform:

### CPU Complex

| Specification | Detail |
|---------------|--------|
| Architecture | Zen 5 |
| Cores | 16 |
| Threads | 32 |
| L2 Cache | 16MB (1MB/core) |
| L3 Cache | 64MB shared |
| Base Clock | 3.0 GHz |
| Boost Clock | Up to 5.1 GHz |

### GPU Complex

| Specification | Detail |
|---------------|--------|
| Architecture | RDNA 3.5 |
| Compute Units | 40 CUs |
| Stream Processors | 2560 |
| GPU ID | gfx1151 |
| ROCm Support | Supported (ROCm 7.x) |
| Ray Accelerators | 40 |

### Memory Subsystem

| Specification | Detail |
|---------------|--------|
| Type | LPDDR5X-8000 MT/s (soldered, on-package) |
| Bus width | 256-bit (quad-channel equivalent) |
| Maximum Capacity | 128GB (single configuration; not user-replaceable) |
| Theoretical Bandwidth | ~256 GB/s |
| Practical Bandwidth | ~210-220 GB/s (real-world LLM workloads) |

!!! note "Not a normal desktop board"
    Strix Halo's memory is soldered LPDDR5X-8000 on a 256-bit bus. There are no DIMM slots, no XMP/DOCP profile to enable, and no way to upgrade RAM later. The trade-off for that constraint is roughly 3x the bandwidth of a dual-channel desktop DDR5 board.

## Bandwidth Analysis

Memory bandwidth directly affects LLM inference speed. Each token requires reading the entire model from memory:

```
Token generation rate ~ Memory Bandwidth / Model Size

Example with 70B Q4 model (~40GB):
- LPDDR5X-8000 quad-channel: ~220 GB/s / 40GB ~ 5.5 reads/sec ceiling
- Real-world with ROCm/HIP: ~6-9 tokens/sec

Example with 32B Q4 model (~20GB):
- ~220 GB/s / 20GB ~ 11 reads/sec ceiling
- Real-world: ~15-20 tokens/sec

Example with 8B Q4 model (~5GB):
- ~220 GB/s / 5GB ~ 44 reads/sec ceiling
- Real-world: ~50-70 tokens/sec
```

### Bandwidth Comparison

| Memory Type | Theoretical | Practical | Use Case |
|-------------|-------------|-----------|----------|
| Desktop DDR5-5600 (dual-channel) | ~90 GB/s | ~75 GB/s | Reference; what most home boards run |
| LPDDR5X-8000 quad-channel (MS-S1 MAX) | ~256 GB/s | ~210-220 GB/s | Large models at usable speeds |
| Apple M4 Max unified | ~546 GB/s | ~400 GB/s | Faster but pricier and ARM/Metal |
| GDDR6X (RTX 4090) | 1008 GB/s | ~900 GB/s | Small models, fast inference |
| HBM3 (H100) | 3350 GB/s | ~3000 GB/s | Enterprise inference |

The MS-S1 MAX trades raw GPU bandwidth for capacity. A 70B model at Q6 (~52GB) runs entirely in memory — impossible on a 24GB discrete GPU without CPU offloading (which creates its own bandwidth bottleneck over PCIe at ~32 GB/s).

## Platform Comparison

| Aspect | MS-S1 MAX | Mac Studio M4 Max | GPU Workstation |
|--------|-----------|-------------------|-----------------|
| Memory | 128GB LPDDR5X-8000 | 128GB Unified | 64GB DDR5 + 24GB VRAM |
| GPU Memory | Shared 128GB | Shared 128GB | 24GB dedicated |
| Memory Bandwidth | ~256 GB/s | ~546 GB/s | ~90 GB/s system + ~1000 GB/s VRAM |
| Max Model (Q4) | 200B+ | 200B+ | 45B (GPU only) |
| Max Model (Q8) | 100B+ | 100B+ | 22B (GPU only) |
| System Power Draw | ~130W sustained | 40-120W | 400-700W |
| OS | Linux (ROCm) | macOS (Metal) | Linux (CUDA) |

## Unified Memory Explained

In a discrete GPU system, data must be copied between system RAM and VRAM:

1. Load model into system RAM
2. Copy relevant portions to VRAM (limited by VRAM size)
3. Run inference on GPU
4. Copy results back to system RAM

This creates the "VRAM wall" - models larger than VRAM must be split across CPU and GPU, with PCIe becoming the bottleneck.

With unified memory:

1. Load model into RAM
2. Both CPU and GPU access the same memory directly
3. No copying, no PCIe bottleneck
4. Entire 128GB available for models

The trade-off is bandwidth — LPDDR5X is slower than GDDR6X. But for large models, having the model fit entirely in GPU-accessible memory is more important than raw bandwidth.

## Thermal &amp; Power

The MS-S1 MAX uses a 320W external PSU and pulls roughly **160W peak / 130W sustained** at the wall under full load. Cooling and TDP behaviour:

- **Active cooling**: Dual-fan system with vapor chamber
- **Configurable platform power**: BIOS exposes power-limit knobs; sensible 24/7 settings stay well under the PSU's sustained budget
- **Throttling behaviour**: CPU/GPU reduce clocks under thermal pressure rather than violating power limits

For sustained AI workloads, ambient temperature matters and GPU-heavy inference stresses cooling more than CPU-heavy workloads.

## Practical Implications

### What Works Well

- **70B models at Q4-Q6**: Core use case, fits comfortably
- **405B models at Q2-Q3**: Fits in memory, slow but functional
- **Multiple smaller models**: Can keep several 7B-13B models loaded
- **Long context**: Memory capacity allows large context windows

### Limitations

- **Speed**: ~6-9 tok/s on 70B Q4, ~15-20 on 32B Q4, ~50-70 on 8B Q4 with ROCm/HIP
- **ROCm support**: Requires modern kernel (Ubuntu 26.04's 7.0 kernel is fine) and ROCm 7.x
- **No tensor cores**: RDNA 3.5 lacks dedicated matrix-multiply units like NVIDIA's tensor cores
- **Single GPU**: Cannot scale with additional GPUs

## Related Documentation

- [Hardware](hardware.md) - System specifications
- [BIOS Setup](bios-setup.md) - Optimizing BIOS settings for AI workloads
- [GPU Setup](../ai/gpu/index.md) - ROCm installation and configuration
- [Memory Configuration](../ai/gpu/memory-configuration.md) - UMA frame buffer settings
