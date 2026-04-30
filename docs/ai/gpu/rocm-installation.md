# ROCm Installation

Install AMD ROCm stack natively on Ubuntu 26.04 LTS for the AMD Ryzen AI Max+ 395 APU.

!!! tip "26.04 ships ROCm in the archive"
    Ubuntu 26.04 ships **ROCm 7.1.0** in the Universe repo, so `sudo apt install rocm` gives you a working stack with no third-party repository. The in-distro version trails upstream by roughly one minor release; use the AMD repo path below only if you need newer than 7.1.0.

## APU Support Status

!!! success "Strix Halo Support"
    As of ROCm 7.x, AMD officially supports gfx1151 (Strix Halo / Strix Point). The `HSA_OVERRIDE_GFX_VERSION` workaround is no longer needed.

### Current Compatibility

| Component | Support Level | Notes |
|-----------|---------------|-------|
| amdgpu kernel driver | Good | Linux 7.0 (26.04 default) covers gfx1151; min for upstream is 6.18.4 / 6.17 HWE |
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

Ubuntu 26.04 ships **Linux 7.0**, which has full gfx1151 support out of the box. The 26.04 server installer also auto-installs HWE/OEM metapackages when matching hardware is detected, so no manual kernel install is needed on the MS-S1 Max.

Verify:

```bash
uname -r
# Should show 7.0.x or newer
```

If you are still on an older release, AMD's published minimum for gfx1151 is kernel 6.18.4 mainline or 6.17 HWE.

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

### Method 1: In-distro `apt install rocm` (Recommended for 26.04)

```bash
sudo apt update
sudo apt install rocm
```

This pulls ROCm 7.1.0 from Ubuntu's Universe repo. It includes the runtime, HIP, OpenCL, and Lemonade Server. Use this unless you specifically need a newer ROCm than 7.1.0.

### Method 2: amdgpu-install (Newer ROCm via AMD's repo)

The `amdgpu-install` script tracks upstream ROCm faster than the Ubuntu archive.

**Download the installer:**

```bash
# AMD's resolute (26.04) path may not be published yet. Check repo.radeon.com first;
# fall back to the noble (24.04) installer if needed.
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

!!! note "DKMS is optional on 26.04"
    The 7.0 kernel includes upstream amdgpu support for gfx1151, so DKMS is no longer strictly required to make ROCm work. Including `dkms` is still useful when you need a fresher amdgpu than the in-tree driver — for example to pick up a Strix-Halo-specific fix that hasn't landed in the running kernel yet.

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
# AMD's repo may not yet publish a 'resolute' suite at 26.04 launch. The noble (24.04) suite typically works
# on 26.04 since ROCm packages are largely libstdc++/glibc-compatible across versions; switch to 'resolute'
# once it appears.

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

# Rebuild initramfs after changes (26.04 uses dracut by default, which is invoked the same way)
sudo update-initramfs -u
sudo reboot
```

### Wrong Kernel Booting After Upgrade

If the system boots an older kernel:

```bash
# List installed kernels
dpkg -l | grep linux-image

# Set the desired kernel as GRUB default (replace with the actual entry name)
sudo sed -i 's/GRUB_DEFAULT=.*/GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 7.0.0-N-generic"/' /etc/default/grub
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
