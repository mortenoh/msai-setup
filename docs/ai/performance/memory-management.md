# Memory Management

Optimize memory usage for LLM inference on systems with limited or shared memory.

## Memory Components

### What Uses Memory

```
Total Memory Usage:
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Model Weights     │  KV Cache      │  Activations │ System │
│  (Fixed)           │  (Grows with   │  (Small)     │ (OS)   │
│                    │   context)     │              │        │
│  ████████████████  │  ████████      │  ██          │  ████  │
│  ~43GB (70B Q4)    │  ~2-32GB       │  ~1GB        │  ~8GB  │
│                    │  (8K-128K ctx) │              │        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Memory Calculation

```
Total = Model + KV Cache + Activations + System

Example (70B Q4, 8K context):
- Model: 43 GB
- KV Cache: 4 GB
- Activations: 1 GB
- System: 8 GB
- Total: ~56 GB

With 32K context:
- Model: 43 GB
- KV Cache: 16 GB
- Total: ~68 GB
```

## GPU Layer Allocation

### Full GPU Offload

Best performance when model fits entirely in VRAM:

```bash
# All layers on GPU
./llama-server -m model.gguf -ngl 99
```

### Partial Offload

When model exceeds VRAM:

```bash
# Only some layers on GPU
./llama-server -m model.gguf -ngl 40

# Check GPU memory and adjust
nvidia-smi  # Check usage
# Increase -ngl if room, decrease if OOM
```

### Layer Allocation Formula

```
layers_on_gpu = (available_vram - system_reserve) / per_layer_size

Example (70B on 48GB VRAM):
- 70B Q4 has ~80 layers
- Each layer ≈ 0.5 GB
- Available: 48 - 4 (reserve) = 44 GB
- Layers: 44 / 0.5 ≈ 88 → All fit!

Example (70B on 24GB VRAM):
- Available: 24 - 4 = 20 GB
- Layers: 20 / 0.5 = 40 layers on GPU
- -ngl 40
```

## Multi-Model Strategies

### Serial Loading

Load one model at a time:

```bash
# Ollama auto-manages
OLLAMA_MAX_LOADED_MODELS=1

# Unload before loading new model
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.3:70b", "keep_alive": 0}'
```

### Concurrent Models

For 128GB with multiple models:

```yaml
# Example: 70B + 8B simultaneously
# 70B Q4: ~43GB
# 8B Q8: ~10GB
# Total: ~53GB (fits with room)

environment:
  - OLLAMA_MAX_LOADED_MODELS=2
```

### Model Swapping

Configure unload timeout:

```bash
# Keep models loaded for 30 minutes
OLLAMA_KEEP_ALIVE=30m

# Unload after 5 minutes idle (save memory)
OLLAMA_KEEP_ALIVE=5m
```

## Quantization for Memory

### Quantization vs Memory

| Quantization | 70B Size | VRAM for 8K | Quality |
|--------------|----------|-------------|---------|
| Q8_0 | 75GB | 79GB | Best |
| Q6_K | 57GB | 61GB | Excellent |
| Q5_K_M | 48GB | 52GB | Very Good |
| Q4_K_M | 43GB | 47GB | Good |
| Q3_K_M | 35GB | 39GB | Acceptable |
| Q2_K | 28GB | 32GB | Degraded |

### Selection Guide

```
Available Memory → Recommended Quantization

128GB: 70B Q6_K, or 405B Q2_K
96GB:  70B Q4_K_M or Q5_K_M
64GB:  70B Q3_K_M, or 34B Q5_K_M
48GB:  70B Q2_K, or 34B Q4_K_M
32GB:  34B Q3_K_M, or 13B Q5_K_M
24GB:  13B Q4_K_M, or 7B Q6_K
```

## Offloading Strategies

### GPU → CPU Fallback

When model partially fits:

```bash
# Specify GPU and CPU layers
./llama-server -m model.gguf \
  -ngl 40 \       # 40 layers on GPU
  --threads 8     # CPU threads for remaining
```

### Performance Impact

| Configuration | Speed | Notes |
|---------------|-------|-------|
| All GPU | 1.0x | Baseline |
| 75% GPU | 0.6x | Moderate slowdown |
| 50% GPU | 0.4x | Significant slowdown |
| 25% GPU | 0.2x | Very slow |
| All CPU | 0.1x | Not recommended |

### NVMe Offload (Experimental)

For extremely large models:

```bash
# If supported by engine
--model-offload-dir /path/to/nvme
```

## System Memory Optimization

### Disable Swap for LLMs

Swapping kills performance:

```bash
# Temporarily disable
sudo swapoff -a

# Or set vm.swappiness low
echo 1 | sudo tee /proc/sys/vm/swappiness
```

### Huge Pages

Better memory performance:

```bash
# Allocate huge pages
echo 32768 | sudo tee /proc/sys/vm/nr_hugepages

# Verify
grep HugePages /proc/meminfo
```

### Memory Overcommit

Prevent OOM issues:

```bash
# Disable overcommit
echo 2 | sudo tee /proc/sys/vm/overcommit_memory
```

## Monitoring

### Real-time Monitoring

```bash
# GPU memory (NVIDIA)
watch -n 1 nvidia-smi

# GPU memory (AMD)
watch -n 1 rocm-smi

# System memory
watch -n 1 free -h

# Combined
watch -n 1 'nvidia-smi; echo "---"; free -h'
```

### Memory Pressure

```bash
# Check memory pressure
cat /proc/pressure/memory

# Watch for issues
dmesg | grep -i "out of memory"
```

### Ollama Memory

```bash
# Currently loaded models
ollama ps

# Output shows memory per model
# NAME              SIZE     PROCESSOR
# llama3.3:70b      43 GB    GPU
```

## Multi-Instance Deployment

### Memory Partitioning

For multiple llama.cpp instances:

```bash
# Instance 1: GPU 0, layers 0-40
./llama-server -m model1.gguf -ngl 40 --port 8081

# Instance 2: GPU 0, layers from different model
./llama-server -m model2.gguf -ngl 20 --port 8082
```

### Container Memory Limits

```yaml
services:
  llama-small:
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]

  llama-large:
    deploy:
      resources:
        limits:
          memory: 64G
```

## Troubleshooting

### Out of Memory (OOM)

```bash
# Symptoms
dmesg | grep -i "killed process"

# Solutions
# 1. Reduce GPU layers
-ngl 30  # Instead of 99

# 2. Use smaller quantization
model-q4_k_s.gguf  # Instead of q4_k_m

# 3. Reduce context
-c 4096  # Instead of 8192

# 4. Unload other models
ollama stop other-model
```

### Slow After Loading

Memory thrashing symptoms:

```bash
# Check swap usage
swapon --show

# If swap is being used heavily, model is too large
# Solution: smaller model or higher quantization
```

### GPU Memory Fragmentation

```bash
# Restart engine to defragment
sudo systemctl restart ollama

# Or for Docker
docker restart ollama
```

## Best Practices

1. **Size models for available memory** - Leave 20% headroom
2. **Use appropriate quantization** - Q4_K_M is usually best balance
3. **Monitor during operation** - Watch for memory pressure
4. **Set keep_alive appropriately** - Don't hold unused models
5. **Use flash attention** - Reduces KV cache memory
6. **Disable swap for LLM workloads** - Prevent thrashing

## See Also

- [Performance Index](index.md) - Overview
- [Context Optimization](context-optimization.md) - Context tuning
- [Quantization](../models/quantization.md) - Size reduction
- [Benchmarking](benchmarking.md) - Measuring performance
