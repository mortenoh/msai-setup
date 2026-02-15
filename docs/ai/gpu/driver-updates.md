# Driver Updates

Procedures for keeping AMD GPU drivers and ROCm components current.

## Checking Current Versions

### Kernel Driver

```bash
# amdgpu kernel module version
modinfo amdgpu | grep ^version

# Currently loaded driver
cat /sys/module/amdgpu/version

# Kernel version (driver tied to kernel)
uname -r
```

### ROCm Version

```bash
# ROCm version file
cat /opt/rocm/.info/version

# Installed ROCm packages
apt list --installed | grep rocm

# ROCm release info
rocminfo | head -20
```

### GPU Firmware

```bash
# Firmware version
cat /sys/kernel/debug/dri/0/amdgpu_firmware_info

# Or via rocm-smi
rocm-smi --showfwinfo
```

## Update Procedures

### Routine Updates (amdgpu-install)

When AMD releases new ROCm versions:

**Check for updates:**

```bash
# Update package lists
sudo apt update

# Check available amdgpu-install version
apt policy amdgpu-install
```

**Upgrade ROCm:**

```bash
# Upgrade using amdgpu-install
sudo amdgpu-install --usecase=rocm

# Or just upgrade packages
sudo apt upgrade
```

### Major Version Upgrades

For major ROCm version changes (e.g., 6.x to 7.x):

!!! warning "OEM Kernel Compatibility"
    When upgrading to ROCm 7.x, ensure you are running the OEM kernel (`linux-oem-24.04c`, 6.14+). ROCm 7.x with gfx1151 requires this kernel for full support. See [ROCm Installation](rocm-installation.md) for kernel setup.

**Step 1: Backup configuration**

```bash
# Note current working environment variables
env | grep -E 'HSA|HIP|ROCM' > ~/rocm-env-backup.txt

# Save package list
dpkg -l | grep -E 'rocm|amdgpu' > ~/rocm-packages-backup.txt
```

**Step 2: Remove old version**

```bash
# Full uninstall
sudo amdgpu-install --uninstall

# Clean residual packages
sudo apt autoremove
```

**Step 3: Install new version**

```bash
# Download new amdgpu-install
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/noble/amdgpu-install_X.X.XXXXX-1_all.deb

# Install new installer
sudo apt install ./amdgpu-install_X.X.XXXXX-1_all.deb

# Install ROCm
sudo amdgpu-install --usecase=rocm
```

**Step 4: Reboot and verify**

```bash
sudo reboot

# After reboot
rocminfo
rocm-smi
```

### Kernel Driver Updates

The amdgpu kernel driver updates come through:

1. **Ubuntu kernel updates** - Included driver improvements
2. **amdgpu-dkms** - DKMS module from AMD repository

**DKMS module update:**

```bash
# Check DKMS status
dkms status

# If amdgpu-dkms is installed
sudo apt update
sudo apt upgrade amdgpu-dkms

# Rebuild for current kernel
sudo dkms autoinstall
```

**After kernel upgrades:**

```bash
# DKMS should rebuild automatically, but verify
dkms status | grep amdgpu

# If missing, reinstall
sudo dkms install amdgpu/<version>
```

### Firmware Updates

GPU firmware typically updates with the driver package:

```bash
# Check for firmware updates
sudo apt update
apt list --upgradable | grep firmware

# Install firmware updates
sudo apt upgrade linux-firmware
```

!!! warning "linux-firmware Regression"
    The `linux-firmware` version 20251125 has been reported to break ROCm on Strix Halo systems. If ROCm stops working after a firmware update, downgrade to a previous version and hold the package:

    ```bash
    sudo apt install linux-firmware=<previous-version>
    sudo apt-mark hold linux-firmware
    ```

## Handling Conflicts

### Package Conflicts

When apt reports conflicts:

```bash
# Identify conflicting packages
apt list --installed | grep -E 'rocm|amdgpu' | sort

# Remove conflicting version
sudo apt remove <conflicting-package>

# Clean and retry
sudo apt autoremove
sudo apt install -f
```

### Multiple ROCm Versions

Avoid installing multiple ROCm versions. If needed:

```bash
# List all ROCm installations
ls /opt/rocm*

# Remove old versions
sudo rm -rf /opt/rocm-<old-version>

# Update symlink
sudo ln -sfn /opt/rocm-<new-version> /opt/rocm
```

### DKMS Build Failures

```bash
# Check DKMS log
cat /var/lib/dkms/amdgpu/<version>/build/make.log

# Common fixes:
# 1. Install kernel headers
sudo apt install linux-headers-$(uname -r)

# 2. Remove and reinstall
sudo dkms remove amdgpu/<version> --all
sudo apt install --reinstall amdgpu-dkms

# 3. Build manually
sudo dkms build amdgpu/<version>
sudo dkms install amdgpu/<version>
```

## Rollback Procedures

### Quick Rollback

If an update breaks functionality:

**Option 1: Boot previous kernel**

1. Reboot and hold Shift during boot
2. Select "Advanced options for Ubuntu"
3. Choose previous kernel version
4. Test if GPU works with old kernel

**Option 2: Downgrade packages**

```bash
# Find available versions
apt policy rocm-hip-runtime

# Install specific version
sudo apt install rocm-hip-runtime=<previous-version>
```

### Full Rollback

For major issues requiring complete reinstall:

```bash
# Remove all ROCm components
sudo amdgpu-install --uninstall

# Remove repository
sudo rm /etc/apt/sources.list.d/rocm.list
sudo rm /etc/apt/sources.list.d/amdgpu.list

# Clean up
sudo apt autoremove
sudo apt clean

# Remove residual files
sudo rm -rf /opt/rocm*

# Reinstall known-good version
wget https://repo.radeon.com/amdgpu-install/<known-good-version>/ubuntu/noble/amdgpu-install_<version>_all.deb
sudo apt install ./amdgpu-install_<version>_all.deb
sudo amdgpu-install --usecase=rocm
```

## Monitoring for Updates

### AMD Announcements

Monitor ROCm releases:

- [ROCm GitHub Releases](https://github.com/RadeonOpenCompute/ROCm/releases)
- [AMD ROCm Documentation](https://rocm.docs.amd.com/)
- [AMD Community Forums](https://community.amd.com/)

### Automated Notifications

Set up update notifications:

```bash
# Check for ROCm updates weekly (add to crontab)
0 0 * * 0 apt update && apt list --upgradable 2>/dev/null | grep -E 'rocm|amdgpu' | mail -s "ROCm Updates Available" your@email.com
```

### Version Tracking

Keep track of working configurations:

```bash
# Save working state
cat > ~/rocm-working-config.txt << EOF
Date: $(date)
Kernel: $(uname -r)
ROCm: $(cat /opt/rocm/.info/version 2>/dev/null || echo "not installed")
amdgpu: $(modinfo amdgpu | grep ^version)
HSA_OVERRIDE_GFX_VERSION: $HSA_OVERRIDE_GFX_VERSION
EOF
```

## Best Practices

### Before Updating

1. **Check release notes** - Review changes and known issues
2. **Verify compatibility** - Ensure new version supports your GPU
3. **Backup configuration** - Save environment variables and settings
4. **Test non-critical first** - If possible, test on non-production system

### Update Schedule

| Component | Frequency | Notes |
|-----------|-----------|-------|
| Security patches | Immediately | Via apt upgrade |
| Point releases | Monthly | After community testing |
| Major versions | Quarterly | Test thoroughly first |

### Stability vs Features

For production workloads:

- Prefer stable releases over bleeding edge
- Wait for community feedback on new versions
- Keep rollback capability ready
- Document working configurations

## See Also

- [ROCm Installation](rocm-installation.md) - Initial setup
- [Memory Configuration](memory-configuration.md) - APU memory settings
- [Troubleshooting](../reference/troubleshooting.md) - Common issues
