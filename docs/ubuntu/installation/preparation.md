# Pre-Installation Preparation

Proper preparation ensures a smooth installation and establishes a secure baseline.

## Hardware Verification

### Check System Compatibility

Before installation, verify your hardware is compatible with Ubuntu 24.04 LTS.

```bash
# From a live USB or existing Linux system
# Check CPU architecture and features
lscpu | grep -E "(Architecture|Flags)"

# Check available RAM
free -h

# List storage devices
lsblk

# Check network interfaces
ip link show
```

### UEFI vs Legacy BIOS

Ubuntu 24.04 supports both UEFI and Legacy BIOS boot modes. UEFI is strongly recommended for:

- **Secure Boot support** - Cryptographic verification of boot components
- **GPT partitioning** - Supports disks larger than 2 TB
- **Faster boot times** - More efficient boot process
- **Modern security features** - Better integration with TPM

Check your current boot mode:

```bash
# If this directory exists, you're booted in UEFI mode
ls /sys/firmware/efi
```

### Hardware Compatibility Checklist

| Component | Check | Action if Incompatible |
|-----------|-------|------------------------|
| CPU | 64-bit capable | Required for 24.04 |
| RAM | 1 GB minimum | Upgrade or use server-minimal |
| Storage | SATA/NVMe supported | Use compatible controller |
| Network | Recognized by kernel | May need firmware package |
| GPU | Basic framebuffer works | Usually fine for server |

## Download and Verify

### Obtain the ISO

Download Ubuntu Server 24.04 LTS from the official source:

```bash
# Download from official mirror
wget https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso
```

!!! warning "Official Sources Only"
    Always download from `releases.ubuntu.com` or official mirrors. Never use ISOs from untrusted sources.

### Verify ISO Integrity

Verification ensures the ISO hasn't been corrupted or tampered with.

**Step 1: Download verification files**

```bash
wget https://releases.ubuntu.com/24.04/SHA256SUMS
wget https://releases.ubuntu.com/24.04/SHA256SUMS.gpg
```

**Step 2: Verify GPG signature**

```bash
# Import Ubuntu's signing key
gpg --keyid-format long --keyserver hkp://keyserver.ubuntu.com \
    --recv-keys 0x843938DF228D22F7B3742BC0D94AA3F0EFE21092

# Verify signature
gpg --verify SHA256SUMS.gpg SHA256SUMS
```

You should see "Good signature from Ubuntu CD Image Automatic Signing Key".

**Step 3: Verify checksum**

```bash
sha256sum -c SHA256SUMS 2>&1 | grep ubuntu-24.04-live-server-amd64.iso
```

Expected output: `ubuntu-24.04-live-server-amd64.iso: OK`

### Verification Summary

| Check | Purpose |
|-------|---------|
| GPG signature | Confirms checksums are from Canonical |
| SHA256 checksum | Confirms ISO wasn't corrupted in transit |
| Official download | Ensures you have the authentic image |

## Create Boot Media

### USB Drive Preparation

**Using dd (Linux/macOS):**

```bash
# Identify the USB device (be careful!)
lsblk

# Write ISO to USB (replace /dev/sdX with your device)
sudo dd if=ubuntu-24.04-live-server-amd64.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

!!! danger "Double-Check Device"
    The `dd` command will overwrite the target device without warning. Verify you have the correct device before running.

**Using Balena Etcher (Cross-platform):**

1. Download Balena Etcher from https://etcher.balena.io/
2. Select the Ubuntu ISO
3. Select your USB drive
4. Click "Flash"

### Verify Boot Media

After creating the boot media, verify it works:

1. Boot a test system from the USB
2. Select "Check disc for defects" from the boot menu
3. Let the verification complete

## BIOS/UEFI Configuration

### Access Firmware Settings

Access varies by manufacturer:

| Manufacturer | Common Keys |
|--------------|-------------|
| Dell | F2, F12 |
| HP | F10, Esc |
| Lenovo | F1, F2 |
| Supermicro | Del, F2 |
| ASUS | Del, F2 |

### Recommended Settings

**Security Settings:**

| Setting | Recommended Value | Purpose |
|---------|-------------------|---------|
| Secure Boot | Enabled | Verify boot components |
| TPM | Enabled | Hardware security module |
| Boot Password | Set | Prevent unauthorized boot changes |
| Setup Password | Set | Protect BIOS settings |

**Boot Settings:**

| Setting | Recommended Value | Purpose |
|---------|-------------------|---------|
| Boot Mode | UEFI | Modern boot process |
| Fast Boot | Disabled | Allows USB boot, full POST |
| CSM/Legacy | Disabled | UEFI only |
| Boot Order | USB first (temporarily) | Boot from installation media |

**Virtualization Settings (if using KVM):**

| Setting | Recommended Value | Purpose |
|---------|-------------------|---------|
| VT-x/AMD-V | Enabled | Hardware virtualization |
| VT-d/IOMMU | Enabled | Device passthrough |
| ACS Override | Enabled (if available) | Better IOMMU grouping |

## Network Planning

### IP Address Assignment

Decide on network configuration before installation:

**Option 1: DHCP during install, static post-install**

- Simpler installation process
- Configure static IP via Netplan after first boot
- Recommended for most scenarios

**Option 2: Static IP during install**

- Requires knowing network details upfront
- Immediate accessibility at known address
- Better for headless installs

### Required Network Information

For static IP configuration, gather:

| Information | Example | Your Value |
|-------------|---------|------------|
| IP Address | 192.168.1.100 | |
| Subnet Mask | 255.255.255.0 | |
| Gateway | 192.168.1.1 | |
| DNS Server(s) | 1.1.1.1, 8.8.8.8 | |
| Hostname | server01 | |
| Domain | example.com | |

### Network Interface Identification

Modern Ubuntu uses predictable network interface names:

| Pattern | Meaning | Example |
|---------|---------|---------|
| `enp*s*` | PCI Ethernet | enp5s0 |
| `eno*` | Onboard Ethernet | eno1 |
| `ens*` | Hotplug slot | ens192 |

Identify your interfaces before installation if possible:

```bash
# From live USB
ip link show
```

## Pre-Installation Checklist

Before starting the installer, confirm:

- [ ] Hardware meets minimum requirements
- [ ] UEFI mode enabled in BIOS
- [ ] Secure Boot enabled (optional but recommended)
- [ ] TPM enabled (if available)
- [ ] ISO downloaded and verified
- [ ] Boot media created and tested
- [ ] Network information gathered
- [ ] Hostname decided
- [ ] Disk partitioning plan determined
- [ ] Encryption passphrase chosen (if using LUKS)
- [ ] Initial user credentials prepared

## Next Step

Continue to [Secure Boot Configuration](secure-boot.md) to understand and configure UEFI Secure Boot, or skip to [Disk Partitioning](disk-partitioning.md) if you're not using Secure Boot.
