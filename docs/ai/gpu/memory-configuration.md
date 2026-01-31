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

### Setting in BIOS

See [BIOS Setup](../../getting-started/bios-setup.md) for detailed instructions. The setting is typically found under:

- Advanced > Graphics Configuration > UMA Frame Buffer Size
- Or: Advanced > AMD CBS > NBIO > GFX Configuration

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
| UMA Frame Buffer | 8-16GB (from BIOS) |
| Available for models | 100-110GB |

**Example calculation for 128GB system:**

```
Total RAM:            128GB
- OS overhead:          4GB
- Services:             4GB
- UMA (if 16GB):       16GB
------------------------
Available for LLMs:   104GB
```

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
