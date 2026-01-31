# LoRA Fine-Tuning

LoRA (Low-Rank Adaptation) enables efficient fine-tuning by training small adapter layers instead of the full model.

## How LoRA Works

```
Original weights (frozen): W (d x d matrix)
LoRA adapters (trainable): A (d x r) and B (r x d) where r << d

Forward pass: output = W*x + (A*B)*x
                       └─────┘   └─────┘
                       frozen   trainable

Example: d=4096, r=16
- Full fine-tuning: 4096 x 4096 = 16M params per layer
- LoRA: (4096 x 16) + (16 x 4096) = 131K params per layer
```

## Installation

```bash
# Core libraries
pip install torch transformers datasets accelerate peft bitsandbytes

# For faster training
pip install unsloth
```

## Basic LoRA with PEFT

### Load Model with Quantization

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    quantization_config=bnb_config,
    device_map="auto",
)

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B")
tokenizer.pad_token = tokenizer.eos_token
```

### Configure LoRA

```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Prepare model for training
model = prepare_model_for_kbit_training(model)

# LoRA configuration
lora_config = LoraConfig(
    r=16,                     # Rank (lower = fewer params, faster)
    lora_alpha=32,            # Scaling factor
    target_modules=[          # Which layers to adapt
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 6,553,600 || all params: 3,219,546,112 || trainable%: 0.20%
```

## LoRA Parameters

### Rank (r)

Controls the size of the adapter matrices:

| Rank | Memory | Quality | Use Case |
|------|--------|---------|----------|
| 8 | Lowest | Basic | Simple tasks |
| 16 | Low | Good | General fine-tuning |
| 32 | Medium | Better | Complex tasks |
| 64 | Higher | Best | Maximum quality |

### Alpha

Scaling factor for LoRA updates:

```
effective_weight = (alpha / r) * (A * B)
```

Common settings:
- `alpha = r` (scaling = 1)
- `alpha = 2*r` (scaling = 2, stronger adaptation)

### Target Modules

Which layers to add adapters to:

```python
# Attention only (faster, less expressive)
target_modules = ["q_proj", "v_proj"]

# Full attention
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

# Attention + MLP (most expressive)
target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"
]
```

### Dropout

Regularization during training:

- `0.0` - No dropout (faster convergence)
- `0.05` - Light regularization
- `0.1` - Stronger regularization (prevent overfitting)

## Unsloth (Recommended)

Unsloth provides 2x faster training with optimized kernels:

```python
from unsloth import FastLanguageModel

# Load model (automatically applies optimizations)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    dtype=None,  # Auto-detect
    load_in_4bit=True,
)

# Apply LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",  # Memory optimization
    random_state=42,
)
```

## Saving and Loading

### Save Adapters Only

```python
# Save just the LoRA weights (small, ~50MB)
model.save_pretrained("./lora-adapters")
tokenizer.save_pretrained("./lora-adapters")
```

### Load Adapters

```python
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B")

# Load adapters
model = PeftModel.from_pretrained(base_model, "./lora-adapters")
```

### Merge Adapters

Combine adapters with base model for inference:

```python
# Merge LoRA into base model
merged_model = model.merge_and_unload()

# Save merged model
merged_model.save_pretrained("./merged-model")
tokenizer.save_pretrained("./merged-model")
```

## Multiple Adapters

Train and swap different adapters:

```python
from peft import PeftModel

# Load base model
base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B")

# Load first adapter
model = PeftModel.from_pretrained(base, "./adapter-code", adapter_name="code")

# Load second adapter
model.load_adapter("./adapter-chat", adapter_name="chat")

# Switch between adapters
model.set_adapter("code")
# ... generate code ...

model.set_adapter("chat")
# ... generate chat ...
```

## Convert to GGUF

For use with llama.cpp or Ollama:

```bash
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Convert merged model
python convert_hf_to_gguf.py ../merged-model --outfile model.gguf

# Quantize
./llama-quantize model.gguf model-q4_k_m.gguf Q4_K_M
```

## Use with Ollama

```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM ./model-q4_k_m.gguf
TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>"""
PARAMETER stop "<|end|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|assistant|>"
EOF

# Create model
ollama create my-model -f Modelfile

# Run
ollama run my-model
```

## Common Issues

### Out of Memory

```python
# Reduce batch size
training_args = TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,  # Effective batch = 8
)

# Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Use lower precision
model = model.to(torch.bfloat16)
```

### Adapter Not Applying

```python
# Ensure model is in training mode
model.train()

# Check trainable parameters
model.print_trainable_parameters()
```

### Quality Issues

- Increase rank (r=32 or r=64)
- Add more target modules
- Train longer with lower learning rate
- Use more/better training data

## See Also

- [Training Guide](training.md)
- [Inference Guide](inference.md)
- [Models Overview](../models/index.md)
