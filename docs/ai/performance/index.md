# Performance

Optimize and measure LLM inference performance on your system.

## Overview

Key performance metrics:

- **Tokens/second** - Generation speed
- **Time to First Token (TTFT)** - Initial response latency
- **Context processing** - Prompt evaluation speed
- **Memory usage** - VRAM and RAM utilization

## Performance Factors

```
┌─────────────────────────────────────────────────────────────────┐
│                    Performance Equation                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tokens/sec = f(Memory Bandwidth, GPU Compute, Model Size)      │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Memory Bandwidth│  │  GPU/Compute    │  │   Model Size    │  │
│  │  (Primary)      │  │  (Secondary)    │  │  (Constraint)   │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  │
│  │ Higher = faster │  │ More = faster   │  │ Smaller = faster│  │
│  │ token generation│  │ prompt eval     │  │ for given HW    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Performance Reference

### Expected Performance (NVIDIA RTX 4090)

| Model | Quant | Tokens/sec | TTFT |
|-------|-------|------------|------|
| 7B | Q8_0 | 80-100 | <50ms |
| 13B | Q4_K_M | 60-80 | <100ms |
| 34B | Q4_K_M | 35-50 | <200ms |
| 70B | Q4_K_M | 20-35 | <300ms |

### Expected Performance (AMD GPU/128GB RAM)

| Model | Quant | Tokens/sec | Notes |
|-------|-------|------------|-------|
| 7B | Q8_0 | 50-70 | Vulkan or ROCm |
| 34B | Q4_K_M | 25-40 | Good balance |
| 70B | Q4_K_M | 15-25 | Memory bandwidth limited |

## Topics

<div class="grid cards" markdown>

-   :material-gauge: **Benchmarking**

    ---

    Measure and compare inference performance

    [:octicons-arrow-right-24: Benchmarking](benchmarking.md)

-   :material-resize: **Context Optimization**

    ---

    Balance context length and memory usage

    [:octicons-arrow-right-24: Context optimization](context-optimization.md)

-   :material-memory: **Memory Management**

    ---

    GPU layers, offloading, and multi-model strategies

    [:octicons-arrow-right-24: Memory management](memory-management.md)

</div>

## Quick Wins

### Immediate Optimizations

| Optimization | Impact | Complexity |
|--------------|--------|------------|
| Use GPU (all layers) | 5-20x | Low |
| Optimal quantization | 20-50% speed | Low |
| Reduce context | 10-30% speed | Low |
| Flash attention | 20-40% for long context | Medium |
| Batch requests | 2-4x throughput | Medium |

### Hardware Upgrades

| Upgrade | Impact | Cost |
|---------|--------|------|
| More VRAM | Run larger models | High |
| Faster memory | Better bandwidth | High |
| Better GPU | More compute | High |
| NVMe SSD | Faster loading | Medium |

## Monitoring

### Real-Time Metrics

```bash
# GPU utilization (NVIDIA)
nvidia-smi -l 1

# GPU utilization (AMD)
rocm-smi

# Memory pressure
watch -n 1 free -h

# llama.cpp server metrics
curl http://localhost:8080/metrics
```

### Key Indicators

| Metric | Good | Warning |
|--------|------|---------|
| GPU utilization | 80-100% | <50% |
| Memory usage | <90% | >95% |
| Tokens/sec | Model dependent | Degrading over time |
| TTFT | <500ms | >2s |

## Bottleneck Identification

```
Slow Generation?
       │
       ▼
┌──────────────────┐
│ Check GPU usage  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  Low?      High?
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ GPU not │ │ Memory  │
│ used    │ │ bound   │
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼
Add more    Use smaller
GPU layers  quant/model
```

## See Also

- [Quantization](../models/quantization.md) - Size/speed tradeoffs
- [Choosing Models](../models/choosing-models.md) - Model selection
- [GPU Containers](../containers/gpu-containers.md) - GPU configuration
