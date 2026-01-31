# Power Management

APU power and thermal control for balancing performance, power consumption, and noise.

## CPU Power Governors

### cpupower Tool

Install CPU frequency utilities:

```bash
sudo apt install -y linux-tools-common linux-tools-$(uname -r)
```

View current governor:

```bash
cpupower frequency-info
```

### Available Governors

| Governor | Behavior | Use Case |
|----------|----------|----------|
| performance | Max frequency always | LLM inference, benchmarks |
| powersave | Min frequency always | Idle, overnight |
| schedutil | Dynamic, kernel-driven | Default, balanced |
| ondemand | Dynamic, userspace | Legacy systems |

Set governor temporarily:

```bash
sudo cpupower frequency-set -g performance
```

### Persistent Governor

Create a systemd service for boot-time setting:

```bash
# /etc/systemd/system/cpupower.service
[Unit]
Description=Set CPU governor
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/cpupower frequency-set -g schedutil
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable cpupower.service
```

## AMD P-State Driver

Modern AMD processors use the amd-pstate driver for efficient power management.

### Verify Driver

```bash
# Check active driver
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver
```

Expected output: `amd-pstate` or `amd-pstate-epp`

### P-State Modes

| Mode | Description |
|------|-------------|
| amd-pstate | Basic frequency scaling |
| amd-pstate-epp | Enhanced with Energy Performance Preference |

Enable EPP mode via kernel parameter:

```bash
# /etc/default/grub
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amd_pstate=active"
```

Update GRUB:

```bash
sudo update-grub
```

### Energy Performance Preference (EPP)

EPP allows fine-tuning the power/performance balance:

```bash
# View current EPP
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference

# Available options
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_available_preferences
```

Options:

| EPP Value | Behavior |
|-----------|----------|
| performance | Maximum performance |
| balance_performance | Slight performance bias |
| balance_power | Slight power saving bias |
| power | Maximum power saving |

Set EPP for all cores:

```bash
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    echo "balance_performance" | sudo tee "$cpu"
done
```

## Platform Power Profiles

### power-profiles-daemon

Ubuntu includes power-profiles-daemon for system-wide power management:

```bash
# Check status
powerprofilesctl
```

### Available Profiles

| Profile | Description |
|---------|-------------|
| performance | Maximum performance, higher power |
| balanced | Default, adaptive behavior |
| power-saver | Reduced power, lower performance |

Set profile:

```bash
# Switch to performance
powerprofilesctl set performance

# Switch to balanced
powerprofilesctl set balanced

# Switch to power-saver
powerprofilesctl set power-saver
```

### Profile Effects

The power profile affects:

- CPU frequency scaling
- GPU power states
- Platform power limits
- Turbo boost behavior

## Thermal Management

### Temperature Monitoring

Monitor temperatures continuously:

```bash
watch -n 2 sensors
```

Key temperature points:

| Component | Target | Throttle |
|-----------|--------|----------|
| CPU (Tctl) | < 80C | ~95C |
| GPU | < 85C | ~100C |
| NVMe | < 60C | ~80C |

### Thermal Throttling

Check if thermal throttling is occurring:

```bash
# CPU throttle events
dmesg | grep -i throttl

# Current vs max frequency
cpupower frequency-info | grep -E "(current|hardware limits)"
```

### Thermal Relationship

Higher TDP (power limit) means:

- More performance
- Higher temperatures
- More fan noise

Reducing power limits via BIOS or kernel parameters can lower temperatures at the cost of performance.

### When to Reduce Power

Consider power reduction when:

- Thermal throttling occurs frequently
- Fan noise is unacceptable
- Ambient temperature is high
- Running sustained workloads

## Fan Control

### BIOS vs OS Control

Most systems manage fans via BIOS/firmware. Check current fan status:

```bash
sensors | grep -i fan
```

### fancontrol (if applicable)

Some systems support OS-level fan control:

```bash
sudo apt install -y fancontrol

# Configure (if supported)
sudo pwmconfig
```

!!! note
    Many modern systems, especially laptops and SFF PCs, don't expose fan control to the OS. Fan curves are managed in BIOS.

### Noise Considerations

| Fan Behavior | Cause | Solution |
|--------------|-------|----------|
| Constant high speed | High sustained load | Reduce power profile |
| Ramps up/down frequently | Bursty workloads | Adjust fan curve in BIOS |
| Always loud | Aggressive fan curve | Modify BIOS settings |

## Workload-Based Profiles

### High-Performance Profile

For LLM inference and compute-intensive tasks:

```bash
#!/bin/bash
# /usr/local/bin/profile-performance.sh

powerprofilesctl set performance

for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    echo "performance" | sudo tee "$cpu" > /dev/null
done

echo "Performance profile activated"
```

### Balanced Profile

For mixed workloads (default):

```bash
#!/bin/bash
# /usr/local/bin/profile-balanced.sh

powerprofilesctl set balanced

for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    echo "balance_performance" | sudo tee "$cpu" > /dev/null
done

echo "Balanced profile activated"
```

### Quiet Profile

For idle or overnight operation:

```bash
#!/bin/bash
# /usr/local/bin/profile-quiet.sh

powerprofilesctl set power-saver

for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    echo "power" | sudo tee "$cpu" > /dev/null
done

echo "Quiet profile activated"
```

### Install Profile Scripts

```bash
sudo chmod +x /usr/local/bin/profile-*.sh
```

Switch profiles as needed:

```bash
# Before LLM inference
sudo profile-performance.sh

# Back to normal
sudo profile-balanced.sh

# Overnight
sudo profile-quiet.sh
```

### Automatic Profile Switching

Create a systemd service for overnight quiet mode:

```bash
# /etc/systemd/system/quiet-night.timer
[Unit]
Description=Enable quiet mode at night

[Timer]
OnCalendar=*-*-* 23:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# /etc/systemd/system/quiet-night.service
[Unit]
Description=Enable quiet profile

[Service]
Type=oneshot
ExecStart=/usr/local/bin/profile-quiet.sh
```

And a corresponding morning timer to restore balanced mode.

## Quick Reference

| Task | Command |
|------|---------|
| View current governor | `cpupower frequency-info` |
| Set governor | `sudo cpupower frequency-set -g <gov>` |
| View power profile | `powerprofilesctl` |
| Set power profile | `powerprofilesctl set <profile>` |
| Check EPP | `cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference` |
| Monitor temps | `watch -n 2 sensors` |
| Check throttling | `dmesg \| grep -i throttl` |
