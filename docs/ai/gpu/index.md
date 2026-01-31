# GPU Setup

Configure AMD integrated graphics for AI workloads on the MS-S1 MAX.

## Overview

The AMD Ryzen AI Max+ 395 APU combines CPU and GPU on a single chip with access to system memory. Unlike discrete GPUs with dedicated VRAM, the integrated RDNA 3.5 graphics shares the 128GB DDR5 system RAM.

For a comprehensive explanation of the APU architecture, memory subsystem, and design trade-offs, see [Hardware Architecture](../../getting-started/hardware-architecture.md).

## Quick Reference

| Aspect | MS-S1 MAX APU |
|--------|---------------|
| Architecture | RDNA 3.5 |
| Compute Units | 40 CUs |
| GPU ID | gfx1151 |
| Memory | Shared 128GB DDR5 |
| Bandwidth | ~90 GB/s |
| ROCm Support | Experimental (requires HSA_OVERRIDE_GFX_VERSION) |

## Why APU for LLMs?

The MS-S1 MAX's 128GB configuration enables running large models that exceed typical discrete GPU VRAM:

- **70B models at high quantization** - Full Q6 or Q8 fits in memory
- **405B models at lower quantization** - Q2-Q3 within reach
- **No model offloading** - Entire model stays in accessible memory
- **Simple setup** - No PCIe passthrough needed

The tradeoff is lower memory bandwidth compared to discrete GPUs, resulting in slower tokens/second. However, the ability to run larger models often outweighs raw speed.

## Section Contents

### [ROCm Installation](rocm-installation.md)

Native ROCm installation for Ubuntu 24.04:

- APU compatibility and current support status
- Installation using amdgpu-install
- Environment variables for Strix Point
- Verification with rocminfo and rocm-smi

### [Driver Updates](driver-updates.md)

Keeping AMD drivers current:

- Checking installed versions
- Update procedures
- Handling conflicts
- Rollback if needed

### [Memory Configuration](memory-configuration.md)

Optimizing memory for AI workloads:

- UMA Frame Buffer Size settings
- Memory allocation strategies
- Bandwidth considerations
- Monitoring memory usage

## Related Documentation

- [BIOS Setup](../../getting-started/bios-setup.md) - Configure BIOS for optimal APU performance
- [Hardware](../../getting-started/hardware.md) - MS-S1 MAX specifications
- [GPU Containers](../containers/gpu-containers.md) - ROCm in Docker
- [Unified Memory](../fundamentals/unified-memory.md) - Memory concepts (Apple Silicon focused, but concepts apply)
