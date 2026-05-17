# GPU Containers

Configure GPU access for containerized LLM inference on the MS-S1 MAX
(AMD Strix Halo, ROCm) and — for cross-reference — Apple Silicon laptops.

## GPU Support Matrix

| Platform | GPU | Container support | Toolchain |
|----------|-----|-------------------|-----------|
| MS-S1 MAX (Linux) | AMD Strix Halo iGPU (gfx1151) | Yes — `/dev/kfd` + `/dev/dri` passthrough | ROCm 7.x |
| Linux | AMD discrete (RDNA 3/CDNA) | Yes | ROCm 7.x |
| macOS | Apple Silicon | None — Docker Desktop does not expose Metal | Run natively (MLX, llama.cpp Metal) |

> **Not used on the MS-S1 MAX**: NVIDIA / `nvidia-container-toolkit` / CUDA images.
> The Strix Halo iGPU is an AMD device; this whole site assumes a CUDA-free stack.

## AMD ROCm setup (this build)

!!! tip "Native vs container"
    For direct inference without containers, see
    [ROCm Installation](../gpu/rocm-installation.md). For an APU like the
    MS-S1 MAX, native installation can simplify debugging; containers buy
    you reproducibility and isolation.

### Install ROCm on the host

```bash
# Ubuntu 26.04: ROCm 7.1 ships in Universe
sudo apt update
sudo apt install rocm

# Grant container processes access to the GPU
sudo usermod -aG video,render $USER
```

For ROCm newer than what is in the Ubuntu archive, install AMD's
`amdgpu-install` from `repo.radeon.com`. See
[ROCm Installation](../gpu/rocm-installation.md) for the upstream path.

### Verify the host can talk to the GPU

```bash
rocminfo | head
rocm-smi
ls -l /dev/kfd /dev/dri
```

You should see `gfx1151` in `rocminfo` output and the `kfd` + `dri`
devices on disk.

### Docker Compose configuration

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"  # only needed for older ROCm
    volumes:
      - /mnt/tank/ai/models/ollama:/root/.ollama
```

### `docker run` syntax

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -e HSA_OVERRIDE_GFX_VERSION=11.5.1 \
  -v /mnt/tank/ai/models/ollama:/root/.ollama \
  ollama/ollama:rocm
```

### ROCm with llama.cpp

```yaml
services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    environment:
      HSA_OVERRIDE_GFX_VERSION: "11.5.1"
    command: >
      -m /models/llama-3.3-70b-q4_k_m.gguf
      --host 0.0.0.0
      -c 8192
      -ngl 99
```

## Vulkan (fallback)

For GPUs where the ROCm runtime is not ready (or you want a portable
build), llama.cpp also ships a Vulkan backend.

### Host setup

```bash
sudo apt install vulkan-tools libvulkan1
vulkaninfo | head
```

### Container configuration

```yaml
services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-vulkan
    devices:
      - /dev/dri
    group_add:
      - video
      - render
```

Vulkan is generally slower than ROCm on the Strix Halo iGPU, but is
useful as a sanity check if a ROCm image misbehaves.

## Memory management

### Sharing the 128GB unified memory pool

The MS-S1 MAX has a single iGPU sharing the system memory pool, so
container "GPU memory limits" don't apply the way they do on a
discrete-GPU box. Instead:

- Choose quantization that fits comfortably (Q4_K_M for 70B, etc.).
- Use the BIOS UMA frame buffer setting to give ROCm enough headroom —
  see [Memory Configuration](../gpu/memory-configuration.md).
- Only run one inference engine at a time unless you have explicit
  reason to share.

### Shared memory

Some workloads (vLLM, tensor-parallel runs on multi-GPU rigs) need
larger `shm`:

```yaml
services:
  llama-server:
    shm_size: '16gb'
```

### Offloading strategies

If a model is too big even at Q4:

```bash
# Partial GPU offload — keep some layers on CPU
llama-server -m model.gguf -ngl 30

# Ollama adjusts automatically based on available memory
```

## Monitoring GPU usage

### From the host

```bash
# Real-time monitoring (AMD ROCm)
watch -n 1 rocm-smi

# GPU utilization
rocm-smi --showuse

# VRAM (unified memory carved out for the GPU)
rocm-smi --showmeminfo vram
```

### From inside a container

```bash
docker exec ollama rocm-smi
docker stats ollama
docker logs ollama 2>&1 | grep -iE 'rocm|hip|gpu'
```

## Troubleshooting

### GPU not detected in the container

```bash
# Host first: do you see the GPU at all?
rocminfo | head
ls -l /dev/kfd /dev/dri

# Then in a clean container
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal:latest rocminfo | head
```

If the host sees the GPU but the container doesn't, the most common
cause is missing `--device=` / `--group-add` flags.

### Permission denied (`/dev/kfd` or `/dev/dri/renderD*`)

```bash
# Add user to groups (one-time)
sudo usermod -aG video,render $USER

# New shell to pick up the groups
newgrp video
newgrp render

# Verify device permissions
ls -la /dev/kfd /dev/dri/*
```

### Out of GPU memory

```bash
# Check what's currently using the GPU
rocm-smi

# Solutions:
# 1. Use higher quantization (Q4 instead of Q8)
# 2. Reduce context length
# 3. Reduce GPU layers (-ngl)
# 4. Unload unused models
docker exec ollama ollama stop model-name
```

### `HSA_OVERRIDE_GFX_VERSION` confusion

On older ROCm (6.x) the Strix Halo iGPU required
`HSA_OVERRIDE_GFX_VERSION=11.5.1` because the runtime didn't recognise
`gfx1151` by default. ROCm 7.x supports `gfx1151` natively, so the
override is no longer required — but setting it does no harm and lets
the same Compose file work on both ROCm 6 and 7.

## Environment variables reference

### AMD / ROCm

| Variable | Description |
|----------|-------------|
| `HIP_VISIBLE_DEVICES` | Limit which GPUs HIP sees |
| `ROCR_VISIBLE_DEVICES` | Alternative device selection (HSA runtime) |
| `HSA_OVERRIDE_GFX_VERSION` | Override GPU architecture (e.g. `11.5.1` for gfx1151 on older ROCm) |
| `GPU_MAX_HW_QUEUES` | Bound on hardware queue count, useful for tuning |

## See also

- [Container Deployment](index.md) — container overview
- [llama.cpp Docker](llama-cpp-docker.md) — llama.cpp container details
- [Ollama Docker](ollama-docker.md) — Ollama container details
- [vLLM](../inference-engines/vllm.md) — multi-engine serving (reference)
- [ROCm Installation](../gpu/rocm-installation.md) — native ROCm setup
- [Memory Configuration](../gpu/memory-configuration.md) — APU memory optimization
