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

### Expected Performance (MS-S1 MAX — AMD Strix Halo iGPU, 128GB unified)

| Model | Quant | Tokens/sec | Notes |
|-------|-------|------------|-------|
| 7B | Q8_0 | 50-70 | ROCm/HIP, fits easily |
| 8B | Q4_K_M | 50-70 | Sweet spot for chat |
| 32B | Q4_K_M | 15-20 | Good balance |
| 70B | Q4_K_M | 6-9 | Memory bandwidth limited |
| 405B | Q2_K | 1-2 | Fits in 128GB, very slow |

### Expected Performance (Apple Silicon — M-series unified memory)

| Model | Quant | Tokens/sec | Notes |
|-------|-------|------------|-------|
| 7B | Q8_0 | 60-90 | Metal/MLX |
| 32B | Q4_K_M | 20-30 | Memory bandwidth dependent |
| 70B | Q4_K_M | 8-12 | Requires high-memory M-Max/M-Ultra |

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
# GPU utilization (AMD ROCm — MS-S1 MAX)
rocm-smi
watch -n 1 rocm-smi

# GPU utilization (Apple Silicon, laptop)
sudo powermetrics --samplers gpu_power -i 1000

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
       v
┌──────────────────┐
│ Check GPU usage  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    v         v
  Low?      High?
    │         │
    v         v
┌─────────┐ ┌─────────┐
│ GPU not │ │ Memory  │
│ used    │ │ bound   │
└────┬────┘ └────┬────┘
     │           │
     v           v
Add more    Use smaller
GPU layers  quant/model
```

## See Also

- [Quantization](../models/quantization.md) - Size/speed tradeoffs
- [Choosing Models](../models/choosing-models.md) - Model selection
- [GPU Containers](../containers/gpu-containers.md) - GPU configuration
