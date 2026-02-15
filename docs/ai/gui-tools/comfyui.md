# ComfyUI

Node-based generative AI workbench for images, video, audio, and 3D.

## Overview

ComfyUI provides:

- **Node-based workflow editor** - Visual graph for building generation pipelines
- **Multi-modal generation** - Images, video, audio/music, and 3D models
- **Native AMD ROCm support** - Official partnership with AMD as of v0.7+
- **Extensible** - Thousands of custom nodes via ComfyUI Manager
- **API-driven** - Every workflow is a JSON graph, fully automatable
- **No vendor lock-in** - Open source (GPL-3.0), runs locally

### Supported Modalities

| Modality | Models | Status |
|----------|--------|--------|
| **Image** | FLUX, SDXL, SD 1.5, SD 3.5 | Mature |
| **Video** | LTX Video, HunyuanVideo, Wan 2.1/2.2 | Stable |
| **Audio/Music** | ACE-Step, Stable Audio, DiffRhythm | Growing |
| **3D** | Hunyuan3D, Stable Fast 3D, Tripo | Emerging |

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | AMD RDNA2+ / NVIDIA RTX 20+ / Apple M1+ | AMD RDNA 3.5 / NVIDIA RTX 40+ |
| **VRAM** | 8 GB | 16+ GB (or unified memory APU) |
| **RAM** | 16 GB | 32+ GB |
| **Python** | 3.10 | 3.12 |
| **Browser** | Any modern browser | Chromium-based |
| **Disk** | 20 GB (base) | 100+ GB (with models) |

!!! info "AMD Strix Halo APU"
    The Ryzen AI Max+ 395 with unified memory is well suited for ComfyUI. Large models that exceed typical discrete GPU VRAM can run using shared system memory. ROCm 7.x provides native `gfx1151` support -- no `HSA_OVERRIDE_GFX_VERSION` workaround needed.

## Installation

### Native (Recommended for AMD APU)

Set up a Python virtual environment with ROCm-enabled PyTorch:

```bash
# Create and activate virtual environment
python3.12 -m venv ~/comfyui-venv
source ~/comfyui-venv/bin/activate

# Install PyTorch with ROCm support
pip install torch torchvision torchaudio \
  --index-url https://repo.radeon.com/rocm/manylinux/rocm-rel-7.1/
```

Clone and install ComfyUI:

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI
cd ~/ComfyUI
pip install -r requirements.txt
```

Launch:

```bash
python3 main.py --listen 0.0.0.0
```

Access at `http://localhost:8188`

!!! tip "ROCm Setup"
    If ROCm is not yet installed, see the [ROCm Installation Guide](../gpu/rocm-installation.md) first. Ensure your user is in the `video` and `render` groups.

### Docker (AMD ROCm)

```yaml
services:
  comfyui:
    image: hardandheavy/comfyui-rocm:latest
    container_name: comfyui
    ports:
      - "8188:8188"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    volumes:
      - /tank/ai/comfyui/models:/app/models
      - /tank/ai/comfyui/output:/app/output
      - /tank/ai/comfyui/custom_nodes:/app/custom_nodes
    environment:
      - HIP_VISIBLE_DEVICES=0
    restart: unless-stopped
```

```bash
docker compose up -d
```

### Docker (NVIDIA)

```yaml
services:
  comfyui:
    image: ghcr.io/ai-dock/comfyui:latest
    container_name: comfyui
    ports:
      - "8188:8188"
    volumes:
      - /tank/ai/comfyui/models:/app/models
      - /tank/ai/comfyui/output:/app/output
      - /tank/ai/comfyui/custom_nodes:/app/custom_nodes
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

See [GPU Containers](../containers/gpu-containers.md) for more NVIDIA Docker details.

### Comfy CLI

Quick alternative using the official CLI:

```bash
pip install comfy-cli
comfy install
comfy launch
```

## Model Management

### ComfyUI Manager

ComfyUI Manager is built into recent versions and provides:

- Browse and install custom nodes from a registry
- Download models directly from the UI
- Resolve missing dependencies automatically
- Detect and fix node conflicts
- Security scanning for custom nodes

Access via the **Manager** button in the top menu bar.

### Model Directories

Place models in the corresponding subdirectory under `ComfyUI/models/`:

| Directory | Model Type | Examples |
|-----------|-----------|----------|
| `checkpoints/` | Base models | FLUX, SDXL, SD 1.5 |
| `loras/` | LoRA adapters | Style LoRAs, character LoRAs |
| `vae/` | VAE models | SDXL VAE, custom VAEs |
| `controlnet/` | ControlNet | Canny, depth, pose |
| `clip/` | CLIP text encoders | CLIP-L, CLIP-G, T5-XXL |
| `unet/` | UNet / diffusion models | FLUX dev/schnell UNets |
| `upscale_models/` | Upscalers | RealESRGAN, 4x-UltraSharp |
| `clip_vision/` | CLIP vision encoders | For IP-Adapter, style transfer |

### Shared Model Paths

To share models across tools, create symlinks or use ComfyUI's `extra_model_paths.yaml`:

```yaml
# ComfyUI/extra_model_paths.yaml
shared:
  base_path: /tank/ai/models/
  checkpoints: checkpoints/
  loras: loras/
  vae: vae/
```

## Image Generation

### Supported Models

| Model | Parameters | VRAM | Notes |
|-------|-----------|------|-------|
| FLUX.1 Dev | 12B | 16+ GB | High quality, guidance distilled |
| FLUX.1 Schnell | 12B | 16+ GB | Fast (4 steps), Apache-2.0 |
| FLUX Kontext | 12B | 16+ GB | In-context editing |
| SDXL | 3.5B | 8+ GB | Mature ecosystem, many LoRAs |
| SD 1.5 | 860M | 4+ GB | Lightweight, huge LoRA library |
| SD 3.5 | 2.5B-8B | 8-16 GB | Latest Stability AI release |

### Key Capabilities

- **Text-to-image** -- Type a prompt, get an image
- **Image-to-image** -- Transform existing images with style or content changes
- **Inpainting** -- Edit specific regions using masks
- **Outpainting** -- Extend images beyond their borders
- **ControlNet** -- Guide generation with edge detection, depth maps, or poses
- **LoRA** -- Apply fine-tuned style/character adapters on top of base models
- **Upscaling** -- Increase resolution with dedicated upscaler nodes

### Basic Workflow

A minimal text-to-image workflow connects these nodes:

```
Load Checkpoint --> CLIP Text Encode (positive) --> KSampler --> VAE Decode --> Save Image
                --> CLIP Text Encode (negative) ↗
                --> Empty Latent Image ↗
```

ComfyUI ships with default workflows. Load them via **Load Default** or drag a workflow JSON onto the canvas.

## Video Generation

### Supported Models

| Model | Parameters | Resolution | Notes |
|-------|-----------|------------|-------|
| LTX Video | 2B | Up to 768x512 | Built into ComfyUI core |
| HunyuanVideo 1.5 | 13B | Up to 1280x720 | High quality, text-to-video and image-to-video |
| Wan 2.1 / 2.2 | 1.3B-14B | Up to 1280x720 | Multiple sizes, strong motion |

### Capabilities

- **Text-to-video** -- Generate video clips from text descriptions
- **Image-to-video** -- Animate a still image
- **Video-to-video** -- Restyle or modify existing clips
- **Frame interpolation** -- Increase FPS of generated video

### Memory Requirements

| Model | Minimum VRAM | Recommended |
|-------|-------------|-------------|
| LTX Video 2B | 8 GB | 16 GB |
| HunyuanVideo 13B | 24+ GB | 48+ GB |
| Wan 2.1 1.3B | 8 GB | 16 GB |
| Wan 2.1 14B | 24+ GB | 48+ GB |

!!! tip "APU Shared Memory Advantage"
    Unified memory APUs like the Ryzen AI Max+ 395 can allocate well beyond typical discrete VRAM limits. A system with 128 GB RAM can run models that would not fit on a 24 GB discrete GPU. Use `--lowvram` and `--disable-pinned-memory` flags for best results with large video models.

## Audio and Music Generation

### ACE-Step

ACE-Step is a 3.5B parameter music generation model capable of producing full songs:

- Generate complete songs in under 10 seconds on consumer hardware
- 50+ language support for lyrics
- Structural tags: `[verse]`, `[chorus]`, `[bridge]`, `[intro]`, `[outro]`
- Text-to-audio, audio-to-audio, style transfer, voice cloning
- Apache-2.0 license, free for commercial use

**Setup:**

1. Download `ace_step_v1_3.5b.safetensors` to `models/checkpoints/`
2. Install ACE-Step custom nodes via ComfyUI Manager

**Basic node chain:**

```
Load Checkpoint --> TextEncodeAceStepAudio --> KSampler --> Save Audio
                --> EmptyAceStepLatentAudio ↗
```

**Example prompt:**

```
[verse]
Walking through the city at night
Neon lights reflecting in the rain

[chorus]
We are the dreamers, we are the light
```

With style tag: `electronic, synthwave, 120bpm, female vocal`

### Stable Audio

- Generate up to 3-minute tracks in under 2 seconds
- Multi-part structure support (intros, developments, outros)
- Available via Stability AI custom nodes

### DiffRhythm

- Open-source music generation alternative
- Strong rhythmic consistency
- Available as ComfyUI custom node pack

## 3D Generation

### Supported Models

| Model | Capability | Output | Notes |
|-------|-----------|--------|-------|
| Hunyuan3D 2.0/3.0 | Text-to-3D, image-to-3D | UV-mapped meshes | Tencent, high fidelity |
| Stable Fast 3D | Single image to mesh | Textured mesh | ~500ms generation |
| Tripo v3.0 | Text/image-to-3D | PBR materials | High-fidelity meshes |

### Output Formats

- UV-mapped meshes (OBJ, GLB)
- PBR material textures (albedo, normal, roughness)
- Ready for import into Blender, Unity, Unreal Engine

Install 3D generation nodes via ComfyUI Manager. Most require the `trimesh` and `pytorch3d` Python packages.

## Configuration

### Launch Parameters

| Flag | Description | When to Use |
|------|-------------|-------------|
| `--listen 0.0.0.0` | Listen on all interfaces | Network access |
| `--port 8188` | Set port number | Change default port |
| `--lowvram` | Aggressive memory optimization | Large models, limited VRAM |
| `--disable-pinned-memory` | Disable CUDA/HIP pinned memory | APU unified memory |
| `--cpu` | Force CPU inference | No GPU available |
| `--force-fp16` | Force FP16 precision | Save memory |
| `--preview-method auto` | Enable live previews | See generation progress |

**Recommended for AMD APU:**

```bash
python3 main.py --listen 0.0.0.0 --lowvram --disable-pinned-memory --force-fp16
```

### Environment Variables

For AMD ROCm:

```bash
export HIP_VISIBLE_DEVICES=0
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True
export HSA_ENABLE_SDMA=0
```

### Custom Nodes

Install via ComfyUI Manager (recommended) or manually:

```bash
cd ~/ComfyUI/custom_nodes
git clone https://github.com/author/node-pack.git
pip install -r node-pack/requirements.txt
```

Restart ComfyUI after installing nodes.

**Popular custom node packs:**

| Node Pack | Purpose |
|-----------|---------|
| rgthree-comfy | Quality-of-life nodes (reroute, mute, bookmark) |
| ComfyUI-Impact-Pack | Detection, segmentation, and batch processing |
| ComfyUI-KJNodes | Utility nodes for advanced workflows |
| ComfyUI-VideoHelperSuite | Video loading, saving, and frame manipulation |
| ComfyUI-AnimateDiff | Animation and video generation helpers |

## API Usage

Every ComfyUI workflow is a JSON graph that can be queued via the REST API.

### Queue a Prompt

```python
import requests
import json
import uuid

def queue_prompt(workflow: dict, server: str = "http://localhost:8188") -> str:
    """Queue a ComfyUI workflow and return the prompt ID."""
    response = requests.post(
        f"{server}/prompt",
        json={
            "prompt": workflow,
            "client_id": str(uuid.uuid4()),
        },
    )
    return response.json()["prompt_id"]
```

### Retrieve Output

```python
import time

def get_output(prompt_id: str, server: str = "http://localhost:8188") -> bytes:
    """Poll for completion and return the first generated image."""
    while True:
        response = requests.get(f"{server}/history/{prompt_id}")
        history = response.json()

        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            for node_id, output in outputs.items():
                if "images" in output:
                    filename = output["images"][0]["filename"]
                    img = requests.get(
                        f"{server}/view",
                        params={"filename": filename},
                    )
                    return img.content
        time.sleep(0.5)
```

### WebSocket Connection

For real-time progress updates, connect via WebSocket:

```python
import websocket

ws = websocket.create_connection("ws://localhost:8188/ws?clientId=my-client")
while True:
    msg = json.loads(ws.recv())
    if msg["type"] == "progress":
        print(f"Step {msg['data']['value']}/{msg['data']['max']}")
    elif msg["type"] == "executed":
        print("Done")
        break
```

## Performance Tips

- **Use `--lowvram`** on APU systems to aggressively offload between nodes
- **Use `--disable-pinned-memory`** on unified memory systems
- **Use `--force-fp16`** to halve memory usage with minimal quality loss
- **Keep models loaded** -- ComfyUI caches loaded models in VRAM between runs
- **Reduce resolution first** -- Generate at lower res, then upscale with a dedicated node
- **Batch wisely** -- Small batches avoid memory spikes on memory-constrained systems
- **Monitor GPU usage** -- Run `rocm-smi` (AMD) or `nvidia-smi` (NVIDIA) during inference to verify the GPU is active

## Troubleshooting

### ROCm Not Detected

```bash
# Verify driver is loaded
lsmod | grep amdgpu

# Check device nodes exist
ls -la /dev/kfd /dev/dri/render*

# Verify group membership
groups | grep -E "video|render"

# Test PyTorch sees the GPU
python3 -c "import torch; print(torch.cuda.is_available())"
```

See [ROCm Installation](../gpu/rocm-installation.md) for full setup instructions.

### Out of Memory

- Add `--lowvram` and `--disable-pinned-memory` flags
- Use `--force-fp16` to reduce memory usage
- Reduce image resolution (start with 512x512, upscale later)
- Close other GPU-using applications
- For video models, reduce frame count or resolution

### Slow Generation

- Verify GPU is being used: `rocm-smi` should show activity during inference
- Check that PyTorch is using the correct device (not falling back to CPU)
- Reduce inference steps (20-30 is often sufficient for FLUX Schnell)
- Enable `--preview-method auto` only when needed (adds overhead)

### Custom Node Conflicts

- Use ComfyUI Manager to check compatibility between installed nodes
- Disable recently installed nodes if ComfyUI fails to start
- Check the terminal/console output for Python import errors
- Remove conflicting nodes from `custom_nodes/` and restart

### Black or Corrupt Output

- Verify the correct VAE is connected in the workflow
- Check model format matches expected type (e.g., SDXL checkpoint with SDXL workflow)
- Ensure the model file downloaded completely (check file size)
- Try a different sampler or scheduler

## See Also

- [GPU Setup](../gpu/index.md) - GPU driver and configuration
- [ROCm Installation](../gpu/rocm-installation.md) - AMD ROCm stack setup
- [Memory Configuration](../gpu/memory-configuration.md) - VRAM and unified memory tuning
- [GPU Containers](../containers/gpu-containers.md) - Docker GPU passthrough
- [Image Generation](../multimodal/image-generation.md) - Diffusers and other image generation tools
- [Open WebUI](open-webui.md) - Web interface for LLM chat
