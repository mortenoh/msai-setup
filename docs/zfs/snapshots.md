# Snapshots

## Overview

Snapshots are read-only, point-in-time copies of datasets. They're instant and space-efficient.

## Manual Snapshots

### Create Snapshot

```bash
sudo zfs snapshot tank/nextcloud-data@before-upgrade
```

### Recursive Snapshot

```bash
sudo zfs snapshot -r tank@daily-2024-01-15
```

### List Snapshots

```bash
zfs list -t snapshot
zfs list -t snapshot -r tank/nextcloud-data
```

### Delete Snapshot

```bash
sudo zfs destroy tank/nextcloud-data@before-upgrade
```

## Rollback

!!! warning "Destructive Operation"
    Rollback destroys all changes since the snapshot.

```bash
sudo zfs rollback tank/nextcloud-data@before-upgrade
```

For rollback to older snapshots, destroy intermediate ones:

```bash
sudo zfs rollback -r tank/nextcloud-data@old-snapshot
```

## Access Snapshot Data

Snapshots are accessible in a hidden directory:

```bash
ls /mnt/tank/nextcloud-data/.zfs/snapshot/
```

Recover individual files by copying from snapshot.

## Automated Snapshots

### Using zfs-auto-snapshot

```bash
sudo apt install -y zfs-auto-snapshot
```

Default policies:

- Frequent: every 15 minutes, keep 4
- Hourly: keep 24
- Daily: keep 31
- Weekly: keep 8
- Monthly: keep 12

### Disable for Specific Datasets

```bash
sudo zfs set com.sun:auto-snapshot=false tank/containers
```

## Snapshot Policies

| Dataset | Policy | Rationale |
|---------|--------|-----------|
| nextcloud-data | Frequent + Daily + Monthly | User data, needs recovery options |
| db | Hourly + Daily | Database state changes often |
| media | Weekly only | Large, rarely changes |
| containers | None | Disposable state |
| vm | Before major changes | Manual snapshots preferred |

## Send/Receive

Transfer snapshots between pools or machines:

```bash
# Local copy
zfs send tank/data@snap | zfs receive backup/data

# Remote backup
zfs send tank/data@snap | ssh backup-server zfs receive pool/data

# Incremental
zfs send -i @snap1 tank/data@snap2 | zfs receive backup/data
```
