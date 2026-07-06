# Troubleshooting

Common problems and solutions for local LLM deployment on the MS-S1 MAX
(AMD ROCm) and Apple Silicon laptops (Metal). NVIDIA / CUDA is not used
in this build; if you see a CUDA-specific error here, treat it as
generic "GPU memory" guidance.

## Model loading issues

### Model file not found

```
Error: model file not found
```

**Causes:**
- Incorrect path
- Model not downloaded
- Wrong mount in Docker

**Solutions:**
```bash
# Verify file exists
ls -la /path/to/model.gguf

# For Docker, check mount
docker exec ollama ls -la /root/.ollama/models

# Ollama: re-pull model
ollama pull llama3.3:70b
```

### Invalid model format

```
Error: invalid model format
```

**Causes:**
- Corrupted download
- Wrong format for engine
- Incompatible quantization

**Solutions:**
```bash
# Re-download
ollama rm llama3.3:70b
ollama pull llama3.3:70b

# For GGUF, verify file
file model.gguf
# Should show: GGUF model data
```

### Model too large

```
Error: out of memory
Error: failed to mmap model
```

**Causes:**
- Insufficient GPU-accessible memory (GTT allocation too small)
- Model exceeds available RAM
- `amd-ttm`/GTT sizing needs tuning — not the BIOS UMA framebuffer, which stays small (see [Memory Configuration](../gpu/memory-configuration.md#software-vram-allocation-amd-ttm))

**Solutions:**
```bash
# Use smaller quantization
ollama pull llama3.3:70b-instruct-q4_K_S  # Smaller than Q4_K_M

# Reduce GPU layers
./llama-server -m model.gguf -ngl 30  # Partial offload

# Reduce context length
./llama-server -m model.gguf -c 4096
```

## GPU issues

### GPU not detected (AMD ROCm — MS-S1 MAX)

```
No GPU detected
Using CPU backend
```

```bash
# Host: confirm ROCm sees the iGPU
rocminfo | head
rocm-smi
ls -l /dev/kfd /dev/dri

# Docker: confirm device passthrough
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal rocminfo | head

# If the container can't see the iGPU, the Compose file is almost
# certainly missing `devices:` or `group_add:`.
```

If `rocminfo` returns "No agents found", ROCm itself isn't installed
correctly — see [ROCm Installation](../gpu/rocm-installation.md).

### GPU not detected (Apple Silicon, laptop)

```
Metal not available
```

- Make sure you're not running inside Docker Desktop: it cannot expose
  Metal to containers, so MLX / Metal-backed builds must run natively.
- For PyTorch, verify with `torch.backends.mps.is_available()`.
- For llama.cpp, build with `LLAMA_METAL=1`.

### GPU memory exhausted

```
Error: out of memory
HIP error: out of memory
```

**Solutions:**
```bash
# AMD: check current usage
rocm-smi --showmeminfo vram

# Unload unused models
ollama stop other-model

# Use a smaller model/quantization
ollama run llama3.3:70b-instruct-q3_K_M  # Instead of Q4_K_M

# Reduce context
--num-ctx 4096
```

On the MS-S1 MAX, "GPU memory" is drawn from the unified-memory pool via
the dynamically sized GTT allocation, not the small fixed BIOS UMA frame
buffer. Do **not** raise the UMA setting to fix OOM — leave it at 512MB.
If you keep running out, adjust the `amd-ttm`/GTT sizing (e.g.
`amd-ttm --set 108`) and make sure enough of the 128GB pool is available
to the GPU — see the amd-ttm section in
[Memory Configuration](../gpu/memory-configuration.md#software-vram-allocation-amd-ttm).

### Slow GPU performance

```
Tokens/sec much lower than expected
```

**Causes:**
- Not all layers on GPU
- Thermal throttling
- Power management
- `HSA_OVERRIDE_GFX_VERSION` set incorrectly (or unset on older ROCm)

**Solutions:**
```bash
# Verify GPU layers
# Look for "GPU layers: 99" / "offloaded N layers to GPU" in startup log

# Check temperature and clocks (AMD)
rocm-smi --showtemp --showclocks

# Confirm ROCm backend is actually active in logs
journalctl -u ollama -f | grep -iE 'rocm|hip|gpu'

# Force full GPU offload
-ngl 99
```

## API issues

### Connection refused

```
Error: connection refused
curl: (7) Failed to connect
```

**Solutions:**
```bash
# Check service is running
systemctl status ollama
docker ps | grep ollama

# Check binding
ss -tuln | grep 11434

# Check firewall
sudo ufw status

# Bind to all interfaces
OLLAMA_HOST=0.0.0.0 ollama serve
```

### Timeout on requests

```
Error: request timeout
```

**Causes:**
- Model loading slowly
- Large prompt
- Slow hardware

**Solutions:**
```bash
# Increase timeout in client
curl --max-time 300 http://localhost:11434/api/generate

# Pre-load model
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.3:70b", "keep_alive": "1h"}'

# Check model is loaded
ollama ps
```

### Empty or truncated response

```
Response has no content or stops abruptly
```

**Causes:**
- max_tokens too low
- Stop token triggered
- Context overflow

**Solutions:**
```bash
# Increase max_tokens
curl ... -d '{"max_tokens": 2000}'

# Check stop tokens
# Remove or adjust stop sequences

# Check context length
# Reduce prompt size or increase context
```

## Docker issues

### Container won't start

```bash
# Check logs
docker logs ollama

# Check image
docker images | grep ollama

# Pull fresh image (use :rocm on the MS-S1 MAX)
docker pull ollama/ollama:rocm
```

### GPU not available in container

```bash
# AMD: Check devices
ls -la /dev/kfd /dev/dri

# Verify permissions
groups  # Should include video, render

# Verify Compose file passes them through
docker compose config | grep -A4 -E 'devices|group_add'
```

### Volume mount issues

```bash
# Check mount
docker exec ollama ls -la /root/.ollama

# Fix permissions
sudo chown -R 1000:1000 /mnt/tank/ai/models/ollama

# SELinux (if applicable)
chcon -Rt svirt_sandbox_file_t /mnt/tank/ai/models/ollama
```

## Performance issues

### Slow token generation

**Causes:**
- CPU fallback (ROCm not actually engaged)
- Memory thrashing
- Suboptimal quantization

**Solutions:**
```bash
# Verify GPU usage
watch -n 1 rocm-smi

# Check for swap usage
free -h
swapon --show  # Should be minimal

# Use appropriate quantization
# Q4_K_M is a good balance, not Q2_K
```

### High latency (TTFT)

**Causes:**
- Large context
- Model loading
- Cold start

**Solutions:**
```bash
# Keep model loaded
OLLAMA_KEEP_ALIVE=1h

# Pre-load on start
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.3:70b", "keep_alive": "24h"}'

# Reduce context
-c 4096
```

### Memory pressure

```bash
# Monitor memory
watch -n 1 free -h

# Reduce simultaneous models
OLLAMA_MAX_LOADED_MODELS=1

# Use smaller quantization
```

## Coding tool issues

### Tool can't connect

```
Error: Cannot connect to API
```

**Solutions:**
```bash
# Set environment
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=not-needed

# Verify API responds
curl $OPENAI_API_BASE/models

# Check tool-specific config
```

### Wrong model used

```bash
# Specify model explicitly
aider --model ollama/deepseek-coder-v2:16b

# Check available models
ollama list

# In config files, use exact model name
```

### Slow code completion

- Use a faster model for completion (7-8B)
- Use a larger model for complex tasks
- Reduce context sent with requests

## Log analysis

### Ollama logs

```bash
# View logs
journalctl -u ollama -f

# Docker logs
docker logs -f ollama

# Debug mode
OLLAMA_DEBUG=1 ollama serve
```

### llama.cpp logs

```bash
# Enable verbose
./llama-server -m model.gguf --verbose

# Log to file
./llama-server -m model.gguf --log-file server.log
```

### System logs

```bash
# Check for OOM
dmesg | grep -i "killed process"

# GPU errors (AMD)
dmesg | grep -iE "amdgpu|kfd|hip"
```

## Recovery steps

### Full reset (Ollama, native)

```bash
sudo systemctl stop ollama
# Clear models (optional, large!)
rm -rf ~/.ollama/models
sudo systemctl start ollama
ollama pull llama3.3:70b
```

### Full reset (Docker, ROCm)

```bash
docker stop ollama
docker rm ollama

# Optional: clear data
sudo rm -rf /mnt/tank/ai/models/ollama/*

# Start fresh
# No HSA_OVERRIDE_GFX_VERSION needed — ROCm 7.x supports gfx1151 natively.
docker run -d \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  -v /mnt/tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama:rocm
```

### GPU driver reset (AMD)

```bash
# Reload the amdgpu kernel module
sudo rmmod amdgpu
sudo modprobe amdgpu

# If that doesn't unstick the GPU, reboot
sudo reboot
```

## Getting help

### Collect diagnostic info

```bash
# System info
uname -a
cat /etc/os-release

# GPU info (AMD)
rocminfo | head
rocm-smi

# Memory
free -h

# Docker
docker version
docker info

# Ollama
ollama --version
ollama list
```

### Where to ask

- [Ollama GitHub issues](https://github.com/ollama/ollama/issues)
- [llama.cpp discussions](https://github.com/ggml-org/llama.cpp/discussions)
- [ROCm GitHub](https://github.com/ROCm/ROCm/issues)
- [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA)

## See also

- [Performance Index](../performance/index.md) - Optimization
- [Memory Management](../performance/memory-management.md) - Memory issues
- [GPU Containers](../containers/gpu-containers.md) - Container GPU setup
