# Fine-Tuning LLMs

Fine-tuning adapts pre-trained models to specific tasks or domains, improving performance on your use case.

## When to Fine-Tune

Fine-tuning is useful when:

- **Domain expertise needed** - Legal, medical, technical jargon
- **Consistent style required** - Specific tone, format, or structure
- **Task-specific behavior** - Classification, extraction, structured output
- **RAG isn't enough** - Model needs to internalize knowledge, not just retrieve it

## Fine-Tuning vs Alternatives

| Approach | Best For | Effort | Cost |
|----------|----------|--------|------|
| Prompt engineering | Quick iterations | Low | Low |
| RAG | Dynamic knowledge | Medium | Medium |
| Fine-tuning | Behavior change | High | High |
| Continued pre-training | Large domain shift | Very high | Very high |

## Methods

### Full Fine-Tuning

Updates all model weights:
- Requires significant GPU memory (model size + gradients + optimizer states)
- Best results but most resource-intensive
- Risk of catastrophic forgetting

### LoRA (Low-Rank Adaptation)

Updates small adapter layers:
- Much lower memory requirements
- Faster training
- Can swap adapters at inference time
- Most practical for local fine-tuning

### QLoRA

Quantized LoRA:
- Combines 4-bit quantization with LoRA
- Enables fine-tuning on consumer GPUs
- Minimal quality loss

## In This Section

| Document | Description |
|----------|-------------|
| [LoRA](lora.md) | Low-Rank Adaptation fine-tuning |
| [Training](training.md) | Preparing data and running training |
| [Inference](inference.md) | Using fine-tuned models |

## Hardware Requirements

### Minimum (QLoRA, 7B model)

- GPU: 8GB VRAM (RTX 3070 or better)
- RAM: 16GB
- Storage: 50GB

### Recommended (LoRA, 7B model)

- GPU: 24GB VRAM (RTX 3090/4090)
- RAM: 32GB
- Storage: 100GB

### Full Fine-Tuning (7B model)

- GPU: 80GB+ VRAM (A100, H100)
- RAM: 64GB+
- Storage: 200GB+

## Quick Start

### Unsloth (Fastest)

```python
from unsloth import FastLanguageModel

# Load model with 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
)

# Train (see training.md for details)
```

### Using with Ollama

After fine-tuning, convert and use with Ollama:

```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM ./model-merged
TEMPLATE "{{ .Prompt }}"
EOF

# Create Ollama model
ollama create my-finetuned -f Modelfile

# Run
ollama run my-finetuned
```

## Common Use Cases

### Instruction Following

Train the model to follow specific instruction formats:

```json
{"instruction": "Summarize in 3 bullet points", "input": "...", "output": "..."}
```

### Code Generation

Specialize for a programming language or framework:

```json
{"prompt": "Write a Python function to...", "completion": "def ..."}
```

### Classification

Train for consistent categorization:

```json
{"text": "Product review...", "label": "positive"}
```

### Structured Output

Train to produce specific JSON structures:

```json
{"input": "Extract entities from: ...", "output": "{\"name\": \"...\", \"date\": \"...\"}"}
```

## See Also

- [LoRA Guide](lora.md)
- [Training Guide](training.md)
- [Models Overview](../models/index.md)
- [RAG](../rag/index.md) - Alternative to fine-tuning
