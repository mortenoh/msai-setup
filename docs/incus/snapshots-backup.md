# Snapshots & backup

This page is the instance-level backup workflow: Incus snapshots, export/import, and how the whole thing fits this build's [sanoid/syncoid/restic philosophy](../operations/backup.md). It builds on [Storage](storage.md) (how instance datasets are laid out) and the [ZFS snapshots](../zfs/snapshots.md) mechanics — read those for the underlying model.

## Two layers, same as the rest of the build

The build's backup model is two layers ([backup & recovery](../operations/backup.md)): **snapshots** for accidents and bad upgrades, **replication** for disk/host loss. Incus instances slot into both because they're ZFS datasets under `hot/incus`.

| Layer | Protects against | Tool for Incus instances |
|---|---|---|
| Snapshots | oops, bad in-instance change | `incus snapshot` (deliberate) + sanoid (scheduled) |
| Off-host replication | disk/host loss | syncoid on `hot/incus` |
| Off-site file backup | site loss | restic (for data inside instances that warrants it) |

## Incus snapshots

### Create, list, restore, delete

```bash
incus snapshot create web before-upgrade      # named snapshot
incus snapshot create web                      # auto-named (snapN)
incus snapshot list web
incus snapshot restore web before-upgrade      # roll the instance back
incus snapshot delete web before-upgrade
```

Each `incus snapshot create` is a ZFS snapshot on the instance's dataset that Incus also tracks in its database — that dual bookkeeping is why `incus snapshot restore` works cleanly (versus a raw `zfs rollback`, which Incus wouldn't know about). Use `incus snapshot` for **deliberate, Incus-aware checkpoints**: "I'm about to upgrade the app inside this container / run Windows Update in this VM."

### Stateful snapshots (running-state capture)

For a running instance you can optionally capture memory state too:

```bash
incus snapshot create builder live-state --stateful
```

`--stateful` checkpoints the instance's running memory (via CRIU for containers, or the hypervisor for VMs) so a restore resumes *running* rather than rebooting. It's heavier and not always supported for every workload; for most service instances a plain (stopped-or-not) snapshot plus a clean restart is simpler and more reliable. Reach for stateful only when resume-in-place genuinely matters.

### Scheduled Incus snapshots — or let sanoid do it

Incus can self-schedule snapshots:

```bash
incus config set web snapshots.schedule "@daily"
incus config set web snapshots.expiry 2w
incus config set web snapshots.pattern "auto-%d"
```

**But this build lets sanoid own the schedule** for `hot/incus`, consistent with every other dataset (see [Storage](storage.md#composing-with-sanoid-and-syncoid)). Leave `snapshots.schedule` **unset** and add to `/etc/sanoid/sanoid.conf`:

```ini
[hot/incus]
    use_template = data
    recursive = yes
```

!!! note "Deliberate = Incus, scheduled = sanoid"
    Keep the two roles distinct: `incus snapshot create` for the checkpoints you take by hand before risky changes (Incus-aware, restorable via `incus snapshot restore`), sanoid for the always-on hourly/daily/weekly safety net (raw ZFS, restored via `.zfs/snapshot/` or a stopped-instance `zfs rollback`). Running *both* schedulers against the same dataset just makes two competing retention policies — pick sanoid for the schedule, Incus for the manual checkpoints.

## Export and import — portable archives

Snapshots live on the pool. **Exports** are self-contained archive files you can move off-box, hand to another host, or keep as a cold artifact.

```bash
# Export an instance (optionally including its snapshots) to a tarball
incus export web /tank/backups/web-$(date +%F).tar.gz

# Export without snapshots (smaller)
incus export web /tank/backups/web-clean.tar.gz --instance-only

# Import it (here or on another Incus host)
incus import /tank/backups/web-2026-07-06.tar.gz
```

Exports are the format for "give this instance to a different machine" or "keep a portable copy independent of the ZFS pool." For **bulk, incremental, off-host** backup of many instances, syncoid on the datasets is more efficient than repeated full exports — use export for portability and one-off archives, syncoid for the routine replication pipeline.

!!! note "Export lands on `tank`, not `hot`"
    Write exports to `/tank/backups` ([tank/backups](../zfs/datasets.md), `compression=zstd-3`) — the cold-archive dataset — not onto `hot` next to the live instances. That keeps a full-pool problem on `hot` from taking the archives with it, and `tank/backups` is itself covered by the backup schedule.

## Replication with syncoid

Because instances are datasets, [syncoid](../zfs/snapshots.md#syncoid-practical-replication) replicates them exactly like `tank` data. Add `hot/incus` to the replication jobs:

```bash
# On-site replica of the whole instance tree
syncoid -r hot/incus backup-host:backup/incus

# Off-site over Tailscale to a remote ZFS host
syncoid -r hot/incus tailscale-backup:backup/incus
```

Wire it into the same daily job as the other datasets ([backup.md's cron](../operations/backup.md)):

```bash
# add to the daily syncoid runner
/usr/sbin/syncoid -r hot/incus  backup-host:backup/incus
```

This sends the raw datasets — container root filesystems, VM zvols, and all snapshots — so a restore rebuilds instance storage bit-for-bit. Pair it with the preserved [preseed file](installation.md), which reconstructs Incus's *configuration* (which instances exist, their profiles/devices). Storage is the data; preseed is the shape.

!!! warning "Stop an instance before receiving over its dataset"
    Restoring by overwriting a live instance's dataset (a syncoid receive or `zfs rollback`) while the instance runs corrupts it — especially VM zvols. `incus stop <name>` first, do the ZFS-level operation, then `incus start`. For a consistent *source* snapshot of a running VM, prefer stopping it before the snapshot; a hot zvol snapshot is only crash-consistent.

## Restic for file-level data inside instances

syncoid handles the block layer off-site; **restic** handles the file layer for user data that warrants encrypted, deduplicated, cross-platform off-site backup (Nextcloud user files, photos) — matching [backup.md's split](../operations/backup.md). Two ways to point restic at data inside an instance:

- **Preferred:** keep important user data on a **host dataset bind-mounted into the instance** (e.g. `tank/nextcloud-data` mounted into the Nextcloud container), and run restic against the host path. The data was never trapped inside the instance to begin with — this is the pattern [Storage](storage.md) recommends.
- **If data lives inside the instance's root dataset:** restic against `/hot/incus/containers/<name>/rootfs/...` on the host, or run restic *inside* the instance against its own paths.

The first is cleaner and is what this build does — instance roots stay disposable, valuable data lives on named host datasets that both syncoid and restic already cover.

## Restore workflows

### Roll back a bad in-instance change

```bash
# Deliberate checkpoint existed:
incus snapshot restore web before-upgrade

# Or from a sanoid snapshot (instance stopped, raw ZFS):
incus stop web
sudo zfs rollback hot/incus/containers/web@autosnap_2026-07-06_03:00:00_hourly
incus start web
```

### Recover a single file from a scheduled snapshot

```bash
# sanoid snapshots are browsable via .zfs (same as any dataset)
ls /hot/incus/containers/web/.zfs/snapshot/
cp /hot/incus/containers/web/.zfs/snapshot/<snap>/rootfs/etc/app/config.yaml /tmp/
```

### Rebuild an instance from off-site

```bash
# After host rebuild + hot import + incus admin init --preseed
# Pull the instance's datasets back from the backup host
syncoid -r backup-host:backup/incus/containers/web hot/incus/containers/web
# Incus re-adopts it; if config was lost, recreate from preseed/profile
```

### Import a portable export

```bash
incus import /tank/backups/web-2026-07-06.tar.gz
incus start web
```

## The rebuild path (instances)

From the [rebuild checklist](../operations/rebuild-checklist.md), the instance-recovery sequence:

1. Import `hot` → `hot/incus` and every instance dataset returns.
2. `incus admin init --preseed < incus-preseed.yaml` → Incus re-attaches to `source: hot/incus`.
3. Instances re-adopt their datasets; `boot.autostart` brings service instances up.
4. Restore file-level user data (Nextcloud, photos) from restic.

If the pool itself is lost, step 1 becomes "recreate `hot`, then `syncoid` each instance dataset back from `backup/incus`" before step 2.

## Verify

```bash
# Incus snapshots
incus snapshot list web
incus info web | grep -A10 Snapshots

# ZFS view (sanoid + Incus snapshots together)
zfs list -t snapshot -r hot/incus/containers/web

# Replication landed
ssh backup-host 'zfs list -t snapshot -r backup/incus | tail'
```

## Next steps

- [Storage](storage.md) — the dataset layout these snapshots operate on.
- [ZFS snapshots](../zfs/snapshots.md) — send/receive, bookmarks, holds, tuning.
- [Backup & recovery](../operations/backup.md) — the whole-build strategy and schedule.
- [Rebuild checklist](../operations/rebuild-checklist.md) — the full recovery runbook.
