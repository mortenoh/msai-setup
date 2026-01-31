# Fine-Tuned Model Inference

Using your fine-tuned models for inference.

## Loading Fine-Tuned Models

### LoRA Adapters (Separate)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    torch_dtype=torch.float16,
    device_map="auto",
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B")

# Load LoRA adapters
model = PeftModel.from_pretrained(base_model, "./lora-adapters")
model.eval()
```

### Merged Model

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load merged model directly
model = AutoModelForCausalLM.from_pretrained(
    "./merged-model",
    torch_dtype=torch.float16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("./merged-model")
model.eval()
```

### With Quantization

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    "./merged-model",
    quantization_config=bnb_config,
    device_map="auto",
)
```

## Generation

### Basic Generation

```python
def generate(prompt: str, max_tokens: int = 256) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response[len(prompt):]  # Remove prompt from output

# Use
prompt = """### Instruction:
Summarize the following text in one sentence.

### Input:
Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.

### Response:
"""

response = generate(prompt)
print(response)
```

### Streaming Generation

```python
from transformers import TextIteratorStreamer
from threading import Thread

def stream_generate(prompt: str, max_tokens: int = 256):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True
    )

    generation_kwargs = {
        **inputs,
        "max_new_tokens": max_tokens,
        "temperature": 0.7,
        "streamer": streamer,
    }

    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for text in streamer:
        print(text, end="", flush=True)

    thread.join()
```

### Batch Generation

```python
def batch_generate(prompts: list[str], max_tokens: int = 256) -> list[str]:
    tokenizer.pad_token = tokenizer.eos_token

    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    responses = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return [r[len(p):] for r, p in zip(responses, prompts)]
```

## Converting to GGUF

For use with llama.cpp, Ollama, or other inference engines.

### Merge and Convert

```python
# First merge LoRA adapters
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    torch_dtype=torch.float16,
)
model = PeftModel.from_pretrained(base_model, "./lora-adapters")

# Merge and save
merged = model.merge_and_unload()
merged.save_pretrained("./merged-model")
tokenizer.save_pretrained("./merged-model")
```

### Convert to GGUF

```bash
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Install requirements
pip install -r requirements.txt

# Convert
python convert_hf_to_gguf.py ../merged-model --outfile model-f16.gguf

# Quantize
./llama-quantize model-f16.gguf model-q4_k_m.gguf Q4_K_M
```

### Quantization Options

| Quant | Size | Speed | Quality |
|-------|------|-------|---------|
| Q2_K | Smallest | Fastest | Lowest |
| Q3_K_M | Small | Fast | Low |
| Q4_K_M | Medium | Good | Good |
| Q5_K_M | Large | Slower | Better |
| Q6_K | Larger | Slow | High |
| Q8_0 | Largest | Slowest | Highest |

## Deploy with Ollama

### Create Modelfile

```dockerfile
# Modelfile
FROM ./model-q4_k_m.gguf

# Chat template (adjust for your model)
TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>"""

# Generation parameters
PARAMETER stop "<|end|>"
PARAMETER stop "<|user|>"
PARAMETER temperature 0.7
PARAMETER top_p 0.9

# System prompt (optional)
SYSTEM """You are a helpful assistant specialized in..."""
```

### Create and Run

```bash
# Create model
ollama create my-finetuned -f Modelfile

# Test
ollama run my-finetuned "Your prompt here"

# API access
curl http://localhost:11434/api/generate -d '{
  "model": "my-finetuned",
  "prompt": "Your prompt here",
  "stream": false
}'
```

## Deploy with vLLM

High-throughput serving:

```bash
# Install
pip install vllm

# Serve (merged model or GPTQ)
python -m vllm.entrypoints.openai.api_server \
    --model ./merged-model \
    --dtype float16 \
    --max-model-len 4096

# With quantization
python -m vllm.entrypoints.openai.api_server \
    --model ./merged-model \
    --quantization awq \
    --dtype float16
```

```python
# Client
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")

response = client.chat.completions.create(
    model="./merged-model",
    messages=[{"role": "user", "content": "Your prompt"}],
    temperature=0.7,
)
print(response.choices[0].message.content)
```

## FastAPI Server

```python
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

# Load model at startup
model = AutoModelForCausalLM.from_pretrained(
    "./merged-model",
    torch_dtype=torch.float16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("./merged-model")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    response: str

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    inputs = tokenizer(request.prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return GenerateResponse(response=response[len(request.prompt):])
```

## Performance Optimization

### Batch Requests

```python
# Accumulate requests and batch process
from asyncio import Queue, create_task, sleep

request_queue = Queue()
BATCH_SIZE = 8
BATCH_TIMEOUT = 0.1  # seconds

async def batch_processor():
    while True:
        batch = []
        while len(batch) < BATCH_SIZE:
            try:
                item = await asyncio.wait_for(
                    request_queue.get(),
                    timeout=BATCH_TIMEOUT
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break

        if batch:
            prompts = [item["prompt"] for item in batch]
            responses = batch_generate(prompts)
            for item, response in zip(batch, responses):
                item["future"].set_result(response)
```

### KV Cache

```python
# Enable KV cache for faster generation
outputs = model.generate(
    **inputs,
    use_cache=True,  # Default, but explicit
    ...
)
```

### Flash Attention

```python
# Install flash-attn
pip install flash-attn

# Load model with Flash Attention
model = AutoModelForCausalLM.from_pretrained(
    "./merged-model",
    torch_dtype=torch.float16,
    attn_implementation="flash_attention_2",
    device_map="auto",
)
```

## See Also

- [LoRA Guide](lora.md)
- [Training Guide](training.md)
- [Ollama Integration](../inference-engines/ollama/index.md)
- [vLLM Guide](../inference-engines/vllm/index.md)
