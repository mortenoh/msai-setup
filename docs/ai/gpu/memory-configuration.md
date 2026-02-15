# Memory Configuration

Optimizing memory allocation for AMD APU AI workloads on the MS-S1 MAX.

## APU Shared Memory Architecture

Unlike discrete GPUs with dedicated VRAM, the AMD Ryzen AI Max+ 395 APU shares system memory between CPU and GPU:

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
│   │     DDR5 System Memory (128GB)        │   │
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

For persistent VRAM allocation without `amd-debug-tools`, you can set kernel parameters via GRUB. This uses the `amdttm.pages_limit` and `amdttm.page_pool_size` parameters.

### Calculation

Convert the desired GB allocation to the kernel parameter value:

```
pages = (GB * 1024 * 1024) / 4.096
```

For 108GB:

```
pages = (108 * 1024 * 1024) / 4.096 = 27,648,000
```

### GRUB Configuration

```bash
# Edit GRUB defaults
sudo nano /etc/default/grub

# Add to GRUB_CMDLINE_LINUX_DEFAULT:
# amdttm.pages_limit=27648000 amdttm.page_pool_size=27648000
```

```bash
sudo update-grub
sudo reboot
```

!!! note "Kernel 6.16.9+"
    Kernel versions 6.16.9 and later may handle GTT sizing automatically based on available memory, reducing the need for manual configuration.

## System Memory Considerations

### The 128GB Advantage

With 128GB DDR5, the MS-S1 MAX can run models that exceed typical discrete GPU memory:

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
| DDR5-4800 | ~77 GB/s (dual-channel) | Baseline |
| DDR5-5600 | ~90 GB/s (dual-channel) | +17% |
| DDR5-6400 | ~102 GB/s (dual-channel) | +32% |
| GDDR6X (RTX 4090) | ~1008 GB/s | ~11x faster |
| HBM3 (H100) | ~3350 GB/s | ~37x faster |

**Practical impact:**

| Model | DDR5-5600 APU | RTX 4090 |
|-------|---------------|----------|
| 7B Q4 | ~15-20 tok/s | ~100+ tok/s |
| 70B Q4 | ~2-4 tok/s | N/A (won't fit) |
| 70B Q2 | ~4-6 tok/s | N/A |

The APU is slower per token but can run larger models that don't fit in discrete GPUs.

### Optimizing Bandwidth

**Enable XMP/DOCP:**

Memory runs at JEDEC default (4800 MHz) without XMP. Enable in BIOS for rated speed.

```bash
# Check current memory speed
sudo dmidecode -t memory | grep -E "Speed:|Configured Memory Speed:"
```

**Verify dual-channel:**

```bash
# Both channels should be populated
sudo dmidecode -t memory | grep -E "Locator:|Size:"
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
