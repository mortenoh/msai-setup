# Datasets

A dataset is a ZFS filesystem (or zvol) inside a pool. Datasets are cheap, can be created/destroyed/renamed at will, and have **per-dataset properties** that you tune for the workload they hold. This page covers the dataset layout for this build, the property reference, and the inheritance model that ties it all together.

## The dataset layout for this build

```
tank/
+-- ai/                  # GGUF/safetensors model files; compression=off, recordsize=1M
+-- backups/             # cold archive target; compression=zstd-3
+-- containers/          # Docker bind-mount targets per service
|   +-- pihole/
|   +-- traefik/
|   +-- authentik/
|   +-- homepage/
|   +-- ...
+-- db/                  # databases (Postgres, MariaDB); recordsize=16K
|   +-- postgres/
|   +-- mariadb/
+-- media/               # Plex/Jellyfin libraries; recordsize=1M
+-- nextcloud-app/       # Nextcloud application files
+-- nextcloud-data/      # Nextcloud user data; the snapshot-critical one
+-- vm/                  # VM disk images; recordsize=64K
|   +-- win11/
|   +-- linux-utility/
```

The split into per-service datasets under `containers/` is so you can:

- Snapshot one service's data without dragging in others (`zfs snapshot tank/containers/nextcloud@before-update`).
- Replicate selectively (sanoid/syncoid per dataset).
- Set per-service quotas if one service starts misbehaving.

## A note on device placement

Datasets are units of *policy* (compression, recordsize, quotas), **not** units of *device placement*. It's a common instinct to want "put `tank/vm` and `tank/db` on the fast primary NVMe (PCIe 4.0 x4) and let `tank/media` live on the slow secondary (x1)". With this build's single pool, **you can't**:

- `tank` is one pool made of two top-level striped vdevs (the ~1 TB primary partition + the whole 4 TB secondary).
- ZFS's allocator spreads every new write across all top-level vdevs based on free space. There is no per-dataset "pin this dataset to that device" knob in stock ZFS.
- So a dataset's blocks end up on *both* drives regardless of what you'd prefer, and the slower x1 link is part of every dataset's effective performance.

If guaranteed placement on the fast drive actually matters for a workload (a latency-sensitive database, say), the only real option is to **not** fold the primary drive's leftover space into `tank` and instead build a **second, separate pool** from it — e.g. a `fast` pool on the primary partition alone, with the workload's dataset there. That buys real placement guarantees at the cost of the shared capacity and a second pool to manage. For this homelab the single-pool simplicity wins; treat "keep hot data on the fast drive" as a soft preference the allocator can't actually honour, not a guarantee. See [Pool Creation -> What this pool is not](pool-creation.md#what-this-pool-is-not).

## Create the datasets

After [Pool Creation](pool-creation.md):

```bash
# AI models — already-compressed binary blobs; big sequential reads
sudo zfs create -o recordsize=1M -o compression=off tank/ai

# Cold archive backups — CPU-for-space tradeoff
sudo zfs create -o compression=zstd-3 tank/backups

# Per-service container state (defaults are fine; child datasets can override)
sudo zfs create tank/containers
sudo zfs create tank/containers/pihole
sudo zfs create tank/containers/traefik
sudo zfs create tank/containers/authentik
sudo zfs create tank/containers/homepage
sudo zfs create tank/containers/uptime-kuma

# Databases
sudo zfs create -o recordsize=16K tank/db
sudo zfs create tank/db/postgres
sudo zfs create tank/db/mariadb

# Media (Plex / Jellyfin libraries)
sudo zfs create -o recordsize=1M tank/media

# Nextcloud — split user data from app state
sudo zfs create tank/nextcloud-data
sudo zfs create tank/nextcloud-app

# VM disks (use 64K records; zvols are separate — see vm-storage.md)
sudo zfs create -o recordsize=64K tank/vm
```

Verify:

```bash
zfs list
zfs get compression,recordsize -r tank
```

## Property inheritance

Properties cascade from parent to child unless explicitly overridden. The `SOURCE` column in `zfs get` tells you where a value comes from:

```bash
zfs get -o name,property,value,source compression tank tank/media tank/ai
```

Possible sources:

- `default` — the ZFS-wide default value.
- `local` — set explicitly on this dataset.
- `inherited from <ancestor>` — picked up from a parent.
- `received` — set via `zfs receive`, can be overridden by `local`.
- `temporary` — set with `zfs mount -o` for one mount cycle only.

To unset a local value and re-inherit from parent:

```bash
sudo zfs inherit recordsize tank/db
sudo zfs inherit -r recordsize tank/db   # recursive
```

This is essential for cleanup — if you experiment with properties and want to "reset to defaults", `zfs inherit -r` is the way.

## The property reference

ZFS has many properties. The ones that matter most:

### Compression

```bash
zfs set compression=lz4 tank/foo
zfs set compression=zstd-3 tank/backups
zfs set compression=off tank/ai
```

See [Concepts -> Compression](concepts.md#compression). Options:

| Value | Speed | Ratio | Use |
|---|---|---|---|
| `off` | N/A | 1.0 | Already-compressed data (GGUF, safetensors, encrypted blobs) |
| `lz4` | Very fast | Modest (1.2-1.5x typical) | Default; safe everywhere |
| `zstd` (= `zstd-3`) | Fast | Better than lz4 | Backup / cold data target |
| `zstd-1`..`zstd-19` | Slower with higher levels | Better at higher levels | `zstd-3` is the sweet spot |
| `gzip-1`..`gzip-9` | Old, slow | Similar to zstd at same effort | Legacy; prefer zstd |

### Recordsize

```bash
zfs set recordsize=1M tank/media
zfs set recordsize=16K tank/db
zfs set recordsize=64K tank/vm
```

See [Tuning -> `recordsize` per workload](tuning.md#recordsize-per-workload). Only affects writes after the change; existing data keeps its block size until rewritten.

For zvols use `volblocksize=…` at creation time (and only at creation time — it's immutable). See [VM Storage](vm-storage.md).

### Atime, relatime

```bash
zfs set atime=off tank
```

Set at the pool root, inherited everywhere unless a child overrides. There's almost no good reason to leave atime on in 2026.

If something specifically needs atime (some mail spools), use:

```bash
zfs set atime=on tank/special
zfs set relatime=on tank/special   # only updates atime when older than mtime
```

### Mountpoint, mounted

```bash
zfs set mountpoint=/srv/media tank/media        # explicit
zfs set mountpoint=none tank/foo                 # don't mount this dataset
zfs set mountpoint=legacy tank/bar               # don't auto-mount; use /etc/fstab
zfs inherit mountpoint tank/baz                  # inherit from parent
```

- `none` is useful for "namespace organisation" datasets that hold child datasets but don't need to be mounted themselves.
- `legacy` is for /-on-ZFS setups or specific cases needing fstab control. Not relevant here.

### Quotas and reservations

```bash
# Quota — hard upper bound (this dataset and its children combined)
zfs set quota=500G tank/nextcloud-data

# refquota — hard upper bound on this dataset only (NOT including snapshots or children)
zfs set refquota=200G tank/db/postgres

# Reservation — guarantee minimum free space (this dataset and children)
zfs set reservation=50G tank/db

# refreservation — guarantee minimum free for the dataset itself, excluding snapshots
zfs set refreservation=10G tank/db/postgres
```

| Setting | What it counts |
|---|---|
| `quota` | dataset + descendants + snapshots |
| `refquota` | dataset only, excluding descendants and snapshots |
| `reservation` | dataset + descendants + snapshots |
| `refreservation` | dataset only |

Use `refquota` if you want to cap "live data in this one dataset" regardless of how many snapshots accumulate. Use `quota` for "the entire subtree, including snapshots, cannot grow past N".

### Sync mode

```bash
zfs set sync=standard tank/foo    # default
zfs set sync=disabled tank/scratch
zfs set sync=always tank/critical
```

`standard` is correct for almost everything. See [Tuning -> sync mode](tuning.md#sync-mode).

### `primarycache` / `secondarycache`

```bash
zfs set primarycache=metadata tank/media
zfs set primarycache=all tank/db        # default
```

What ARC (`primary`) and L2ARC (`secondary`) cache for this dataset:

- `all`: metadata + data (default).
- `metadata`: metadata only.
- `none`: neither.

`metadata` is the right choice for datasets where the data is too big and too cold to benefit from caching (media archives, cold backups). Frees ARC for hotter datasets.

### `xattr` and `acltype`

Set at pool creation as `xattr=sa` and `acltype=posixacl` per [Pool Creation](pool-creation.md). Don't change.

### `dedup` — leave OFF

```bash
# DO NOT do this on a home pool:
# zfs set dedup=on tank/foo
```

Block-level inline deduplication. Requires the DDT (deduplication table) to live in RAM; size is roughly 320 bytes per unique block. For a TB-sized dataset that's a lot of RAM. Almost always a net loss for home workloads.

If you have very specific data that dedups well (VM images of the same OS, backup-image targets), the **safe** alternative is to use `zstd` compression — modern ZFS compresses common runs of zeros (and many other patterns) implicitly.

### `dnodesize=auto`

Set at pool creation. Lets ZFS allocate larger inode-equivalents when needed. Pairs with `xattr=sa`. Don't change.

### `redundant_metadata`

```bash
zfs set redundant_metadata=most tank/media   # ~5-10% space savings on bulk data
```

Default `all` keeps three copies of metadata for redundancy. `most` keeps fewer copies of some metadata levels. Save space on bulk-data datasets if storage is tight; leave default on critical metadata.

### `casesensitivity`, `normalization`, `utf8only`

Set at creation only:

- `casesensitivity=sensitive` (default) — POSIX.
- `casesensitivity=insensitive` — for Mac/Windows-like compatibility (Samba share targets).
- `casesensitivity=mixed` — strange middle ground; avoid.
- `normalization=formD` — Unicode form for filename normalization; rarely used on Linux.

If you're going to share a dataset over SMB for use by Macs, `casesensitivity=insensitive` and `normalization=formD` are reasonable. For Linux-only access, defaults are correct.

### `user properties`

Custom properties prefixed `module:property` (must contain `:`):

```bash
sudo zfs set com.example:owner='morten' tank/foo
sudo zfs set com.example:cost-center='homelab' tank/foo
zfs get com.example:owner tank/foo
```

ZFS doesn't interpret these. Use them for annotations, automation hooks, tooling state (sanoid/syncoid use `com.sun:auto-snapshot` and friends).

## Per-dataset properties for this build

```bash
# AI models — read-mostly, sequential, already compressed
sudo zfs set recordsize=1M tank/ai
sudo zfs set compression=off tank/ai
sudo zfs set primarycache=metadata tank/ai     # models are mmap'd; ARC won't help much

# Cold backups
sudo zfs set compression=zstd-3 tank/backups
sudo zfs set primarycache=metadata tank/backups

# Media archives
sudo zfs set recordsize=1M tank/media
sudo zfs set primarycache=metadata tank/media
sudo zfs set redundant_metadata=most tank/media   # save metadata space on bulk

# Databases — small random IO, ARC hits matter
sudo zfs set recordsize=16K tank/db

# VM disks — balanced
sudo zfs set recordsize=64K tank/vm

# Defaults are fine for everything else
```

Verify:

```bash
zfs get -r recordsize,compression,primarycache tank | grep -v default
```

This shows only the explicitly-set values, which is a useful audit.

## Permissions on bind-mount targets

Containers run as non-root users. The bind-mount target needs to be owned by the right UID/GID **inside the container** (which may not be a real user on the host).

Typical containers:

| Container | UID | GID | Notes |
|---|---|---|---|
| Nextcloud (official) | 33 | 33 | `www-data` in the image |
| linuxserver.io images (Sonarr/Radarr/Jellyfin/Plex/etc.) | configurable via `PUID/PGID` env | typically 1000 | Default values; you set them |
| Postgres official | 999 | 999 | `postgres` user in image |
| Plex official | 997 | 997 | |
| Authentik | 1000 | 1000 | |

Set ownership on each dataset to match:

```bash
# Nextcloud
sudo chown -R 33:33 /mnt/tank/nextcloud-data /mnt/tank/nextcloud-app

# Postgres for Authentik
sudo chown -R 999:999 /mnt/tank/db/postgres

# linuxserver.io services with PUID/PGID=1000 (your user)
sudo chown -R 1000:1000 /mnt/tank/containers/sonarr /mnt/tank/containers/radarr
```

Confirm the container documentation for each service before assuming. UIDs vary.

## Listing, renaming, destroying

```bash
# List with useful columns
zfs list -o name,used,available,referenced,mountpoint,compression,recordsize

# Filter
zfs list -r tank/containers
zfs list -t all                                # include snapshots and bookmarks
zfs list -t filesystem,volume                  # exclude snapshots

# Rename — also moves the mountpoint if it's inherited
sudo zfs rename tank/foo tank/bar

# Destroy — IRREVERSIBLE
sudo zfs destroy tank/foo                       # only if empty / no snapshots
sudo zfs destroy -r tank/foo                    # with descendants
sudo zfs destroy -R tank/foo                    # with descendants AND dependent clones
sudo zfs destroy tank/foo@snapshot              # destroy one snapshot
```

`zfs destroy` is the most dangerous command in the suite. Always:

- `zfs list -r <target>` first to confirm what you're about to destroy.
- Have a recent off-host backup.
- Consider taking one final snapshot and replicating it before destroying.

## Mounting and unmounting

```bash
# Mount/unmount a single dataset
sudo zfs mount tank/foo
sudo zfs unmount tank/foo

# Mount everything (normally done by zfs-mount.service at boot)
sudo zfs mount -a

# Show what's mounted
zfs mount
```

If `zfs mount` fails with "filesystem already mounted" or "directory not empty", investigate before forcing — you may be hiding data.

## Snapshot, clone, hold — see [Snapshots](snapshots.md)

That's its own page.

## Next steps

- [Snapshots](snapshots.md) — manage point-in-time copies, clones, holds, send/receive.
- [VM Storage](vm-storage.md) — zvols and libvirt integration.
- [Docker Integration](docker-integration.md) — bind-mount patterns.
- [Operations](operations.md) — scrubs, replace, expand.
