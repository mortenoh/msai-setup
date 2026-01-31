# BIOS Setup

MS-S1 MAX specific BIOS configuration for optimal performance with AMD APU workloads.

## Accessing BIOS

Power on the system and press the appropriate key during POST:

| Method | Key |
|--------|-----|
| Primary | Del |
| Alternative | F2 |

!!! tip "Timing"
    Press the key repeatedly as soon as you see the Minisforum logo. USB keyboards may have a slight delay.

## Memory Settings

Memory configuration is critical for APU performance since the integrated GPU shares system RAM.

### XMP/DOCP Profile

Enable memory profiles to run DDR5 at rated speeds:

| Setting | Location | Recommended |
|---------|----------|-------------|
| XMP/DOCP | Advanced > Memory | Enabled |
| Memory Profile | Advanced > Memory | Profile 1 (highest rated) |

The MS-S1 MAX ships with DDR5-5600 memory. Without XMP/DOCP enabled, memory may default to JEDEC speeds (4800 MHz), significantly reducing performance.

**Why memory speed matters:**

- Token generation is memory-bandwidth bound
- Higher frequency = more bandwidth = faster inference
- DDR5-5600 vs DDR5-4800 is ~17% bandwidth difference

### UMA Frame Buffer Size

The UMA (Unified Memory Architecture) Frame Buffer allocates a portion of system RAM as dedicated video memory for the integrated GPU:

| Setting | Location | Recommended |
|---------|----------|-------------|
| UMA Frame Buffer | Advanced > Graphics | Auto or 16GB |
| VRAM Size | (same setting, different name) | Auto or 16GB |

**Setting options explained:**

| Value | Use Case |
|-------|----------|
| Auto | Dynamic allocation, usually sufficient |
| 512MB-4GB | Desktop/server without GPU workloads |
| 8GB-16GB | GPU compute, AI inference |
| 32GB+ | Heavy 3D rendering (rarely needed for LLMs) |

!!! note "LLM Inference"
    For llama.cpp and similar tools, the UMA setting is less critical than total system RAM. The inference engines manage memory directly. However, ROCm applications may benefit from larger UMA allocation.

### Memory Interleaving

Ensure memory is running in dual-channel mode:

| Setting | Location | Recommended |
|---------|----------|-------------|
| Channel Interleaving | Advanced > Memory | Auto or Enabled |
| Bank Interleaving | Advanced > Memory | Auto or Enabled |

Verify dual-channel operation from Linux:

```bash
sudo dmidecode -t memory | grep -E "Number Of Devices|Locator"
```

Both DIMM slots should be populated for dual-channel bandwidth.

## AMD APU Settings

### IOMMU (AMD-Vi)

Required for virtualization and GPU passthrough:

| Setting | Location | Recommended |
|---------|----------|-------------|
| IOMMU | Advanced > AMD CBS | Enabled |
| ACS Enable | Advanced > AMD CBS | Enabled (if available) |

Verify from Linux:

```bash
dmesg | grep -i iommu
```

### Above 4G Decoding

Allows PCIe devices to use memory addresses above 4GB:

| Setting | Location | Recommended |
|---------|----------|-------------|
| Above 4G Decoding | Advanced > PCI | Enabled |
| Re-Size BAR | Advanced > PCI | Enabled |

Re-Size BAR (Resizable BAR) enables the CPU to access the full GPU memory range, beneficial for some workloads.

### iGPU Configuration

| Setting | Location | Recommended |
|---------|----------|-------------|
| Primary Display | Advanced > Graphics | Auto or IGFX |
| iGPU Multi-Monitor | Advanced > Graphics | Enabled (if using displays) |

For headless server operation, these settings have minimal impact. The iGPU remains available for compute regardless.

## CPU Settings

### Precision Boost Overdrive (PBO)

PBO allows the CPU to boost beyond stock limits when thermal and power headroom exists:

| Setting | Location | Recommended |
|---------|----------|-------------|
| PBO | Advanced > AMD CBS > SMU | Advanced or Enabled |
| PBO Limits | Advanced > AMD CBS > SMU | Auto |

For 24/7 server operation, consider:

- **Conservative**: PBO Disabled - Stable, predictable power
- **Balanced**: PBO Auto - Reasonable boost, default behavior
- **Performance**: PBO Advanced - Maximum performance, higher power/heat

### SMT (Simultaneous Multi-Threading)

| Setting | Location | Recommended |
|---------|----------|-------------|
| SMT | Advanced > AMD CBS | Enabled |

SMT provides 32 threads from 16 cores. Disable only if specific workloads perform better with SMT off (rare for server workloads).

### cTDP / TDP Settings

If available, configure power limits:

| Setting | Description |
|---------|-------------|
| cTDP | Configurable TDP limit |
| PPT | Package Power Tracking limit |
| TDC | Thermal Design Current limit |
| EDC | Electrical Design Current limit |

For 24/7 operation, stock settings provide a good balance. Increase only if cooling is adequate.

## Power and Thermal Settings

### Power Profile

| Setting | Location | Recommended |
|---------|----------|-------------|
| Power Profile | Advanced > Power | Balanced or Performance |
| Package Power Limit | Advanced > Power | Auto |

For server use:

- **Balanced** - Good performance, reasonable power
- **Performance** - Maximum speed, higher power draw
- **Low Power** - Reduced performance, quieter operation

### AC Power Recovery

Important for unattended operation:

| Setting | Location | Recommended |
|---------|----------|-------------|
| AC Power Loss | Advanced > Power | Power On |
| Power On After Power Fail | (same) | Always On |

This ensures the server restarts automatically after power outages.

### Fan Control

| Setting | Location | Recommended |
|---------|----------|-------------|
| Fan Mode | Hardware Monitor or Advanced > Thermal | Auto or Silent |
| Fan Curve | (if available) | Custom |

For 24/7 operation, prioritize cooling over noise. The system should maintain safe temperatures under sustained load.

## Virtualization Settings

For KVM/QEMU virtual machines:

| Setting | Location | Recommended |
|---------|----------|-------------|
| SVM | Advanced > CPU | Enabled |
| IOMMU | Advanced > AMD CBS | Enabled |
| NX Mode | Advanced > CPU | Enabled |
| SME | Advanced > AMD CBS | Enabled (optional) |

SVM (Secure Virtual Machine) is AMD's virtualization technology, equivalent to Intel VT-x.

## Boot Settings

| Setting | Location | Recommended |
|---------|----------|-------------|
| Boot Mode | Boot | UEFI |
| Secure Boot | Boot > Security | Enabled (optional) |
| Fast Boot | Boot | Disabled |
| Boot Order | Boot | NVMe first |

!!! note "Secure Boot"
    Secure Boot can be enabled with Ubuntu but may complicate kernel module loading for out-of-tree drivers. Disable if troubleshooting driver issues.

## Settings Summary

Quick reference for AI/server workloads:

| Category | Setting | Value |
|----------|---------|-------|
| Memory | XMP/DOCP | Enabled |
| Memory | UMA Frame Buffer | Auto or 16GB |
| AMD | IOMMU | Enabled |
| AMD | Above 4G Decoding | Enabled |
| AMD | Re-Size BAR | Enabled |
| CPU | PBO | Auto or Enabled |
| CPU | SMT | Enabled |
| Power | AC Power Loss | Power On |
| Boot | Boot Mode | UEFI |

## Saving and Exit

After making changes:

1. Press F10 or navigate to Exit > Save Changes and Reset
2. Confirm saving changes
3. System will reboot with new settings

## Verifying Settings from Linux

After booting Ubuntu, verify BIOS settings took effect:

```bash
# Check memory speed
sudo dmidecode -t memory | grep Speed

# Check IOMMU
dmesg | grep -i -e DMAR -e IOMMU

# Check Resizable BAR
lspci -vvv | grep -i "resize"

# Check virtualization
grep -E 'svm|vmx' /proc/cpuinfo

# Check PBO/boost status
cat /sys/devices/system/cpu/cpu0/cpufreq/boost
```

## See Also

- [Hardware](hardware.md) - MS-S1 MAX specifications
- [Memory Configuration](../ai/gpu/memory-configuration.md) - APU memory optimization
- [ROCm Installation](../ai/gpu/rocm-installation.md) - GPU driver setup
- [KVM Setup](../virtualization/kvm-setup.md) - Virtualization configuration
