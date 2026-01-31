# vLLM

High-throughput LLM serving engine with PagedAttention and continuous batching for production deployments.

## Overview

vLLM provides:

- **14-24x throughput** vs HuggingFace Transformers
- **PagedAttention** - Efficient KV cache memory management
- **Continuous batching** - Dynamic request scheduling
- **OpenAI-compatible API** - Drop-in replacement
- **Multi-GPU support** - Tensor and pipeline parallelism

## Requirements

- **NVIDIA GPU** - Primary support (CUDA 11.8+)
- **AMD GPU** - ROCm support (experimental)
- **Linux** - Primary platform
- **Python 3.9+**

!!! note "Apple Silicon"
    vLLM does not support Apple Silicon. Use [MLX](mlx.md) or [llama.cpp](llama-cpp.md) instead.

## Installation

### pip Install

```bash
# Basic installation
pip install vllm

# With specific CUDA version
pip install vllm --extra-index-url https://download.pytorch.org/whl/cu121
```

### Docker

```bash
docker run --gpus all \
  -v /tank/ai/models/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.3-70B-Instruct
```

### From Source

```bash
git clone https://github.com/vllm-project/vllm.git
cd vllm
pip install -e .
```

## Quick Start

### Command Line

```bash
# Start OpenAI-compatible server
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --host 0.0.0.0 \
  --port 8000

# With quantization
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --quantization awq
```

### Python API

```python
from vllm import LLM, SamplingParams

# Initialize model
llm = LLM(model="meta-llama/Llama-3.3-70B-Instruct")

# Generate
sampling_params = SamplingParams(temperature=0.7, max_tokens=100)
outputs = llm.generate(["What is machine learning?"], sampling_params)

for output in outputs:
    print(output.outputs[0].text)
```

## Server Configuration

### Basic Server

```bash
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 8192
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--model` | Model name or path | Required |
| `--host` | Listen address | `localhost` |
| `--port` | Listen port | `8000` |
| `--tensor-parallel-size` | GPUs for tensor parallelism | 1 |
| `--pipeline-parallel-size` | GPUs for pipeline parallelism | 1 |
| `--max-model-len` | Maximum context length | Model default |
| `--gpu-memory-utilization` | GPU memory fraction | 0.9 |
| `--quantization` | Quantization method | None |
| `--dtype` | Data type | `auto` |

### Multi-GPU Setup

```bash
# 2 GPUs with tensor parallelism
vllm serve meta-llama/Llama-3.1-405B-Instruct \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.95

# 4 GPUs with pipeline + tensor
vllm serve meta-llama/Llama-3.1-405B-Instruct \
  --tensor-parallel-size 2 \
  --pipeline-parallel-size 2
```

## API Usage

### Chat Completion

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain Docker containers."}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Streaming

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

### Completions

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "prompt": "The capital of France is",
    "max_tokens": 20
  }'
```

### Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Required but not validated
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[
        {"role": "user", "content": "Write a haiku about coding"}
    ]
)
print(response.choices[0].message.content)
```

## Quantization

### AWQ

```bash
# Use AWQ-quantized model
vllm serve TheBloke/Llama-2-70B-Chat-AWQ \
  --quantization awq
```

### GPTQ

```bash
vllm serve TheBloke/Llama-2-70B-Chat-GPTQ \
  --quantization gptq
```

### Supported Quantization

| Method | Memory Savings | Quality | Notes |
|--------|---------------|---------|-------|
| AWQ | ~75% | Good | Recommended for vLLM |
| GPTQ | ~75% | Good | Wide model availability |
| SqueezeLLM | ~75% | Good | Newer method |
| FP8 | ~50% | Excellent | H100/RTX 40 series |

## Performance Features

### Continuous Batching

Automatically batches concurrent requests:

```python
# Multiple concurrent requests handled efficiently
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="x")

async def generate(prompt):
    response = await client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Run 10 requests concurrently
prompts = [f"Question {i}" for i in range(10)]
results = asyncio.run(asyncio.gather(*[generate(p) for p in prompts]))
```

### PagedAttention

Memory-efficient KV cache management:

```
Traditional: Contiguous memory allocation
┌─────────────────────────────────────┐
│ Request 1 KV Cache (wasted space)   │
├─────────────────────────────────────┤
│ Request 2 KV Cache                  │
└─────────────────────────────────────┘

PagedAttention: Paged memory blocks
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ R1 │ R2 │ R1 │ R3 │ R2 │ R1 │ R3 │ R2 │
└────┴────┴────┴────┴────┴────┴────┴────┘
```

Benefits:
- Near-zero memory waste
- More concurrent requests
- Better GPU utilization

### Speculative Decoding

Use draft model for faster inference:

```bash
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --speculative-model meta-llama/Llama-3.2-1B-Instruct \
  --num-speculative-tokens 5
```

## Docker Deployment

### docker-compose

```yaml
version: '3.8'

services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    volumes:
      - /tank/ai/models/huggingface:/root/.cache/huggingface
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    command: >
      --model meta-llama/Llama-3.3-70B-Instruct
      --tensor-parallel-size 1
      --max-model-len 8192
      --gpu-memory-utilization 0.9
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Monitoring

### Prometheus Metrics

```bash
# Enable metrics
vllm serve model --enable-metrics

# Metrics available at
curl http://localhost:8000/metrics
```

Key metrics:
- `vllm:num_requests_running` - Active requests
- `vllm:num_requests_waiting` - Queued requests
- `vllm:gpu_cache_usage_perc` - KV cache utilization
- `vllm:avg_prompt_throughput_toks_per_s` - Input throughput
- `vllm:avg_generation_throughput_toks_per_s` - Output throughput

### Logging

```bash
# Verbose logging
vllm serve model --log-level debug
```

## Performance Tuning

### Memory Optimization

```bash
# Increase GPU memory usage
vllm serve model --gpu-memory-utilization 0.95

# Reduce max context for more concurrent requests
vllm serve model --max-model-len 4096
```

### Throughput Optimization

```bash
# Enable chunked prefill for better batching
vllm serve model --enable-chunked-prefill

# Tune block size
vllm serve model --block-size 32
```

### Benchmarking

```python
# Use vLLM benchmarking tools
python -m vllm.entrypoints.openai.api_server_benchmark \
  --model meta-llama/Llama-3.3-70B-Instruct \
  --num-prompts 100 \
  --request-rate 10
```

## Troubleshooting

### CUDA Out of Memory

```bash
# Reduce memory usage
--gpu-memory-utilization 0.8
--max-model-len 4096

# Use quantization
--quantization awq
```

### Model Not Loading

```bash
# Check HuggingFace token for gated models
export HUGGING_FACE_HUB_TOKEN=your_token

# Or use local path
vllm serve /tank/ai/models/huggingface/models--meta-llama--Llama-3.3-70B-Instruct/snapshots/...
```

### Slow Startup

First startup is slow due to model loading. Subsequent starts use cache:

```bash
# Pre-download model
huggingface-cli download meta-llama/Llama-3.3-70B-Instruct
```

## Comparison with Alternatives

| Feature | vLLM | llama.cpp | Ollama |
|---------|------|-----------|--------|
| Throughput | Highest | Medium | Medium |
| Batching | Continuous | Basic | Basic |
| GPU Support | NVIDIA/AMD | All | All |
| Setup | Medium | Easy | Easiest |
| Memory Efficiency | Excellent | Good | Good |
| Apple Silicon | No | Yes | Yes |

Use vLLM when:
- Running on NVIDIA GPUs
- Need high throughput
- Serving multiple concurrent users

## See Also

- [Inference Engines Index](index.md) - Engine comparison
- [Load Balancing](../api-serving/load-balancing.md) - Multi-backend setup
- [API Serving](../api-serving/index.md) - Production deployment
- [Benchmarking](../performance/benchmarking.md) - Performance testing
