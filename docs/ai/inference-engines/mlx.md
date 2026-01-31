# MLX

Apple's machine learning framework optimized for Apple Silicon, providing up to 87% faster inference than llama.cpp.

## Overview

MLX provides:

- **Apple Silicon native** - Designed for M-series unified memory
- **Metal acceleration** - Full GPU utilization
- **Lazy evaluation** - Efficient memory usage
- **NumPy-like API** - Familiar Python interface
- **Active development** - Regular performance improvements

## Requirements

- macOS 13.5+ (Ventura or later)
- Apple Silicon (M1, M2, M3, M4 series)
- Python 3.9+

## Installation

### Basic Installation

```bash
# Install mlx and language model support
pip install mlx-lm

# Or with uv
uv pip install mlx-lm
```

### With Development Tools

```bash
pip install mlx-lm transformers huggingface_hub
```

### Verify Installation

```python
import mlx.core as mx
print(f"MLX version: {mx.__version__}")
print(f"Default device: {mx.default_device()}")
# Should show: gpu
```

## Quick Start

### Command Line

```bash
# Generate text (downloads model if needed)
mlx_lm.generate \
  --model mlx-community/Llama-3.3-70B-Instruct-4bit \
  --prompt "Explain recursion in programming"

# Chat mode
mlx_lm.chat --model mlx-community/Llama-3.3-70B-Instruct-4bit
```

### Python API

```python
from mlx_lm import load, generate

# Load model (cached after first download)
model, tokenizer = load("mlx-community/Llama-3.3-70B-Instruct-4bit")

# Generate
response = generate(
    model,
    tokenizer,
    prompt="What is Docker?",
    max_tokens=200,
    temp=0.7
)
print(response)
```

## MLX-Community Models

Pre-quantized models optimized for MLX:

| Model | Size | HuggingFace Path |
|-------|------|------------------|
| Llama 3.3 70B 4-bit | ~40GB | `mlx-community/Llama-3.3-70B-Instruct-4bit` |
| Llama 3.3 70B 8-bit | ~70GB | `mlx-community/Llama-3.3-70B-Instruct-8bit` |
| Qwen 2.5 72B 4-bit | ~42GB | `mlx-community/Qwen2.5-72B-Instruct-4bit` |
| DeepSeek Coder 33B | ~20GB | `mlx-community/DeepSeek-Coder-V2-Instruct-4bit` |
| Mistral 7B 4-bit | ~4GB | `mlx-community/Mistral-7B-Instruct-v0.3-4bit` |

Browse all at [huggingface.co/mlx-community](https://huggingface.co/mlx-community).

## Model Conversion

Convert models to MLX format:

### From Hugging Face

```bash
# Convert and quantize
mlx_lm.convert \
  --hf-path meta-llama/Llama-3.3-70B-Instruct \
  --mlx-path ./llama-3.3-70b-4bit \
  -q  # Quantize to 4-bit
```

### Quantization Options

```bash
# 4-bit (smallest)
mlx_lm.convert --hf-path model -q --q-bits 4

# 8-bit (higher quality)
mlx_lm.convert --hf-path model -q --q-bits 8

# Group size for quantization
mlx_lm.convert --hf-path model -q --q-bits 4 --q-group-size 64
```

### From GGUF

```bash
# Convert GGUF to MLX format
mlx_lm.convert \
  --gguf-path /path/to/model.gguf \
  --mlx-path ./converted-model
```

## Server Mode

Run MLX as an OpenAI-compatible server:

### Using mlx-lm-server

```bash
# Install server
pip install mlx-lm[server]

# Start server
mlx_lm.server \
  --model mlx-community/Llama-3.3-70B-Instruct-4bit \
  --host 0.0.0.0 \
  --port 8080
```

### API Usage

```bash
# Chat completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### With LiteLLM Proxy

For more robust serving:

```bash
pip install litellm

# Start proxy pointing to MLX
litellm --model mlx/mlx-community/Llama-3.3-70B-Instruct-4bit
```

## Advanced Generation

### Streaming

```python
from mlx_lm import load, stream_generate

model, tokenizer = load("mlx-community/Llama-3.3-70B-Instruct-4bit")

for token in stream_generate(
    model,
    tokenizer,
    prompt="Write a haiku about programming:",
    max_tokens=50
):
    print(token, end="", flush=True)
```

### Custom Parameters

```python
from mlx_lm import generate

response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    temp=0.7,           # Temperature
    top_p=0.95,         # Nucleus sampling
    repetition_penalty=1.1,
    repetition_context_size=20
)
```

### Chat Format

```python
from mlx_lm import load, generate

model, tokenizer = load("mlx-community/Llama-3.3-70B-Instruct-4bit")

messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Write a Python function to reverse a string."}
]

# Apply chat template
prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

response = generate(model, tokenizer, prompt=prompt, max_tokens=500)
```

## Performance Optimization

### Memory Management

```python
import mlx.core as mx

# Clear memory cache
mx.metal.clear_cache()

# Check memory usage
print(f"Peak memory: {mx.metal.get_peak_memory() / 1e9:.2f} GB")
print(f"Active memory: {mx.metal.get_active_memory() / 1e9:.2f} GB")
```

### Batch Generation

```python
# Generate multiple responses
prompts = ["Question 1:", "Question 2:", "Question 3:"]

for prompt in prompts:
    response = generate(model, tokenizer, prompt=prompt, max_tokens=100)
    print(response)
    mx.metal.clear_cache()  # Clear between generations
```

### KV Cache Optimization

For long conversations, the KV cache can grow large:

```python
# Limit context for memory efficiency
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    max_kv_size=4096  # Limit KV cache
)
```

## Performance Comparison

Benchmarks on M4 Max (128GB), Llama 3.3 70B 4-bit:

| Framework | Tokens/sec | TTFT | Notes |
|-----------|------------|------|-------|
| MLX | 45-50 | ~100ms | Metal optimized |
| llama.cpp (Metal) | 35-40 | ~150ms | Good baseline |
| Ollama | 33-38 | ~200ms | Convenience overhead |

MLX advantages:
- 20-40% faster token generation
- Better memory efficiency
- Lower time to first token

## Speculative Decoding

Use a small model to speed up a large model:

```python
from mlx_lm import load, generate

# Load draft and target models
draft_model, _ = load("mlx-community/Llama-3.2-1B-Instruct-4bit")
target_model, tokenizer = load("mlx-community/Llama-3.3-70B-Instruct-4bit")

# Speculative generation (coming in mlx-lm)
response = generate(
    target_model,
    tokenizer,
    prompt="Explain quantum computing",
    draft_model=draft_model,
    max_tokens=500
)
```

## Troubleshooting

### Out of Memory

```bash
# Use smaller quantization
mlx_lm.generate --model mlx-community/Llama-3.3-70B-Instruct-4bit

# Or reduce context
mlx_lm.generate --model model --max-kv-size 4096
```

### Slow First Load

Model loading includes compilation. Subsequent runs are faster:

```python
# First run: ~30 seconds (compilation)
# Subsequent runs: ~5 seconds (cached)
```

### Model Not Found

```bash
# Login for gated models
huggingface-cli login

# Set cache directory
export HF_HOME=/tank/ai/models/huggingface
```

### GPU Not Used

```python
import mlx.core as mx

# Verify GPU is available
print(mx.default_device())  # Should show: Device(gpu, 0)

# Force GPU
mx.set_default_device(mx.gpu)
```

## See Also

- [Inference Engines Index](index.md) - Engine comparison
- [Unified Memory](../fundamentals/unified-memory.md) - Memory architecture
- [Hugging Face](../models/huggingface.md) - Model downloads
- [Benchmarking](../performance/benchmarking.md) - Performance testing
