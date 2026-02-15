# ROCm Installation

Install AMD ROCm stack natively on Ubuntu 24.04 for the AMD Ryzen AI Max+ 395 APU.

## APU Support Status

!!! success "Strix Halo Support"
    As of ROCm 7.x, AMD officially supports gfx1151 (Strix Halo / Strix Point). The `HSA_OVERRIDE_GFX_VERSION` workaround is no longer needed.

### Current Compatibility

| Component | Support Level | Notes |
|-----------|---------------|-------|
| amdgpu kernel driver | Good | Requires OEM kernel 6.14+ |
| ROCm runtime | Supported (ROCm 7.x) | Native gfx1151 support |
| HIP | Supported | Applications work natively |
| OpenCL | Good | Generally functional |

The AMD Ryzen AI Max+ 395 uses the RDNA 3.5 architecture with GPU ID `gfx1151`.

### APU vs Discrete GPU

| Aspect | APU | Discrete GPU |
|--------|-----|--------------|
| ROCm support | Newer, less tested | Mature |
| Memory | Shared system RAM | Dedicated VRAM |
| Device nodes | `/dev/kfd`, `/dev/dri` | Same |
| Performance | Memory bandwidth limited | Higher bandwidth |

## Prerequisites

### Kernel Requirements

The stock Ubuntu 24.04 kernel (6.8) does not include full gfx1151 support. Install the OEM kernel (6.14+):

```bash
sudo apt install linux-oem-24.04c
sudo reboot
```

Verify after reboot:

```bash
uname -r
# Should show 6.14.x or newer
```

### Check GPU Detection

Verify the APU is recognized:

```bash
# Check for AMD GPU
lspci | grep -i vga
# Output should include AMD Radeon

# Check DRI devices
ls -la /dev/dri/
# Should show card0 and renderD128
```

### Required Groups

```bash
# Add user to required groups
sudo usermod -aG video,render $USER

# Apply group changes (or log out and back in)
newgrp video
newgrp render
```

## Installation Methods

### Method 1: amdgpu-install (Recommended)

The `amdgpu-install` script provides the simplest installation path.

**Download the installer:**

```bash
# Ubuntu 24.04 (Noble)
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/noble/amdgpu-install_7.1.1.70101-1_all.deb

# Install the installer package
sudo apt install ./amdgpu-install_7.1.1.70101-1_all.deb
```

!!! note "Version Numbers"
    The version (7.1.1.70101-1) changes with ROCm releases. Check [repo.radeon.com](https://repo.radeon.com/amdgpu-install/) for the latest.

**Install ROCm:**

```bash
# Install ROCm with all common components
sudo amdgpu-install --usecase=rocm,hip,opencl,graphics,dkms
```

!!! warning "Do not skip DKMS"
    The `--no-dkms` flag skips building the amdgpu kernel module via DKMS. This will prevent ROCm from working with the OEM kernel. Always include `dkms` in the use cases.

**Available use cases:**

| Use Case | Components |
|----------|------------|
| `rocm` | Full ROCm stack |
| `graphics` | Graphics drivers only |
| `opencl` | OpenCL runtime |
| `hip` | HIP development |
| `rocmdev` | ROCm development tools |

### Method 2: Manual Installation

For more control over components:

**Add AMD repository:**

```bash
# Import GPG key
wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/rocm.gpg

# Add repository
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/7.1 noble main" | sudo tee /etc/apt/sources.list.d/rocm.list

# Update package lists
sudo apt update
```

**Install components:**

```bash
# Core ROCm runtime
sudo apt install rocm-hip-runtime

# ROCm SMI for monitoring
sudo apt install rocm-smi-lib

# Development tools (optional)
sudo apt install rocm-dev

# OpenCL runtime
sudo apt install rocm-opencl-runtime
```

## Environment Configuration

### Path Setup

Add ROCm to your PATH:

```bash
# Add to ~/.bashrc or ~/.profile
echo 'export PATH=$PATH:/opt/rocm/bin' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib' >> ~/.bashrc

# Apply changes
source ~/.bashrc
```

### HSA_OVERRIDE_GFX_VERSION (Legacy)

!!! note "ROCm 7.x -- Not Needed"
    ROCm 7.x has native gfx1151 support. The `HSA_OVERRIDE_GFX_VERSION` override is **not needed** and should not be set. If you have it in your `~/.bashrc`, remove it.

For users still on ROCm 6.x (not recommended), the override was required:

```bash
# ROCm 6.x only -- not needed for ROCm 7.x
export HSA_OVERRIDE_GFX_VERSION=11.0.0
```

The `HSA_OVERRIDE_GFX_VERSION` variable tells ROCm to treat the GPU as a different (supported) architecture. This causes instability and reduced performance compared to native support.

### Other Useful Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `HSA_OVERRIDE_GFX_VERSION` | Force GPU architecture | `11.0.0` |
| `HIP_VISIBLE_DEVICES` | Limit visible GPUs | `0` |
| `ROCR_VISIBLE_DEVICES` | Alternative device selection | `0` |
| `GPU_MAX_HW_QUEUES` | Hardware queue limit | `8` |

## Verification

### rocminfo

Check ROCm detects the GPU:

```bash
rocminfo
```

Expected output includes:

```
ROCk module is loaded
HSA System Attributes:
  ...
Agent 1:
  Name:                    gfx1151
  Marketing Name:          AMD Radeon Graphics
  ...
  Pool Info:
    Segment:               GLOBAL; FLAGS: FINE GRAINED
    Size:                  XX(XXX)KB
```

You should see `gfx1151` listed as a detected agent.

### rocm-smi

Monitor GPU status:

```bash
# Basic status
rocm-smi

# Detailed info
rocm-smi --showallinfo

# Memory usage
rocm-smi --showmeminfo vram

# Watch in real-time
watch -n 1 rocm-smi
```

### clinfo (OpenCL)

Verify OpenCL functionality:

```bash
# Install clinfo if needed
sudo apt install clinfo

# Check OpenCL devices
clinfo
```

Look for your AMD device in the output.

### Simple GPU Test

Run a basic HIP test:

```bash
# Install ROCm examples
sudo apt install rocm-hip-sdk

# Run device query
/opt/rocm/bin/hipInfo
```

## Troubleshooting

### GPU Not Detected

```bash
# Check if amdgpu module is loaded
lsmod | grep amdgpu

# If not loaded, try loading it
sudo modprobe amdgpu

# Check for errors
dmesg | grep -i amdgpu
```

### Permission Denied

```bash
# Verify group membership
groups $USER
# Should include: video render

# Check device permissions
ls -la /dev/kfd /dev/dri/*

# If permissions wrong, add udev rule
echo 'KERNEL=="kfd", GROUP="render", MODE="0660"' | sudo tee /etc/udev/rules.d/70-kfd.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### HSA Error: Invalid Code Object

This typically means architecture mismatch. On ROCm 7.x with gfx1151, ensure you do **not** have `HSA_OVERRIDE_GFX_VERSION` set:

```bash
# Check if override is set (should be empty on ROCm 7.x)
echo $HSA_OVERRIDE_GFX_VERSION

# Remove from bashrc if present
sed -i '/HSA_OVERRIDE_GFX_VERSION/d' ~/.bashrc
source ~/.bashrc
```

### amdgpu Blacklisted

If `rocminfo` fails, check for blacklist entries:

```bash
grep -r amdgpu /etc/modprobe.d/
# Remove any lines containing "blacklist amdgpu"

# Rebuild initramfs after changes
sudo update-initramfs -u
sudo reboot
```

### Wrong Kernel Booting After Upgrade

If the system boots an older kernel instead of the OEM kernel:

```bash
# List installed kernels
dpkg -l | grep linux-image

# Set OEM kernel as GRUB default
sudo sed -i 's/GRUB_DEFAULT=.*/GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 6.14.0-1-oem"/' /etc/default/grub
sudo update-grub
sudo reboot
```

### ROCm Version Mismatch

```bash
# Check installed version
apt list --installed | grep rocm

# Remove conflicting versions
sudo amdgpu-install --uninstall

# Reinstall specific version
sudo amdgpu-install --usecase=rocm
```

### Kernel Module Issues

```bash
# Check DKMS status
dkms status

# Rebuild modules if needed
sudo dkms autoinstall

# Or reinstall amdgpu-dkms
sudo apt install --reinstall amdgpu-dkms
```

## Integration with AI Frameworks

### llama.cpp with ROCm

Build llama.cpp with HIP support:

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with HIP (ROCm)
make GGML_HIP=1
```

### Ollama with ROCm

Ollama includes ROCm support:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Run with ROCm (detected automatically if installed)
ollama run llama3.2
```

Check Ollama is using GPU:

```bash
ollama ps
# Should show GPU memory usage
```

### PyTorch with ROCm

Install PyTorch with ROCm support:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.1
```

!!! note "PyTorch ROCm Wheels"
    Check the [PyTorch get-started page](https://pytorch.org/get-started/locally/) for the latest ROCm-compatible wheel URL. The index URL changes with each ROCm major release.

Verify:

```python
import torch
print(torch.cuda.is_available())  # Uses HIP, still returns True
print(torch.cuda.device_count())
print(torch.cuda.get_device_name(0))
```

## Updating ROCm

See [Driver Updates](driver-updates.md) for procedures on keeping ROCm current.

## See Also

- [Quick Start](quick-start.md) - Consolidated quick-start guide
- [Driver Updates](driver-updates.md) - Update procedures
- [Memory Configuration](memory-configuration.md) - APU memory optimization
- [BIOS Setup](../../getting-started/bios-setup.md) - BIOS settings for APU
- [GPU Containers](../containers/gpu-containers.md) - ROCm in Docker
