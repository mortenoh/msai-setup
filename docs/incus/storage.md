# Storage — the ZFS driver in depth

Incus's ZFS storage driver is why this build trusts it with instance data: every container and VM is a native ZFS dataset under `rpool/incus`, so snapshots, clones, and `zfs send`/`receive` all work per instance with no bind-mount choreography. This page covers how that mapping works, how Incus snapshots relate to raw `zfs` snapshots, and how the whole thing composes with this build's [sanoid/syncoid](../zfs/snapshots.md) backup tooling.

## How `rpool/incus` becomes Incus's pool

During [installation](installation.md) you answered `no` to "create a new ZFS pool" and pointed Incus at the existing **`rpool/incus`** dataset (created in [disk partitioning](../ubuntu/installation/disk-partitioning.md)). That created an Incus storage pool named `default` with:

```yaml
name: default
driver: zfs
config:
  source: rpool/incus
  zfs.pool_name: rpool/incus
```

The `source` key is the load-bearing one: it tells Incus "manage this existing dataset," not "take over a raw disk." Incus then builds a dataset tree beneath it:

```bash
zfs list -r rpool/incus
```

```
rpool/incus
rpool/incus/containers                # one child per container
rpool/incus/containers/web
rpool/incus/virtual-machines          # one child per VM (holds a zvol)
rpool/incus/virtual-machines/win11
rpool/incus/images                    # cached image datasets
rpool/incus/custom                    # custom volumes (shared data)
rpool/incus/deleted                   # staging for deletions
```

!!! danger "Incus assumes full control of `rpool/incus` and everything under it"
    The Incus docs are explicit: Incus assumes it owns the dataset you hand it. **Do not** manually create datasets under `rpool/incus`, rename Incus's datasets, or `zfs destroy` them out from under Incus — you will desynchronize Incus's database from the on-disk reality and instances will fail to start. Manage instance storage through `incus` commands. Raw `zfs` is for *reading* (inspecting, sending snapshots for backup), not for restructuring what Incus created. Other datasets on `rpool` (`rpool/ROOT`, `rpool/home`, `rpool/ai`, `rpool/db`) are outside `rpool/incus` and are yours to manage normally.

## Per-instance datasets

### Containers

Each container's root filesystem is a ZFS dataset. Create one and watch it appear:

```bash
incus launch images:ubuntu/24.04 web
zfs list -r rpool/incus/containers
# rpool/incus/containers/web   <- the container's root dataset
```

Because it is a real dataset, it inherits `rpool`'s properties (compression, etc.) and can be inspected, snapshotted, and sent like any other.

### VMs

A VM's disk is a **zvol** (a ZFS block device), not a filesystem dataset — a VM has its own filesystem inside, so Incus gives it a raw block volume:

```bash
incus launch images:ubuntu/24.04 builder --vm
zfs list -t all -r rpool/incus/virtual-machines
# rpool/incus/virtual-machines/builder        (a small config filesystem)
# rpool/incus/virtual-machines/builder.block   (the zvol — the VM's disk)
```

### Sizing and properties

Set a size limit on an instance's root disk via its `disk` device (this becomes a ZFS quota/refquota):

```bash
# Cap a container's root at 20 GiB
incus config device set web root size=20GiB

# Set at launch via profile override
incus launch images:ubuntu/24.04 web -d root,size=20GiB
```

ZFS-specific volume properties (compression, block size, whether snapshots follow) are set on the **storage pool** or per **volume**:

```bash
# Pool-wide defaults for new volumes
incus storage set default volume.zfs.use_refquota true

# Per-volume tuning (e.g. a database volume wanting a smaller recordsize)
incus storage volume set default db-data zfs.blocksize 16KiB
```

!!! note "recordsize and the model files live outside Incus"
    This build keeps large AI model files on the dedicated `rpool/ai` dataset (`recordsize=1M`, `compression=off`) — see [ZFS datasets](../zfs/datasets.md) — **not** inside an instance's root dataset. Instances that need models reach them via a bind-mount `disk` device (below), so the tuned `rpool/ai` properties apply, not Incus's generic volume defaults. Don't copy 40 GB of GGUF into a container's root dataset; mount `rpool/ai` in.

## Custom storage volumes

Beyond per-instance root disks, Incus manages **custom volumes** — independent datasets you attach to one or more instances for shared or persistent data.

```bash
# Create a filesystem volume
incus storage volume create default shared-config

# Attach it to a container at a path
incus config device add web config disk pool=default source=shared-config path=/srv/config

# List and inspect
incus storage volume list default
incus storage volume show default shared-config
```

Custom volumes survive instance deletion — good for data you want decoupled from a disposable instance.

## Bind-mounting host datasets into containers

For data that already lives on a tuned host dataset (`rpool/ai` models, `tank/media` libraries), bind-mount the host path into the container with a `disk` device pointing at `source=<host-path>`:

```bash
# Mount the host's model dataset read-only into an AI container
incus config device add ai-stack models disk \
  source=/rpool/ai path=/models readonly=true
```

!!! note "Bind mounts and unprivileged containers: shiftfs / idmap"
    Unprivileged containers remap UIDs/GIDs (root in the container is a high, unprivileged UID on the host). A plain bind mount of a host directory can therefore show up with `nobody:nogroup` ownership inside the container. Incus handles this with idmapped mounts automatically on modern kernels (26.04's 7.0 kernel supports them), but if you see permission surprises on a bind-mounted host path, that mapping is the usual cause. For VMs there is no bind mount — share host data via a `disk` device that Incus exposes over virtiofs, or over the network. See [Troubleshooting](troubleshooting.md).

## Snapshots and clones — Incus vs raw ZFS

This is the part that composes with the rest of the build. There are two ways to snapshot an instance, and they are the *same underlying ZFS snapshot* seen from two angles.

### Via Incus (the managed way)

```bash
# Snapshot an instance (container or VM)
incus snapshot create web before-upgrade

# List an instance's snapshots
incus snapshot list web

# Restore the instance to a snapshot
incus snapshot restore web before-upgrade

# Delete a snapshot
incus snapshot delete web before-upgrade
```

Under the hood, `incus snapshot create web before-upgrade` produces a ZFS snapshot on the instance's dataset:

```bash
zfs list -t snapshot -r rpool/incus/containers/web
# rpool/incus/containers/web@snapshot-before-upgrade
```

Incus tracks the snapshot in its own database (that's how `incus snapshot list` knows about it and how `restore` works cleanly). **Prefer `incus snapshot` for anything Incus should know about** — it keeps the database and ZFS in sync.

### Automatic instance snapshots

Incus can take scheduled snapshots per instance without sanoid:

```bash
incus config set web snapshots.schedule "@daily"
incus config set web snapshots.expiry 2w
incus config set web snapshots.pattern "auto-%d"
```

This is Incus's own scheduler. Whether to use it or sanoid is a real decision — see [the sanoid interaction](#composing-with-sanoid-and-syncoid) below.

### Clones

Incus copies (with `--instance-only` or full) use ZFS clones under the hood when `zfs.clone_copy` is enabled (the default):

```bash
# Copy an instance (fast, ZFS-clone-backed)
incus copy web web-experiment
```

The pool's `zfs.clone_copy` controls whether copies are lightweight clones (share blocks, fast) or full independent datasets:

```bash
incus storage get default zfs.clone_copy
# true  -> ZFS clones (fast, space-efficient, dependent on source snapshot)
# false -> full copy (independent, slower, more space)
```

### Raw `zfs snapshot` still works

Because these are real ZFS datasets, `zfs snapshot rpool/incus/containers/web@manual` works too. **But Incus won't know about it** — it won't show in `incus snapshot list`, and `incus snapshot restore` can't use it. A raw snapshot is fine as a backup source for `zfs send` (below), but for *managing* instance state, go through Incus so its database stays consistent.

## Composing with sanoid and syncoid

This build's backup story is [sanoid for local retention, syncoid for replication](../operations/backup.md). Incus's datasets live under `rpool/incus`, so they are reachable by both tools — but there is a coordination question.

### Snapshots: pick one scheduler per dataset

Both sanoid and Incus's `snapshots.schedule` can auto-snapshot the same dataset. Running both means two independent retention policies fighting over the same dataset's snapshot namespace, which is confusing and wasteful.

**Recommended for this build:** let **sanoid own the snapshot schedule** for Incus datasets, consistent with how it owns every other dataset on `rpool` and `tank`. Point sanoid at `rpool/incus` recursively:

```ini
# /etc/sanoid/sanoid.conf  (add to the existing config)

[rpool/incus]
    use_template = data
    recursive = yes
```

This gives Incus instances the same hourly/daily/weekly retention as the rest of the build, in one place, with the naming convention (`autosnap_...`) the [snapshots page](../zfs/snapshots.md) documents. Leave `incus config set ... snapshots.schedule` **unset** so the two don't collide.

!!! note "Trade-off: Incus won't 'see' sanoid's snapshots"
    sanoid's `autosnap_*` snapshots are raw ZFS snapshots, so `incus snapshot list` won't display them and `incus snapshot restore` can't roll back to them. That is an accepted trade-off: sanoid snapshots are for the *disaster/oops* recovery path (restore a file from `.zfs/snapshot/`, or `zfs rollback` a whole instance dataset while the instance is stopped), while `incus snapshot create` is for *deliberate, Incus-aware* checkpoints (before an in-container upgrade you might `incus snapshot restore`). Use `incus snapshot` for the "I'm about to do something risky in this instance" case; rely on sanoid for the always-on safety net. Keep the two purposes distinct and they don't conflict.

### Replication: syncoid on `rpool/incus`

syncoid replicates the Incus datasets off-host exactly like any other ZFS data. Add `rpool/incus` to the replication jobs alongside the `tank` datasets:

```bash
# On-site replica of the whole Incus dataset tree
syncoid -r rpool/incus backup-host:backup/incus

# Off-site over Tailscale to a remote ZFS host
syncoid -r --sshport=22 rpool/incus tailscale-backup:backup/incus
```

Because syncoid sends the raw datasets (root filesystems and VM zvols and all their snapshots), a restore reconstructs the instance's storage bit-for-bit. Pair it with the preserved [preseed file](installation.md) so Incus's *configuration* (which instances exist, their profiles and devices) is reproducible too — the storage is the data, the preseed is the shape.

!!! warning "Restoring a live instance's dataset requires the instance stopped"
    Rolling back or overwriting an instance's dataset (via `zfs rollback` or a syncoid receive) while the instance is running corrupts it. Stop the instance first (`incus stop web`), do the ZFS-level operation, then start it. For VM zvols especially, a receive over a running guest's block device is a guaranteed way to break the guest filesystem.

### VM zvols and send efficiency

VM disks are zvols, which are less compressible and larger than container root datasets. The [snapshots page's send tuning](../zfs/snapshots.md) applies — use `-c` (compressed send) and `-L` (large blocks) when replicating them, and consider whether VM disk images need off-site replication at all (this build treats `vm` as optional off-site, matching the [backup schedule](../operations/backup.md)).

## The rebuild path

Storage is what makes the [rebuild checklist](../operations/rebuild-checklist.md) fast. On a fresh host:

1. Import `rpool` — `rpool/incus` and all its instance datasets come back with it.
2. `incus admin init --preseed < incus-preseed.yaml` — points Incus at the preserved `rpool/incus` source.
3. Incus re-adopts the existing datasets; instances are recreated from the preseed/config.
4. Restore any file-level data (Nextcloud, photos) from the [off-site restic backup](../operations/backup.md).

The datasets never had to be rebuilt — they survived on the pool, and re-attaching Incus to `source: rpool/incus` is what re-adopts them.

## Verification

```bash
# Incus's view
incus storage list
incus storage info default
incus storage volume list default

# ZFS's view — the same datasets
zfs list -r rpool/incus
zfs list -t snapshot -r rpool/incus

# Confirm sanoid is snapshotting the Incus tree
zfs list -t snapshot -r rpool/incus | grep autosnap_
```

## Next steps

- [Networking](networking.md) — the `incusbr0` bridge and UFW.
- [Snapshots & backup](snapshots-backup.md) — the instance-level backup workflow in full.
- [ZFS snapshots](../zfs/snapshots.md) — the underlying snapshot/send/receive mechanics.
- [Backup & recovery](../operations/backup.md) — the whole-build backup philosophy.
