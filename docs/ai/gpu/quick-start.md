# Strix Halo ROCm Quick Start

Single-page path from bare Ubuntu 24.04 to running LLMs on GPU with the AMD Ryzen AI Max+ 395 APU (gfx1151).

!!! info "Tested Environment"
    Ubuntu 24.04, ROCm 7.x, kernel 6.14+ (OEM), 128GB DDR5. For detailed configuration of individual components, see the linked pages throughout this guide.

## 1. Install OEM Kernel

The stock Ubuntu 24.04 kernel does not include full gfx1151 support. Install the OEM kernel (6.14+):

```bash
sudo apt install linux-oem-24.04c
sudo reboot
```

Verify after reboot:

```bash
uname -r
# Should show 6.14.x or newer
```

## 2. Install ROCm 7.x

Download and install the `amdgpu-install` package:

```bash
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/noble/amdgpu-install_7.1.1.70101-1_all.deb
sudo apt install ./amdgpu-install_7.1.1.70101-1_all.deb
```

Install the ROCm stack:

```bash
sudo amdgpu-install --usecase=rocm,hip,opencl,graphics,dkms
```

Add your user to the required groups:

```bash
sudo usermod -aG video,render $USER
newgrp video
newgrp render
```

## 3. Verify GPU Detection

```bash
rocminfo | grep gfx
# Should show: Name:                    gfx1151

rocm-smi
# Should show the AMD Radeon device with temperature, power, etc.
```

!!! note "No HSA Override Needed"
    ROCm 7.x has native gfx1151 support. You do **not** need `HSA_OVERRIDE_GFX_VERSION`.

## 4. Allocate VRAM with amd-ttm

By default, the system allocates roughly 62GB as GPU-accessible memory. For large LLMs, allocate more using `amd-debug-tools`:

```bash
# Install amd-debug-tools
pipx install amd-debug-tools

# Check current allocation
amd-ttm
# Shows current GTT (Graphics Translation Table) size

# Set to 108GB (leaves ~20GB for OS)
amd-ttm --set 108
sudo reboot
```

Verify after reboot:

```bash
amd-ttm
# Should confirm ~108GB allocation

rocm-smi --showmeminfo vram
# Should reflect the new allocation
```

For more details on memory allocation strategies, see [Memory Configuration](memory-configuration.md).

## 5. Install and Test Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Run a test model:

```bash
ollama run llama3.2
```

Verify GPU usage:

```bash
ollama ps
# Should show GPU memory usage, not CPU
```

## 6. llama.cpp (Docker)

For llama.cpp via Docker with ROCm:

```bash
docker run -d \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  -v /path/to/models:/models \
  -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server-rocm \
  -m /models/your-model.gguf \
  --host 0.0.0.0 \
  -ngl 99
```

See [GPU Containers](../containers/gpu-containers.md) for Docker Compose examples.

## Troubleshooting

### GPU not detected by rocminfo

```bash
# Check amdgpu driver is loaded
lsmod | grep amdgpu

# If not loaded
sudo modprobe amdgpu

# Check for blacklist entries
grep -r amdgpu /etc/modprobe.d/
# Remove any blacklist lines if found

# Rebuild initramfs after changes
sudo update-initramfs -u
sudo reboot
```

### Wrong kernel booting

```bash
# Check which kernels are installed
dpkg -l | grep linux-image

# Set OEM kernel as default
sudo sed -i 's/GRUB_DEFAULT=.*/GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 6.14.0-1-oem"/' /etc/default/grub
sudo update-grub
sudo reboot
```

### rocm-smi shows no devices

Ensure your user is in the `video` and `render` groups:

```bash
groups $USER
# Should include: video render

# If not, add and re-login
sudo usermod -aG video,render $USER
# Log out and back in
```

## What's Next

- [ROCm Installation](rocm-installation.md) -- detailed installation options and environment configuration
- [Memory Configuration](memory-configuration.md) -- VRAM allocation strategies and kernel parameters
- [Driver Updates](driver-updates.md) -- keeping ROCm current

## Sources

This guide consolidates information from the following community resources:

- [Shoresh613 - ROCm on Strix Halo](https://github.com/Shoresh613/ROCm_on_StrixHalo) -- comprehensive setup notes
- [hakedev - ROCm for Strix Halo](https://hakedev.com/rocm-for-strix-halo/) -- kernel and driver walkthrough
- [pablo-ross - Strix Halo ROCm setup](https://github.com/pablo-ross/strix-halo-rocm-setup) -- tested configuration
- [Jeff Geerling - AMD Strix Halo](https://www.jeffgeerling.com/tags/strix-halo) -- hardware and software notes
