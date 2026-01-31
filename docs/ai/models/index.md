# Model Management

Understanding model selection, formats, and acquisition for local LLM inference.

## Model Ecosystem Overview

```
┌────────────────────────────────────────────────────────────┐
│                     Model Sources                          │
├────────────────────────────────────────────────────────────┤
│  Hugging Face    │    Ollama Library    │   Direct Download│
│  (hub.hf.co)     │    (ollama.com)      │   (vendors)      │
└────────┬─────────┴──────────┬───────────┴────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────────────────────────────────────────────────┐
│                     Model Formats                          │
├────────────────────────────────────────────────────────────┤
│  GGUF           │  Safetensors      │  PyTorch (.bin)     │
│  (llama.cpp,    │  (vLLM, MLX,      │  (Legacy,           │
│   Ollama)       │   transformers)   │   conversion req)   │
└────────┬────────┴─────────┬─────────┴──────────┬───────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌────────────────────────────────────────────────────────────┐
│                   Inference Engines                        │
├────────────────────────────────────────────────────────────┤
│  llama.cpp      │  Ollama           │  vLLM              │
│  (GGUF native)  │  (GGUF native)    │  (Safetensors)     │
└────────────────────────────────────────────────────────────┘
```

## Quick Reference

### Models for 128GB System

| Model | Parameters | Quantization | VRAM | Best For |
|-------|------------|--------------|------|----------|
| Llama 3.2 8B | 8B | Q8_0 | ~10GB | Fast responses |
| Qwen 2.5 32B | 32B | Q5_K_M | ~25GB | Balanced |
| DeepSeek Coder V2 | 16B/236B | Q4_K_M | ~12GB/~140GB | Coding |
| Llama 3.3 70B | 70B | Q4_K_M | ~43GB | General purpose |
| Qwen 2.5 72B | 72B | Q4_K_M | ~45GB | Multilingual |
| Llama 3.1 405B | 405B | Q2_K | ~95GB | Maximum capability |

### Format Selection

| Format | Use With | Pros | Cons |
|--------|----------|------|------|
| GGUF | llama.cpp, Ollama | Quantized, small | Limited to llama.cpp ecosystem |
| Safetensors | vLLM, transformers | Safe, fast loading | Larger files |
| AWQ | vLLM | Fast inference | NVIDIA only |
| GPTQ | vLLM, transformers | Wide support | Slightly slower |

## Model Categories

### General Purpose

| Model | Strengths | Size Range |
|-------|-----------|------------|
| Llama 3.3 | Reasoning, instruction following | 70B |
| Qwen 2.5 | Multilingual, long context | 0.5B-72B |
| Mistral Large | European languages, reasoning | 123B |
| Gemma 2 | Efficient, well-tuned | 2B-27B |

### Code-Specialized

| Model | Languages | Notes |
|-------|-----------|-------|
| DeepSeek Coder V2 | Python, TypeScript, Go, Rust | Fill-in-middle support |
| Qwen 2.5 Coder | Python, JavaScript | Strong completion |
| CodeLlama | Python, C++, Java | Based on Llama 2 |
| StarCoder2 | 80+ languages | Open training data |

### Domain-Specific

| Model | Domain | Notes |
|-------|--------|-------|
| Meditron | Medical | Llama-based |
| Lawyer LLM | Legal | Document analysis |
| FinGPT | Finance | Market analysis |

## Storage Layout

Recommended ZFS dataset structure:

```
tank/ai/models/
├── gguf/              # GGUF format models
│   ├── llama-3.3-70b-q4_k_m.gguf
│   └── deepseek-coder-v2-16b-q5_k_m.gguf
├── huggingface/       # HF cache directory
│   └── hub/
│       └── models--meta-llama--Llama-3.3-70B-Instruct/
└── ollama/            # Ollama model storage
    └── models/
        └── blobs/
```

See [Model Volumes](../containers/model-volumes.md) for ZFS configuration.

## Topics

<div class="grid cards" markdown>

-   :material-brain: **Choosing Models**

    ---

    Model selection criteria for different use cases

    [:octicons-arrow-right-24: Selection guide](choosing-models.md)

-   :material-package-down: **Quantization**

    ---

    Understanding Q4, Q5, Q6, Q8 and their tradeoffs

    [:octicons-arrow-right-24: Quantization guide](quantization.md)

-   :material-cloud-download: **Hugging Face**

    ---

    Downloading models with huggingface-cli

    [:octicons-arrow-right-24: HF downloads](huggingface.md)

-   :material-file-cog: **GGUF Formats**

    ---

    GGUF file format and conversion

    [:octicons-arrow-right-24: GGUF details](gguf-formats.md)

</div>

## See Also

- [Inference Engines](../inference-engines/index.md) - Which engine for which format
- [Memory Management](../performance/memory-management.md) - Fitting models in memory
- [Model Volumes](../containers/model-volumes.md) - Storage configuration
