# Troubleshooting

Common problems and solutions for local LLM deployment.

## Model Loading Issues

### Model File Not Found

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

### Invalid Model Format

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

### Model Too Large

```
Error: CUDA out of memory
Error: failed to mmap model
```

**Causes:**
- Insufficient GPU memory
- Model exceeds available RAM

**Solutions:**
```bash
# Use smaller quantization
ollama pull llama3.3:70b-instruct-q4_K_S  # Smaller than Q4_K_M

# Reduce GPU layers
./llama-server -m model.gguf -ngl 30  # Partial offload

# Reduce context length
./llama-server -m model.gguf -c 4096
```

## GPU Issues

### GPU Not Detected

```
No GPU detected
Using CPU backend
```

**NVIDIA Solutions:**
```bash
# Check driver
nvidia-smi

# Check CUDA
nvcc --version

# Docker: Verify nvidia-container-toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Reinstall toolkit
sudo apt install nvidia-container-toolkit
sudo systemctl restart docker
```

**AMD Solutions:**
```bash
# Check ROCm
rocminfo
rocm-smi

# Docker: Check device access
docker run --rm --device=/dev/kfd --device=/dev/dri rocm/rocm-terminal rocminfo
```

### GPU Memory Exhausted

```
CUDA error: out of memory
```

**Solutions:**
```bash
# Check current usage
nvidia-smi

# Unload unused models
ollama stop other-model

# Use smaller model/quantization
ollama run llama3.3:70b-instruct-q3_K_M  # Instead of Q4_K_M

# Reduce context
--num-ctx 4096  # Instead of default
```

### Slow GPU Performance

```
Tokens/sec much lower than expected
```

**Causes:**
- Not all layers on GPU
- Thermal throttling
- Power management

**Solutions:**
```bash
# Verify GPU layers
# Look for "GPU layers: 99" in startup log

# Check temperature
nvidia-smi -q -d TEMPERATURE

# Check power state
nvidia-smi -q -d PERFORMANCE

# Force full GPU offload
-ngl 99
```

## API Issues

### Connection Refused

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

### Timeout on Requests

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

### Empty or Truncated Response

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

## Docker Issues

### Container Won't Start

```bash
# Check logs
docker logs ollama

# Check image
docker images | grep ollama

# Pull fresh image
docker pull ollama/ollama:latest
```

### GPU Not Available in Container

```bash
# NVIDIA: Check runtime
docker info | grep -i runtime

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# AMD: Check devices
ls -la /dev/kfd /dev/dri

# Verify permissions
groups  # Should include video, render
```

### Volume Mount Issues

```bash
# Check mount
docker exec ollama ls -la /root/.ollama

# Fix permissions
sudo chown -R 1000:1000 /tank/ai/models/ollama

# SELinux (if applicable)
chcon -Rt svirt_sandbox_file_t /tank/ai/models/ollama
```

## Performance Issues

### Slow Token Generation

**Causes:**
- CPU fallback
- Memory thrashing
- Suboptimal quantization

**Solutions:**
```bash
# Verify GPU usage
nvidia-smi -l 1

# Check for swap usage
free -h
swapon --show  # Should be minimal

# Use appropriate quantization
# Q4_K_M is good balance, not Q2_K
```

### High Latency (TTFT)

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
-c 4096  # Instead of larger
```

### Memory Pressure

**Solutions:**
```bash
# Monitor memory
watch -n 1 free -h

# Reduce simultaneous models
OLLAMA_MAX_LOADED_MODELS=1

# Use smaller quantization
```

## Coding Tool Issues

### Tool Can't Connect

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

### Wrong Model Used

**Solutions:**
```bash
# Specify model explicitly
aider --model ollama/deepseek-coder-v2:16b

# Check available models
ollama list

# In config files, use exact model name
```

### Slow Code Completion

**Solutions:**
- Use faster model for completion (7-8B)
- Use larger model for complex tasks
- Reduce context sent with requests

## Log Analysis

### Ollama Logs

```bash
# View logs
journalctl -u ollama -f

# Docker logs
docker logs -f ollama

# Debug mode
OLLAMA_DEBUG=1 ollama serve
```

### llama.cpp Logs

```bash
# Enable verbose
./llama-server -m model.gguf --verbose

# Log to file
./llama-server -m model.gguf --log-file server.log
```

### System Logs

```bash
# Check for OOM
dmesg | grep -i "killed process"

# GPU errors
dmesg | grep -i "gpu\|nvidia\|amd"
```

## Recovery Steps

### Full Reset (Ollama)

```bash
# Stop service
sudo systemctl stop ollama

# Clear models (optional)
rm -rf ~/.ollama/models

# Restart
sudo systemctl start ollama

# Re-pull models
ollama pull llama3.3:70b
```

### Full Reset (Docker)

```bash
# Stop and remove
docker stop ollama
docker rm ollama

# Optional: clear data
sudo rm -rf /tank/ai/models/ollama/*

# Start fresh
docker run -d --gpus all \
  -v /tank/ai/models/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

### GPU Driver Reset

```bash
# NVIDIA
sudo nvidia-smi --gpu-reset

# If that fails
sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia
sudo modprobe nvidia

# Reboot if necessary
sudo reboot
```

## Getting Help

### Collect Diagnostic Info

```bash
# System info
uname -a
cat /etc/os-release

# GPU info
nvidia-smi  # or rocm-smi

# Memory
free -h

# Docker
docker version
docker info | grep -i nvidia

# Ollama
ollama --version
ollama list
```

### Where to Ask

- [Ollama GitHub Issues](https://github.com/ollama/ollama/issues)
- [llama.cpp Discussions](https://github.com/ggml-org/llama.cpp/discussions)
- [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA)

## See Also

- [Performance Index](../performance/index.md) - Optimization
- [Memory Management](../performance/memory-management.md) - Memory issues
- [GPU Containers](../containers/gpu-containers.md) - Container GPU setup
