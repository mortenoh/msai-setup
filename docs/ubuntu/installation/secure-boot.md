# Secure Boot Configuration

UEFI Secure Boot provides cryptographic verification of boot components, ensuring only authorized code runs during system startup.

## Understanding Secure Boot

### What Secure Boot Does

Secure Boot creates a chain of trust from firmware to operating system:

```
┌─────────────────────────────────────────────────────────────┐
│                    UEFI Firmware                             │
│              (Contains Platform Key - PK)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              v Verifies
┌─────────────────────────────────────────────────────────────┐
│                    GRUB Bootloader                           │
│                 (Signed with Microsoft key)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              v Verifies
┌─────────────────────────────────────────────────────────────┐
│                     Linux Kernel                             │
│                 (Signed with Canonical key)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              v Verifies (when enabled)
┌─────────────────────────────────────────────────────────────┐
│                   Kernel Modules                             │
│              (Must be signed or MOK enrolled)                │
└─────────────────────────────────────────────────────────────┘
```

### Key Types

| Key | Owner | Purpose |
|-----|-------|---------|
| Platform Key (PK) | Hardware OEM | Master key, controls all others |
| Key Exchange Key (KEK) | Microsoft/OEM | Authorizes db/dbx updates |
| Signature Database (db) | Microsoft/Canonical | Allowed signing keys |
| Forbidden Signatures (dbx) | Microsoft | Revoked/blacklisted hashes |

### Ubuntu's Secure Boot Implementation

Ubuntu uses a "shim" bootloader signed by Microsoft:

1. **shim** - Signed by Microsoft, loaded by firmware
2. **GRUB** - Signed by Canonical, verified by shim
3. **Kernel** - Signed by Canonical, verified by GRUB
4. **Modules** - Must be signed or enrolled via MOK

## Enabling Secure Boot

### In BIOS/UEFI Settings

1. Enter firmware settings (F2, Del, or manufacturer-specific key)
2. Navigate to Security or Boot section
3. Find "Secure Boot" option
4. Set to "Enabled"
5. Ensure "Secure Boot Mode" is "Standard" (not "Custom")
6. Save and exit

### Verify Secure Boot Status

After booting Ubuntu:

```bash
# Check if Secure Boot is enabled
mokutil --sb-state

# Expected output for enabled:
# SecureBoot enabled

# Alternative check
dmesg | grep -i secure
# Look for: "Secure boot enabled"
```

### Common Issues

**"Secure Boot violation" error:**

- The bootloader or kernel isn't properly signed
- Solution: Re-download the official ISO, verify checksums

**System won't boot with Secure Boot enabled:**

- Third-party drivers may not be signed
- Solution: Enroll MOK (Machine Owner Key) or disable Secure Boot temporarily

## Machine Owner Keys (MOK)

MOK allows you to sign and load modules not signed by Canonical.

### When MOK is Needed

- Using **amdgpu-dkms** (the ROCm install path on Strix Halo)
- Using **zfs-dkms** (the ZFS data pool in this build)
- Loading custom kernel modules
- Other third-party DKMS modules (VirtualBox additions, vendor drivers, etc.)

!!! note "This build keeps Secure Boot disabled"
    The default for this MS-S1 MAX build is **Secure Boot off** (see [BIOS Setup](../../getting-started/bios-setup.md)). All MOK procedures below apply only if you specifically want Secure Boot enabled. Don't enroll a MOK casually — the operational complexity (every kernel/DKMS upgrade re-prompts) usually doesn't pay back the marginal threat-model improvement on a private headless server.

### MOK Enrollment Process

**During DKMS installation:**

Ubuntu automatically prompts for MOK enrollment when installing unsigned modules:

```bash
# Example: Installing a DKMS module triggers enrollment
sudo apt install amdgpu-dkms
# System prompts for MOK password (one-time, on first DKMS module install)
```

**Manual enrollment:**

```bash
# Generate your own key
openssl req -new -x509 -newkey rsa:2048 \
    -keyout /root/MOK.priv \
    -outform DER -out /root/MOK.der \
    -nodes -days 36500 \
    -subj "/CN=My Module Signing Key/"

# Enroll the key
sudo mokutil --import /root/MOK.der
# Enter a one-time password (you'll need this on next reboot)

# Reboot and complete enrollment in MOK Manager
sudo reboot
```

**On reboot:**

1. MOK Manager appears automatically
2. Select "Enroll MOK"
3. Select "Continue"
4. Enter the password you set
5. Select "Reboot"

### Sign Modules with Your Key

```bash
# Sign a kernel module
sudo /usr/src/linux-headers-$(uname -r)/scripts/sign-file \
    sha256 /root/MOK.priv /root/MOK.der \
    /path/to/module.ko
```

### Verify MOK Enrollment

```bash
# List enrolled keys
mokutil --list-enrolled

# Check specific key
mokutil --test-key /root/MOK.der
```

## Secure Boot and Third-Party Software

### amdgpu-dkms / ROCm (relevant to this build)

The ROCm install path includes `amdgpu-dkms`. Under Secure Boot it must be MOK-signed:

```bash
sudo apt install amdgpu-dkms
# Ubuntu prompts for a MOK password; reboot, complete enrollment in MOK Manager.
# Subsequent kernel upgrades re-build and re-sign automatically.
```

If `modprobe amdgpu` fails after a kernel update with "key was rejected by service", the rebuilt module didn't get signed — re-run DKMS:

```bash
sudo dkms autoinstall
sudo modprobe amdgpu
```

### ZFS (relevant to this build for the data pool)

```bash
sudo apt install zfs-dkms
# Same MOK flow as amdgpu-dkms above.
```

Without MOK signing, `modprobe zfs` fails silently and the pool won't import at boot. Confirm:

```bash
sudo dkms status
sudo modprobe zfs && echo OK || journalctl --since "5 minutes ago" | grep -i zfs
```

### VirtualBox

```bash
# VirtualBox modules need signing
sudo apt install virtualbox-dkms
# Follow MOK enrollment prompts
```

## Troubleshooting Secure Boot

### Check Current State

```bash
# Secure Boot status
mokutil --sb-state

# Enrolled keys
mokutil --list-enrolled

# Check if module is signed
modinfo <module_name> | grep sig

# Kernel lockdown status
cat /sys/kernel/security/lockdown
```

### Module Won't Load

```bash
# Check why module failed
dmesg | grep -i "module verification"

# Check module signature
modinfo <module_name> | grep sig
```

**Solutions:**

1. Enroll MOK and sign the module
2. Temporarily disable Secure Boot to test
3. Use officially signed alternatives

### Lost MOK Password

If you forget the MOK enrollment password:

```bash
# Remove pending enrollment request
sudo mokutil --reset

# Re-import with new password
sudo mokutil --import /root/MOK.der
```

### Disable Secure Boot Temporarily

For troubleshooting, you may need to disable Secure Boot:

1. Reboot and enter BIOS/UEFI settings
2. Navigate to Security or Boot section
3. Disable Secure Boot
4. Save and reboot

!!! warning "Security Impact"
    Disabling Secure Boot removes boot-time integrity verification. Re-enable after troubleshooting.

## Secure Boot Best Practices

### Security Recommendations

| Practice | Reason |
|----------|--------|
| Keep Secure Boot enabled | Prevents boot-time malware |
| Use official packages | Pre-signed, no MOK needed |
| Protect MOK private key | Treat like root credentials |
| Set BIOS/Setup password | Prevent unauthorized changes |
| Monitor dbx updates | Stay current on revoked keys |

### Key Management

```bash
# Store MOK keys securely
sudo chmod 400 /root/MOK.priv
sudo chmod 444 /root/MOK.der

# Backup keys (encrypted)
sudo tar czf - /root/MOK.* | gpg -c > mok-backup.tar.gz.gpg
```

### Auditing

```bash
# Check Secure Boot configuration
bootctl status

# Verify bootloader signature
sbverify --cert /path/to/cert.pem /boot/efi/EFI/ubuntu/shimx64.efi
```

## Secure Boot Decision Matrix

| Scenario | Secure Boot Recommendation |
|----------|---------------------------|
| Production server, standard software | Enable |
| Development machine, frequent module changes | Consider disabling or use MOK |
| High-security environment | Enable, restrict physical access |
| Using `amdgpu-dkms` / ROCm (this build's GPU path) | Enable with MOK, or leave disabled per [BIOS Setup](../../getting-started/bios-setup.md) |
| Using `zfs-dkms` (this build's data pool) | Enable with MOK, or leave disabled |
| Virtual machine (guest) | Depends on hypervisor support |

## Next Step

Continue to [Disk Partitioning](disk-partitioning.md) to plan your storage layout with encryption.
