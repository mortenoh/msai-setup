# Context Optimization

Balance context length, memory usage, and performance.

## Understanding Context

Context length determines:

- How much conversation history the model "remembers"
- How much code/text can be analyzed at once
- Memory requirements for KV cache
- Time to first token (longer context = slower)

## Context vs Memory

### KV Cache Growth

```
KV Cache Size ≈ 2 × num_layers × context_length × hidden_size × bytes_per_param

Example (70B model, FP16 KV cache):
- 80 layers × 8192 context × 8192 hidden × 2 bytes × 2 (K+V)
- ≈ 21 GB for 8K context

Scaling:
- 4K context:  ~10 GB KV cache
- 8K context:  ~21 GB KV cache
- 16K context: ~42 GB KV cache
- 32K context: ~84 GB KV cache
```

### Memory Budget

For 128GB system with 70B Q4 model:

| Component | Memory | Notes |
|-----------|--------|-------|
| Model weights | 43GB | Q4_K_M |
| System reserve | 16GB | OS, apps |
| Available for KV | ~69GB | Context budget |
| Max context | ~32K | With headroom |

## Context Length Settings

### llama.cpp

```bash
# Set context length
./llama-server -m model.gguf -c 8192

# Long context with flash attention
./llama-server -m model.gguf -c 32768 --flash-attn
```

### Ollama

```bash
# Via API
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3:70b", "options": {"num_ctx": 8192}}'

# In Modelfile
PARAMETER num_ctx 16384
```

### Per-Request

```json
{
  "model": "llama3.3",
  "messages": [...],
  "options": {
    "num_ctx": 16384
  }
}
```

## Flash Attention

Reduces memory usage for long contexts:

### Enable in llama.cpp

```bash
# Compile with flash attention
cmake -B build -DGGML_FLASH_ATTN=ON

# Run with flash attention
./llama-server -m model.gguf -c 32768 --flash-attn
```

### Benefits

| Context | Without Flash | With Flash | Savings |
|---------|---------------|------------|---------|
| 8K | 21GB | 15GB | 29% |
| 16K | 42GB | 25GB | 40% |
| 32K | 84GB | 45GB | 46% |

## RoPE Scaling

Extend context beyond trained length:

### Scaling Methods

| Method | Description | Quality |
|--------|-------------|---------|
| Linear | Simple scaling | Good for 2-4x |
| NTK-aware | Better quality | Good for 4-8x |
| YaRN | Best quality | Best for 8x+ |

### Configuration

```bash
# llama.cpp with RoPE scaling
./llama-server \
  -m model.gguf \
  -c 32768 \
  --rope-freq-base 1000000 \
  --rope-freq-scale 0.5
```

### Caveats

- Quality degrades beyond trained context
- Test carefully for your use case
- Some models have native long context (128K)

## Optimizing for Use Cases

### Chat/Conversation

- 4-8K context usually sufficient
- Lower context = faster responses
- Implement conversation summarization for long sessions

```python
def optimize_conversation(messages, max_tokens=4000):
    """Keep recent messages within context limit."""
    # Estimate tokens (rough)
    total = sum(len(m['content']) // 4 for m in messages)

    while total > max_tokens and len(messages) > 2:
        messages.pop(1)  # Remove oldest (keep system)
        total = sum(len(m['content']) // 4 for m in messages)

    return messages
```

### Code Analysis

- Larger context for full file analysis
- 16-32K for multi-file context
- Consider chunking large files

```python
def chunk_code(code, chunk_size=8000, overlap=500):
    """Split code into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(code):
        end = start + chunk_size
        chunks.append(code[start:end])
        start = end - overlap
    return chunks
```

### RAG Applications

- Smaller context per query
- Rely on retrieval instead of context
- 4-8K usually sufficient

## Context Window Strategies

### Sliding Window

Keep only recent context:

```python
def sliding_window(messages, max_messages=20):
    """Keep only recent messages."""
    if len(messages) <= max_messages:
        return messages
    # Keep system prompt + recent
    return [messages[0]] + messages[-(max_messages-1):]
```

### Summarization

Summarize old context:

```python
def summarize_old_context(messages, summarizer):
    """Summarize old messages, keep recent."""
    if len(messages) < 20:
        return messages

    old = messages[1:-10]  # Old messages (skip system)
    recent = messages[-10:]  # Recent messages

    summary = summarizer(old)
    return [messages[0], {"role": "system", "content": f"Previous context summary: {summary}"}] + recent
```

### Smart Truncation

Truncate intelligently:

```python
def smart_truncate(messages, max_tokens=8000):
    """Truncate while preserving important messages."""
    # Always keep: system prompt, last N messages
    # Score middle messages by importance
    # Remove lowest-scored first
    pass
```

## Monitoring Context Usage

### Check Current Usage

```bash
# llama.cpp metrics
curl http://localhost:8080/metrics | grep context

# Ollama
ollama ps  # Shows context usage
```

### Track Over Time

```python
def track_context(messages):
    """Log context size over time."""
    import logging
    tokens = sum(len(m['content'].split()) * 1.3 for m in messages)
    logging.info(f"Context size: ~{int(tokens)} tokens")
```

## Performance Impact

### Context Length vs Speed

| Context | Prompt Eval | Generation | TTFT |
|---------|-------------|------------|------|
| 2K | Fast | Fast | <100ms |
| 8K | Good | Good | <200ms |
| 16K | Slower | Good | <400ms |
| 32K | Much slower | Good | <800ms |

### Recommendation

```
Default: 8192 (good balance)
Chat: 4096-8192
Code: 16384-32768
RAG: 4096-8192
Long docs: 32768+ (with flash attention)
```

## Troubleshooting

### Out of Memory

```bash
# Reduce context
-c 4096  # Instead of 8192

# Enable flash attention
--flash-attn

# Use smaller quantization
model-q4_k_s.gguf  # Instead of q4_k_m
```

### Slow First Token

- Reduce context length
- Use flash attention
- Pre-compute KV cache for static prompts

### Context Overflow Errors

- Implement token counting
- Truncate messages before sending
- Use model's actual context limit

## See Also

- [Performance Index](index.md) - Overview
- [Memory Management](memory-management.md) - Memory optimization
- [Benchmarking](benchmarking.md) - Measuring impact
- [Quantization](../models/quantization.md) - Size reduction
