# Multi-Modal AI

Multi-modal AI processes and generates multiple types of content: text, images, audio, and video.

## Capabilities

```
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Modal AI                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input Modalities              Output Modalities            │
│  ┌─────────────┐               ┌─────────────┐             │
│  │    Text     │──────────────>│    Text     │             │
│  ├─────────────┤               ├─────────────┤             │
│  │   Images    │──────────────>│   Images    │             │
│  ├─────────────┤      LLM      ├─────────────┤             │
│  │   Audio     │──────────────>│   Audio     │             │
│  ├─────────────┤               ├─────────────┤             │
│  │   Video     │──────────────>│   Video     │             │
│  └─────────────┘               └─────────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Local Multi-Modal Options

| Feature | Ollama | LocalAI | llama.cpp |
|---------|--------|---------|-----------|
| Vision (image input) | Yes | Yes | Yes |
| Image generation | No | Yes | No |
| Audio transcription | No | Yes | No |
| Text-to-speech | No | Yes | No |

## In This Section

| Document | Description |
|----------|-------------|
| [Vision](vision.md) | Image understanding with local models |
| [Audio](audio.md) | Speech-to-text and text-to-speech |
| [Image Generation](image-generation.md) | Local image generation |

## Vision Models

### With Ollama

```bash
# Pull a vision model
ollama pull llava
ollama pull llava-llama3
ollama pull moondream
```

```python
import ollama
import base64

# Encode image
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Query with image
response = ollama.chat(
    model="llava",
    messages=[{
        "role": "user",
        "content": "What's in this image?",
        "images": [image_data]
    }]
)

print(response["message"]["content"])
```

### With OpenAI-Compatible API

```python
from openai import OpenAI
import base64

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="llava",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            }
        ]
    }]
)

print(response.choices[0].message.content)
```

## Vision Models Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| moondream | 1.6B | Fast | Good | Quick descriptions |
| llava | 7B | Medium | Better | General vision |
| llava-llama3 | 8B | Medium | Better | Latest architecture |
| llava:34b | 34B | Slow | Best | Detailed analysis |

## Quick Vision Examples

### Image Description

```python
def describe_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": "Describe this image in detail.",
            "images": [image_data]
        }]
    )
    return response["message"]["content"]
```

### OCR (Text Extraction)

```python
def extract_text(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": "Extract all text visible in this image. Return only the text, nothing else.",
            "images": [image_data]
        }]
    )
    return response["message"]["content"]
```

### Image Q&A

```python
def ask_about_image(image_path: str, question: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": question,
            "images": [image_data]
        }]
    )
    return response["message"]["content"]

# Example
answer = ask_about_image("chart.png", "What is the trend shown in this chart?")
```

## Audio with LocalAI

### Installation

```yaml
# docker-compose.yml
services:
  localai:
    image: localai/localai:latest-gpu-nvidia-cuda-12
    ports:
      - "8080:8080"
    volumes:
      - ./models:/build/models
    environment:
      - THREADS=4
      - DEBUG=true
```

### Speech-to-Text (Whisper)

```bash
# Download Whisper model
curl -L "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin" \
  -o models/whisper-base.bin
```

```python
import requests

def transcribe_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        response = requests.post(
            "http://localhost:8080/v1/audio/transcriptions",
            files={"file": f},
            data={"model": "whisper-base"}
        )
    return response.json()["text"]

text = transcribe_audio("recording.wav")
```

### Text-to-Speech

```python
def text_to_speech(text: str, output_path: str):
    response = requests.post(
        "http://localhost:8080/tts",
        json={
            "input": text,
            "model": "en-us-amy-low"  # TTS model
        }
    )
    with open(output_path, "wb") as f:
        f.write(response.content)

text_to_speech("Hello, world!", "output.wav")
```

## Image Generation

### With LocalAI (Stable Diffusion)

```python
def generate_image(prompt: str, output_path: str):
    response = requests.post(
        "http://localhost:8080/v1/images/generations",
        json={
            "prompt": prompt,
            "size": "512x512"
        }
    )

    # Decode and save image
    import base64
    image_data = response.json()["data"][0]["b64_json"]
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(image_data))

generate_image("A mountain landscape at sunset", "mountain.png")
```

## Combining Modalities

### Vision + RAG

```python
def vision_rag_query(image_path: str, documents_context: str, question: str) -> str:
    """Combine image understanding with document context."""

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": f"""Context from documents:
{documents_context}

Based on both the image and the context above, {question}""",
            "images": [image_data]
        }]
    )
    return response["message"]["content"]
```

### Audio + Text Pipeline

```python
def audio_to_response(audio_path: str) -> tuple[str, str]:
    """Transcribe audio and generate response."""

    # Transcribe
    transcript = transcribe_audio(audio_path)

    # Generate response
    response = ollama.chat(
        model="llama3.2",
        messages=[{
            "role": "user",
            "content": transcript
        }]
    )

    return transcript, response["message"]["content"]
```

## Hardware Requirements

### Vision Models

| Model | VRAM | RAM |
|-------|------|-----|
| moondream | 2GB | 4GB |
| llava (7B) | 6GB | 8GB |
| llava (13B) | 10GB | 16GB |
| llava (34B) | 20GB | 32GB |

### Audio Models

| Model | VRAM | RAM |
|-------|------|-----|
| Whisper tiny | 1GB | 2GB |
| Whisper base | 1GB | 2GB |
| Whisper medium | 2GB | 4GB |
| Whisper large | 4GB | 8GB |

## See Also

- [Vision Guide](vision.md)
- [Audio Guide](audio.md)
- [Ollama Integration](../inference-engines/ollama.md)
- [LocalAI Guide](../api-serving/localai.md)
