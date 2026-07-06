# Backup & Recovery

This page covers the whole-build backup strategy, recovery testing, and disaster recovery. It spans **both pools** — `rpool` (root + hot data + Incus's storage backend, on the fast 4 TB NVMe) and `tank` (media, backups, cold data, on the slow 2 TB NVMe). For how **Incus instances** (containers and VMs, which are ZFS datasets under `rpool/incus`) fit this same model, see [Incus Snapshots &amp; backup](../incus/snapshots-backup.md) — this page doesn't duplicate that; it references it.

## What lives where

The two pools split hot-vs-cold, and the backup schedule follows the [canonical dataset placement](../zfs/datasets.md) ([hardware](../getting-started/hardware.md) confirms the physical layout):

| Pool | Dataset | Holds | Backup priority |
|---|---|---|---|
| `rpool` | `rpool/ROOT/ubuntu` | The OS root (a boot environment) | Local snapshots = boot environments; on-site replica only (see below) |
| `rpool` | `rpool/home` | User home dirs | Snapshot + replicate |
| `rpool` | `rpool/incus` | Every Incus instance (container rootfs + VM zvols) | Snapshot + replicate — see [Incus backup](../incus/snapshots-backup.md) |
| `rpool` | `rpool/db` | Service databases (Postgres, MariaDB), `recordsize=16K` | Snapshot hourly + replicate |
| `rpool` | `rpool/ai` | GGUF / safetensors model files, `compression=off` | Manual snapshot; replicate optional (large, re-downloadable) |
| `tank` | `tank/media` | Plex / Jellyfin libraries | Weekly snapshot; off-site optional |
| `tank` | `tank/nextcloud-data` | Nextcloud user data — the snapshot-critical one | Hourly + off-site (restic) |
| `tank` | `tank/nextcloud-app` | Nextcloud application state | Daily + replicate |
| `tank` | `tank/backups` | Cold-archive target (`zstd-3`) — instance exports, DB dumps | Daily; is itself covered |

!!! note "Databases and AI models moved to `rpool`"
    Under the old single-pool layout these lived on `tank`. In the two-pool build they're on the fast `rpool` (`rpool/db`, `rpool/ai`). The container/VM datasets that used to be `tank/containers` and `tank/vm` no longer exist as such — **Incus owns that storage now under `rpool/incus`**, one dataset per instance. Back them up via `rpool/incus` (below), not as standalone `tank` datasets.

## Backup Strategy

### Two layers of protection

| Layer | Protects against | Tool |
|-------|------------------|------|
| Snapshots | Accidental deletion, bad upgrades | ZFS snapshots (sanoid), ZFSBootMenu boot environments for root |
| Replication | Disk failure, host loss, site loss | syncoid (block) + restic (file) |

## ZFS Snapshots

This build uses **sanoid** (automatic local snapshot retention) plus **syncoid** (incremental replication to a remote ZFS host) — both from the `sanoid` package. `zfs-auto-snapshot` is upstream-abandoned and is not used here.

### Install sanoid

```bash
sudo apt install -y sanoid
```

Sanoid configuration lives at `/etc/sanoid/sanoid.conf`. Template-based retention is the clean pattern. Note the datasets span **both pools**, and `rpool/ROOT` is included so the OS itself has boot-environment snapshots:

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

[template_os]
    # Boot environments: enough history to roll back a bad upgrade, not a hoard.
    frequently = 0
    hourly = 0
    daily = 14
    weekly = 4
    monthly = 2
    autosnap = yes
    autoprune = yes

# --- rpool (root + hot data + Incus) ---

[rpool/ROOT/ubuntu]
    use_template = os

[rpool/home]
    use_template = data

[rpool/incus]
    use_template = data
    recursive = yes

[rpool/db]
    use_template = db
    recursive = yes

# --- tank (media / cold data) ---

[tank/nextcloud-data]
    use_template = data

[tank/nextcloud-app]
    use_template = data
```

!!! note "sanoid owns the schedule for `rpool/incus` too"
    Incus instances are datasets under `rpool/incus`, so sanoid snapshots them like anything else — leave Incus's own `snapshots.schedule` unset and let sanoid drive the always-on retention, reserving `incus snapshot create` for deliberate pre-change checkpoints. This is spelled out in [Incus Snapshots &amp; backup](../incus/snapshots-backup.md#scheduled-incus-snapshots-or-let-sanoid-do-it) — don't configure two competing schedulers on the same dataset.

Sanoid's systemd timers run automatically:

```bash
systemctl status sanoid.timer
systemctl list-timers sanoid
```

### Manual snapshots

Before major changes (note: snapshot the *specific pool* you're about to disturb):

```bash
# Before an OS upgrade — this IS the boot-environment safety net
sudo zfs snapshot rpool/ROOT/ubuntu@pre-upgrade-$(date +%F)

# Before a data change on tank
sudo zfs snapshot -r tank@pre-change-$(date +%F)
```

A `rpool/ROOT/ubuntu@…` snapshot is directly bootable/rollback-able from the [ZFSBootMenu screen](../ubuntu/installation/zfs-root-alternative.md#zfsbootmenu-recovery) — that's the mechanism behind Scenario A in the [rebuild checklist](rebuild-checklist.md#scenario-a-os-broken-pools-fine-boot-environment-rollback).

## Remote Backups

### Replicate with syncoid

`syncoid` wraps `zfs send|receive` with resumable transfers, incremental detection, and automatic bookmarks. Set up SSH keys to the backup host first, then replicate **each dataset that the "restore everything from off-site" runbook expects** — across both pools:

```bash
# /etc/cron.daily/syncoid-replicate
#!/bin/sh
# Every dataset the "restore from off-site" runbook needs must have a job here,
# or it can't be recovered from the off-site host.

# rpool — hot data + Incus instances
/usr/sbin/syncoid -r rpool/incus            backup-host:backup/incus
/usr/sbin/syncoid -r rpool/db               backup-host:backup/db
/usr/sbin/syncoid -r rpool/home             backup-host:backup/home

# tank — Nextcloud + cold archive
/usr/sbin/syncoid -r tank/nextcloud-data    backup-host:backup/nextcloud-data
/usr/sbin/syncoid -r tank/nextcloud-app     backup-host:backup/nextcloud-app
/usr/sbin/syncoid -r tank/backups           backup-host:backup/backups

# On-site convenience replica of the OS root (see "Replicating root" below).
# Skipped off-site — the host is rebuildable, the data isn't.
/usr/sbin/syncoid -r rpool/ROOT             backup-host:backup/rpool-ROOT

# Optional (large, lower off-site value): AI models and media.
# /usr/sbin/syncoid -r rpool/ai             backup-host:backup/ai
# /usr/sbin/syncoid -r tank/media           backup-host:backup/media
```

Each dataset lands under its own target on the backup host. There is **no single recursive `backup/rpool` or `backup/tank` replica** — the restore runbooks pull each dataset back individually. For the Incus tree specifically, `rpool/incus` sends the container rootfs datasets and VM zvols and all their snapshots, so a restore rebuilds instance storage bit-for-bit — see [Incus replication with syncoid](../incus/snapshots-backup.md#replication-with-syncoid).

### Replicating root (`rpool/ROOT`) — the reasoned call

**Decision for this build:** snapshot `rpool/ROOT/ubuntu` locally with sanoid (mandatory — that *is* the boot-environment rollback mechanism), replicate it to the **on-site** LAN replica as a convenience, and **do not** push it off-site (no Tailscale/restic copy of the OS root).

Reasoning, from START.md's "the host is rebuildable, the data isn't" philosophy:

- **Local snapshots of `rpool/ROOT` are non-negotiable** — without them there are no boot environments and Scenario A (one-keystroke rollback) doesn't exist. sanoid's `[template_os]` above provides them.
- **On-site replication is cheap and speeds recovery.** A `syncoid rpool/ROOT` to the LAN replica means a same-hardware rebuild can `zfs receive` a working root instead of re-running the whole [root-on-ZFS install](../ubuntu/installation/installation-walkthrough.md). Low cost, real time savings.
- **Off-site replication of the OS root is not worth the bytes.** The OS is fully reproducible from the install walkthrough plus the captured host config (netplan, SSH keys, sanoid config, the Incus preseed). Off-site capacity and transfer budget are better spent on the irreplaceable data — Nextcloud user files, photos, databases, and the Incus instance datasets. A stale off-site root image would likely be rebuilt from docs anyway.

So `rpool/ROOT` is **local + on-site**, never off-site. If you disagree for your threat model (e.g. you keep heavy per-host customization that's painful to reproduce), adding `rpool/ROOT` to the off-site syncoid job is harmless — it's a deliberate trade of off-site capacity for rebuild speed.

### Off-site target

On-site replication protects against disk failure on the primary host. **It does not protect against site loss (theft, fire, full-pool corruption).** For this build the recommended split is:

| Layer | Tool | Target | Scope |
|---|---|---|---|
| Local snapshots | sanoid | `rpool` + `tank` (incl. `rpool/ROOT`, `rpool/incus`) | Everything |
| On-site replica | syncoid | Always-on ZFS host on LAN | Everything incl. `rpool/ROOT` |
| Off-site (block) | syncoid over Tailscale | Remote ZFS host (e.g. friend's homelab) | Data datasets + `rpool/incus`; **not** `rpool/ROOT` |
| Off-site (file) | restic | B2/S3 (encrypted) | Nextcloud user data + photos |

restic handles the file layer for user data that warrants encrypted, deduplicated, cross-platform off-site backup; syncoid over Tailscale handles the block layer. For data that lives *inside* an Incus instance, the pattern is to keep it on a host dataset bind-mounted into the instance and back up the host path — see [Incus restic guidance](../incus/snapshots-backup.md#restic-for-file-level-data-inside-instances).

## Database Backups

Databases live on `rpool/db` and run inside the Docker-in-Incus container. Dump before schema-affecting changes, writing the dump to the cold-archive dataset:

```bash
# Exec into the Docker-in-Incus container, dump, land it on tank/backups
incus exec docker-host -- \
  docker exec nextcloud-db mysqldump -u root -p nextcloud \
  > /tank/backups/nextcloud-db-$(date +%Y%m%d).sql
```

### Before container updates

Always snapshot the database dataset before updating (stop the instance for a consistent VM/zvol snapshot):

```bash
sudo zfs snapshot rpool/db@pre-update-$(date +%F)
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
| `ROOT/ubuntu` (OS) | rpool | Daily (boot environments) | On-site only |
| `home` | rpool | Hourly | Daily |
| `incus` (instances) | rpool | Hourly | Daily |
| `db` | rpool | Hourly | Daily |
| `ai` (models) | rpool | Manual (pre-change) | Optional |
| `nextcloud-data` | tank | Hourly | Daily + off-site (restic) |
| `nextcloud-app` | tank | Daily | Daily |
| `media` | tank | Weekly | Optional (see cron) |
| `backups` | tank | Daily | Daily |

Everything with a scheduled remote backup above has a matching syncoid job in the daily cron and is therefore restorable from off-site (except `rpool/ROOT`, which is on-site only by design — see [Replicating root](#replicating-root-rpoolroot-the-reasoned-call)). `ai` and `media` are off-site only if you enable the optional jobs — otherwise they rely on local snapshots and the on-site replica.

## Recovery Testing

Regular recovery testing validates that backups are actually restorable.

### Test schedule

| Test | Frequency | Duration |
|------|-----------|----------|
| File restore from snapshot | Monthly | 15 min |
| Boot-environment rollback (Scenario A) | Quarterly | 10 min |
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

### Quarterly: boot-environment rollback test

Confirm the OS-rollback path actually works before you need it in anger: snapshot `rpool/ROOT/ubuntu`, make a trivial change, then reboot and roll back to the snapshot from the [ZFSBootMenu screen](../ubuntu/installation/zfs-root-alternative.md#boot-a-different-working-boot-environment). Verify the change is gone and log it.

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

**Recovery**: this is a boot-environment rollback, **not** a restore. Interrupt the ZFSBootMenu countdown, boot a previous environment or roll a `rpool/ROOT/ubuntu` snapshot back — full steps in [ZFS Root (Alternative) — ZFSBootMenu Recovery](../ubuntu/installation/zfs-root-alternative.md#zfsbootmenu-recovery) and [Rebuild Checklist — Scenario A](rebuild-checklist.md#scenario-a-os-broken-pools-fine-boot-environment-rollback).

**Estimated recovery time**: minutes.

### Scenario 2: single disk / pool failure

**Symptoms**: `zpool status` shows a degraded or faulted disk. Each pool is a single-disk vdev, so a disk failure means the *whole pool* is lost — there is no in-pool redundancy to resilver from.

**Recovery**: replace the drive, recreate the pool, and pull each replicated dataset back from off-site individually (there is no single recursive `backup/rpool@latest` or `backup/tank@latest`):

```bash
# After replacing the failed drive and recreating the pool (see Pool Creation)
# rpool datasets:
for ds in incus db home; do
    syncoid -r backup-host:backup/$ds rpool/$ds
done
# tank datasets:
for ds in nextcloud-data nextcloud-app backups; do
    syncoid -r backup-host:backup/$ds tank/$ds
done
# ai / media only if you enabled their optional off-site jobs.
```

If it's `rpool` that was lost, you also reinstall root-on-ZFS + ZFSBootMenu first (Scenario B) before re-attaching Incus to the recovered `rpool/incus`.

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
4. Roll affected datasets back to a pre-infection snapshot (stop Incus instances first for `rpool/incus` datasets):
   ```bash
   sudo incus stop --all
   sudo zfs rollback rpool/incus/containers/<name>@pre-infection
   sudo zfs rollback tank/nextcloud-data@pre-infection
   ```
5. Before reconnecting: investigate the vector, patch, rotate all credentials.

**Estimated recovery time**: 4-24 hours.

## Recovery Runbooks

### Runbook: Nextcloud restore

**Prerequisites**: SSH access, ZFS snapshots available. Nextcloud runs in the Docker-in-Incus container; its data is on `tank/nextcloud-data` / `tank/nextcloud-app`, its DB on `rpool/db`.

1. Stop Nextcloud inside the container:
   ```bash
   incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose down'
   ```
2. Roll the datasets back:
   ```bash
   sudo zfs rollback tank/nextcloud-data@<snap>
   sudo zfs rollback tank/nextcloud-app@<snap>
   sudo zfs rollback rpool/db@<snap>
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

This is the [Rebuild Checklist](rebuild-checklist.md) Scenario B in full — reinstall root-on-ZFS + ZFSBootMenu, re-import `tank`, `incus admin init --preseed` at `rpool/incus`, restore the instances (from syncoid replicas or exports), and restore file-level user data from restic. The off-site copy is a set of **per-dataset** replicas, not a single recursive image — pull each one back individually:

```bash
for ds in incus db home; do syncoid -r backup-host:backup/$ds rpool/$ds; done
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
