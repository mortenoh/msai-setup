# Fine-Tuning Training Guide

Preparing data and running training for LLM fine-tuning.

## Data Preparation

### Dataset Formats

#### Instruction Format (Alpaca-style)

```json
[
  {
    "instruction": "Summarize the following text",
    "input": "Long text to summarize...",
    "output": "Concise summary..."
  },
  {
    "instruction": "Translate to French",
    "input": "Hello, how are you?",
    "output": "Bonjour, comment allez-vous?"
  }
]
```

#### Chat Format

```json
[
  {
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is Python?"},
      {"role": "assistant", "content": "Python is a programming language..."}
    ]
  }
]
```

#### Completion Format

```json
[
  {"text": "<s>[INST] Question here [/INST] Answer here</s>"},
  {"text": "<s>[INST] Another question [/INST] Another answer</s>"}
]
```

### Data Quality Guidelines

1. **Quantity**: 100-10,000 examples (more isn't always better)
2. **Quality**: High-quality examples matter more than quantity
3. **Diversity**: Cover the range of expected inputs
4. **Consistency**: Use consistent formatting throughout
5. **Length**: Match expected input/output lengths in production

### Loading Data

```python
from datasets import load_dataset, Dataset
import json

# From JSON file
dataset = load_dataset("json", data_files="training_data.json", split="train")

# From Hugging Face
dataset = load_dataset("databricks/dolly-15k", split="train")

# From Python dict
data = [
    {"instruction": "...", "input": "...", "output": "..."},
    # ...
]
dataset = Dataset.from_list(data)
```

### Formatting Function

```python
def format_instruction(example):
    """Format example into prompt template."""
    if example.get("input"):
        text = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{example["instruction"]}

### Input:
{example["input"]}

### Response:
{example["output"]}"""
    else:
        text = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{example["instruction"]}

### Response:
{example["output"]}"""
    return {"text": text}

# Apply formatting
dataset = dataset.map(format_instruction)
```

### Chat Template Formatting

```python
def format_chat(example):
    """Format using tokenizer's chat template."""
    messages = example["messages"]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}

dataset = dataset.map(format_chat)
```

## Training with SFTTrainer

### Basic Training

```python
from transformers import TrainingArguments
from trl import SFTTrainer

training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.03,
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,  # or bf16=True
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    dataset_text_field="text",
    max_seq_length=2048,
    packing=True,  # Pack multiple examples into one sequence
)

trainer.train()
```

### Training with Unsloth

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# Load model (see lora.md)
model, tokenizer = FastLanguageModel.from_pretrained(...)
model = FastLanguageModel.get_peft_model(...)

training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=5,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=42,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=training_args,
)

trainer_stats = trainer.train()
```

## Hyperparameters

### Learning Rate

| Model Size | Learning Rate |
|------------|---------------|
| < 1B | 1e-4 to 5e-4 |
| 1B - 7B | 1e-4 to 2e-4 |
| 7B - 13B | 5e-5 to 2e-4 |
| > 13B | 1e-5 to 1e-4 |

### Batch Size

Effective batch size = `per_device_batch_size * gradient_accumulation_steps * num_gpus`

```python
# Memory limited: small batch, more accumulation
per_device_train_batch_size=1
gradient_accumulation_steps=16

# More memory: larger batch, less accumulation
per_device_train_batch_size=8
gradient_accumulation_steps=2
```

### Epochs

- **1-3 epochs**: Most fine-tuning tasks
- **3-5 epochs**: Smaller datasets (< 1000 examples)
- **> 5 epochs**: Risk of overfitting, use validation set

### Warmup

- Linear warmup for 3-10% of total steps
- Helps stabilize early training

```python
warmup_ratio=0.03  # 3% of steps
# or
warmup_steps=100
```

## Memory Optimization

### Gradient Checkpointing

Trade compute for memory:

```python
model.gradient_checkpointing_enable()

# Or in Unsloth
model = FastLanguageModel.get_peft_model(
    model,
    use_gradient_checkpointing="unsloth",
    ...
)
```

### Mixed Precision

```python
training_args = TrainingArguments(
    fp16=True,   # For older GPUs
    bf16=True,   # For Ampere+ (RTX 30xx, 40xx)
    ...
)
```

### 8-bit Optimizer

```python
training_args = TrainingArguments(
    optim="adamw_8bit",
    ...
)
```

## Validation

### Train/Validation Split

```python
dataset = dataset.train_test_split(test_size=0.1)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    ...
)
```

### Evaluation During Training

```python
training_args = TrainingArguments(
    evaluation_strategy="steps",
    eval_steps=100,
    ...
)
```

## Monitoring

### Weights & Biases

```python
import wandb

wandb.init(project="fine-tuning")

training_args = TrainingArguments(
    report_to="wandb",
    run_name="llama-3-lora",
    ...
)
```

### TensorBoard

```python
training_args = TrainingArguments(
    logging_dir="./logs",
    report_to="tensorboard",
    ...
)
```

```bash
tensorboard --logdir ./logs
```

## Checkpointing

### Save Strategy

```python
training_args = TrainingArguments(
    save_strategy="steps",
    save_steps=500,
    save_total_limit=3,  # Keep only last 3
    ...
)
```

### Resume Training

```python
trainer.train(resume_from_checkpoint="./output/checkpoint-500")
```

## Full Training Script

```python
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Config
MODEL_NAME = "unsloth/llama-3-8b-bnb-4bit"
MAX_SEQ_LENGTH = 2048
OUTPUT_DIR = "./output"

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

# Apply LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# Load and format data
dataset = load_dataset("json", data_files="data.json", split="train")

def format_example(example):
    return {"text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"}

dataset = dataset.map(format_example)
dataset = dataset.train_test_split(test_size=0.1)

# Training args
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.03,
    weight_decay=0.01,
    logging_steps=10,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    optim="adamw_8bit",
)

# Train
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    tokenizer=tokenizer,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    packing=True,
)

trainer.train()

# Save
model.save_pretrained(f"{OUTPUT_DIR}/lora-adapters")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/lora-adapters")
```

## See Also

- [LoRA Guide](lora.md)
- [Inference Guide](inference.md)
- [Models Overview](../models/index.md)
