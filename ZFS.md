# ZFS: preserving pools across an OS reinstall

This host has two ZFS pools that must survive a reinstall to Ubuntu Server. A
zpool's configuration lives *on the disks* (in the pool labels/metadata), not in
the OS, so the reinstall does not touch a pool as long as its member disks are
not wiped. You export before, and import after.

## Current layout (recorded 2026-07-12)

```
pool   device (by-id)                                        mountpoint
lab    nvme-KINGSTON_SKC3000D4096G_50026B76876EF04A-part3    /data/lab
store  nvme-CT2000P310SSD8_253652DC56D3                      /data/store
```

Neither pool uses native encryption (`encryption=off` everywhere), so there are
no keys to reload.

Datasets and their mountpoints:

```
lab                    /data/lab
lab/models             /data/lab/models
lab/incus              legacy      <-- Incus ZFS storage backend (whole subtree)
lab/incus/...          legacy          managed by the Incus daemon, not fstab
store                  /data/store
store/downloads        /data/store/downloads
store/media            /data/store/media
store/steam            /data/store/steam
```

### Important: `lab/incus` is Incus-managed

The entire `lab/incus` subtree uses `mountpoint=legacy` and is mounted/unmounted
by the Incus daemon (its `zfs` storage driver), NOT by `zfs-mount` or `/etc/fstab`.
Do not add fstab entries for these. After the reinstall these datasets import
with the pool, but Incus itself needs to be reinstalled and pointed back at the
existing storage pool for it to use them again (its instance/config database is
separate from the ZFS data). If you don't care about the old Incus instances,
you can ignore or destroy the `lab/incus` subtree later.

## Before the reinstall (export)

sudo needs a password in this shell, so run these yourself. Incus holds the
`lab/incus` datasets, so stop it first or the `lab` export will report "pool is
busy".

```bash
# 1. Stop Incus so it releases the lab/incus datasets
sudo systemctl stop incus incus.socket

# 2. Export both pools cleanly (marks them not-in-use so no -f is needed later)
sudo zpool export store
sudo zpool export lab

# 3. Confirm they are gone from the active system but still importable
zpool list                 # should list neither
sudo zpool import          # should show both 'store' and 'lab' as importable
```

If an export still says the pool is busy, find the holder with
`sudo fuser -vm /data/store` (or `/data/lab`), stop it, and retry. As a last
resort you can skip the clean export — you'll just import with `-f` afterward.

## During the Ubuntu Server install

Install ONLY to the OS disk. Do NOT let the installer format or partition the
pool member disks:

- `lab` lives on the Kingston SKC3000D (partition 3 of that NVMe).
- `store` lives on the Crucial CT2000P310 NVMe.

Use manual partitioning if unsure and leave those two devices untouched. This is
the single real risk in the whole procedure.

## After Ubuntu Server is installed (import)

```bash
# 1. Install ZFS tooling
sudo apt update
sudo apt install -y zfsutils-linux

# 2. See what is importable (read-only, makes no changes)
sudo zpool import

# 3. Import by-id (stable device naming), cleanly exported so no -f needed
sudo zpool import -d /dev/disk/by-id store
sudo zpool import -d /dev/disk/by-id lab
#   if you skipped the clean export earlier, add -f:
#   sudo zpool import -f -d /dev/disk/by-id lab

# 4. Verify datasets mounted at their stored mountpoints
zpool status
zfs list -o name,mountpoint,mounted
```

Non-legacy datasets (`/data/lab`, `/data/lab/models`, `/data/store` and its
children) remount automatically at their stored mountpoints — that property
lives in the pool. The `lab/incus/*` legacy datasets stay unmounted until Incus
is reinstalled and reconnected to the pool.

## Make pools auto-import and mount on every boot

Importing once does not persist. Set the cachefile and enable the systemd units
(Ubuntu's default mechanism):

```bash
sudo zpool set cachefile=/etc/zfs/zpool.cache store
sudo zpool set cachefile=/etc/zfs/zpool.cache lab

sudo systemctl enable zfs-import-cache.service zfs-mount.service zfs.target
sudo systemctl enable zfs-import.target zfs-volume.target 2>/dev/null || true

sudo reboot
# after reboot, confirm:
zfs list -o name,mountpoint,mounted
```

Alternative to the cachefile approach: `sudo systemctl enable zfs-import-scan.service`
imports any pool found at boot without a cachefile.

## Notes / gotchas

- Legacy mountpoints (`lab/incus/*`) will never auto-mount via `zfs-mount`; they
  are the Incus daemon's responsibility. Do not add them to `/etc/fstab`.
- No dataset here uses native encryption, so there are no keys to `zfs load-key`.
- Prefer `zpool import -d /dev/disk/by-id` so the pool references stable device
  names rather than `/dev/nvmeXn1` which can renumber across boots/hardware.
