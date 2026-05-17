# Memory Configuration

Optimizing memory allocation for AMD APU AI workloads on the MS-S1 MAX.

## APU Shared Memory Architecture

Unlike discrete GPUs with dedicated VRAM, the AMD Ryzen AI Max+ 395 (Strix Halo) APU shares system memory between CPU and GPU. On the MS-S1 MAX that pool is **128GB LPDDR5X-8000, soldered, on a 256-bit (quad-channel) bus** — roughly 3× the bandwidth of a typical desktop dual-channel DDR5 board.

```
Discrete GPU Memory Model:
┌─────────────────┐        ┌─────────────────┐
│      CPU        │  PCIe  │       GPU       │
│   (128GB RAM)   │◄──────►│   (24GB VRAM)   │
└─────────────────┘        └─────────────────┘
        │                          │
        ▼                          ▼
   System RAM                 GPU VRAM
   (Model won't fit)         (Model lives here)

APU Shared Memory Model:
┌───────────────────────────────────────────────┐
│           AMD Ryzen AI Max+ 395               │
│   ┌─────────────┐         ┌─────────────┐     │
│   │  CPU Cores  │◄───────►│   RDNA 3.5  │     │
│   └──────┬──────┘         └──────┬──────┘     │
│          │                       │            │
│          ▼                       ▼            │
│   ┌───────────────────────────────────────┐   │
│   │  LPDDR5X-8000 (128GB, quad-channel)   │   │
│   │   CPU and GPU share the same pool     │   │
│   └───────────────────────────────────────┘   │
└───────────────────────────────────────────────┘
```

## UMA Frame Buffer Size

### What It Controls

The UMA (Unified Memory Architecture) Frame Buffer Size setting in BIOS reserves a portion of system RAM as dedicated video memory. This memory is:

- **Always allocated** - Unavailable to the OS regardless of GPU usage
- **Used for display** - Framebuffer, video decode, 3D rendering
- **Visible to ROCm** - Appears as VRAM in `rocm-smi`

### Recommended Settings

| Use Case | UMA Setting | Rationale |
|----------|-------------|-----------|
| Headless server | 512MB - 2GB | Minimal display needs |
| Desktop with display | 4GB - 8GB | Comfortable for desktop compositing |
| AI/ML workloads | Auto or 16GB | Balance between GPU reservation and flexibility |
| Heavy GPU compute | 16GB - 32GB | More dedicated GPU memory pool |

!!! note "Auto Mode"
    The "Auto" setting allows dynamic allocation. For LLM inference with llama.cpp or Ollama, this typically works well as these tools manage memory directly rather than relying on the UMA pool.

!!! tip "amd-ttm is the Primary Method"
    The BIOS UMA setting reserves a fixed amount of memory (typically up to 32GB). For AI workloads requiring maximum GPU-accessible memory, use the software-based `amd-ttm` tool instead. See the [Software VRAM Allocation](#software-vram-allocation-amd-ttm) section below.

### Setting in BIOS

See [BIOS Setup](../../getting-started/bios-setup.md) for detailed instructions. The setting is typically found under:

- Advanced > Graphics Configuration > UMA Frame Buffer Size
- Or: Advanced > AMD CBS > NBIO > GFX Configuration

## Software VRAM Allocation (amd-ttm)

The `amd-ttm` tool from `amd-debug-tools` provides software-based control over how much system memory is accessible as GPU memory (GTT -- Graphics Translation Table). This is the primary method for maximizing GPU-accessible memory for LLM inference.

### Why amd-ttm?

| Method | Max GPU Memory | Persistence | Notes |
|--------|---------------|-------------|-------|
| BIOS UMA | ~32GB | Permanent | Fixed reservation, always unavailable to OS |
| amd-ttm | ~115GB | Survives reboot | Software-controlled, flexible |

The BIOS UMA setting and `amd-ttm` are complementary. UMA reserves a fixed pool visible as VRAM, while `amd-ttm` controls the GTT size that the GPU can use from system memory. For LLM inference, `amd-ttm` is far more impactful.

### Installation

```bash
pipx install amd-debug-tools
```

### Check Current Allocation

```bash
amd-ttm
# Shows current GTT allocation (default is ~62GB on 128GB systems)
```

### Set Allocation

```bash
# Allocate 108GB for GPU use (leaves ~20GB for OS and services)
amd-ttm --set 108
sudo reboot
```

After reboot, verify:

```bash
amd-ttm
# Should confirm ~108GB

rocm-smi --showmeminfo vram
```

!!! warning "High Allocation Values"
    Setting values above 90% of total RAM (e.g., 115GB on a 128GB system) triggers warnings from `amd-ttm` but does work. However, leaving too little for the OS can cause instability under heavy system load. 108GB is a safe default for a 128GB system.

### Recommended Values

| Total RAM | amd-ttm Value | OS Headroom | Use Case |
|-----------|--------------|-------------|----------|
| 128GB | 108GB | ~20GB | Large LLMs (70B Q6, 405B Q2) |
| 128GB | 96GB | ~32GB | Conservative, mixed workloads |
| 64GB | 48GB | ~16GB | Smaller models |

## Kernel Parameter Alternative

For persistent GTT sizing without `amd-debug-tools`, you can set kernel module parameters via GRUB. The module is `ttm` (the kernel's Translation Table Manager, shared by `amdgpu`/`radeon`); the parameters are `ttm.pages_limit` and `ttm.page_pool_size`.

### Calculation

A page on x86-64 is 4096 bytes. Convert GB to pages:

```
pages = (GB × 1024 × 1024 × 1024) / 4096
      = GB × 262144
```

For 108 GB:

```
pages = 108 × 262144 = 28,311,552
```

### GRUB Configuration

```bash
# Edit GRUB defaults
sudo nano /etc/default/grub

# Add to GRUB_CMDLINE_LINUX_DEFAULT:
# ttm.pages_limit=28311552 ttm.page_pool_size=28311552
```

```bash
sudo update-grub
sudo reboot
```

!!! note "Verify the module name on your kernel"
    Recent AMD trees occasionally ship downstream patches that rename or namespace the TTM parameters. If `ttm.pages_limit=…` is rejected at boot, check `modinfo ttm | grep parm` and `modinfo amdgpu | grep parm` for the actual parameter names on your running kernel.

!!! note "Newer kernels may auto-tune"
    Kernel versions 6.16.9 and later may handle GTT sizing automatically based on available memory, reducing the need for manual configuration. `amd-ttm --set` is still the most reliable way to pin a value.

## System Memory Considerations

### The 128GB Advantage

With 128GB LPDDR5X-8000 (quad-channel), the MS-S1 MAX can run models that exceed typical discrete GPU memory:

| Model Size | Quantization | Memory Required | Fits in 24GB GPU? |
|------------|--------------|-----------------|-------------------|
| 7B | Q8 | ~8GB | Yes |
| 13B | Q8 | ~14GB | Yes |
| 34B | Q4 | ~20GB | Yes |
| 70B | Q4 | ~40GB | No |
| 70B | Q6 | ~55GB | No |
| 405B | Q2 | ~100GB | No |

The APU can run 70B+ models that simply don't fit in consumer discrete GPUs.

### Memory Allocation Strategy

Reserve memory for different components:

| Component | Recommended Allocation |
|-----------|------------------------|
| Operating system | 4-8GB |
| System services | 2-4GB |
| GPU memory (via amd-ttm) | 108-115GB |
| Available for models | 108-115GB |

**Example calculation for 128GB system with amd-ttm:**

```
Total RAM:            128GB
amd-ttm allocation:  108GB  (GPU-accessible)
OS headroom:          ~20GB  (remaining for OS, services)
```

With `amd-ttm`, the GPU can access up to 108-115GB for model inference, significantly more than the 100-104GB available with BIOS UMA alone.

### Memory Pressure Monitoring

Monitor memory usage during inference:

```bash
# Overall memory status
free -h

# Detailed memory breakdown
cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|Buffers|Cached'

# Watch in real-time
watch -n 1 free -h
```

**GPU-specific monitoring:**

```bash
# ROCm memory info
rocm-smi --showmeminfo vram

# Memory used by GPU processes
rocm-smi --showpidgpumem

# Continuous monitoring
watch -n 1 'rocm-smi --showmeminfo vram'
```

## Memory Bandwidth Impact

### Why Bandwidth Matters

LLM token generation is memory-bandwidth bound. Each token requires reading the entire model from memory:

```
Tokens/second ≈ Memory Bandwidth / Model Size
```

### Bandwidth Comparison

| Memory Type | Bandwidth | Relative Speed |
|-------------|-----------|----------------|
| DDR5-5600 (typical desktop, dual-channel) | ~90 GB/s | Reference for comparison |
| DDR5-6400 (high-end desktop, dual-channel) | ~102 GB/s | +13% |
| LPDDR5X-8000 quad-channel (MS-S1 MAX) | ~256 GB/s peak, ~210-220 GB/s real | ~3× a dual-channel DDR5 board |
| Unified (Apple M4 Max) | ~546 GB/s | ~6× |
| GDDR6X (RTX 4090) | ~1008 GB/s | ~11× |
| HBM3 (H100) | ~3350 GB/s | ~37× |

**Practical impact (Strix Halo on ROCm/HIP):**

| Model | MS-S1 MAX (LPDDR5X-8000) | RTX 4090 |
|-------|--------------------------|----------|
| 8B Q4 | ~50-70 tok/s | ~100+ tok/s |
| 32B Q4 | ~15-20 tok/s | fits, faster |
| 70B Q4 | ~6-9 tok/s | doesn't fit |
| 70B Q6 | ~4-6 tok/s | doesn't fit |
| 405B IQ2/IQ1 | ~1-2 tok/s, fits at low quant | doesn't fit |

The APU is slower per token than a top-end discrete GPU, but it runs models that simply don't fit in 24GB VRAM at all.

### Verifying Memory Configuration

The MS-S1 MAX ships with soldered LPDDR5X — there is no XMP/DOCP to enable and no DIMM slots to populate. Just confirm the kernel sees the rated speed and 128 GB:

```bash
# Check reported memory speed (should be ~8000 MT/s)
sudo dmidecode -t memory | grep -E "Speed:|Configured Memory Speed:"

# Confirm total capacity and form factor
sudo dmidecode -t memory | grep -E "Size:|Locator:|Form Factor"
```

Single-channel halves available bandwidth.

## Comparison: APU vs Discrete GPU

| Aspect | APU (128GB DDR5) | Discrete GPU (24GB) |
|--------|------------------|---------------------|
| Max model size | 405B Q2 | 70B Q4 (offload) |
| 70B Q4 speed | ~3 tok/s | N/A |
| 7B Q8 speed | ~20 tok/s | ~100+ tok/s |
| Power consumption | ~65W TDP | ~300W+ |
| Cost | Included | $1000-2000 |
| Setup complexity | Simpler | PCIe slot, power |

**When to choose APU:**

- Running large models (70B+)
- Power efficiency matters
- No PCIe slots available
- Cost sensitive

**When to add discrete GPU:**

- Speed critical for small models
- Running many concurrent requests
- Training workloads

## Memory Management for LLMs

### llama.cpp Memory Control

```bash
# Specify GPU layers (more = more GPU memory)
llama-server -m model.gguf -ngl 99 -c 8192

# Context length affects memory
# -c 4096: Lower memory, shorter context
# -c 32768: Higher memory, longer context
```

### Ollama Memory Settings

```bash
# Check memory usage
ollama ps

# Unload models to free memory
ollama stop model-name

# Environment variables
export OLLAMA_MAX_LOADED_MODELS=1  # Limit concurrent models
```

### Monitoring During Inference

Create a monitoring script:

```bash
#!/bin/bash
# monitor-inference.sh

while true; do
    clear
    echo "=== System Memory ==="
    free -h

    echo ""
    echo "=== GPU Memory ==="
    rocm-smi --showmeminfo vram 2>/dev/null || echo "ROCm not available"

    echo ""
    echo "=== Top Memory Consumers ==="
    ps aux --sort=-%mem | head -6

    sleep 2
done
```

## Troubleshooting

### Out of Memory Errors

```bash
# Check what's using memory
ps aux --sort=-%mem | head -20

# Check for swap usage (bad for inference)
swapon --show
cat /proc/swaps

# Disable swap if needed
sudo swapoff -a
```

**Solutions:**

1. Use higher quantization (Q4 instead of Q8)
2. Reduce context length
3. Unload unused models
4. Close unnecessary applications

### GPU Memory Not Recognized

```bash
# Check ROCm sees memory
rocm-smi --showmeminfo vram

# If showing 0 or wrong value
# 1. Check UMA setting in BIOS
# 2. Verify amdgpu driver loaded
lsmod | grep amdgpu
```

### Slow Performance

If inference is slower than expected:

```bash
# Verify memory speed
sudo dmidecode -t memory | grep Speed

# Check for thermal throttling
sensors | grep -i temp
cat /sys/class/drm/card0/device/gpu_busy_percent
```

## See Also

- [BIOS Setup](../../getting-started/bios-setup.md) - Configure UMA and memory settings
- [ROCm Installation](rocm-installation.md) - GPU driver setup
- [Memory Management](../performance/memory-management.md) - General optimization
- [Unified Memory](../fundamentals/unified-memory.md) - Concepts (Apple Silicon focused)
