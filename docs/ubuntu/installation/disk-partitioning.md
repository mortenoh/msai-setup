# Disk Partitioning

This page is the canonical disk layout for the MS-S1 MAX install: **root-on-ZFS via ZFSBootMenu on the primary 4 TB NVMe, with a fully independent second ZFS pool on the secondary 2 TB NVMe**.

Authoritative spec (slot speeds matter — see warning below): [Minisforum MS-S1 MAX product page](https://www.minisforum.com/products/ms-s1-max).

!!! note "Two storage slots, two speeds — drives swapped from this project's original layout"
    The MS-S1 MAX exposes **two M.2 slots: PCIe 4.0 x4 (primary) and PCIe 4.0 x1 (secondary)**. The x1 slot tops out around 2 GB/s. This build puts the **4 TB drive in the fast x4 slot** and the **2 TB drive in the slow x1 slot** — the reverse of an earlier draft of this project, so the larger-capacity drive gets the faster bus and hosts everything performance-sensitive (root, Incus storage, databases, model files).

## Canonical Layout — root-on-ZFS, two independent pools

This is the layout used by [`hardware.md`](../../getting-started/hardware.md), [`zfs/partitioning.md`](../../zfs/partitioning.md), `incus/storage.md`, and the [`rebuild-checklist.md`](../../operations/rebuild-checklist.md).

### Primary NVMe (slot 1, 4 TB, PCIe 4.0 x4) — boot + root + hot data

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| EFI System | 512 MB | FAT32 (esp) | `/boot/efi` | Holds the ZFSBootMenu EFI binary |
| Pool member | ~4 TB | (ZFS) | — | Entire remainder -> `rpool` |

No separate `/boot` partition and no classic `bpool`/`rpool` split. ZFSBootMenu finds a kernel/initramfs pair directly inside a dataset at boot time — it doesn't need GRUB's workaround of a small, feature-limited boot pool sitting outside the main pool. One pool, one EFI partition, that's it.

### Secondary NVMe (slot 2, 2 TB, PCIe 4.0 x1) — bulk cold data

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| ZFS data | 2 TB | (ZFS) | — | Entire disk -> `tank`, a fully independent pool |

`tank` is not part of `rpool` and is never striped with it — these are two separate pools on two separate disks, imported independently. See [ZFS Pool Creation](../../zfs/pool-creation.md) for the exact `zpool create` invocations for both.

### Why this layout

- **Root-on-ZFS, not ext4.** The OS itself gets ZFS's checksums, compression, and — critically — **snapshots as boot environments**. A bad `apt upgrade` or kernel update is a ZFSBootMenu boot-environment rollback, not a reinstall. See `START.md`'s "Things this build intentionally avoids" for why this project moved away from ext4 root.
- **ZFSBootMenu over GRUB.** GRUB's ZFS module has real limitations (it can't read every ZFS feature flag, historically breaking if a pool gains a feature GRUB doesn't understand), which is why classic root-on-ZFS guides split a `bpool`/`rpool` pair to work around it. ZFSBootMenu boots via its own dracut-built EFI executable instead of GRUB reading ZFS directly, so that split isn't needed — simpler, and no risk of an incompatible pool feature bricking the bootloader.
- **Two independent pools, not one striped across both drives.** An earlier draft of this project used a single pool spanning both NVMe drives. That doesn't actually let you control which drive a given dataset's writes land on — ZFS's allocator balances a striped pool's top-level vdevs by free space, not by "put this on the fast one." Two separate pools give a real, enforceable guarantee: anything on `rpool` is on the fast drive, full stop.
- **No LVM.** Neither pool needs volume management — ZFS's own datasets already do what LVM would, without a second abstraction layer on top.
- **No LUKS by default** on this build. The host lives on a private network behind UFW/Tailscale; LUKS just adds a remote-unlock problem on a headless box. ZFS native encryption is the modern equivalent if you want encryption later — see the "Encrypted alternative" section below.

## Creating the Layout

This is deliberately a manual process. Ubuntu Server's installer (Subiquity), including its `autoinstall` automation, has **no root-on-ZFS path** — that only exists in the Desktop installer's guided mode, and even that doesn't support the two-independent-pools split this build wants. The full step-by-step command sequence (live environment, partitioning, `zpool create` for both pools, bootstrapping Ubuntu into `rpool`, chroot, ZFSBootMenu install) lives in [Installation Walkthrough](installation-walkthrough.md) — this section is the reference summary.

### Partition the primary 4 TB NVMe

```bash
# From the live/rescue environment — replace with your actual device path
# (prefer /dev/disk/by-id/... over /dev/nvme0n1 for stability across boots)
sgdisk --zap-all "$PRIMARY_DISK"
sgdisk -n1:1M:+512M -t1:EF00 "$PRIMARY_DISK"   # EFI
sgdisk -n2:0:0      -t2:BF00 "$PRIMARY_DISK"   # ZFS pool member (rest of disk)
```

### Create `rpool` (primary, fast drive)

```bash
zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on -O canmount=off -O mountpoint=none \
    -R /mnt \
    rpool "${PRIMARY_DISK}-part2"

zfs create -o canmount=off -o mountpoint=none rpool/ROOT
zfs create -o canmount=noauto -o mountpoint=/ rpool/ROOT/ubuntu
zfs create -o mountpoint=/home rpool/home
```

`rpool/ROOT/ubuntu` uses `canmount=noauto` deliberately — with more than one boot environment present, ZFS must not try to auto-mount all of them; ZFSBootMenu (or an explicit `zfs mount`) decides which one actually becomes `/` at boot.

### Partition and create `tank` (secondary, slow drive)

```bash
sgdisk --zap-all "$SECONDARY_DISK"
sgdisk -n1:0:0 -t1:BF00 "$SECONDARY_DISK"

zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    -R /mnt \
    tank "${SECONDARY_DISK}-part1"
```

`tank` doesn't need the `canmount=off` / `ROOT` dance `rpool` does — it holds no boot environments, just data datasets (`tank/media`, `tank/backups`, etc. — see [ZFS Datasets](../../zfs/datasets.md)).

!!! danger "Verify device paths before running any of this"
    `zpool create` and `sgdisk --zap-all` are destructive. Confirm `$PRIMARY_DISK` and `$SECONDARY_DISK` resolve to the 4 TB and 2 TB drives respectively (`lsblk`, `nvme list`) before running anything above — see [Installation Walkthrough](installation-walkthrough.md) for the full verification sequence.

## Mount Options for Security

The EFI partition still uses traditional fstab-style mount options; everything else is a ZFS dataset property instead of an fstab line:

```
# /etc/fstab — EFI partition only; rpool/tank datasets mount via ZFS, not fstab
/dev/disk/by-uuid/<efi-uuid>   /boot/efi   vfat   umask=0077,fmask=0077,dmask=0077   0 1
```

For datasets, the ZFS equivalents of `nodev,nosuid,noexec` are per-dataset properties — set them where it makes sense (e.g. a dataset backing a service's scratch/tmp space):

```bash
zfs set devices=off setuid=off exec=off rpool/some-dataset
```

Root itself (`rpool/ROOT/ubuntu`) keeps the defaults (needs `exec`, `setuid`, `devices` for a working system) — this granularity is the point of per-dataset properties over one fstab line for the whole filesystem.

## Post-Partitioning Verification

```bash
# Pool status for both pools
zpool status rpool
zpool status tank

# Dataset layout
zfs list -r rpool
zfs list -r tank

# EFI partition
lsblk "$PRIMARY_DISK"
```

## Ext4 Root — Documented Alternative

Earlier drafts of this project used a plain ext4 root (with ZFS only for data, never root). That's no longer this build's default, but it's a reasonable, simpler choice if you don't want ZFSBootMenu's boot-environment machinery — it trades snapshot-based OS rollback for the operational simplicity of `e2fsck` and a bootloader (GRUB) everyone already knows.

### Ext4 root layout

| Partition | Size | Filesystem | Mount |
|-----------|------|------------|-------|
| EFI System | 512 MB | FAT32 | `/boot/efi` |
| Boot | 1 GB | ext4 | `/boot` |
| Root | remainder or a fixed size (e.g. 100-200 GB) | ext4 | `/` |
| Pool member | rest of the drive | — | ZFS, added post-install |

With this layout, Subiquity's guided/custom storage screen handles the root partitioning directly (no manual live-environment process needed) — see the ext4 install steps preserved in this page's git history, or adapt the [ZFS pool creation](../../zfs/pool-creation.md) commands above to a single pool spanning the leftover space on both drives if you want the original single-pool design instead.

## Encrypted Alternative — ZFS Native Encryption or LUKS + LVM

If you need encryption at rest (regulated environment, physical-theft concern):

- **ZFS native encryption** is the natural fit now that root itself is ZFS — set `-O encryption=aes-256-gcm -O keyformat=passphrase -O keylocation=prompt` (or `file:///path/to/keyfile` for unattended unlock) on `rpool` at creation time. No LUKS layer, no LVM, and it composes cleanly with ZFSBootMenu (which can prompt for the passphrase at boot). This is the recommended path if you decide you want encryption on this build.
- **LUKS + LVM** remains documented for the ext4-root alternative above, if you go that route instead — the trade-offs (unlock mechanism on a headless box: walk-up, `dropbear-initramfs`, or Clevis+Tang) are unchanged from before. See `cryptsetup` and the LVM man pages for the mechanics; this project doesn't duplicate them.

If you go the encryption route on either layout, plan the unlock mechanism *before* you encrypt — locking yourself out of the only host is not a fun recovery exercise.

## Next Step

Continue to [Installation Walkthrough](installation-walkthrough.md) for the full, step-by-step manual install process.
