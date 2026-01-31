# Benchmarking

Measure and compare LLM inference performance consistently.

## Key Metrics

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Tokens/sec (generation)** | Output speed | User-perceived speed |
| **Tokens/sec (prompt)** | Input processing | First token latency |
| **TTFT** | Time to first token | Responsiveness |
| **Memory usage** | VRAM/RAM consumed | Capacity planning |
| **Perplexity** | Model quality | Quality/speed tradeoff |

## llama-bench

The standard benchmarking tool for llama.cpp.

### Basic Usage

```bash
# Build if needed
cd llama.cpp
cmake --build build --target llama-bench

# Run benchmark
./build/bin/llama-bench -m /path/to/model.gguf
```

### Common Options

```bash
./llama-bench \
  -m model.gguf \
  -p 512 \           # Prompt tokens
  -n 128 \           # Generation tokens
  -ngl 99 \          # GPU layers
  -b 512 \           # Batch size
  -t 8 \             # Threads
  -r 5               # Repetitions for averaging
```

### Output Interpretation

```
model                       size     params   backend  ngl   test     t/s
llama-3.3-70b-q4_k_m       42.5G    70.55B   CUDA     99    pp512   1234.56
llama-3.3-70b-q4_k_m       42.5G    70.55B   CUDA     99    tg128   35.67
```

- `pp512`: Prompt processing (512 tokens), higher is better
- `tg128`: Token generation (128 tokens), higher is better

## Consistent Methodology

### Standard Test Configuration

For reproducible results:

```bash
# Standard test parameters
PROMPT_TOKENS=512
GEN_TOKENS=128
REPETITIONS=5
GPU_LAYERS=99
BATCH_SIZE=512
THREADS=8

./llama-bench \
  -m model.gguf \
  -p $PROMPT_TOKENS \
  -n $GEN_TOKENS \
  -ngl $GPU_LAYERS \
  -b $BATCH_SIZE \
  -t $THREADS \
  -r $REPETITIONS
```

### Benchmark Script

```bash
#!/bin/bash
# benchmark.sh

MODEL=$1
OUTPUT="benchmark_results.txt"

echo "=== Benchmarking $MODEL ===" | tee -a $OUTPUT
echo "Date: $(date)" | tee -a $OUTPUT
echo "" | tee -a $OUTPUT

./llama-bench \
  -m "$MODEL" \
  -p 512 \
  -n 128 \
  -ngl 99 \
  -r 5 | tee -a $OUTPUT

echo "" | tee -a $OUTPUT
```

### Compare Quantizations

```bash
#!/bin/bash
# compare_quants.sh

MODELS=(
  "model-q4_k_m.gguf"
  "model-q5_k_m.gguf"
  "model-q6_k.gguf"
  "model-q8_0.gguf"
)

for model in "${MODELS[@]}"; do
  echo "Testing: $model"
  ./llama-bench -m "$model" -p 512 -n 128 -ngl 99 -r 3
  echo ""
done
```

## Ollama Benchmarking

### Basic Test

```bash
# Time a completion
time curl -s http://localhost:11434/api/generate \
  -d '{"model": "llama3.3:70b", "prompt": "Hello", "stream": false}' \
  | jq .
```

### Throughput Test

```python
#!/usr/bin/env python3
"""Benchmark Ollama throughput."""

import time
import ollama

def benchmark(model: str, prompt: str, num_runs: int = 5):
    times = []
    tokens = []

    for _ in range(num_runs):
        start = time.time()
        response = ollama.generate(model=model, prompt=prompt)
        elapsed = time.time() - start

        times.append(elapsed)
        tokens.append(response['eval_count'])

    avg_time = sum(times) / len(times)
    avg_tokens = sum(tokens) / len(tokens)
    tps = avg_tokens / avg_time

    print(f"Model: {model}")
    print(f"Avg time: {avg_time:.2f}s")
    print(f"Avg tokens: {avg_tokens:.0f}")
    print(f"Tokens/sec: {tps:.1f}")

benchmark("llama3.3:70b", "Write a short poem about coding.")
```

## API Benchmarking

### Single Request

```bash
# Time API call
time curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3",
    "messages": [{"role": "user", "content": "Count to 100."}],
    "max_tokens": 200
  }' | jq .usage
```

### Concurrent Requests

```python
#!/usr/bin/env python3
"""Benchmark concurrent API requests."""

import asyncio
import time
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="x")

async def single_request(prompt: str):
    start = time.time()
    response = await client.chat.completions.create(
        model="llama3.3",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    elapsed = time.time() - start
    return elapsed, response.usage.completion_tokens

async def benchmark(num_requests: int, concurrency: int):
    semaphore = asyncio.Semaphore(concurrency)

    async def limited_request(i):
        async with semaphore:
            return await single_request(f"Question {i}: What is 2+2?")

    start = time.time()
    results = await asyncio.gather(*[limited_request(i) for i in range(num_requests)])
    total_time = time.time() - start

    total_tokens = sum(r[1] for r in results)
    print(f"Requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Requests/sec: {num_requests/total_time:.1f}")
    print(f"Tokens/sec: {total_tokens/total_time:.1f}")

asyncio.run(benchmark(20, 4))
```

## Memory Profiling

### Monitor During Benchmark

```bash
# Terminal 1: Run benchmark
./llama-bench -m model.gguf -p 512 -n 128 -ngl 99

# Terminal 2: Monitor GPU memory (NVIDIA)
nvidia-smi -l 1

# Terminal 2: Monitor GPU memory (AMD)
watch -n 1 rocm-smi

# Terminal 3: Monitor system memory
watch -n 1 free -h
```

### Record Peak Usage

```bash
# Log GPU memory during test
nvidia-smi --query-gpu=memory.used --format=csv -l 1 > gpu_mem.log &
PID=$!

./llama-bench -m model.gguf -p 512 -n 128 -ngl 99

kill $PID

# Find peak
sort -t',' -k1 -n gpu_mem.log | tail -1
```

## Perplexity Testing

Test model quality (lower is better):

```bash
# Download test data
wget https://huggingface.co/datasets/wikitext/resolve/main/wikitext-2-v1/wiki.test.raw

# Run perplexity test
./llama-perplexity \
  -m model-q4.gguf \
  -f wiki.test.raw \
  --chunks 100
```

### Compare Quantizations

```bash
for quant in q4_k_m q5_k_m q6_k q8_0; do
  echo "Testing $quant"
  ./llama-perplexity -m "model-${quant}.gguf" -f wiki.test.raw --chunks 50
done
```

## Results Recording

### Spreadsheet Format

| Model | Quant | Size | GPU Layers | Prompt (t/s) | Gen (t/s) | VRAM |
|-------|-------|------|------------|--------------|-----------|------|
| Llama 3.3 70B | Q4_K_M | 43GB | 99 | 1200 | 35 | 45GB |
| Llama 3.3 70B | Q5_K_M | 48GB | 99 | 1100 | 32 | 50GB |

### JSON Output

```bash
./llama-bench -m model.gguf -p 512 -n 128 -ngl 99 -o json > results.json
```

## Comparative Benchmarks

### Same Model, Different Engines

```bash
# llama.cpp
./llama-bench -m model.gguf -p 512 -n 128

# Ollama (uses llama.cpp)
python3 bench_ollama.py

# Compare results
```

### Same Model, Different Quantizations

```bash
for q in q4_k_s q4_k_m q5_k_m q6_k q8_0; do
  echo "=== $q ==="
  ./llama-bench -m "model-${q}.gguf" -p 512 -n 128 -ngl 99
done
```

## Troubleshooting

### Inconsistent Results

- Increase repetitions (`-r 10`)
- Close other applications
- Check thermal throttling
- Use fixed CPU frequency

### GPU Not Fully Utilized

- Increase batch size (`-b 1024`)
- Verify GPU layers (`-ngl 99`)
- Check for memory bottleneck

### Results Lower Than Expected

- Check GPU driver version
- Verify CUDA/ROCm installation
- Compare with reported benchmarks
- Check for background processes

## See Also

- [Performance Index](index.md) - Overview
- [Memory Management](memory-management.md) - Optimization
- [Quantization](../models/quantization.md) - Quality tradeoffs
- [llama.cpp](../inference-engines/llama-cpp.md) - Engine reference
