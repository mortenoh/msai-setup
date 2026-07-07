# Disk Partitioning

This page is the canonical disk layout for the MS-S1 MAX install: **plain ext4 root (500 GB) on the primary 4 TB NVMe, with the leftover space and the entire secondary 2 TB NVMe becoming two independent ZFS pools**. Root itself is deliberately *not* on ZFS — see [Why this layout](#why-this-layout) and, if you want OS boot environments anyway, the [ZFS Root (Alternative)](zfs-root-alternative.md).

Authoritative spec (slot speeds matter — see warning below): [Minisforum MS-S1 MAX product page](https://www.minisforum.com/products/ms-s1-max).

!!! note "Two storage slots, two speeds — drives swapped from this project's original layout"
    The MS-S1 MAX exposes **two M.2 slots: PCIe 4.0 x4 (primary) and PCIe 4.0 x1 (secondary)**. The x1 slot tops out around 2 GB/s. This build puts the **4 TB drive in the fast x4 slot** and the **2 TB drive in the slow x1 slot**, so the larger-capacity drive gets the faster bus and hosts everything performance-sensitive (root, Incus storage, databases, model files).

## Canonical Layout — ext4 root, two independent ZFS pools

This is the layout used by [`hardware.md`](../../getting-started/hardware.md), [`zfs/partitioning.md`](../../zfs/partitioning.md), `incus/storage.md`, and the [`rebuild-checklist.md`](../../operations/rebuild-checklist.md).

### Primary NVMe (slot 1, 4 TB, PCIe 4.0 x4) — boot + root + hot data

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| EFI System | 512 MB | FAT32 (esp) | `/boot/efi` | UEFI bootloader (GRUB) |
| Boot | 1 GB | ext4 | `/boot` | Kernel, initramfs |
| Root | 500 GB | ext4 | `/` | Host OS, `/home`, Incus/compose config |
| Pool member | ~3.4 TB | (ZFS) | — | Remainder -> `hot`, added post-install |

Subiquity's guided/custom storage screen creates the first three partitions directly. The ~3.4 TB left over becomes a ZFS pool member **after** the OS is installed — the installer never touches it.

### Secondary NVMe (slot 2, 2 TB, PCIe 4.0 x1) — bulk cold data

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| ZFS data | 2 TB | (ZFS) | — | Entire disk -> `tank`, a fully independent pool |

`tank` is not part of `hot` and is never striped with it — these are two separate pools on two separate disks, imported independently. See [ZFS Pool Creation](../../zfs/pool-creation.md) for the exact `zpool create` invocations for both.

### Why this layout

- **Ext4 root is boring infrastructure.** Excellent recovery tooling, zero operational surprises, mature `e2fsck` and GRUB. When the OS breaks, you reinstall it — fast, and the host is disposable by design (everything that matters lives on ZFS or off-host).
- **Separate `/boot`** survives a corrupted root and gives GRUB a stable home — the original design's reasoning, restored.
- **ZFS is for data, not root.** Both pools give the OS's *data* — containers, VMs, databases, media — checksums, compression, snapshots, and replication. The thin OS layer trades snapshot rollback for the simplicity of a boring bootloader; under Incus everything stateful is already on ZFS with full snapshot coverage.
- **Two independent pools, not one striped across both drives.** ZFS's allocator balances a striped pool's top-level vdevs by free space, not by "put this on the fast one." Two separate pools give a real, enforceable guarantee: anything on `hot` is on the fast drive, full stop.
- **No LVM.** Neither pool needs volume management — ZFS's own datasets already do what LVM would, and the ext4 root either fits in 500 GB or it doesn't (it does, with room to spare).
- **No LUKS by default** on this build. The host lives on a private network behind UFW/Tailscale; LUKS just adds a remote-unlock problem on a headless box. See the [Encrypted Alternative](#encrypted-alternative-zfs-native-encryption-or-luks-lvm) section below if you need encryption.

## Creating the Layout

The root partitioning is handled by Ubuntu's guided installer (Subiquity) — there is no manual live-environment dance for the canonical build. The ZFS pools are created **post-install, from the running system**.

### Step 1 — partition the primary in the installer

At the installer's storage screen choose **Custom storage layout** (not guided/entire-disk — it would reformat the wrong drive on a two-NVMe box). On the primary 4 TB NVMe, create:

1. **EFI System Partition** — 512 MB, `fat32`, mount `/boot/efi`.
2. **Boot** — 1 GB, `ext4`, mount `/boot`.
3. **Root** — 500 GB, `ext4`, mount `/`.
4. Leave the remaining ~3.4 TB as **free space** — it becomes the `hot` pool member later.

Leave the secondary 2 TB NVMe **untouched** (no partitions) — ZFS claims the whole disk post-install. Full click-by-click steps are in the [Installation Walkthrough](installation-walkthrough.md).

### Step 2 — create the `hot` pool on the primary's leftover space

After first boot, add a partition spanning the free space and create the pool. This runs from the **running system**, so there is no `-R /mnt` altroot and no `canmount`/`ROOT` dance — `hot` is a plain data pool:

```bash
# Add a ZFS pool-member partition (p4) on the primary's ~3.4 TB of free space
# (prefer /dev/disk/by-id/... over /dev/nvme0n1 for stability across boots)
sgdisk -n4:0:0 -t4:BF00 "$PRIMARY_DISK"

zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    hot "${PRIMARY_DISK}-part4"

# Datasets. Default mountpoint is /hot (mirrors /tank); hot/incus is the
# Incus storage backend and never mounts at a path itself.
zfs create -o mountpoint=none hot/incus
zfs create hot/db
zfs create hot/ai
```

There is **no `hot/home`** — `/home` lives on the ext4 root, as in this project's original design. See [ZFS Datasets](../../zfs/datasets.md) for the per-dataset property details (`hot/db` recordsize, `hot/ai` compression, etc.).

### Partition and create `tank` (secondary, slow drive)

```bash
sgdisk --zap-all "$SECONDARY_DISK"
sgdisk -n1:0:0 -t1:BF00 "$SECONDARY_DISK"

zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    tank "${SECONDARY_DISK}-part1"
```

`tank` holds media, backups, and other cold data (`tank/media`, `tank/backups`, etc. — see [ZFS Datasets](../../zfs/datasets.md)). Default mountpoint `/tank`.

!!! danger "Verify device paths before running any of this"
    `zpool create` and `sgdisk` are destructive. Confirm `$PRIMARY_DISK` and `$SECONDARY_DISK` resolve to the 4 TB and 2 TB drives respectively (`lsblk`, `nvme list`) before running anything above — and double-check that the `sgdisk -n4` on the primary targets free space, not an existing partition.

## Mount Options for Security

Root, `/boot`, and `/boot/efi` are classic ext4/FAT filesystems with fstab entries; the ZFS pools mount natively via ZFS properties. Harden the fstab mounts after install:

```
# /etc/fstab — the ext4 root layout; hot/tank datasets mount via ZFS, not fstab
/dev/disk/by-uuid/<efi-uuid>    /boot/efi   vfat   umask=0077,fmask=0077,dmask=0077   0 1
/dev/disk/by-uuid/<boot-uuid>   /boot       ext4   defaults,nodev,nosuid,noexec       0 2
/dev/disk/by-uuid/<root-uuid>   /           ext4   defaults                           0 1
```

For datasets, the ZFS equivalents of `nodev,nosuid,noexec` are per-dataset properties — set them where it makes sense (e.g. a dataset backing a service's scratch/tmp space):

```bash
zfs set devices=off setuid=off exec=off hot/some-dataset
```

Root itself keeps ext4 defaults (needs `exec`, `setuid`, `devices` for a working system). If you want stricter isolation, mount `/tmp` and `/var/log` as separate filesystems (or `tmpfs` for `/tmp`) with `nodev,nosuid,noexec`.

## Post-Partitioning Verification

```bash
# ext4 layout on the primary
lsblk "$PRIMARY_DISK"
findmnt /
cat /etc/fstab

# Pool status for both pools
zpool status hot
zpool status tank

# Dataset layout
zfs list -r hot
zfs list -r tank
```

## ZFS Root — Documented Alternative

If you want the OS itself covered by ZFS snapshots — a bad `apt upgrade` or kernel becoming a one-keystroke **boot-environment rollback** instead of a reinstall — root can live on a ZFS pool booted by [ZFSBootMenu](https://zfsbootmenu.org/) instead of ext4 + GRUB. That path is fully documented, including the honest reasons it is *not* the canonical build (no Subiquity support, upstream guides stop at 22.04, the boot path can't be rehearsed in the lab, and the OpenZFS + kernel 7.0 combo is flagged experimental):

**-> [ZFS Root (Alternative)](zfs-root-alternative.md)**

The live-tested `msai lab install-zfs-root` command rehearses that flow in a VM.

## Encrypted Alternative — ZFS Native Encryption or LUKS + LVM

If you need encryption at rest (regulated environment, physical-theft concern):

- **ZFS native encryption** is the natural fit for the *data* pools — set `-O encryption=aes-256-gcm -O keyformat=passphrase -O keylocation=prompt` (or `file:///path/to/keyfile` for unattended unlock) on `hot` and/or `tank` at `zpool create` time. No LUKS layer, no LVM. This encrypts everything stateful (containers, VMs, databases, media) while leaving the small ext4 OS root in the clear.
- **LUKS + LVM** is the route if you also want the ext4 **root** encrypted. The trade-offs (unlock mechanism on a headless box: walk-up, `dropbear-initramfs`, or Clevis+Tang) are the classic ones. See `cryptsetup` and the LVM man pages for the mechanics; this project doesn't duplicate them.
- If you take the [ZFS Root (Alternative)](zfs-root-alternative.md) path, ZFS native encryption on the root pool composes cleanly with ZFSBootMenu, which prompts for the passphrase at boot — the recommended encryption option there.

If you go the encryption route, plan the unlock mechanism *before* you encrypt — locking yourself out of the only host is not a fun recovery exercise.

## Next Step

Continue to [Installation Walkthrough](installation-walkthrough.md) for the step-by-step guided install.
