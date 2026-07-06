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

This build is an AMD Ryzen AI Max+ 395 (Strix Halo) APU with 128GB of unified LPDDR5X memory and no discrete GPU. Fine-tuning here runs on the iGPU through the ROCm build of PyTorch, drawing on the same unified-memory pool used for inference (see [Memory Configuration](../gpu/memory-configuration.md)). There is no NVIDIA card to add, so the practical question is "what fits in the unified memory budget" versus "what is worth renting cloud GPU time for".

!!! warning "Fine-tuning on ROCm is a rougher path than inference"
    The mainstream fine-tuning stack (Unsloth, `bitsandbytes` 4-bit QLoRA, FlashAttention) is CUDA-first and has partial or immature ROCm support on gfx1151. Plain Hugging Face `transformers` + `peft` LoRA on the ROCm build of PyTorch is the most reliable local route, but expect to hit rough edges. If you need turnkey QLoRA today, renting a cloud GPU is often less friction than making the AMD path work. See the caveats in [LoRA](lora.md) and [Training](training.md).

### Realistic to fine-tune locally on this box

- **LoRA / QLoRA on small-to-mid models (up to ~13B, and 70B at low ranks)** — 128GB of unified memory is generous for LoRA, which only trains small adapter layers. The constraint is ROCm tooling maturity, not memory. Start with a 3B-8B model to validate the pipeline.
- **RAM**: shared with the OS; the 128GB pool comfortably covers adapters, optimizer state, and activations for these sizes.
- **Storage**: keep datasets, checkpoints, and merged models on the `tank/ai` ZFS dataset (budget 50-200GB depending on model size).

### Better done as a rented cloud GPU

- **Full (all-weights) fine-tuning of 7B+ models** — needs model weights + gradients + optimizer states resident at once; even where memory allows, it is slow on this bandwidth-limited iGPU and leans on CUDA-only kernels. Rent an 80GB-class GPU (or a multi-GPU node) by the hour instead.
- **Anything depending on Unsloth or `bitsandbytes` 4-bit that you cannot get working on ROCm** — a short cloud rental is usually cheaper than the debugging time.

## Quick Start

### Unsloth (Fastest, but CUDA-focused)

!!! warning "Unsloth on this hardware"
    Unsloth is the fastest path on NVIDIA/CUDA GPUs, but has little to no ROCm support on gfx1151. On this AMD build, prefer plain `transformers` + `peft` LoRA on the ROCm build of PyTorch (see [LoRA](lora.md)). The snippet below is shown for reference and is not expected to work as-is on this box.

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
