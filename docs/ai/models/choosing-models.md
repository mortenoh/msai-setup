# Choosing Models

Select the right model for your use case, hardware, and quality requirements.

## Decision Framework

```
┌─────────────────────────────────────────────────────────────┐
│                  What's your primary use case?              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │  Code   │          │  Chat   │          │  Docs   │
   │ Assist  │          │  /QA    │          │ Process │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│ DeepSeek Coder │   │ Llama 3.3 70B  │   │ Qwen 2.5 72B   │
│ Qwen 2.5 Coder │   │ Qwen 2.5 72B   │   │ (Long context) │
└────────────────┘   └────────────────┘   └────────────────┘
```

## Models by Memory Tier

### 32GB RAM/VRAM

| Model | Quant | Size | Use Case |
|-------|-------|------|----------|
| Llama 3.2 8B | Q8_0 | ~10GB | Fast general |
| Qwen 2.5 7B | Q8_0 | ~9GB | Multilingual |
| DeepSeek Coder V2 Lite | Q8_0 | ~9GB | Coding |
| Mistral 7B | Q8_0 | ~9GB | Efficient general |
| Gemma 2 9B | Q8_0 | ~11GB | Balanced |

### 64GB RAM/VRAM

| Model | Quant | Size | Use Case |
|-------|-------|------|----------|
| Llama 3.3 70B | Q3_K_M | ~35GB | General (quality tradeoff) |
| Qwen 2.5 32B | Q6_K | ~28GB | Quality balance |
| DeepSeek Coder 33B | Q5_K_M | ~25GB | Coding |
| Mistral Large | Q3_K_M | ~38GB | Reasoning |
| Mixtral 8x7B | Q5_K_M | ~35GB | MoE efficiency |

### 128GB RAM/VRAM

| Model | Quant | Size | Use Case |
|-------|-------|------|----------|
| Llama 3.3 70B | Q4_K_M | ~43GB | Best 70B balance |
| Llama 3.3 70B | Q6_K | ~58GB | Higher quality |
| Qwen 2.5 72B | Q5_K_M | ~55GB | Multilingual |
| DeepSeek V3 | Q4_K_M | ~75GB | Latest reasoning |
| Llama 3.1 405B | Q2_K | ~95GB | Maximum capability |

### 192GB+ RAM/VRAM

| Model | Quant | Size | Use Case |
|-------|-------|------|----------|
| Llama 3.1 405B | Q4_K_M | ~180GB | Full quality 405B |
| Llama 3.3 70B | Q8_0 | ~75GB | Highest 70B quality |
| Multiple 70B | Q4_K_M | 43GB each | Multi-model serving |

## Use Case Recommendations

### AI-Assisted Coding

**Primary choice: DeepSeek Coder V2 or Qwen 2.5 Coder**

| Requirement | Model | Notes |
|-------------|-------|-------|
| Fast completions | DeepSeek Coder V2 Lite (16B) | Low latency |
| High quality | DeepSeek Coder V2 (236B) | Best code quality |
| Balanced | Qwen 2.5 Coder 32B | Good quality/speed |
| Fill-in-middle | DeepSeek Coder | Native FIM support |

```bash
# Recommended for coding
ollama pull deepseek-coder-v2:16b
ollama pull qwen2.5-coder:32b
```

### General Chat/Assistant

**Primary choice: Llama 3.3 70B or Qwen 2.5 72B**

| Requirement | Model | Notes |
|-------------|-------|-------|
| Best reasoning | Llama 3.3 70B | Latest Llama |
| Multilingual | Qwen 2.5 72B | 29 languages |
| Fast response | Llama 3.2 8B | Sub-second latency |
| Long context | Qwen 2.5 (128K) | Document analysis |

### Document Processing

**Primary choice: Qwen 2.5 with long context**

| Requirement | Model | Notes |
|-------------|-------|-------|
| Long documents | Qwen 2.5 72B (128K) | Full document context |
| Summarization | Llama 3.3 70B | Strong instruction following |
| Extraction | Mixtral 8x7B | Efficient for structured |

### RAG/Embeddings

**Pair with embedding model:**

| Embedding Model | Dimensions | Notes |
|-----------------|------------|-------|
| nomic-embed-text | 768 | Good default |
| mxbai-embed-large | 1024 | Higher quality |
| all-MiniLM-L6-v2 | 384 | Fast, small |

```bash
ollama pull nomic-embed-text
```

## Quality vs Speed Tradeoffs

### Response Latency

| Model Size | TTFT | Tokens/sec | Use Case |
|------------|------|------------|----------|
| 7-8B | <100ms | 50-80 | Interactive |
| 32-34B | 100-300ms | 30-50 | Balanced |
| 70B | 200-500ms | 20-40 | Quality focus |
| 405B | 500ms+ | 10-20 | Maximum quality |

### Quality Benchmarks

Approximate rankings (higher = better):

```
General Reasoning (MMLU-like):
Llama 3.1 405B > DeepSeek V3 > Llama 3.3 70B > Qwen 2.5 72B > 32B models

Coding (HumanEval-like):
DeepSeek Coder V2 > Qwen 2.5 Coder > Llama 3.3 70B > CodeLlama

Instruction Following:
Llama 3.3 70B > Qwen 2.5 72B > Mistral Large > 32B models
```

## Model Families

### Meta Llama

| Model | Parameters | Context | Notes |
|-------|------------|---------|-------|
| Llama 3.2 | 1B, 3B, 8B | 128K | Efficient, mobile |
| Llama 3.3 | 70B | 128K | Latest, best 70B |
| Llama 3.1 | 8B, 70B, 405B | 128K | Full range |

### Qwen (Alibaba)

| Model | Parameters | Context | Notes |
|-------|------------|---------|-------|
| Qwen 2.5 | 0.5B-72B | 128K | Multilingual |
| Qwen 2.5 Coder | 1.5B-32B | 128K | Code specialized |
| Qwen 2.5 Math | 1.5B-72B | - | Math/reasoning |

### DeepSeek

| Model | Parameters | Context | Notes |
|-------|------------|---------|-------|
| DeepSeek V3 | 671B (MoE) | 128K | Latest flagship |
| DeepSeek Coder V2 | 16B, 236B | 128K | Code + reasoning |
| DeepSeek R1 | Various | - | Reasoning focused |

### Mistral

| Model | Parameters | Context | Notes |
|-------|------------|---------|-------|
| Mistral 7B | 7B | 32K | Efficient |
| Mixtral 8x7B | 47B (MoE) | 32K | MoE efficiency |
| Mistral Large 2 | 123B | 128K | Flagship |

## Practical Recommendations

### Single Model Setup

For a 128GB system running one model at a time:

```bash
# Best all-around
ollama pull llama3.3:70b-instruct-q4_K_M

# Best for coding
ollama pull deepseek-coder-v2:236b-q4_K_M  # If fits
ollama pull deepseek-coder-v2:16b          # Fallback
```

### Multi-Model Setup

Run specialized models for different tasks:

```bash
# Code assistant (keep loaded)
ollama pull qwen2.5-coder:32b-instruct-q5_K_M

# General chat (load on demand)
ollama pull llama3.3:70b-instruct-q4_K_M

# Embeddings (always available)
ollama pull nomic-embed-text
```

### Development vs Production

| Environment | Priority | Recommendation |
|-------------|----------|----------------|
| Development | Speed | 8-32B models, Q4-Q5 |
| Testing | Balance | 32-70B models, Q4-Q5 |
| Production | Quality | 70B+ models, Q5-Q6 |

## Version Considerations

### Instruct vs Base

- **Instruct/Chat**: Fine-tuned for conversation, use for most tasks
- **Base**: Raw model, use for fine-tuning or specialized prompting

```bash
# Use instruct versions
ollama pull llama3.3:70b-instruct-q4_K_M
# NOT
ollama pull llama3.3:70b-text-q4_K_M  # Base model
```

### Latest Versions

Check for updates periodically:

```bash
# Update Ollama models
ollama list  # Check installed
ollama pull llama3.3:70b  # Re-pull for updates
```

## See Also

- [Quantization](quantization.md) - Size vs quality tradeoffs
- [Memory Management](../performance/memory-management.md) - Fitting models
- [Inference Engines](../inference-engines/index.md) - Engine compatibility
- [Hugging Face](huggingface.md) - Downloading models
