# Snapshots, Clones, Send & Receive

ZFS's snapshot/clone/send-receive model is the heart of why this build trusts ZFS with its data. This page covers all four operations in depth, the space accounting that catches people out, and the practical workflow with sanoid/syncoid.

## Snapshots — the basics

A snapshot is a **read-only, point-in-time reference** to a dataset's state at a transaction-group boundary. It costs O(1) to create — the snapshot starts as "the same set of pointers as the live dataset" and grows as the live dataset diverges.

```bash
# Single dataset
sudo zfs snapshot tank/nextcloud-data@before-upgrade-2026-05-17

# Recursive (snapshot a parent and all its children atomically)
sudo zfs snapshot -r tank@daily-$(date +%F)

# Multiple at once (atomic across all listed datasets)
sudo zfs snapshot tank/a@s1 tank/b@s1 tank/c@s1
```

Snapshot names live in the dataset's namespace separated by `@`. Naming convention is yours — pick one and stick to it. Common patterns:

- `dataset@autosnap_2026-05-17_03:00:00_daily` — sanoid's format
- `dataset@before-<change>` — manual safety nets
- `dataset@v1.2.3` — releases / versioned milestones

List snapshots:

```bash
zfs list -t snapshot
zfs list -t snapshot -r tank/nextcloud-data
zfs list -t snapshot -o name,used,refer,creation -s creation
```

Destroy:

```bash
sudo zfs destroy tank/nextcloud-data@before-upgrade-2026-05-17
sudo zfs destroy -r tank@daily-2026-05-17           # recursive
sudo zfs destroy tank/foo@a%c                        # range: snapshot 'a' through 'c'
```

## Reading from a snapshot

Each dataset exposes its snapshots through a hidden directory:

```bash
ls /tank/nextcloud-data/.zfs/snapshot/
# autosnap_2026-05-17_03:00:00_daily/

# Look around as of that snapshot
ls /tank/nextcloud-data/.zfs/snapshot/autosnap_2026-05-17_03:00:00_daily/

# Recover a single file
cp /tank/nextcloud-data/.zfs/snapshot/<snap>/path/to/file /tmp/
```

`.zfs/snapshot/...` is read-only and acts like a normal directory tree for most purposes. `tar`, `rsync`, `cp` all work against it.

By default this `.zfs` directory is **hidden** from `ls` (it doesn't show up with `ls -a`). You can make it visible:

```bash
sudo zfs set snapdir=visible tank/nextcloud-data
ls -la /tank/nextcloud-data/             # now .zfs shows up
```

## Space accounting

The single most confusing aspect of ZFS snapshots is the space columns:

```bash
zfs list -o name,used,refer,usedsnap,usedds,usedchild tank/foo
```

| Column | Meaning |
|---|---|
| `USED` | Total space "this dataset" consumes (data + snapshots + children) |
| `REFER` | Bytes referenced by the live filesystem |
| `USEDSNAP` | Bytes used **only** by snapshots (no longer in live filesystem) |
| `USEDDS` | Bytes used by the dataset itself, excluding snapshots and children |
| `USEDCHILD` | Bytes used by child datasets |

For a snapshot specifically:

```bash
zfs list -t snapshot -o name,used,refer tank/foo
```

| Column | Meaning |
|---|---|
| `USED` | Bytes used **only by this snapshot** (would be freed if it were destroyed). |
| `REFER` | Bytes referenced by this snapshot. The same data may also be referenced by the live filesystem or other snapshots. |

A snapshot can have `USED=0` and `REFER=200G` — the snapshot itself isn't growing space because everything it references is still in the live filesystem. Once you change/delete those files in the live filesystem, the snapshot's `USED` grows as it becomes the sole holder of those blocks.

## Rollback

Rolls the live dataset back to a snapshot. Destroys all intermediate snapshots and clones.

```bash
sudo zfs rollback tank/foo@s1                # only works if s1 is the most recent snapshot
sudo zfs rollback -r tank/foo@s1             # destroy newer snapshots first, then rollback
```

The `-r` flag is irreversible — newer snapshots are gone. Use sparingly. Usually you'd rather:

- Read from the snapshot via `.zfs/snapshot/...` and copy the file you wanted back.
- Clone the snapshot to a new writable dataset for experimentation.

## Clones

A clone is a writable filesystem forked from a snapshot. Initially shares all blocks with the snapshot; diverges as you write.

```bash
sudo zfs snapshot hot/db@golden
sudo zfs clone hot/db@golden hot/db-experiment

# Make changes in hot/db-experiment without touching hot/db

# When done:
sudo zfs destroy hot/db-experiment       # destroy the clone
sudo zfs destroy hot/db@golden           # destroy the snapshot (if no clones remain)
```

Clones depend on their parent snapshot. You can't destroy the snapshot while a clone exists — `zfs destroy` will refuse.

!!! note "For Incus instances, clone through Incus, not raw `zfs`"
    The clone/promote mechanics below apply to any dataset you own — but **don't raw-clone datasets under `hot/incus`**. Instance copies go through `incus copy` (which uses ZFS clones under the hood and keeps Incus's database consistent) — see [Incus storage → clones](../incus/storage.md#clones). Raw `zfs clone` is for datasets you manage directly (`hot/db`, `tank/media`, …).

### Promote

Swap parent and clone roles. Useful when the clone is the new canonical:

```bash
# Before promote:
#   hot/db            (original) - has snapshot @golden
#   hot/db-new        (clone of @golden)

sudo zfs promote hot/db-new

# After promote:
#   hot/db-new        now holds @golden
#   hot/db            is now the "clone" of @golden on hot/db-new

# Now you can destroy the original:
sudo zfs destroy hot/db
```

Promote is how you "graduate" an experimental clone to be the new primary.

## Bookmarks — snapshots without the data

A bookmark records "where a snapshot was in the txg timeline" without holding any data. Bookmarks let you do incremental send/receive *after* the snapshot itself has been deleted:

```bash
sudo zfs snapshot tank/foo@s1
sudo zfs bookmark tank/foo@s1 tank/foo#s1     # bookmark uses '#'

# Time passes; you no longer need the snapshot for restore purposes
sudo zfs destroy tank/foo@s1

# Later: incremental send still works against the bookmark
sudo zfs snapshot tank/foo@s2
sudo zfs send -i tank/foo#s1 tank/foo@s2 | ssh backup-host 'zfs receive backup/foo'
```

Why this matters: keeping snapshots forever consumes space (sometimes a lot, when the working set churns). Bookmarks are tiny (~bytes). They let you free disk space without losing the ability to do incrementals.

List bookmarks:

```bash
zfs list -t bookmark
```

## Holds

A "hold" prevents a snapshot from being destroyed. Useful when you want to guarantee an automated cleanup process can't kill a specific snapshot:

```bash
sudo zfs hold sentinel tank/foo@critical          # hold tagged 'sentinel'
zfs holds tank/foo@critical                        # list holds

# zfs destroy now refuses:
sudo zfs destroy tank/foo@critical
# error: dataset is busy

sudo zfs release sentinel tank/foo@critical
sudo zfs destroy tank/foo@critical                 # now works
```

sanoid uses holds during replication transfers to protect snapshots from auto-pruning until replication completes.

## Diff between snapshots

What changed between two points in time:

```bash
sudo zfs diff tank/foo@s1 tank/foo@s2
```

Output:

```
M       /tank/foo/file1            (modified)
+       /tank/foo/file2            (added)
-       /tank/foo/file3            (deleted)
R       /tank/foo/oldname -> /tank/foo/newname    (renamed)
```

Compare a snapshot to the live filesystem:

```bash
sudo zfs diff tank/foo@s1                # implicit second arg = live
```

Useful for understanding "what changed before the bad thing happened?" before rolling back.

## `zfs send` / `zfs receive`

Replicate snapshots to another pool, locally or over SSH.

### Full send

```bash
# Locally — between two pools on the same host
sudo zfs snapshot tank/foo@s1
sudo zfs send tank/foo@s1 | sudo zfs receive backup/foo

# Over SSH
sudo zfs send tank/foo@s1 | ssh backup-host 'sudo zfs receive backup/foo'

# To a file (for offline transport — USB drive, etc.)
sudo zfs send tank/foo@s1 > /mnt/usb/foo-s1.zfsstream
# Restore:
sudo zfs receive backup/foo < /mnt/usb/foo-s1.zfsstream
```

### Incremental send

```bash
sudo zfs snapshot tank/foo@s2
sudo zfs send -i tank/foo@s1 tank/foo@s2 | ssh backup-host 'sudo zfs receive backup/foo'
```

`-i` sends only the delta between the two snapshots. The receiving side **must** already have `@s1` (which it does, because we full-sent it earlier).

### Useful flags

| Flag | Effect |
|---|---|
| `-i <snap>` | Incremental from a single ancestor snapshot |
| `-I <snap>` | Incremental from `<snap>` through all intermediate snapshots |
| `-R` | Replication mode — sends descendant datasets, snapshots, clone hierarchy, and properties |
| `-c` | Compressed send — keep on-disk-compressed blocks compressed on the wire |
| `-L` | Large blocks — allow records > 128 KiB (paired with `recordsize=1M` datasets) |
| `-e` | Embedded data — small records sent inline |
| `-w` | Raw — for encrypted datasets, sends ciphertext (see [Encryption](encryption.md)) |
| `-s` | Reservable — receiving side can hold/resume an interrupted send |
| `-v` | Verbose progress |

A reasonable "production" send command for an encrypted dataset:

```bash
sudo zfs send -wRcv tank/secrets@s2 | ssh backup-host 'sudo zfs receive -s backup/secrets'
```

Receiving side flags:

| Flag | Effect |
|---|---|
| `-F` | Force receive even if it would discard newer snapshots on the destination |
| `-u` | Don't mount after receive (useful for backup hosts) |
| `-s` | Save partial state for resumable receive |
| `-d` / `-e` | Append the source path components to the destination (rarely needed) |

### Resumable transfers

If a send is interrupted (network drop, ctrl-C), you can resume rather than starting over:

```bash
# Receiving side aborts mid-stream. Find the resume token:
zfs get receive_resume_token backup/foo

# Resume on the sender:
sudo zfs send -t <token> | ssh backup-host 'sudo zfs receive -s backup/foo'
```

This is huge for replicating large datasets over slow links. Combine with `-s` on receive to be sure tokens are stored.

### `--dryrun` / verbose

```bash
sudo zfs send -nv tank/foo@s2                       # what would I send?
sudo zfs send -nv -i tank/foo@s1 tank/foo@s2        # what's the delta size?
```

Useful before committing to a multi-hundred-GB transfer.

## syncoid — practical replication

`syncoid` (part of the `sanoid` package) wraps `zfs send | zfs receive` with sensible defaults: it tracks the last replicated snapshot per source/destination pair, decides full vs incremental automatically, uses bookmarks for cleanup, handles SSH connection reuse, and resumes interrupted transfers.

```bash
sudo apt install -y sanoid

# Local replication
sudo syncoid tank/foo backup/foo
sudo syncoid -r tank backup            # recursive

# Over SSH
sudo syncoid tank/foo backup-host:backup/foo

# Useful flags
sudo syncoid --sendoptions='w' tank/secrets backup-host:backup/secrets    # raw send
sudo syncoid --no-sync-snap tank/foo backup/foo                            # don't take a new snapshot; use existing
sudo syncoid --identifier=daily tank/foo backup/foo                        # tag this replication channel
```

Schedule via systemd timer or cron. Example:

```bash
# /etc/cron.d/syncoid
30 03 * * *  root  /usr/sbin/syncoid -r --quiet tank backup-host:backup
```

## sanoid — practical snapshot retention

`sanoid` is the policy engine: "for this dataset, keep N hourly + M daily + P weekly snapshots, automatically".

```bash
sudo tee /etc/sanoid/sanoid.conf > /dev/null <<'EOF'
[template_data]
    hourly = 24
    daily = 30
    weekly = 4
    monthly = 6
    yearly = 0
    autosnap = yes
    autoprune = yes

[template_db]
    frequently = 6
    hourly = 48
    daily = 30
    autosnap = yes
    autoprune = yes

# hot — hot data + Incus instances (root is ext4, not snapshotted here)
[hot/incus]
    use_template = data
    recursive = yes

[hot/db]
    use_template = db
    recursive = yes

# tank — Nextcloud + cold data
[tank/nextcloud-data]
    use_template = data
EOF
```

This mirrors the canonical [backup config](../operations/backup.md#zfs-snapshots) — sanoid owns the schedule for `hot/incus` too (leave Incus's own `snapshots.schedule` unset). See [Incus storage → composing with sanoid](../incus/storage.md#composing-with-sanoid-and-syncoid).

sanoid's systemd timers handle the rest:

```bash
systemctl list-timers sanoid
systemctl status sanoid.timer
```

Manually run a sanoid pass (don't normally need to):

```bash
sudo sanoid --cron --verbose
```

Inspect what sanoid is keeping:

```bash
zfs list -t snapshot | grep autosnap_
```

## Restore workflows

### "I accidentally deleted file X this morning"

```bash
# Find the most recent snapshot that has it
ls /tank/nextcloud-data/.zfs/snapshot/

# Copy it back
cp /tank/nextcloud-data/.zfs/snapshot/autosnap_2026-05-17_03:00:00_hourly/path/to/file \
   /tank/nextcloud-data/path/to/file
```

### "I borked a service's data; roll the dataset back"

Services run as Docker stacks nested inside an Incus container, but their persistent data lives on host datasets (`tank/nextcloud-data`, `hot/db`, …). Stop the consuming service, roll the host dataset back, restart:

```bash
# Stop the compose stack inside the Docker-in-Incus container
incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose down'

# List recent snapshots
zfs list -t snapshot tank/nextcloud-data -s creation

# Roll back to before the change
sudo zfs rollback -r tank/nextcloud-data@autosnap_2026-05-17_03:00:00_hourly

# Restart
incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose up -d'
```

For an Incus *instance's own* dataset (a container rootfs or VM zvol under `hot/incus`), stop the instance first (`incus stop <name>`) before any `zfs rollback` — see the [stop-before-you-receive warning](../incus/storage.md#composing-with-sanoid-and-syncoid).

### "The whole pool is dead; restore from backup-host"

```bash
# After rebuilding host and recreating the pool
ssh backup-host 'sudo zfs send -R backup/nextcloud-data@latest' | sudo zfs receive tank/nextcloud-data
```

`-R` sends the full subtree (descendants, snapshots, properties, clone hierarchy). Restoring is symmetrical to the original send.

## Things that go wrong

### "cannot destroy snapshot: dataset is busy"

A clone depends on it, or a hold protects it. Either destroy the clone first, or `zfs release` the hold.

### Snapshot grows mysteriously

```bash
zfs list -t snapshot -o name,used,refer -s used tank/foo
```

The biggest `USED` snapshots are the most expensive. They're expensive because the live filesystem has diverged from them — files they referenced are no longer in live (so the snapshot now uniquely holds the blocks).

Two responses: destroy the snapshot, or accept the cost.

### `zfs receive` errors with "dataset exists"

The destination already has data. Either:

- `-F` to force-receive (destroys data on the destination if it diverges).
- Pick a fresh destination path.
- Manually destroy the destination first.

### Sends are too slow

Profile what's slow:

```bash
sudo zfs send -nv tank/foo@s2                 # confirm send size
sudo zfs send tank/foo@s2 | pv | ssh ... 'zfs receive ...'    # rate-watch with pv
```

Common improvements:

- Add `-cL` to keep compressed blocks compressed in transit (saves bandwidth).
- Use a faster cipher in SSH: `ssh -c chacha20-poly1305@openssh.com ...`.
- Use `mbuffer` between send and ssh: `... | mbuffer -s 128k -m 256M | ssh ...`.
- Make sure the receive side isn't `sync=always` on the target dataset.

## Next steps

- [VM Storage](vm-storage.md) — snapshots of zvols backing VM disks.
- [Operations](operations.md) — scrub schedules, disk replacement, scale-out.
- [Troubleshooting](troubleshooting.md) — recovering from broken sends, partial receives, missing snapshots.
- [Backup & Recovery](../operations/backup.md) — high-level strategy.
