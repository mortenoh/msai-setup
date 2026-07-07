# Backup & Recovery

This page covers the whole-build backup strategy, recovery testing, and disaster recovery. It spans **both pools** — `hot` (hot data + Incus's storage backend, on the fast 4 TB NVMe) and `tank` (media, backups, cold data, on the slow 2 TB NVMe). The OS root is a small ext4 partition, not a ZFS dataset, and is deliberately outside this plan (see [OS root — deliberately not backed up](#os-root-ext4-deliberately-not-backed-up)). For how **Incus instances** (containers and VMs, which are ZFS datasets under `hot/incus`) fit this model, see [Incus Snapshots &amp; backup](../incus/snapshots-backup.md) — this page doesn't duplicate that; it references it.

## What lives where

The two pools split hot-vs-cold, and the backup schedule follows the [canonical dataset placement](../zfs/datasets.md) ([hardware](../getting-started/hardware.md) confirms the physical layout):

| Pool | Dataset | Holds | Backup priority |
|---|---|---|---|
| `hot` | `hot/incus` | Every Incus instance (container rootfs + VM zvols) | Snapshot + replicate — see [Incus backup](../incus/snapshots-backup.md) |
| `hot` | `hot/db` | Service databases (Postgres, MariaDB), `recordsize=16K` | Snapshot hourly + replicate |
| `hot` | `hot/ai` | GGUF / safetensors model files, `compression=off` | Manual snapshot; replicate optional (large, re-downloadable) |
| `tank` | `tank/media` | Plex / Jellyfin libraries | Weekly snapshot; off-site optional |
| `tank` | `tank/nextcloud-data` | Nextcloud user data — the snapshot-critical one | Hourly + off-site (restic) |
| `tank` | `tank/nextcloud-app` | Nextcloud application state | Daily + replicate |
| `tank` | `tank/backups` | Cold-archive target (`zstd-3`) — instance exports, DB dumps | Daily; is itself covered |

The OS root and `/home` live on the ext4 root partition, not on `hot` — they are not in the table because they are not backed up here (see [below](#os-root-ext4-deliberately-not-backed-up)).

!!! note "Databases and AI models moved to `hot`"
    Under the old single-pool layout these lived on `tank`. In the two-pool build they're on the fast `hot` (`hot/db`, `hot/ai`). The container/VM datasets that used to be `tank/containers` and `tank/vm` no longer exist as such — **Incus owns that storage now under `hot/incus`**, one dataset per instance. Back them up via `hot/incus` (below), not as standalone `tank` datasets.

## Backup Strategy

### Two layers of protection

| Layer | Protects against | Tool |
|-------|------------------|------|
| Snapshots | Accidental deletion, bad upgrades | ZFS snapshots (sanoid) on the data pools |
| Replication | Disk failure, host loss, site loss | syncoid (block) + restic (file) |

## ZFS Snapshots

This build uses **sanoid** (automatic local snapshot retention) plus **syncoid** (incremental replication to a remote ZFS host) — both from the `sanoid` package. `zfs-auto-snapshot` is upstream-abandoned and is not used here.

### Install sanoid

```bash
sudo apt install -y sanoid
```

Sanoid configuration lives at `/etc/sanoid/sanoid.conf`. Template-based retention is the clean pattern. The datasets span **both pools**; the OS root is ext4 and is not snapshotted here (see [below](#os-root-ext4-deliberately-not-backed-up)) — only the ZFS data datasets are:

```ini
# /etc/sanoid/sanoid.conf

[template_data]
    frequently = 0
    hourly = 24
    daily = 30
    weekly = 8
    monthly = 6
    yearly = 0
    autosnap = yes
    autoprune = yes

[template_db]
    frequently = 6
    hourly = 48
    daily = 30
    weekly = 4
    monthly = 3
    autosnap = yes
    autoprune = yes

# --- hot (hot data + Incus) ---

[hot/incus]
    use_template = data
    recursive = yes

[hot/db]
    use_template = db
    recursive = yes

# --- tank (media / cold data) ---

[tank/nextcloud-data]
    use_template = data

[tank/nextcloud-app]
    use_template = data
```

!!! note "sanoid owns the schedule for `hot/incus` too"
    Incus instances are datasets under `hot/incus`, so sanoid snapshots them like anything else — leave Incus's own `snapshots.schedule` unset and let sanoid drive the always-on retention, reserving `incus snapshot create` for deliberate pre-change checkpoints. This is spelled out in [Incus Snapshots &amp; backup](../incus/snapshots-backup.md#scheduled-incus-snapshots-or-let-sanoid-do-it) — don't configure two competing schedulers on the same dataset.

Sanoid's systemd timers run automatically:

```bash
systemctl status sanoid.timer
systemctl list-timers sanoid
```

### Manual snapshots

Before major changes (note: snapshot the *specific dataset* you're about to disturb):

```bash
# Before a data change on a hot dataset
sudo zfs snapshot hot/db@pre-change-$(date +%F)

# Before a data change on tank
sudo zfs snapshot -r tank@pre-change-$(date +%F)
```

The OS root is ext4, so there's no `zfs snapshot` of `/`. An OS upgrade you want to be able to undo is handled by reinstall-from-capture ([Rebuild Checklist — Scenario A](rebuild-checklist.md#scenario-a-os-broken-pools-fine-reinstall-the-os)) — or, if you want a true one-keystroke rollback of the OS, by the [ZFS Root alternative](../ubuntu/installation/zfs-root-alternative.md).

## Remote Backups

### Replicate with syncoid

`syncoid` wraps `zfs send|receive` with resumable transfers, incremental detection, and automatic bookmarks. Set up SSH keys to the backup host first, then replicate **each dataset that the "restore everything from off-site" runbook expects** — across both pools:

```bash
# /etc/cron.daily/syncoid-replicate
#!/bin/sh
# Every dataset the "restore from off-site" runbook needs must have a job here,
# or it can't be recovered from the off-site host.

# hot — hot data + Incus instances
/usr/sbin/syncoid -r hot/incus            backup-host:backup/incus
/usr/sbin/syncoid -r hot/db               backup-host:backup/db

# tank — Nextcloud + cold archive
/usr/sbin/syncoid -r tank/nextcloud-data    backup-host:backup/nextcloud-data
/usr/sbin/syncoid -r tank/nextcloud-app     backup-host:backup/nextcloud-app
/usr/sbin/syncoid -r tank/backups           backup-host:backup/backups

# Optional (large, lower off-site value): AI models and media.
# /usr/sbin/syncoid -r hot/ai             backup-host:backup/ai
# /usr/sbin/syncoid -r tank/media           backup-host:backup/media
```

Each dataset lands under its own target on the backup host. There is **no single recursive `backup/hot` or `backup/tank` replica** — the restore runbooks pull each dataset back individually. For the Incus tree specifically, `hot/incus` sends the container rootfs datasets and VM zvols and all their snapshots, so a restore rebuilds instance storage bit-for-bit — see [Incus replication with syncoid](../incus/snapshots-backup.md#replication-with-syncoid).

### OS root (ext4) — deliberately not backed up

The OS root is a small ext4 partition, not a ZFS dataset, and it is **not** part of the snapshot or replication plan. This is deliberate, straight from START.md's "the host is rebuildable, the data isn't" philosophy: the OS is fully reproducible from the [installation walkthrough](../ubuntu/installation/installation-walkthrough.md) plus the captured host config (netplan, SSH keys, sanoid config, the Incus preseed — see the [rebuild checklist](rebuild-checklist.md) capture phase). `/home` lives on this same ext4 root; keep anything there that you actually care about on a ZFS dataset instead.

If you want the OS itself covered by snapshots — a bad `apt upgrade` becoming a one-keystroke rollback — that is exactly what the [ZFS Root alternative](../ubuntu/installation/zfs-root-alternative.md) buys, and taking it changes this call: root-on-ZFS is then snapshotted by sanoid and replicated like any other dataset.

### Off-site target

On-site replication protects against disk failure on the primary host. **It does not protect against site loss (theft, fire, full-pool corruption).** For this build the recommended split is:

| Layer | Tool | Target | Scope |
|---|---|---|---|
| Local snapshots | sanoid | `hot` + `tank` (incl. `hot/incus`) | All data datasets |
| On-site replica | syncoid | Always-on ZFS host on LAN | All data datasets |
| Off-site (block) | syncoid over Tailscale | Remote ZFS host (e.g. friend's homelab) | Data datasets + `hot/incus` |
| Off-site (file) | restic | B2/S3 (encrypted) | Nextcloud user data + photos |

restic handles the file layer for user data that warrants encrypted, deduplicated, cross-platform off-site backup; syncoid over Tailscale handles the block layer. For data that lives *inside* an Incus instance, the pattern is to keep it on a host dataset bind-mounted into the instance and back up the host path — see [Incus restic guidance](../incus/snapshots-backup.md#restic-for-file-level-data-inside-instances).

## Database Backups

Databases live on `hot/db` and run inside the Docker-in-Incus container. Dump before schema-affecting changes, writing the dump to the cold-archive dataset:

```bash
# Exec into the Docker-in-Incus container, dump, land it on tank/backups
incus exec docker-host -- \
  docker exec nextcloud-db mysqldump -u root -p nextcloud \
  > /tank/backups/nextcloud-db-$(date +%Y%m%d).sql
```

### Before container updates

Always snapshot the database dataset before updating (stop the instance for a consistent VM/zvol snapshot):

```bash
sudo zfs snapshot hot/db@pre-update-$(date +%F)
incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose pull && docker compose up -d'
```

## Backup Verification

### Test restore regularly

1. Clone snapshot to a temporary dataset
2. Start service against the clone
3. Verify data integrity
4. Destroy the clone

```bash
# Clone (data dataset on tank)
zfs clone tank/nextcloud-data@$(SNAP) tank/test-restore

# Verify
ls /tank/test-restore

# Cleanup
zfs destroy tank/test-restore
```

## Backup Schedule

| Data | Pool | Snapshot frequency | Remote backup (syncoid) |
|------|------|-------------------|---------------|
| `incus` (instances) | hot | Hourly | Daily |
| `db` | hot | Hourly | Daily |
| `ai` (models) | hot | Manual (pre-change) | Optional |
| `nextcloud-data` | tank | Hourly | Daily + off-site (restic) |
| `nextcloud-app` | tank | Daily | Daily |
| `media` | tank | Weekly | Optional (see cron) |
| `backups` | tank | Daily | Daily |

The OS root (ext4) and `/home` are not in this table — they are [deliberately not backed up](#os-root-ext4-deliberately-not-backed-up). Everything with a scheduled remote backup above has a matching syncoid job in the daily cron and is therefore restorable from off-site. `ai` and `media` are off-site only if you enable the optional jobs — otherwise they rely on local snapshots and the on-site replica.

## Recovery Testing

Regular recovery testing validates that backups are actually restorable.

### Test schedule

| Test | Frequency | Duration |
|------|-----------|----------|
| File restore from snapshot | Monthly | 15 min |
| Config-capture check (Scenario A prep) | Quarterly | 15 min |
| Clone dataset and verify service | Quarterly | 1 hour |
| Full rebuild on test hardware | Yearly | 4+ hours |

### Monthly: file restore test

```bash
# List available snapshots (sanoid-managed) on the data dataset
ls /tank/nextcloud-data/.zfs/snapshot/

# Copy a file from a recent snapshot to verify access
cp /tank/nextcloud-data/.zfs/snapshot/<snap>/test-file.txt /tmp/

echo "$(date): File restore test PASSED" >> /var/log/recovery-tests.log
```

### Quarterly: config-capture check

Scenario A on the canonical (ext4) build is a reinstall-from-capture, not a boot-environment rollback — so the thing to verify quarterly is that your capture bundle is current and complete: netplan, SSH host keys, sanoid config, the Incus preseed and profiles, and the `/etc` bits a fresh install needs. Confirm they're on `tank/backups` and replicated off-site, and that you could actually re-apply them. (On the [ZFS Root alternative](../ubuntu/installation/zfs-root-alternative.md#boot-a-different-working-boot-environment), this instead becomes a real boot-environment rollback test.)

### Quarterly: service restore test

Clone an Incus instance and verify it starts, using Incus's own tooling (which keeps its database consistent):

```bash
# ZFS-clone-backed copy of a service instance
incus copy docker-host docker-host-restoretest
incus start docker-host-restoretest
# ... verify services inside respond ...
incus delete --force docker-host-restoretest

echo "$(date): Quarterly service restore test PASSED" >> /var/log/recovery-tests.log
```

### Yearly: full rebuild test

On spare or test hardware, follow the [Rebuild Checklist](rebuild-checklist.md) Scenario B end to end and verify all services return.

## Disaster Scenarios

### Scenario 1: bad OS upgrade / broken root

**Symptoms**: box won't boot cleanly, or boots to a broken userspace after an `apt upgrade` or kernel change; **the pools are fine**.

**Recovery**: root is ext4, so this is a reinstall of the OS partitions from captured config — the `hot` and `tank` pools are re-imported untouched. Full steps in [Rebuild Checklist — Scenario A](rebuild-checklist.md#scenario-a-os-broken-pools-fine-reinstall-the-os). (If you took the [ZFS Root alternative](../ubuntu/installation/zfs-root-alternative.md#zfsbootmenu-recovery), this is instead a one-keystroke boot-environment rollback.)

**Estimated recovery time**: reinstall + re-import, roughly 1-2 hours (minutes on the ZFS-root alternative).

### Scenario 2: single disk / pool failure

**Symptoms**: `zpool status` shows a degraded or faulted disk. Each pool is a single-disk vdev, so a disk failure means the *whole pool* is lost — there is no in-pool redundancy to resilver from.

**Recovery**: replace the drive, recreate the pool, and pull each replicated dataset back from off-site individually (there is no single recursive `backup/hot@latest` or `backup/tank@latest`):

```bash
# After replacing the failed drive and recreating the pool (see Pool Creation)
# hot datasets:
for ds in incus db; do
    syncoid -r backup-host:backup/$ds hot/$ds
done
# tank datasets:
for ds in nextcloud-data nextcloud-app backups; do
    syncoid -r backup-host:backup/$ds tank/$ds
done
# ai / media only if you enabled their optional off-site jobs.
```

If it's `hot` that was lost, you recreate the pool and re-attach Incus to the fresh `hot/incus` (Scenario B); if the primary drive itself failed, you also reinstall the OS onto its ext4 partitions first.

**Estimated recovery time**: 4-24 hours depending on data volume.

### Scenario 3: data corruption discovery

**Symptoms**: files unreadable, checksum errors, application errors.

**Recovery**:

```bash
# Identify extent — scrub the affected pool
sudo zpool scrub tank
zpool status -v tank

# Restore a corrupted file from a snapshot
cp /tank/nextcloud-data/.zfs/snapshot/<good-snap>/path/file /tank/nextcloud-data/path/file

# Widespread: roll the dataset back (stop consumers first)
sudo zfs rollback tank/nextcloud-data@<last-good-snapshot>
```

For a corrupted **Incus instance** dataset, stop the instance before any `zfs rollback` — see the [stop-before-you-receive warning](../incus/snapshots-backup.md#restore-workflows).

**Estimated recovery time**: 1-4 hours.

### Scenario 4: ransomware recovery

**Symptoms**: files encrypted, ransom notes present.

**Recovery**:

1. **Immediately** disconnect from the network (`sudo ip link set <iface> down`).
2. Do NOT pay.
3. Assess which datasets and which pools are affected, and when encryption started (`zfs list -t snapshot -o name,creation`).
4. Roll affected datasets back to a pre-infection snapshot (stop Incus instances first for `hot/incus` datasets):
   ```bash
   sudo incus stop --all
   sudo zfs rollback hot/incus/containers/<name>@pre-infection
   sudo zfs rollback tank/nextcloud-data@pre-infection
   ```
5. Before reconnecting: investigate the vector, patch, rotate all credentials.

**Estimated recovery time**: 4-24 hours.

## Recovery Runbooks

### Runbook: Nextcloud restore

**Prerequisites**: SSH access, ZFS snapshots available. Nextcloud runs in the Docker-in-Incus container; its data is on `tank/nextcloud-data` / `tank/nextcloud-app`, its DB on `hot/db`.

1. Stop Nextcloud inside the container:
   ```bash
   incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose down'
   ```
2. Roll the datasets back:
   ```bash
   sudo zfs rollback tank/nextcloud-data@<snap>
   sudo zfs rollback tank/nextcloud-app@<snap>
   sudo zfs rollback hot/db@<snap>
   ```
3. Start Nextcloud:
   ```bash
   incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose up -d'
   ```
4. Verify: web UI reachable, file listing correct, recent files present.

### Runbook: database restore from dump

**Prerequisites**: SQL dump on `tank/backups`.

```bash
incus exec docker-host -- docker compose -f /opt/compose/nextcloud/docker-compose.yml stop nextcloud
incus exec docker-host -- sh -c \
  'docker exec -i nextcloud-db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" nextcloud < /backups/nextcloud-db.sql'
incus exec docker-host -- docker compose -f /opt/compose/nextcloud/docker-compose.yml start nextcloud
incus exec docker-host -- docker exec -u www-data nextcloud php occ files:scan --all
```

### Runbook: full system recovery

**Prerequisites**: backup host accessible, new hardware ready.

This is the [Rebuild Checklist](rebuild-checklist.md) Scenario B in full — reinstall the OS onto its ext4 partitions (Subiquity + GRUB), re-import `hot` + `tank`, `incus admin init --preseed` at `hot/incus`, restore the instances (from syncoid replicas or exports), and restore file-level user data from restic. The off-site copy is a set of **per-dataset** replicas, not a single recursive image — pull each one back individually:

```bash
for ds in incus db; do syncoid -r backup-host:backup/$ds hot/$ds; done
for ds in nextcloud-data nextcloud-app backups; do syncoid -r backup-host:backup/$ds tank/$ds; done
```

### Required access and credentials

Keep secure, offline copies of:

| Item | Location |
|------|----------|
| SSH keys | Password manager, printed |
| Root/admin passwords | Password manager |
| Backup server credentials | Password manager |
| Docker `.env` files (inside the Incus container's compose dirs) | ZFS snapshot, password manager |
| Incus preseed (`incus-preseed.yaml`) + profiles | Private git repo, `tank/backups`, off-site |
| BIOS password | Printed, secure location |
| Encryption keys (if you enabled ZFS native encryption) | Multiple secure locations |

!!! warning "Credential storage"
    Recovery is impossible without access credentials. Store them in multiple secure locations.
