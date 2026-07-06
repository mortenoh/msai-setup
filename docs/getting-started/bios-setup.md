# BIOS Setup

MS-S1 MAX specific BIOS configuration for optimal performance with AMD APU workloads.

Authoritative spec sheet: [minisforum.com/products/ms-s1-max](https://www.minisforum.com/products/ms-s1-max).

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

## Recovering from a Bad BIOS State

The MS-S1 MAX has a physical **BIOS reset hole** on the rear I/O panel (next to the power button) — a hardware CMOS-clear, independent of the OS or any BIOS menu. There's no BMC/IPMI on this board, so this is the fallback if a setting change (or a bad firmware flash) leaves the system unable to POST or unable to display video:

1. Power off and unplug the PSU.
2. Insert a thin pin into the reset hole and hold briefly (a few seconds), per the same convention as a typical motherboard CMOS-clear button.
3. Reconnect power and boot. BIOS settings return to factory defaults — you'll need to redo anything in [Settings Summary](#settings-summary) (Secure Boot off, IOMMU on, UMA frame buffer, etc.) before continuing.

## Memory Settings

Memory configuration is critical for APU performance since the integrated GPU shares system RAM.

!!! info "Soldered LPDDR5X — no XMP/DOCP"
    The MS-S1 MAX ships with 128GB LPDDR5X-8000 MT/s on a 256-bit (quad-channel) bus, **soldered to the SoC package**. There are no DIMM slots, no XMP/DOCP profile to enable, and memory speed is fixed by firmware. The only memory-related knobs in BIOS that matter on this platform are the UMA frame buffer size (below) and the AMD CBS memory interleaving toggles.

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

Ensure channel and bank interleaving are enabled so the SoC actually uses the 256-bit bus:

| Setting | Location | Recommended |
|---------|----------|-------------|
| Channel Interleaving | Advanced > Memory | Auto or Enabled |
| Bank Interleaving | Advanced > Memory | Auto or Enabled |

Verify memory presentation from Linux. Because the LPDDR5X is on-package, `dmidecode` will report it as soldered/embedded (sometimes with non-standard slot strings, depending on firmware):

```bash
sudo dmidecode -t memory | grep -E "Speed|Locator|Size|Form Factor"
```

You should see ~8000 MT/s reported and a single 128GB total. There are no socketed DIMM slots to populate.

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
| Secure Boot | Boot > Security | Disabled (recommended for this build — see note below) |
| Fast Boot | Boot | Disabled |
| Boot Order | Boot | NVMe first |

!!! note "Secure Boot is disabled for this build"
    This setup uses out-of-tree DKMS modules (`amdgpu-dkms`, `zfs-dkms`) which must be MOK-signed to load under Secure Boot. The simpler, lower-friction path is to keep Secure Boot **disabled** on this headless server. The host is protected by network controls (UFW, Tailscale-only management), not boot-time integrity. If you specifically need Secure Boot, plan to enroll a MOK before installing ROCm or ZFS.

## Settings Summary

Quick reference for AI/server workloads:

| Category | Setting | Value |
|----------|---------|-------|
| Memory | UMA Frame Buffer | 512 MB (Strix Halo: keep small, use GTT) |
| AMD | IOMMU | Enabled |
| AMD | Above 4G Decoding | Enabled |
| AMD | Re-Size BAR | Enabled |
| CPU | PBO | Auto or Enabled |
| CPU | SMT | Enabled |
| Power | AC Power Loss | Power On |
| Boot | Boot Mode | UEFI |
| Boot | Secure Boot | Disabled (simpler for amdgpu/ROCm/ZFS DKMS) |

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
