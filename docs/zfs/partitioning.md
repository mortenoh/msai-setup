# Partitioning for ZFS

ZFS can consume **whole disks** or **partitions**. Both work, but they have meaningfully different operational profiles. This page covers when to use which, how to do it correctly on Linux, and the alignment / wiping details that catch people out.

## Whole disk vs partition

| Approach | When to use | Caveats |
|---|---|---|
| **Whole disk** | A disk dedicated to ZFS, no other use. ZFS creates a GPT internally and uses the whole device. | ZFS may enable disk-write-cache; some controllers complain. Some BIOS firmwares dislike a GPT-only "data" disk with no recognisable partitions. |
| **Partition** | A disk shared with something else (e.g. boot OS + ZFS pool member). | You control the partition table; ZFS sees whatever leaf you give it. |

For the MS-S1 MAX build:

- **Primary 2 TB NVMe (slot 1, PCIe 4.0 x4)**: partitioned. Holds EFI + `/boot` + ext4 root + a ZFS partition.
- **Secondary 4 TB NVMe (slot 2, PCIe 4.0 x1)**: whole disk. Dedicated to ZFS.

Even on a whole-disk install, modern OpenZFS will write a GPT with a single ZFS partition spanning the disk — it's *effectively* still a partition, just one created and managed automatically.

## Identify the right device — always

The single most expensive mistake in storage administration is acting on the wrong device. Always identify disks by **persistent ID**, not by kernel-name (`nvme0n1`, `sda`, etc.) which can change between boots.

```bash
# Persistent device IDs (model + serial)
ls -la /dev/disk/by-id/ | grep -E 'nvme|ata' | grep -v part

# Match each to its kernel name and physical slot
lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,WWN
nvme list                       # NVMe-specific
sudo smartctl -i /dev/nvme0n1   # confirm serial vs. label

# Walk the disk tree
sudo lshw -class disk -short
```

A clean snippet for the MS-S1 MAX (yours will differ on serials):

```
nvme-Samsung_SSD_990_PRO_2TB_S6XXXXXXXX -> ../../nvme0n1
nvme-Samsung_SSD_990_PRO_4TB_S7XXXXXXXX -> ../../nvme1n1
```

**Use these `/dev/disk/by-id/...` paths** in every `zpool` command. Kernel names work too but reorder between boots, which means an exported pool may not re-import cleanly. The pool stores a `path` for each device and falls back to scanning if it's missing — but starting from a stable path saves time.

## GPT in 60 seconds

ZFS targets GPT (GUID Partition Table), not the old MBR format. The relevant facts:

- GPT has a primary table at LBA 1 and a backup at the end of the disk. They must agree; tools warn if they don't.
- Each partition has a **GUID type** (a 16-byte UUID) that hints at use. Linux mostly ignores it on read but tools display it for sanity. ZFS doesn't read the type code itself.
- GPT supports up to 128 partitions by default; you'll never come close.
- The first usable LBA is typically 2048 (1 MiB), which is the canonical **alignment** boundary.

Type codes you'll see in `gdisk`:

| Code | Name | Used for |
|---|---|---|
| `EF00` | EFI System | `/boot/efi` |
| `8300` | Linux filesystem | ext4, xfs, btrfs |
| `8200` | Linux swap | swap partition |
| `BF00` | Solaris /usr & Mac ZFS | Historically used for ZFS; on Linux this is informational only |
| `8E00` | Linux LVM | If you use LVM |

For Linux ZFS, **the partition type code is cosmetic** — ZFS does not introspect it. You can use `8300` (Linux filesystem) and it will work identically. Older tutorials use `BF00`; either is fine.

## Alignment

A partition is "aligned" when its start LBA falls on a boundary that matches the disk's physical block size. Misalignment causes every logical 4 KiB block to cross a physical block boundary, doubling I/O on those reads/writes.

- All modern partitioning tools default to 1 MiB alignment (start LBA = 2048).
- This satisfies 512n, 512e, 4Kn, and even 8 KiB NVMe drives.
- Manual `fdisk` interactions on older systems sometimes broke this. Stick to defaults and you're fine.

Confirm alignment on an existing partition:

```bash
sudo parted /dev/nvme0n1 align-check optimal 4
sudo parted /dev/nvme0n1 unit s print free
```

If `align-check optimal` returns "aligned", you're set.

## Wiping a disk before reuse

If a disk has any prior filesystem, ZFS label, or partition signature, OpenZFS will refuse `zpool create` without `-f` and many tools will be confused. Wipe metadata cleanly first:

```bash
# Confirm the device first
lsblk /dev/nvme1n1

# Zap GPT + MBR + all known FS signatures
sudo wipefs -a /dev/nvme1n1
sudo sgdisk --zap-all /dev/nvme1n1

# For paranoia / repurposing a previously encrypted disk:
sudo blkdiscard /dev/nvme1n1      # NVMe / SATA SSD trim/discard all blocks
# or for older spinning rust:
# sudo dd if=/dev/zero of=/dev/nvme1n1 bs=1M count=100   # just clear headers
```

`blkdiscard` is the fastest correct option on NVMe/SATA SSDs — it tells the controller to mark all LBAs as deallocated. The drive then returns zeros (or randomness, depending on TRIM behavior) until something writes to those LBAs again.

!!! danger "blkdiscard is irreversible"
    `blkdiscard /dev/X` flat-out throws away the contents of the whole device. Triple-check the path.

## Creating the partition layout — primary NVMe

This is the partition table the [Disk Partitioning](../ubuntu/installation/disk-partitioning.md) doc has the installer create. The commands below are what you'd run **manually** from a rescue/live USB if you wanted to do it without the installer.

```bash
# Identify primary NVMe (2 TB, slot 1)
DISK=/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_2TB_<your-serial>

# Wipe
sudo wipefs -a "$DISK"
sudo sgdisk --zap-all "$DISK"

# Create the four partitions
sudo sgdisk \
    --new=1:0:+512MiB --typecode=1:ef00 --change-name=1:"EFI System" \
    --new=2:0:+1GiB   --typecode=2:8300 --change-name=2:"Linux /boot" \
    --new=3:0:+1024GiB --typecode=3:8300 --change-name=3:"Linux root" \
    --new=4:0:0       --typecode=4:8300 --change-name=4:"ZFS pool member" \
    "$DISK"

# Reload partition table
sudo partprobe "$DISK"

# Show
lsblk "$DISK"
```

`sgdisk` is the scriptable form of `gdisk`. The `+512MiB` syntax sizes from the current allocation cursor; `0:0` and `0` mean "next available start" and "end of disk".

After this, the partition paths you'll pass to `zpool create` are:

```
/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_2TB_<serial>-part4
/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_4TB_<serial>             (whole disk)
```

## Why use `-part4` not `nvme0n1p4`

When you reboot, kernel device names can swap (`nvme0n1` and `nvme1n1` may switch based on enumeration order). Partition IDs under `/dev/disk/by-id/` are stable across reboots because they're derived from the disk's serial number plus partition index.

If a pool was created with `nvme0n1p4` and that name moves at next boot, ZFS will still find the device by scanning labels — but the pool will show as `UNAVAIL` until it does. Starting with `by-id` avoids that brief panic.

## Partition naming sanity checks

```bash
# What partitions exist on the disk?
sudo parted /dev/nvme0n1 unit GiB print

# Confirm by-id paths exist
ls -la /dev/disk/by-id/ | grep nvme | grep part

# Inspect ZFS label, if any (should be empty on a freshly partitioned device)
sudo zdb -l /dev/disk/by-id/nvme-Samsung_SSD_990_PRO_2TB_<serial>-part4
```

`zdb -l` reads the four ZFS labels at the start and end of a vdev. On an empty partition it returns "no label", which is what you want before `zpool create`.

## Common gotchas

### A pool refuses to create with "EFI label exists"

`zpool create -f` will force, but cleaner to wipe first:

```bash
sudo wipefs -a /dev/disk/by-id/nvme-...-part4
sudo zpool create ...
```

### partprobe says "device or resource busy"

Something has the partition table cached. Reboot, or — if you know what's holding it — stop that service. On a live USB this is rare.

### `lsblk` shows partitions but `/dev/disk/by-id/*-part4` is missing

Race during udev settle. Try:

```bash
sudo udevadm trigger
sudo udevadm settle
ls -la /dev/disk/by-id/ | grep part
```

### NVMe-specific: namespace vs partition

Some enterprise NVMe drives expose multiple **namespaces** (`nvme0n1`, `nvme0n2`), which are like separate devices on the same controller. The consumer NVMe drives in the MS-S1 MAX have a single namespace each, so this won't bite you. Worth knowing if you ever scavenge a datacenter SSD.

## Next steps

- Try the partitioning steps on virtual disks first: [VirtualBox Lab](virtualbox-lab.md).
- Then proceed to [Pool Creation](pool-creation.md) to build the pool itself.
