# GGUF Formats

Understanding the GGUF file format used by llama.cpp and Ollama.

## Overview

GGUF (GPT-Generated Unified Format) is the standard format for quantized LLMs:

- **Single file** - Model, tokenizer, and metadata in one file
- **Quantization** - Built-in support for various precision levels
- **Portability** - Works across llama.cpp, Ollama, LM Studio
- **Efficiency** - Memory-mapped loading, fast startup

## File Structure

```
GGUF File Layout:
┌─────────────────────────────────────────┐
│             Magic Number                │  4 bytes: "GGUF"
├─────────────────────────────────────────┤
│             Version                     │  4 bytes: v3
├─────────────────────────────────────────┤
│             Tensor Count                │
├─────────────────────────────────────────┤
│         Metadata KV Count               │
├─────────────────────────────────────────┤
│                                         │
│           Metadata Section              │  Architecture, tokenizer,
│         (Key-Value Pairs)               │  quantization info, etc.
│                                         │
├─────────────────────────────────────────┤
│           Tensor Info Section           │  Names, shapes, offsets
├─────────────────────────────────────────┤
│                                         │
│                                         │
│            Tensor Data                  │  Actual weights
│           (Bulk of file)                │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

## Naming Conventions

### Standard Pattern

```
{model}-{size}-{variant}-{quantization}.gguf

Examples:
llama-3.3-70b-instruct-q4_k_m.gguf
│      │  │   │         └── Quantization type
│      │  │   └── Variant (instruct, chat, base)
│      │  └── Parameter count (70 billion)
│      └── Model version
└── Model family
```

### Split Files

Large models split across multiple files:

```
llama-3.1-405b-instruct-q4_k_m-00001-of-00004.gguf
llama-3.1-405b-instruct-q4_k_m-00002-of-00004.gguf
llama-3.1-405b-instruct-q4_k_m-00003-of-00004.gguf
llama-3.1-405b-instruct-q4_k_m-00004-of-00004.gguf
```

llama.cpp automatically loads all parts when you specify the first file.

## Inspecting GGUF Files

### Using llama.cpp

```bash
# Show model info
./llama-cli --model model.gguf --version

# Detailed metadata
./llama-gguf-info model.gguf
```

### Using Python

```bash
pip install gguf
```

```python
from gguf import GGUFReader

reader = GGUFReader("model.gguf")

# Print metadata
for key, value in reader.metadata.items():
    print(f"{key}: {value}")

# Architecture info
print(reader.metadata.get("general.architecture"))
print(reader.metadata.get("general.name"))
```

### Key Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `general.architecture` | Model type | `llama` |
| `general.name` | Model name | `Llama-3.3-70B` |
| `general.file_type` | Quantization | `Q4_K_M` |
| `llama.context_length` | Max context | `131072` |
| `llama.embedding_length` | Hidden size | `8192` |
| `llama.block_count` | Layer count | `80` |
| `tokenizer.ggml.model` | Tokenizer type | `llama` |

## Converting to GGUF

### From Safetensors/PyTorch

Using llama.cpp convert script:

```bash
cd llama.cpp

# Convert HuggingFace model to GGUF (FP16)
python convert_hf_to_gguf.py \
  /path/to/hf/model \
  --outfile model-f16.gguf \
  --outtype f16

# Then quantize
./quantize model-f16.gguf model-q4_k_m.gguf Q4_K_M
```

### Direct Conversion + Quantization

```bash
python convert_hf_to_gguf.py \
  /path/to/hf/model \
  --outfile model-q4_k_m.gguf \
  --outtype q4_k_m
```

### From Other Formats

```bash
# Convert older GGML to GGUF
./gguf-convert model.ggml model.gguf
```

## Quantization Process

### Basic Quantization

```bash
# Available types
./quantize --help

# Quantize to Q4_K_M
./quantize model-f16.gguf model-q4_k_m.gguf Q4_K_M

# Quantize to Q5_K_M
./quantize model-f16.gguf model-q5_k_m.gguf Q5_K_M
```

### With Importance Matrix

For better quality at same size:

```bash
# Generate importance matrix from calibration data
./imatrix \
  -m model-f16.gguf \
  -f calibration.txt \
  -o imatrix.dat \
  --chunks 100

# Quantize with imatrix
./quantize \
  model-f16.gguf \
  model-q4_k_m-imat.gguf \
  Q4_K_M \
  --imatrix imatrix.dat
```

### Calibration Data

Use representative text for your use case:

```bash
# For code models, use code samples
# For chat models, use conversation samples

# Example: Download wiki text
wget https://huggingface.co/datasets/wikitext/resolve/main/wikitext-2-v1/wiki.test.raw
```

## Quantization Types Reference

### Standard Types

| Type | Bits/Weight | Best For |
|------|-------------|----------|
| `F32` | 32 | Reference only |
| `F16` | 16 | Maximum quality |
| `Q8_0` | 8 | High quality |
| `Q6_K` | 6.5 | Very good quality |
| `Q5_K_M` | 5.5 | Good quality |
| `Q5_K_S` | 5.0 | Smaller Q5 |
| `Q4_K_M` | 4.5 | **Recommended** |
| `Q4_K_S` | 4.25 | Smaller Q4 |
| `Q4_0` | 4.0 | Legacy |
| `Q3_K_M` | 3.5 | Memory constrained |
| `Q3_K_S` | 3.0 | Smaller Q3 |
| `Q2_K` | 2.5 | Extreme compression |

### I-Quant Types

| Type | Description |
|------|-------------|
| `IQ4_NL` | 4-bit non-linear |
| `IQ4_XS` | 4-bit extra small |
| `IQ3_XS` | 3-bit extra small |
| `IQ3_XXS` | 3-bit extra extra small |
| `IQ2_XXS` | 2-bit extra extra small |

## Verifying GGUF Files

### Check Integrity

```bash
# Verify file is valid GGUF
./llama-cli --model model.gguf --version

# Quick test inference
./llama-cli -m model.gguf -p "Hello" -n 10
```

### Compare Sizes

```bash
# Expected sizes for 70B model
ls -lh *.gguf

# F16:   ~140 GB
# Q8_0:  ~74 GB
# Q6_K:  ~57 GB
# Q5_K_M: ~48 GB
# Q4_K_M: ~43 GB
# Q3_K_M: ~35 GB
# Q2_K:  ~28 GB
```

## Importing to Ollama

### Create Modelfile

```dockerfile
# Modelfile
FROM /tank/ai/models/gguf/llama-3.3-70b-q4_k_m.gguf

# Set chat template
TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

{{ .Response }}<|eot_id|>"""

PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"
```

### Import Model

```bash
# Create Ollama model from GGUF
ollama create my-llama -f Modelfile

# Verify
ollama list
ollama run my-llama
```

## Storage Recommendations

### ZFS Dataset

```bash
# Create dataset optimized for large files
zfs create -o recordsize=1M -o compression=off tank/ai/models/gguf
```

### Organization

```
/tank/ai/models/gguf/
├── llama/
│   ├── llama-3.3-70b-instruct-q4_k_m.gguf
│   └── llama-3.2-8b-instruct-q8_0.gguf
├── qwen/
│   ├── qwen2.5-72b-instruct-q4_k_m.gguf
│   └── qwen2.5-coder-32b-q5_k_m.gguf
└── deepseek/
    └── deepseek-coder-v2-16b-q8_0.gguf
```

## See Also

- [Quantization](quantization.md) - Quantization details
- [Hugging Face](huggingface.md) - Downloading GGUF files
- [llama.cpp](../inference-engines/llama-cpp.md) - Using GGUF files
- [Ollama](../inference-engines/ollama.md) - Importing GGUF to Ollama
- [Model Volumes](../containers/model-volumes.md) - Storage configuration
