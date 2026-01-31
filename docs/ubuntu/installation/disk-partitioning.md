# Disk Partitioning

A well-planned partition layout enhances security, simplifies management, and enables full disk encryption.

## Partitioning Strategies

### Why Partition Layout Matters

| Benefit | How Partitioning Helps |
|---------|------------------------|
| Security | Separate /tmp, /var with noexec, nosuid options |
| Stability | Prevent log floods from filling root filesystem |
| Encryption | LUKS on separate partitions for different protection levels |
| Flexibility | LVM enables resizing without reinstallation |
| Recovery | Separate /boot allows recovery even if root is corrupted |

### Ubuntu 24.04 Partitioning Options

The installer offers three approaches:

1. **Use entire disk** - Automatic, no encryption option
2. **Use entire disk with LVM** - Automatic, optional encryption
3. **Custom storage layout** - Full control (recommended)

## LVM Fundamentals

### What LVM Provides

Logical Volume Manager abstracts physical storage:

```
┌────────────────────────────────────────────────────────────┐
│                    Logical Volumes                          │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│    │  root   │  │  home   │  │   var   │  │  swap   │     │
│    │  20 GB  │  │  50 GB  │  │  30 GB  │  │   8 GB  │     │
│    └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
├────────────────────────────────────────────────────────────┤
│                     Volume Group                            │
│                      "vg-system"                            │
│                       (108 GB)                              │
├────────────────────────────────────────────────────────────┤
│                   Physical Volumes                          │
│         ┌─────────────────────────────────────┐            │
│         │         /dev/nvme0n1p3              │            │
│         │         (LUKS encrypted)             │            │
│         │            ~500 GB                   │            │
│         └─────────────────────────────────────┘            │
└────────────────────────────────────────────────────────────┘
```

### LVM Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Physical Volume (PV) | Raw storage device/partition | /dev/nvme0n1p3 |
| Volume Group (VG) | Pool of physical volumes | vg-system |
| Logical Volume (LV) | Virtual partition | lv-root, lv-home |

### LVM Advantages

- **Resize online** - Grow filesystems without unmounting (ext4, XFS)
- **Snapshots** - Create point-in-time copies
- **Thin provisioning** - Over-allocate storage
- **Span disks** - Volume groups can span multiple physical drives
- **LUKS integration** - Encrypt the entire VG with single passphrase

## LUKS Encryption

### What LUKS Encrypts

LUKS (Linux Unified Key Setup) provides block-level encryption:

```
┌─────────────────────────────────────────┐
│             Filesystem                   │
│            (ext4, xfs)                   │
├─────────────────────────────────────────┤
│          Logical Volume                  │
│        (/dev/vg-system/lv-root)         │
├─────────────────────────────────────────┤
│         dm-crypt (decrypted)             │
├─────────────────────────────────────────┤
│      LUKS Container (encrypted)          │
│         (/dev/nvme0n1p3)                 │
└─────────────────────────────────────────┘
```

### LUKS Benefits

| Benefit | Description |
|---------|-------------|
| Data-at-rest protection | Data unreadable without passphrase |
| Compliance | Meets encryption requirements (HIPAA, PCI, etc.) |
| Decommissioning | Secure disposal by destroying key |
| Full volume encryption | Every byte encrypted, including metadata |

### Encryption Considerations

**What's encrypted:**

- All data on LUKS volume
- Filesystem metadata
- Swap contents
- Temporary files in /tmp, /var

**What's NOT encrypted:**

- /boot partition (contains kernel, initramfs)
- EFI System Partition
- GRUB configuration

!!! info "Boot Partition Security"
    The unencrypted /boot can be a target for Evil Maid attacks. Consider Secure Boot to mitigate this risk.

## Recommended Partition Layout

### Standard Server Layout

For a 500 GB system disk:

| Partition | Size | Type | Mount | Purpose |
|-----------|------|------|-------|---------|
| EFI | 512 MB | FAT32 | /boot/efi | UEFI bootloader |
| Boot | 1 GB | ext4 | /boot | Kernel, initramfs |
| LUKS+LVM | Remaining | LUKS2 | — | Encrypted container |

**Logical volumes within LVM:**

| Volume | Size | Mount | Options |
|--------|------|-------|---------|
| root | 25 GB | / | defaults |
| home | 50 GB | /home | nodev,nosuid |
| var | 50 GB | /var | nodev,nosuid |
| var-log | 20 GB | /var/log | nodev,nosuid,noexec |
| tmp | 5 GB | /tmp | nodev,nosuid,noexec |
| swap | RAM size | swap | — |
| (free) | ~350 GB | — | Reserved for growth |

### Server with ZFS Data Pool

When using ZFS for data storage (like for virtualization or file server), reserve space:

| Partition | Size | Type | Purpose |
|-----------|------|------|---------|
| EFI | 512 MB | FAT32 | UEFI bootloader |
| Boot | 1 GB | ext4 | Kernel |
| LUKS+LVM | 100 GB | LUKS2 | OS volumes |
| Unallocated | Remaining | — | ZFS pool later |

### Minimal Server Layout

For constrained environments:

| Volume | Size | Mount |
|--------|------|-------|
| root | 15 GB | / |
| swap | 2 GB | swap |

## Creating Partitions During Installation

### Using the Ubuntu Installer

**Step 1: Select Custom Layout**

When you reach the storage configuration screen:
- Select "Custom storage layout"
- Click "Done"

**Step 2: Create EFI Partition**

1. Select the target disk
2. Add partition:
   - Size: 512 MB
   - Format: FAT32
   - Mount: /boot/efi

**Step 3: Create Boot Partition**

1. Add partition:
   - Size: 1 GB
   - Format: ext4
   - Mount: /boot

**Step 4: Create LUKS Volume**

1. Add partition:
   - Size: Remaining (or specific size if reserving space)
   - Format: Leave unformatted
2. Select the new partition
3. Choose "Create encrypted volume"
4. Enter encryption passphrase (use a strong passphrase)

**Step 5: Create LVM Volume Group**

1. Select the encrypted volume
2. Choose "Create volume group"
3. Name: `vg-system`

**Step 6: Create Logical Volumes**

For each volume:
1. Select the volume group
2. Choose "Create logical volume"
3. Set name, size, filesystem, mount point

## Manual Partitioning (Advanced)

### From Command Line

If you need to partition manually (e.g., from rescue mode):

```bash
# Create partitions with gdisk
sudo gdisk /dev/nvme0n1

# Commands:
# n - new partition (EFI: type ef00, Linux: type 8300)
# w - write and exit

# Format EFI
sudo mkfs.fat -F32 /dev/nvme0n1p1

# Format boot
sudo mkfs.ext4 /dev/nvme0n1p2

# Create LUKS container
sudo cryptsetup luksFormat --type luks2 /dev/nvme0n1p3

# Open LUKS
sudo cryptsetup open /dev/nvme0n1p3 cryptroot

# Create LVM
sudo pvcreate /dev/mapper/cryptroot
sudo vgcreate vg-system /dev/mapper/cryptroot

# Create logical volumes
sudo lvcreate -L 25G -n lv-root vg-system
sudo lvcreate -L 50G -n lv-home vg-system
sudo lvcreate -L 50G -n lv-var vg-system
sudo lvcreate -L 20G -n lv-var-log vg-system
sudo lvcreate -L 5G -n lv-tmp vg-system
sudo lvcreate -L 8G -n lv-swap vg-system

# Format volumes
sudo mkfs.ext4 /dev/vg-system/lv-root
sudo mkfs.ext4 /dev/vg-system/lv-home
sudo mkfs.ext4 /dev/vg-system/lv-var
sudo mkfs.ext4 /dev/vg-system/lv-var-log
sudo mkfs.ext4 /dev/vg-system/lv-tmp
sudo mkswap /dev/vg-system/lv-swap
```

## Mount Options for Security

### Recommended fstab Options

```
# /etc/fstab
/dev/vg-system/lv-root    /          ext4  defaults                    0 1
/dev/vg-system/lv-home    /home      ext4  defaults,nodev,nosuid       0 2
/dev/vg-system/lv-var     /var       ext4  defaults,nodev,nosuid       0 2
/dev/vg-system/lv-var-log /var/log   ext4  defaults,nodev,nosuid,noexec 0 2
/dev/vg-system/lv-tmp     /tmp       ext4  defaults,nodev,nosuid,noexec 0 2
/dev/vg-system/lv-swap    swap       swap  defaults                    0 0
```

### Mount Option Reference

| Option | Effect |
|--------|--------|
| nodev | Prevent device files |
| nosuid | Ignore setuid/setgid bits |
| noexec | Prevent execution |

## LUKS Configuration Details

### Strong Passphrase Guidelines

- Minimum 20 characters
- Mix of words, numbers, symbols
- Consider a passphrase: "correct horse battery staple"
- Store securely (password manager, separate from server)

### LUKS Key Slots

LUKS supports multiple key slots (passphrases):

```bash
# View key slots
sudo cryptsetup luksDump /dev/nvme0n1p3

# Add additional passphrase
sudo cryptsetup luksAddKey /dev/nvme0n1p3

# Remove a key slot
sudo cryptsetup luksRemoveKey /dev/nvme0n1p3
```

### Recovery Key

Create a recovery key for emergency access:

```bash
# Add a recovery key
dd if=/dev/urandom of=/root/luks-recovery.key bs=512 count=4
sudo cryptsetup luksAddKey /dev/nvme0n1p3 /root/luks-recovery.key

# Store this file securely offline!
# Then remove from server:
shred -u /root/luks-recovery.key
```

## Post-Partitioning Verification

After installation, verify your layout:

```bash
# View block devices
lsblk

# View LVM configuration
sudo pvs
sudo vgs
sudo lvs

# View mounted filesystems with options
mount | grep -E "^/dev"

# Verify LUKS
sudo cryptsetup status cryptroot
```

## Next Step

Continue to [Installation Walkthrough](installation-walkthrough.md) to proceed through the Ubuntu installer.
