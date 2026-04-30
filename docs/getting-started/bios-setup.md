# BIOS Setup

MS-S1 MAX specific BIOS configuration for optimal performance with AMD APU workloads.

## Firmware Version

Run **BIOS 1.06** (released 2026-01-04) or later before installing Ubuntu 26.04. Earlier firmware has known memory training, NVMe, and USB4 v2 stability issues that 26.04's Linux 7.0 kernel exposes more aggressively.

The flash is doable from Linux + EFI shell — see [capetron/minisforum-ms-s1-max-bios](https://github.com/capetron/minisforum-ms-s1-max-bios). Disable Secure Boot during the flash and expect 5-10 minutes of memory retraining on the first boot afterwards (BIOS settings reset to defaults).

!!! warning "Rear USB4 ports"
    A known ACPI power-management flaw on the rear USB4 v2 (80 Gbps) ports is **not fully resolved by 1.06** as of early 2026. Prefer the front 40 Gbps USB4 ports for any device where stability matters.

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
| UMA Frame Buffer | Advanced > Graphics | 512 MB (small) |
| VRAM Size | (same setting, different name) | 512 MB (small) |

**Setting options explained:**

| Value | Use Case |
|-------|----------|
| 512MB | **Recommended for Strix Halo + AI workloads** — keep dedicated VRAM small, use GTT for the rest |
| 1-4GB | Desktop/server with mixed light GPU workloads |
| 8-16GB | Only if a workload specifically requires large fixed VRAM and cannot use GTT |
| 32GB+ | Rarely useful — locks RAM away from the OS |

!!! tip "AMD's official Strix Halo guidance"
    AMD's ROCm system-optimization guide recommends keeping dedicated VRAM **small (~0.5 GB)** and letting GTT-backed allocations dynamically use up to ~50% of system RAM (raisable via `amd-ttm`). Large UMA reservations were the right answer on older APUs but on Strix Halo they just take RAM out of the OS pool without giving ROCm anything it couldn't get via GTT. See [Memory Configuration](../ai/gpu/memory-configuration.md#software-vram-allocation-amd-ttm) for the runtime knobs.

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
| Memory | UMA Frame Buffer | 512 MB (Strix Halo: keep small, use GTT) |
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
