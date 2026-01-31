# Unified Memory for LLMs

Apple Silicon's unified memory architecture provides unique advantages for running large language models.

## Understanding Unified Memory

Unlike discrete GPUs with separate VRAM, Apple Silicon shares memory between CPU and GPU:

```
Traditional Architecture:
┌─────────────┐     PCIe      ┌─────────────┐
│    CPU      │◄────────────►│    GPU      │
│  (64GB RAM) │               │ (24GB VRAM) │
└─────────────┘               └─────────────┘
     │                              │
     ▼                              ▼
  System RAM                   GPU VRAM
  (Unused by GPU)             (Model lives here)

Apple Silicon Unified:
┌─────────────────────────────────────────┐
│            M-Series SoC                 │
│  ┌─────────┐         ┌─────────┐        │
│  │   CPU   │◄───────►│   GPU   │        │
│  └────┬────┘         └────┬────┘        │
│       │                   │             │
│       ▼                   ▼             │
│  ┌──────────────────────────────────┐   │
│  │      Unified Memory (128GB)      │   │
│  │      Shared by CPU + GPU         │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Memory Advantages

### High Capacity

| Platform | Typical Max | Notes |
|----------|-------------|-------|
| Consumer GPUs | 24GB | RTX 4090, limits to ~13B at Q8 |
| Pro GPUs | 48-80GB | A6000, H100 - expensive |
| Mac Studio M2 Ultra | 192GB | Unified, accessible |
| Mac Studio M4 Max | 128GB | Unified, accessible |

### Bandwidth

M4-series memory bandwidth:

| Chip | Bandwidth | Notes |
|------|-----------|-------|
| M4 | 120 GB/s | Base chip |
| M4 Pro | 273 GB/s | Good for inference |
| M4 Max | 546 GB/s | Excellent for large models |

Token generation is memory-bandwidth bound. Higher bandwidth = faster tokens/sec.

## The 75% Rule

Reserve 25% of unified memory for system overhead:

| Total Memory | Available for Models | Comfortable Model Size |
|--------------|---------------------|------------------------|
| 32GB | 24GB | 7-13B at Q4-Q8 |
| 64GB | 48GB | 34B at Q4-Q6, 70B at Q2 |
| 96GB | 72GB | 70B at Q4-Q5 |
| 128GB | 96GB | 70B at Q6, 405B at Q2 |
| 192GB | 144GB | 70B at Q8, 405B at Q3-Q4 |

## Memory Calculation

Estimate VRAM requirements:

```
VRAM (GB) ≈ Parameters (B) × Bits / 8

Examples:
- 70B Q4 (4-bit): 70 × 4 / 8 = 35GB base
- 70B Q4 with context: ~43GB typical
- 405B Q2 (2-bit): 405 × 2 / 8 = 101GB base
```

Add 20-30% overhead for:
- KV cache (scales with context length)
- Activation memory
- System buffers

## Monitoring Memory Usage

### macOS Activity Monitor

```bash
# Memory pressure indicator
memory_pressure

# Detailed memory stats
vm_stat
```

### During Inference

Monitor in real-time:

```bash
# Watch memory usage
watch -n 1 'memory_pressure | head -5'

# For Ollama specifically
ollama ps  # Shows loaded models and memory
```

### Signs of Memory Pressure

| Symptom | Cause | Solution |
|---------|-------|----------|
| Slow generation | Swap usage | Reduce model size or context |
| System unresponsive | Memory exhausted | Lower GPU layers |
| Model fails to load | Insufficient memory | Use higher quantization |

## Optimizing Memory Usage

### Context Length Tradeoffs

KV cache grows linearly with context:

| Context | Additional Memory | Use Case |
|---------|-------------------|----------|
| 4K | ~1GB | Short conversations |
| 8K | ~2GB | Standard coding |
| 32K | ~8GB | Large file context |
| 128K | ~32GB | Repository-wide context |

### Multi-Model Strategies

Running multiple models simultaneously:

```bash
# Example: Code + Chat models
# DeepSeek Coder 33B Q4: ~20GB
# Llama 3.2 8B Q8: ~10GB
# Total: ~30GB, leaves room for 70B main model
```

### Offloading Options

When models exceed available memory:

| Strategy | Tradeoff |
|----------|----------|
| More quantization | Reduce quality slightly |
| Fewer GPU layers | Slower inference (CPU fallback) |
| Smaller context | Less conversation history |
| Unload unused models | Manual model switching |

## Apple Silicon Tiers

Model recommendations by chip:

| Chip | Memory | Recommended Models |
|------|--------|-------------------|
| M1/M2/M3 | 8-16GB | 7B models only |
| M1/M2/M3 Pro | 16-36GB | Up to 13B |
| M1/M2/M3 Max | 32-96GB | Up to 70B (Q4 on 64GB) |
| M1/M2/M3/M4 Ultra | 64-192GB | 70B comfortably, 405B possible |
| M4 Max | 128GB | 70B at Q6, 405B at Q2 |

## Neural Engine

M-series chips include a Neural Engine, but current LLM frameworks primarily use GPU:

| Component | Used By | Performance |
|-----------|---------|-------------|
| GPU (Metal) | MLX, llama.cpp | Primary inference path |
| Neural Engine | CoreML (limited) | Not widely supported for LLMs |
| CPU | Fallback | 10-50x slower than GPU |

MLX can achieve up to 87% performance improvement over llama.cpp by better utilizing Metal.

## See Also

- [Why Local LLMs](why-local-llms.md) - Benefits overview
- [Architecture Decisions](architecture-decisions.md) - Deployment options
- [Memory Management](../performance/memory-management.md) - Optimization techniques
- [Quantization](../models/quantization.md) - Size/quality tradeoffs
