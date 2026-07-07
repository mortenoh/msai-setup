# Datasets

A dataset is a ZFS filesystem (or zvol) inside a pool. Datasets are cheap, can be created/destroyed/renamed at will, and have **per-dataset properties** that you tune for the workload they hold. This page covers the dataset layout for this build, the property reference, and the inheritance model that ties it all together.

## The dataset layout for this build

Two independent pools, one per physical drive. `hot` (fast 4 TB NVMe) holds everything performance-sensitive; `tank` (slow 2 TB NVMe) holds bulk/cold data. Root is not here — it lives on a small ext4 partition on the same primary NVMe (see [Disk Partitioning](../ubuntu/installation/disk-partitioning.md)). See [Pool Creation](pool-creation.md) for how each pool is created and the device layout.

```
hot/                   # fast 4 TB NVMe (slot 1, PCIe 4.0 x4) — hot data + Incus instances
+-- incus/              # Incus's ZFS storage backend — DO NOT hand-carve; Incus owns it
|   +-- containers/...   #   one child per container (created automatically by Incus)
|   +-- virtual-machines/... #   one child per VM (a zvol; created automatically by Incus)
|   +-- images/, custom/, deleted/
+-- db/                  # databases (Postgres, MariaDB); recordsize=16K
+-- ai/                  # GGUF/safetensors model files; compression=off, recordsize=1M

tank/                    # slow 2 TB NVMe (slot 2, PCIe 4.0 x1) — bulk/cold data
+-- media/               # Plex/Jellyfin libraries; recordsize=1M, compression=lz4
+-- nextcloud-data/      # Nextcloud user data; the snapshot-critical one
+-- nextcloud-app/       # Nextcloud application files
+-- backups/             # cold archive target; compression=zstd-3
```

!!! danger "`hot/incus` is Incus's — do not create datasets under it by hand"
    Every container and VM is a ZFS dataset that **Incus** creates and manages beneath `hot/incus`. Do not `zfs create`, rename, or `zfs destroy` anything under `hot/incus` yourself — you'll desynchronize Incus's database from on-disk reality. Manage instance storage through `incus` commands; use raw `zfs` under `hot/incus` only for *reading* (inspecting, sending snapshots for backup). This is the [Incus storage backend](../incus/storage.md) — that page is the source of truth for it. The other `hot` datasets (`db`, `ai`) are yours to manage normally.

There is intentionally **no `tank/containers/<svc>` or `tank/vm` tree** anymore. Under the old single-pool design those held Docker bind-mount targets and raw qcow2/zvol VM disks; both are superseded — per-instance storage is Incus's job now (`hot/incus`), and `db`/`ai` moved to the fast `hot`. Services that still want a *bind-mounted host dataset* (media, model files, Nextcloud data) use the datasets above, mounted into the instance — see [Docker Integration](docker-integration.md) and [Incus storage](../incus/storage.md#bind-mounting-host-datasets-into-containers).

## A note on device placement

Datasets are units of *policy* (compression, recordsize, quotas), **not** units of *device placement* — but this build sidesteps the usual limitation by using **two pools instead of one**. Placement is therefore a real, enforceable guarantee here:

- Anything on **`hot`** is on the fast 4 TB drive (PCIe 4.0 x4). That's why `hot/incus` (all instance storage), `hot/db`, and `hot/ai` live there.
- Anything on **`tank`** is on the slow 2 TB drive (PCIe 4.0 x1). Media, Nextcloud data, and cold backups tolerate the slower link.

An earlier draft of this project used a *single* pool striped across both drives. In that design you genuinely couldn't pin a dataset to a device — ZFS's allocator spreads writes across all top-level vdevs by free space, with no per-dataset device knob. The two-pool split is precisely what makes "hot data on the fast drive" a guarantee rather than a hope. See [Pool Creation → Two pools, not one stripe](pool-creation.md#two-pools-not-one-stripe).

## Create the datasets

The hot-data datasets on `hot` and the data datasets on `tank` are created here — **post-install, from the running system** (root is already up on ext4, so there's no live-environment bootstrap for these). **`hot/incus` is created empty and then handed to Incus** — you do not create the per-instance children; Incus does.

```bash
# --- hot (fast drive) ---

# Incus storage backend — created once, then Incus owns everything beneath it
sudo zfs create -o mountpoint=none hot/incus

# Databases — small random IO
sudo zfs create -o recordsize=16K hot/db

# AI models — already-compressed binary blobs; big sequential reads
sudo zfs create -o recordsize=1M -o compression=off hot/ai

# --- tank (slow drive) ---

# Media (Plex / Jellyfin libraries)
sudo zfs create -o recordsize=1M tank/media

# Nextcloud — split user data from app state
sudo zfs create tank/nextcloud-data
sudo zfs create tank/nextcloud-app

# Cold archive backups — CPU-for-space tradeoff
sudo zfs create -o compression=zstd-3 tank/backups
```

Then point Incus at `hot/incus` (during [Incus installation](../incus/installation.md)) so it builds and manages its own `containers/`, `virtual-machines/`, `images/`, … children — see [Incus storage](../incus/storage.md#how-hotincus-becomes-incuss-pool).

Verify:

```bash
zfs list
zfs get compression,recordsize -r hot
zfs get compression,recordsize -r tank
```

## Property inheritance

Properties cascade from parent to child unless explicitly overridden. The `SOURCE` column in `zfs get` tells you where a value comes from:

```bash
zfs get -o name,property,value,source compression hot tank tank/media hot/ai
```

Possible sources:

- `default` — the ZFS-wide default value.
- `local` — set explicitly on this dataset.
- `inherited from <ancestor>` — picked up from a parent.
- `received` — set via `zfs receive`, can be overridden by `local`.
- `temporary` — set with `zfs mount -o` for one mount cycle only.

To unset a local value and re-inherit from parent:

```bash
sudo zfs inherit recordsize hot/db
sudo zfs inherit -r recordsize hot/db   # recursive
```

This is essential for cleanup — if you experiment with properties and want to "reset to defaults", `zfs inherit -r` is the way.

## The property reference

ZFS has many properties. The ones that matter most:

### Compression

```bash
zfs set compression=lz4 tank/foo
zfs set compression=zstd-3 tank/backups
zfs set compression=off hot/ai
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
zfs set recordsize=16K hot/db
zfs set recordsize=1M hot/ai
```

See [Tuning -> `recordsize` per workload](tuning.md#recordsize-per-workload). Only affects writes after the change; existing data keeps its block size until rewritten.

VM disks are zvols managed by Incus under `hot/incus/virtual-machines/` — you don't set their `volblocksize` by hand; tune it through Incus's `zfs.blocksize` storage-volume knob instead. See [VM Storage](vm-storage.md) and [Incus storage → sizing and properties](../incus/storage.md#sizing-and-properties).

### Atime, relatime

```bash
zfs set relatime=on hot     # both pools are created with -O relatime=on
zfs set relatime=on tank
```

Both pools are created with `relatime=on` (see [Pool Creation](pool-creation.md)) — atime is updated only when it would otherwise be older than mtime, inherited everywhere unless a child overrides. There's almost no good reason to run full `atime=on` in 2026.

If a specific dataset must never update atime at all:

```bash
zfs set atime=off hot/some-dataset
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
zfs set refquota=200G hot/db

# Reservation — guarantee minimum free space (this dataset and children)
zfs set reservation=50G hot/db

# refreservation — guarantee minimum free for the dataset itself, excluding snapshots
zfs set refreservation=10G hot/ai
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
zfs set primarycache=all hot/db        # default
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
# AI models (hot) — read-mostly, sequential, already compressed
sudo zfs set recordsize=1M hot/ai
sudo zfs set compression=off hot/ai
sudo zfs set primarycache=metadata hot/ai     # models are mmap'd; ARC won't help much

# Databases (hot) — small random IO, ARC hits matter
sudo zfs set recordsize=16K hot/db

# Media archives (tank)
sudo zfs set recordsize=1M tank/media
sudo zfs set primarycache=metadata tank/media
sudo zfs set redundant_metadata=most tank/media   # save metadata space on bulk

# Cold backups (tank)
sudo zfs set compression=zstd-3 tank/backups
sudo zfs set primarycache=metadata tank/backups

# Defaults are fine for everything else
```

VM-disk and container-root recordsize/blocksize are set through Incus on `hot/incus`, not here — see [Incus storage → sizing and properties](../incus/storage.md#sizing-and-properties).

Verify (both pools):

```bash
zfs get -r recordsize,compression,primarycache hot tank | grep -v default
```

This shows only the explicitly-set values, which is a useful audit.

## Permissions on host datasets bind-mounted into instances

The persistent-data datasets above (`tank/nextcloud-data`, `tank/media`, `hot/db`, `hot/ai`) are **bind-mounted from the host into an Incus instance**, and from there into the nested Docker compose service — the two-layer chain documented in [Docker Integration](docker-integration.md) and [Docker inside Incus](../incus/docker-in-incus.md). The final consumer (the Docker container) runs as a non-root user, so the host dataset must be owned by the UID/GID that user maps to.

Typical service UIDs (the container-internal user):

| Service | UID | GID | Notes |
|---|---|---|---|
| Nextcloud (official) | 33 | 33 | `www-data` in the image |
| linuxserver.io images (Sonarr/Radarr/Jellyfin/Plex/etc.) | configurable via `PUID/PGID` env | typically 1000 | Default values; you set them |
| Postgres official | 999 | 999 | `postgres` user in image |
| Plex official | 997 | 997 | |
| Authentik | 1000 | 1000 | |

Set ownership on each host dataset to match:

```bash
# Nextcloud (tank)
sudo chown -R 33:33 /tank/nextcloud-data /tank/nextcloud-app

# Postgres database (hot)
sudo chown -R 999:999 /hot/db

# Media library consumed by a PUID/PGID=1000 service (tank)
sudo chown -R 1000:1000 /tank/media
```

!!! note "Unprivileged Incus containers remap UIDs — mind the idmap"
    An unprivileged Incus system container maps container-root to a high host UID, so the ownership the *nested Docker* service needs is not necessarily the raw host UID above. Incus uses idmapped mounts to bridge this automatically on 26.04's kernel; if a bind-mounted dataset shows up as `nobody:nogroup` inside the container, that mapping is the cause. See [Incus storage → bind mounts and idmap](../incus/storage.md#bind-mounting-host-datasets-into-containers). Confirm each service's documentation before assuming a UID.

## Listing, renaming, destroying

```bash
# List with useful columns
zfs list -o name,used,available,referenced,mountpoint,compression,recordsize

# Filter
zfs list -r hot/incus                        # inspect Incus's instance datasets (read-only!)
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
- [VM Storage](vm-storage.md) — how Incus backs VM disks with ZFS zvols.
- [Docker Integration](docker-integration.md) — bind-mounting host datasets into the Docker-in-Incus stack.
- [Incus storage](../incus/storage.md) — the `hot/incus` backend in depth.
- [Operations](operations.md) — scrubs, replace, expand.
