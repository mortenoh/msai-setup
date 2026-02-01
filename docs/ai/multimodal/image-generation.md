# Local Image Generation

Generate images locally using Stable Diffusion and related models.

## Overview

Local image generation options:

| Tool | Ease of Use | Features | GPU Required |
|------|-------------|----------|--------------|
| Automatic1111 | Medium | Full featured | Yes |
| ComfyUI | Complex | Node-based workflows | Yes |
| Fooocus | Easy | Simplified interface | Yes |
| LocalAI | Easy | API-based | Optional |

## Stable Diffusion with Python

### Installation

```bash
pip install diffusers transformers accelerate torch
```

### Basic Generation

```python
from diffusers import StableDiffusionPipeline
import torch

# Load model
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe = pipe.to("cuda")

# Generate image
image = pipe(
    prompt="A serene mountain landscape at sunset, highly detailed",
    negative_prompt="blurry, low quality",
    num_inference_steps=50,
    guidance_scale=7.5
).images[0]

image.save("mountain.png")
```

### SDXL (Higher Quality)

```python
from diffusers import StableDiffusionXLPipeline

pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe = pipe.to("cuda")

image = pipe(
    prompt="A professional photo of a cat wearing a tiny hat",
    num_inference_steps=40
).images[0]

image.save("cat_hat.png")
```

## Automatic1111 Web UI

### Docker Setup

```yaml
# docker-compose.yml
services:
  automatic1111:
    image: ghcr.io/abetlen/automatic1111:latest
    container_name: automatic1111
    ports:
      - "7860:7860"
    volumes:
      - ./models:/app/models
      - ./outputs:/app/outputs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    command: --listen --api
```

### API Usage

```python
import requests
import base64

def generate_image_a1111(
    prompt: str,
    negative_prompt: str = "",
    steps: int = 30,
    width: int = 512,
    height: int = 512
) -> bytes:
    """Generate image using Automatic1111 API."""

    response = requests.post(
        "http://localhost:7860/sdapi/v1/txt2img",
        json={
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": width,
            "height": height,
            "sampler_name": "DPM++ 2M Karras",
            "cfg_scale": 7
        }
    )

    # Decode base64 image
    image_data = response.json()["images"][0]
    return base64.b64decode(image_data)

# Usage
image_bytes = generate_image_a1111("A beautiful sunset over the ocean")
with open("sunset.png", "wb") as f:
    f.write(image_bytes)
```

## ComfyUI

### Docker Setup

```yaml
services:
  comfyui:
    image: ghcr.io/ai-dock/comfyui:latest
    container_name: comfyui
    ports:
      - "8188:8188"
    volumes:
      - ./models:/workspace/ComfyUI/models
      - ./outputs:/workspace/ComfyUI/output
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### API Usage

```python
import requests
import json
import uuid

def queue_prompt(prompt_workflow: dict) -> str:
    """Queue a ComfyUI workflow."""
    response = requests.post(
        "http://localhost:8188/prompt",
        json={
            "prompt": prompt_workflow,
            "client_id": str(uuid.uuid4())
        }
    )
    return response.json()["prompt_id"]

def get_image(prompt_id: str) -> bytes:
    """Get generated image from ComfyUI."""
    # Poll for completion
    while True:
        response = requests.get(f"http://localhost:8188/history/{prompt_id}")
        history = response.json()

        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            for node_id, output in outputs.items():
                if "images" in output:
                    image_data = output["images"][0]
                    filename = image_data["filename"]

                    # Fetch image
                    img_response = requests.get(
                        f"http://localhost:8188/view",
                        params={"filename": filename}
                    )
                    return img_response.content

        time.sleep(0.5)
```

## LocalAI Image Generation

### Setup

```yaml
services:
  localai:
    image: localai/localai:latest-gpu-nvidia-cuda-12
    ports:
      - "8080:8080"
    volumes:
      - ./models:/build/models
    environment:
      - THREADS=4
```

### API Usage

```python
def generate_image_localai(prompt: str, output_path: str):
    """Generate image using LocalAI."""
    response = requests.post(
        "http://localhost:8080/v1/images/generations",
        json={
            "prompt": prompt,
            "size": "512x512",
            "n": 1
        }
    )

    # Get base64 image
    image_data = response.json()["data"][0]["b64_json"]

    import base64
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(image_data))

generate_image_localai("A futuristic cityscape", "city.png")
```

## Image-to-Image

Transform existing images:

```python
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe = pipe.to("cuda")

# Load source image
init_image = Image.open("input.png").convert("RGB")
init_image = init_image.resize((512, 512))

# Transform
result = pipe(
    prompt="Make it look like a watercolor painting",
    image=init_image,
    strength=0.75,  # How much to change (0-1)
    guidance_scale=7.5
).images[0]

result.save("watercolor.png")
```

## Inpainting

Edit specific parts of an image:

```python
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16
)
pipe = pipe.to("cuda")

# Load image and mask (white = area to change)
image = Image.open("photo.png").convert("RGB")
mask = Image.open("mask.png").convert("RGB")

result = pipe(
    prompt="A red sports car",
    image=image,
    mask_image=mask,
    guidance_scale=7.5
).images[0]

result.save("edited.png")
```

## ControlNet

Control generation with structure:

```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from PIL import Image
import cv2
import numpy as np

# Load ControlNet for edge detection
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-canny",
    torch_dtype=torch.float16
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16
)
pipe = pipe.to("cuda")

# Create edge image
image = cv2.imread("input.png")
edges = cv2.Canny(image, 100, 200)
edge_image = Image.fromarray(edges)

# Generate following the edges
result = pipe(
    prompt="A detailed architectural drawing",
    image=edge_image,
    num_inference_steps=30
).images[0]

result.save("controlled.png")
```

## Prompt Engineering

### Effective Prompts

```python
# Structure: [subject], [style], [details], [quality]

prompts = {
    "portrait": "Portrait of a woman, oil painting style, dramatic lighting, highly detailed, masterpiece",

    "landscape": "Mountain valley at golden hour, photorealistic, 8k resolution, volumetric fog, ray tracing",

    "product": "Professional product photo of a watch, studio lighting, white background, commercial photography",

    "concept": "Cyberpunk city street at night, neon signs, rain reflections, cinematic composition, artstation trending"
}

# Negative prompts to avoid common issues
negative = "blurry, low quality, distorted, disfigured, bad anatomy, watermark, text, signature"
```

### Parameter Guide

| Parameter | Range | Effect |
|-----------|-------|--------|
| Steps | 20-50 | More = finer details, slower |
| CFG Scale | 5-15 | Higher = follows prompt more strictly |
| Strength (img2img) | 0.3-0.9 | Higher = more change |
| Seed | Any integer | Same seed = reproducible results |

## Batch Generation

```python
def generate_variations(prompt: str, count: int = 4) -> list:
    """Generate multiple variations of a prompt."""
    images = []

    for i in range(count):
        result = pipe(
            prompt=prompt,
            num_inference_steps=30,
            generator=torch.Generator("cuda").manual_seed(i * 1000)
        ).images[0]
        images.append(result)

    return images

# Create a grid
def create_grid(images: list, cols: int = 2) -> Image:
    """Combine images into a grid."""
    rows = (len(images) + cols - 1) // cols
    w, h = images[0].size

    grid = Image.new("RGB", (w * cols, h * rows))

    for i, img in enumerate(images):
        x = (i % cols) * w
        y = (i // cols) * h
        grid.paste(img, (x, y))

    return grid
```

## Hardware Requirements

| Model | VRAM | Generation Time |
|-------|------|-----------------|
| SD 1.5 | 4GB | ~5s |
| SD 2.1 | 6GB | ~7s |
| SDXL | 8GB | ~15s |
| SDXL + Refiner | 12GB | ~25s |

## See Also

- [Multi-Modal Overview](index.md)
- [Vision Models](vision.md)
- [LocalAI Guide](../api-serving/localai.md)
