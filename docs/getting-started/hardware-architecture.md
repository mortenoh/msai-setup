# Hardware Architecture

Deep dive into the AMD Strix Point APU architecture and why it's well-suited for local AI inference.

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

APU Architecture (Strix Point):
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
|         +--------------------------+             |
+--------------------------------------------------+
                       |
                       v
          +------------------------+
          |   DDR5-5600 (128GB)    |
          |   Dual-channel         |
          |   ~90 GB/s bandwidth   |
          +------------------------+
```

## Strix Point Architecture

The Ryzen AI Max+ 395 is built on the Strix Point platform:

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
| ROCm Support | Experimental (requires HSA_OVERRIDE_GFX_VERSION) |
| Ray Accelerators | 40 |

### Memory Subsystem

| Specification | Detail |
|---------------|--------|
| Type | DDR5-5600 |
| Channels | Dual-channel |
| Maximum Capacity | 128GB (2x64GB) |
| Theoretical Bandwidth | 89.6 GB/s |
| Practical Bandwidth | ~70-80 GB/s |

## Bandwidth Analysis

Memory bandwidth directly affects LLM inference speed. Each token requires reading the entire model from memory:

```
Token generation rate = Memory Bandwidth / Model Size

Example with 70B Q4 model (~35GB):
- DDR5-5600: 80 GB/s / 35GB = ~2.3 reads/sec = ~2.3 tokens/sec (theoretical)
- Actual: 8-15 tokens/sec (parallelism, caching, batching help)

Example with 70B Q8 model (~70GB):
- DDR5-5600: 80 GB/s / 70GB = ~1.1 reads/sec base
- Actual: 5-10 tokens/sec
```

### Bandwidth Comparison

| Memory Type | Theoretical | Practical | Use Case |
|-------------|-------------|-----------|----------|
| DDR5-5600 (MS-S1 MAX) | 89.6 GB/s | ~75 GB/s | Large models, slow inference |
| GDDR6X (RTX 4090) | 1008 GB/s | ~900 GB/s | Small models, fast inference |
| HBM3 (H100) | 3350 GB/s | ~3000 GB/s | Enterprise inference |
| Unified (M4 Max) | 546 GB/s | ~400 GB/s | Balanced approach |

The MS-S1 MAX trades speed for capacity. A 70B model at Q6 (52GB) runs entirely in memory - impossible on a 24GB discrete GPU without CPU offloading (which creates its own bandwidth bottleneck over PCIe at ~32 GB/s).

## Platform Comparison

| Aspect | MS-S1 MAX | Mac Studio M4 Max | GPU Workstation |
|--------|-----------|-------------------|-----------------|
| Memory | 128GB DDR5 | 128GB Unified | 64GB + 24GB VRAM |
| GPU Memory | Shared 128GB | Shared 128GB | 24GB dedicated |
| Memory Bandwidth | ~90 GB/s | ~546 GB/s | ~90 + 1000 GB/s |
| Max Model (Q4) | 200B+ | 200B+ | 45B (GPU only) |
| Max Model (Q8) | 100B+ | 100B+ | 22B (GPU only) |
| Power Draw | 55-120W | 40-120W | 200-600W |
| OS | Linux (ROCm) | macOS (Metal) | Linux (CUDA) |
| Price (2024) | ~$2000 | ~$4000 | ~$5000+ |

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

The trade-off is bandwidth - DDR5 is slower than GDDR6X. But for large models, having the model fit entirely in GPU-accessible memory is more important than raw bandwidth.

## Thermal Considerations

The MS-S1 MAX manages thermals through:

- **Active cooling**: Dual-fan system with vapor chamber
- **TDP configuration**: BIOS-adjustable from 55W to 120W
- **Throttling behavior**: CPU/GPU reduce clocks under thermal pressure

For sustained AI workloads:

- Ambient temperature matters significantly
- 55W TDP provides stable, quiet operation
- 120W TDP for maximum performance with higher noise
- GPU-heavy workloads (inference) stress cooling more than CPU-heavy

## Practical Implications

### What Works Well

- **70B models at Q4-Q6**: Core use case, fits comfortably
- **405B models at Q2-Q3**: Fits in memory, slow but functional
- **Multiple smaller models**: Can keep several 7B-13B models loaded
- **Long context**: Memory capacity allows large context windows

### Limitations

- **Speed**: Expect 5-15 tokens/sec for 70B models
- **ROCm support**: Strix Point requires environment variable overrides
- **No tensor cores**: RDNA 3.5 lacks dedicated AI accelerators
- **Single GPU**: Cannot scale with additional GPUs

## Related Documentation

- [Hardware](hardware.md) - System specifications
- [BIOS Setup](bios-setup.md) - Optimizing BIOS settings for AI workloads
- [GPU Setup](../ai/gpu/index.md) - ROCm installation and configuration
- [Memory Configuration](../ai/gpu/memory-configuration.md) - UMA frame buffer settings
