# GPU Containers

Configure GPU access for containerized LLM inference.

## GPU Support Matrix

| Platform | GPU | Container Support | Framework |
|----------|-----|-------------------|-----------|
| Linux | NVIDIA | Excellent | nvidia-container-toolkit |
| Linux | AMD | Good | ROCm |
| Linux | Intel | Experimental | OneAPI |
| macOS | Apple Silicon | None | Use native |
| Windows WSL2 | NVIDIA | Good | nvidia-container-toolkit |

## NVIDIA Setup

### Install Container Toolkit

```bash
# Add repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Verify Installation

```bash
# Test GPU access in container
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all  # or specific number
              capabilities: [gpu]
```

### Specify GPU Devices

```yaml
# All GPUs
devices:
  - driver: nvidia
    count: all
    capabilities: [gpu]

# Specific number
devices:
  - driver: nvidia
    count: 2
    capabilities: [gpu]

# Specific GPU IDs
devices:
  - driver: nvidia
    device_ids: ['0', '1']
    capabilities: [gpu]
```

### docker run Syntax

```bash
# All GPUs
docker run --gpus all ...

# Specific count
docker run --gpus 2 ...

# Specific device
docker run --gpus '"device=0,1"' ...
```

## AMD ROCm Setup

### Install ROCm

```bash
# Add repository (Ubuntu 22.04)
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/amdgpu-install_6.0.60002-1_all.deb
sudo apt install ./amdgpu-install_6.0.60002-1_all.deb

# Install ROCm
sudo amdgpu-install --usecase=rocm

# Add user to groups
sudo usermod -aG video,render $USER
```

### Verify Installation

```bash
# Check ROCm
rocminfo

# Check GPU
rocm-smi
```

### Container Configuration

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:rocm
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
```

### docker run Syntax

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -v /tank/ai/models/ollama:/root/.ollama \
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
    command: >
      -m /models/llama-3.3-70b-q4_k_m.gguf
      --host 0.0.0.0
      -c 8192
      -ngl 99
```

## Vulkan (Cross-Platform)

For GPUs not well-supported by CUDA or ROCm:

### Host Setup

```bash
# Install Vulkan
sudo apt install vulkan-tools libvulkan1

# Verify
vulkaninfo
```

### Container Configuration

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

## Multi-GPU Configurations

### Split Workloads

Assign different models to different GPUs:

```yaml
version: '3.8'

services:
  chat-model:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0

  code-model:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0  # Container sees it as GPU 0
```

### Tensor Parallelism (vLLM)

For models too large for one GPU:

```yaml
services:
  vllm:
    image: vllm/vllm-openai
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
    command: >
      --model meta-llama/Llama-3.1-405B-Instruct
      --tensor-parallel-size 2
```

## Monitoring GPU Usage

### NVIDIA

```bash
# Real-time monitoring
nvidia-smi -l 1

# Watch specific metrics
watch -n 1 nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv

# From inside container
docker exec ollama nvidia-smi
```

### AMD

```bash
# Real-time monitoring
watch -n 1 rocm-smi

# GPU usage
rocm-smi --showuse

# Memory usage
rocm-smi --showmeminfo vram
```

### Container Stats

```bash
# Docker stats with GPU
docker stats ollama

# GPU utilization in container logs
docker logs ollama 2>&1 | grep -i gpu
```

## Memory Management

### GPU Memory Limits

NVIDIA containers can limit GPU memory:

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0
  # Ollama doesn't support direct memory limits
  # Use model quantization to control memory
```

### Shared Memory

Some workloads need increased shared memory:

```yaml
services:
  llama-server:
    shm_size: '16gb'
```

### Offloading Strategies

When GPU memory is limited:

```bash
# Partial GPU offload
llama-server -m model.gguf -ngl 30  # Only 30 layers on GPU

# Ollama adjusts automatically based on available memory
```

## Troubleshooting

### GPU Not Detected

```bash
# NVIDIA: Check driver
nvidia-smi

# Check container toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# If fails, reconfigure
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Permission Denied (AMD)

```bash
# Add user to groups
sudo usermod -aG video,render $USER

# Log out and back in, or:
newgrp video
newgrp render

# Verify device permissions
ls -la /dev/kfd /dev/dri/*
```

### CUDA Version Mismatch

```bash
# Check host driver version
nvidia-smi

# Use matching container image
# Driver 535+ → CUDA 12.x images
# Driver 525+ → CUDA 11.8 images
docker run --gpus all nvidia/cuda:12.1-base nvidia-smi
```

### Out of GPU Memory

```bash
# Check current usage
nvidia-smi  # or rocm-smi

# Solutions:
# 1. Use higher quantization (Q4 instead of Q8)
# 2. Reduce context length
# 3. Reduce GPU layers (-ngl)
# 4. Unload unused models
docker exec ollama ollama stop model-name
```

### Container Can't Access GPU

```bash
# Verify Docker runtime
docker info | grep -i runtime

# Should show nvidia runtime available
# If not, reinstall nvidia-container-toolkit

# Check GPU passthrough in compose
docker compose config | grep -A5 devices
```

## Environment Variables Reference

### NVIDIA

| Variable | Description |
|----------|-------------|
| `CUDA_VISIBLE_DEVICES` | Limit visible GPUs |
| `NVIDIA_VISIBLE_DEVICES` | Same as above (Docker) |
| `NVIDIA_DRIVER_CAPABILITIES` | Required capabilities |

### AMD/ROCm

| Variable | Description |
|----------|-------------|
| `HIP_VISIBLE_DEVICES` | Limit visible GPUs |
| `ROCR_VISIBLE_DEVICES` | Alternative device selection |
| `HSA_OVERRIDE_GFX_VERSION` | Override GPU architecture |

## See Also

- [Container Deployment](index.md) - Container overview
- [llama.cpp Docker](llama-cpp-docker.md) - llama.cpp container
- [Ollama Docker](ollama-docker.md) - Ollama container
- [vLLM](../inference-engines/vllm.md) - Multi-GPU serving
