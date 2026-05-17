# Unified Memory for LLMs

The MS-S1 MAX's killer feature for local LLMs is **unified memory** — CPU and integrated GPU share a single 128 GB pool of LPDDR5X-8000 on a 256-bit (quad-channel) bus. Models that would never fit in 24 GB of discrete VRAM run in this box's RAM with room to spare.

## Understanding Unified Memory

Unlike a desktop with a discrete GPU and PCIe-attached VRAM, the Strix Halo APU has a single memory controller serving both CPU cores and the iGPU directly:

```
Traditional Discrete-GPU Architecture:
+-------------+     PCIe x16     +------------------+
|    CPU      |<--------------->|    GPU           |
| (64-128GB)  |    ~32 GB/s     | (24GB VRAM)      |
+------+------+                 +--------+---------+
       |                                 |
       v                                 v
   System RAM                       GPU VRAM
   (Unused by GPU)                 (Model lives here)

MS-S1 MAX Unified Memory (Strix Halo):
+--------------------------------------------------+
|              AMD Ryzen AI Max+ 395               |
|  +-------------+         +-------------------+   |
|  |   Zen 5     |<------->|    RDNA 3.5       |   |
|  |   CPU       |  Fabric |    iGPU (gfx1151) |   |
|  +------+------+         +---------+---------+   |
|         |                          |             |
|         +------------+-------------+             |
|                      |                           |
|         +------------v-------------+             |
|         |  Memory Controller       |             |
|         |  256-bit bus             |             |
|         +------------+-------------+             |
+----------------------|---------------------------+
                       v
       +-------------------------------+
       |  128GB LPDDR5X-8000           |
       |  Quad-channel, soldered       |
       |  ~256 GB/s peak               |
       +-------------------------------+
```

## Why This Matters for LLMs

Token generation is memory-bandwidth bound. Each generated token requires reading the entire model from memory once. Two things determine speed:

1. **How big a model fits** (capacity)
2. **How fast the GPU can sweep through it per token** (bandwidth)

The MS-S1 MAX wins decisively on (1) and is competitive on (2) against everything except a top-tier discrete GPU.

### Capacity

| Platform | Memory available to model |
|---|---|
| RTX 4090 (consumer) | 24 GB VRAM |
| RTX 6000 Ada / A6000 (pro) | 48 GB VRAM |
| H100 80GB (datacenter) | 80 GB VRAM |
| **MS-S1 MAX (Strix Halo)** | **~108 GB usable, out of 128 GB unified** |
| Apple M4 Max 128GB | ~96 GB usable |
| Apple M2/M3 Ultra 192GB | ~144 GB usable |

### Bandwidth

| Platform | Peak bandwidth | Real-world |
|---|---|---|
| Desktop DDR5-5600 dual-channel | ~90 GB/s | ~75 GB/s |
| **MS-S1 MAX (LPDDR5X-8000 quad-channel)** | **~256 GB/s** | **~210-220 GB/s** |
| Apple M4 Max unified | ~546 GB/s | ~400 GB/s |
| RTX 4090 (GDDR6X) | ~1008 GB/s | ~900 GB/s |

The MS-S1 MAX has roughly 3x the bandwidth of a typical desktop board and half the bandwidth of an M4 Max — but with a far cheaper entry price.

## How Linux + ROCm Split the Pool

On Linux, the unified pool is **logically partitioned** into two regions the GPU can use:

- **VRAM (UMA frame buffer)** — fixed reservation set in BIOS. ROCm sees this as VRAM in `rocm-smi`. **Keep this small** on Strix Halo (512 MB - 2 GB).
- **GTT (Graphics Translation Table)** — dynamically allocated GPU-accessible system memory. This is where large model weights actually live. Sized via `amd-ttm` or the `ttm.*` kernel parameters.

```
Total RAM (128 GB)
  +-- UMA VRAM (512 MB - 2 GB, BIOS-reserved)
  +-- GTT (configurable; recommended 108 GB for big models)
  +-- Host OS, services, VMs (whatever's left)
```

See [Memory Configuration](../gpu/memory-configuration.md) for the exact `amd-ttm` / `ttm` commands and the BIOS setting. Short version:

```bash
pipx install amd-debug-tools
amd-ttm --set 108        # allocate 108 GB to GTT, leaving ~20 GB for OS
sudo reboot
```

After reboot, `rocm-smi --showmeminfo vram` reports the GTT size as VRAM, and llama.cpp / Ollama can fully GPU-offload models up to ~100 GB.

## The 80/20 Rule

Reserve ~20-25 GB for the OS, ARC ([ZFS ARC capped at 16 GiB](../../zfs/pool-creation.md#cap-the-arc-size)), Docker, and Linux VMs. The rest is yours:

| Available for models | Comfortable model sizes |
|---|---|
| ~96 GB | 70B at Q8, 70B at Q6 with long context, 405B at IQ1/IQ2 (tight) |
| ~108 GB | 70B at Q8 with long context, 405B at IQ2_XXS (tight), MoE 200B-class |

## Memory Calculation

Rough VRAM requirement for a dense model:

```
Weights (GB) ~ Parameters (B) x Bits / 8

  8B Q4:   8 x 4 / 8 =  4 GB base
 32B Q4:  32 x 4 / 8 = 16 GB base
 70B Q4:  70 x 4 / 8 = 35 GB base
 70B Q6:  70 x 6 / 8 = 53 GB base
 70B Q8:  70 x 8 / 8 = 70 GB base
405B Q2: 405 x 2 / 8 = 101 GB base (IQ2/IQ1 quants are slightly smaller)
```

Add **20-40% on top** for:

- KV cache (linear in context length x layers x heads x head_dim)
- Activation memory during inference
- llama.cpp/Ollama internal buffers
- Pre-allocation headroom

A 70B Q4 with 16 k context typically lands at 40-50 GB total; a 70B Q6 at 32 k can reach 70+ GB.

## Monitoring on Linux

### From the GPU side

```bash
# Snapshot
rocm-smi
rocm-smi --showmeminfo vram

# What's actively using the GPU
rocm-smi --showpidgpumem

# Continuous
watch -n 1 rocm-smi --showmeminfo vram
```

### From the system side

```bash
# Overall
free -h

# Detailed
cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|Buffers|Cached'

# Per-process
top                # or htop, btop
```

### From the inference engine

```bash
# Ollama: shows loaded models and their memory footprint
ollama ps

# llama.cpp server reports memory at startup; check the log
journalctl -u llama-server -f      # if running under systemd
```

### Signs of memory pressure

| Symptom | Likely cause | Fix |
|---|---|---|
| `oom-killer` log entries | OS undersized | Reduce GTT (`amd-ttm --set 96`) or trim ZFS ARC further |
| Generation crawls (1-2 tok/s on a 70B) | Spilling to system memory beyond GTT | Pick a smaller quant or lower context |
| Model refuses to load | KV cache + weights exceed GTT | Lower `-c` (context size) or use a smaller quant |
| Swap activity during inference | OS reservation too tight | Increase OS reservation, decrease GTT |

## Context Length Trade-offs

KV cache scales roughly linearly with context. Approximate cost per token of context for a few dense Llama-family models (FP16 KV; lower with KV quant):

| Model | KV per 1 k context | KV at 32 k | KV at 128 k |
|---|---|---|---|
| 8B | ~50 MB | ~1.6 GB | ~6.4 GB |
| 32B | ~150 MB | ~4.8 GB | ~19 GB |
| 70B | ~300 MB | ~9.6 GB | ~38 GB |

Quantized KV (`-fa -ctk q8_0 -ctv q8_0` in llama.cpp) roughly halves these numbers at modest quality cost. Useful when you're trying to keep a 70B Q6 + 32 k context inside ~96 GB.

## Multi-Model Strategies

You can comfortably keep multiple smaller models resident:

```
70B Q4 (chat) ........ ~40 GB
32B Q4 (coding) ...... ~16 GB
8B Q8 (small/fast) ... ~10 GB
                       ------
Total .................. 66 GB  (fits in GTT with plenty of room)
```

Ollama keeps the most recently used model loaded and evicts the LRU when you switch. For more predictable behaviour, run llama-server instances on different ports and route via a reverse proxy.

## When This Box Is Not the Right Tool

- **Latency-critical small models** — an RTX 4090 will do 8B Q4 at 100+ tok/s vs ~60 here. If you only ever run small models, a discrete GPU wins.
- **Training / fine-tuning at scale** — RDNA 3.5 has no tensor cores. LoRA on small models is fine; full fine-tunes of 70B+ are not.
- **High-throughput multi-user serving** — vLLM-on-ROCm doesn't currently support `gfx1151`. For batched/concurrent serving, llama-server's `--parallel N` works but you're sharing the same bandwidth budget.

For everything else — running one or two big local models for personal use, with full context, on a power-efficient always-on box — this is what unified memory was built for.

## See Also

- [Memory Configuration](../gpu/memory-configuration.md) - GTT sizing, `amd-ttm`, BIOS UMA
- [Hardware Architecture](../../getting-started/hardware-architecture.md) - SoC and bandwidth deep dive
- [Architecture Decisions](architecture-decisions.md) - Native vs container vs VM deployment
- [Performance / Memory Management](../performance/memory-management.md) - Runtime tuning
- [Quantization](../models/quantization.md) - Size/quality trade-offs
