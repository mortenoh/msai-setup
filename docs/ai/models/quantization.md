# Quantization

Understanding quantization methods and their impact on model size, quality, and performance.

## What is Quantization?

Quantization reduces model precision from 16/32-bit floats to lower bit representations:

```
Original (FP16):     16 bits per weight  →  100% size, 100% quality
Quantized (Q4):       4 bits per weight  →  ~25% size, ~95% quality
```

## GGUF Quantization Types

### Overview

| Type | Bits | Size Ratio | Quality | Use Case |
|------|------|------------|---------|----------|
| Q2_K | 2.5 | 18% | Poor | Maximum compression |
| Q3_K_S | 3.0 | 22% | Fair | Very limited memory |
| Q3_K_M | 3.5 | 25% | Fair+ | Memory constrained |
| Q4_K_S | 4.25 | 30% | Good | Small + fast |
| Q4_K_M | 4.5 | 32% | Good+ | **Recommended balance** |
| Q5_K_S | 5.0 | 36% | Very Good | Quality focus |
| Q5_K_M | 5.5 | 38% | Very Good+ | Better quality |
| Q6_K | 6.5 | 45% | Excellent | Near full quality |
| Q8_0 | 8.0 | 55% | Near Perfect | Maximum quality |
| F16 | 16 | 100% | Perfect | Full precision |

### Size Calculation

```
Approximate Model Size:

Parameters (B) × Bits / 8 = Size (GB)

70B model:
- F16:   70 × 16 / 8 = 140 GB
- Q8_0:  70 × 8 / 8  = 70 GB
- Q6_K:  70 × 6.5/8  = 57 GB
- Q5_K_M: 70 × 5.5/8 = 48 GB
- Q4_K_M: 70 × 4.5/8 = 39 GB + overhead ≈ 43 GB
- Q3_K_M: 70 × 3.5/8 = 31 GB
- Q2_K:  70 × 2.5/8  = 22 GB
```

### Quality Impact

```
Quality Degradation by Quantization:

        Q8_0  Q6_K  Q5_K_M Q4_K_M Q3_K_M Q2_K
         │     │      │      │      │      │
 100% ───┼─────┼──────┼──────┼──────┼──────┼───
         │     │      │      │      │      │
  95% ───┼─────┼──────┼──────┼──────┼──────┼───
         ■     │      │      │      │      │    Q8_0: ~99%
  90% ───┼─────■──────┼──────┼──────┼──────┼───    Q6_K: ~98%
         │     │      ■      │      │      │
  85% ───┼─────┼──────┼──────■──────┼──────┼───    Q5_K_M: ~96%
         │     │      │      │      ■      │       Q4_K_M: ~94%
  80% ───┼─────┼──────┼──────┼──────┼──────┼───    Q3_K_M: ~90%
         │     │      │      │      │      ■       Q2_K: ~80%
```

## Recommendations by System

### 128GB System (MS-S1 MAX)

| Priority | Model + Quant | Size | Notes |
|----------|---------------|------|-------|
| Best balance | 70B Q4_K_M | ~43GB | Recommended |
| Higher quality | 70B Q5_K_M | ~48GB | Slight quality boost |
| Maximum quality | 70B Q6_K | ~57GB | Best practical 70B |
| Maximum size | 405B Q2_K | ~95GB | Limited context |

### 64GB System

| Priority | Model + Quant | Size | Notes |
|----------|---------------|------|-------|
| Best fit | 70B Q3_K_M | ~35GB | Fits with room |
| Higher quality | 34B Q5_K_M | ~25GB | Better quality, smaller model |
| Maximum quality | 34B Q6_K | ~30GB | Excellent quality |

### 32GB System

| Priority | Model + Quant | Size | Notes |
|----------|---------------|------|-------|
| Best balance | 8B Q8_0 | ~10GB | High quality small model |
| Larger model | 13B Q5_K_M | ~12GB | Good balance |
| Maximum | 34B Q3_K_M | ~18GB | Quality tradeoff |

## K-Quants Explained

The "K" variants use mixed quantization for better quality:

```
Standard Q4:     All weights at 4 bits

Q4_K variants:
┌─────────────────────────────────────────────┐
│ Attention layers │ FFN layers │ Embeddings  │
├─────────────────────────────────────────────┤
│   Higher bits    │  4 bits    │ Higher bits │
│   (important)    │ (bulk)     │ (important) │
└─────────────────────────────────────────────┘

Result: Better quality at similar size
```

### K-Quant Suffixes

| Suffix | Meaning | Quality/Size |
|--------|---------|--------------|
| `_S` | Small | Smaller, lower quality |
| `_M` | Medium | **Balanced (recommended)** |
| `_L` | Large | Larger, higher quality |

## I-Quants (Importance Matrix)

Advanced quantization using calibration data:

| Type | Method | Quality |
|------|--------|---------|
| IQ1_S | 1.5-bit | Experimental |
| IQ2_XXS | 2.0-bit | Better than Q2 |
| IQ3_XS | 3.0-bit | Better than Q3 |
| IQ4_NL | 4.0-bit | Non-linear, good quality |
| IQ4_XS | 4.0-bit | Extra small, good quality |

I-quants require importance matrices for optimal quality.

## Performance Impact

### Inference Speed

Higher quantization = faster inference (less memory bandwidth):

| Quantization | Relative Speed | Notes |
|--------------|----------------|-------|
| F16 | 1.0x (baseline) | Slowest |
| Q8_0 | ~1.2x | Slight improvement |
| Q6_K | ~1.4x | Noticeable |
| Q4_K_M | ~1.6x | **Best balance** |
| Q3_K_M | ~1.8x | Faster but quality loss |
| Q2_K | ~2.0x | Fastest, lowest quality |

### Context Length Impact

Lower quantization = more room for context:

| Model | Quant | Base Size | Room for Context |
|-------|-------|-----------|------------------|
| 70B | Q4_K_M | 43GB | 85GB remaining |
| 70B | Q5_K_M | 48GB | 80GB remaining |
| 70B | Q6_K | 57GB | 71GB remaining |

## Choosing Quantization

### Decision Flow

```
Do you have memory to spare?
├─ Yes → Go up one quant level (Q4→Q5 or Q5→Q6)
└─ No → Is quality critical?
        ├─ Yes → Use smaller model at higher quant
        └─ No → Use current quant level
```

### Practical Guidelines

1. **Start with Q4_K_M** - Best general-purpose choice
2. **Upgrade to Q5_K_M or Q6_K** if memory allows
3. **Use Q8_0** only if model comfortably fits with room for context
4. **Avoid Q2_K/Q3_K** unless necessary - quality degradation noticeable

## Testing Quality

### Perplexity Comparison

Lower is better:

```bash
# Using llama.cpp perplexity tool
./perplexity -m model-q4.gguf -f wiki.test.raw
./perplexity -m model-q6.gguf -f wiki.test.raw
```

### Practical Testing

Test with your actual use cases:

```bash
# Same prompt, different quants
ollama run llama3.3:70b-q4_K_M "Write a Python sorting algorithm"
ollama run llama3.3:70b-q6_K "Write a Python sorting algorithm"
```

## Converting Models

### Quantize with llama.cpp

```bash
# Convert and quantize
./quantize input.gguf output-q4_k_m.gguf Q4_K_M

# Available quantization types
./quantize --help
```

### With Importance Matrix

For better quality quantization:

```bash
# Generate importance matrix
./imatrix -m model.gguf -f calibration.txt -o imatrix.dat

# Quantize with imatrix
./quantize model.gguf output.gguf Q4_K_M --imatrix imatrix.dat
```

## AWQ and GPTQ (vLLM)

For vLLM/NVIDIA deployments:

| Method | Description | Best For |
|--------|-------------|----------|
| AWQ | Activation-aware | vLLM, fast inference |
| GPTQ | Post-training | Wide compatibility |
| FP8 | 8-bit float | H100, RTX 40 series |

```bash
# Using AWQ model with vLLM
vllm serve TheBloke/Llama-2-70B-Chat-AWQ --quantization awq
```

## See Also

- [Choosing Models](choosing-models.md) - Model selection
- [GGUF Formats](gguf-formats.md) - File format details
- [Memory Management](../performance/memory-management.md) - Fitting models
- [Benchmarking](../performance/benchmarking.md) - Testing performance
