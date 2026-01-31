# Recovery

## Recovery Scenarios

| Scenario | Solution |
|----------|----------|
| Accidental file deletion | Restore from snapshot |
| Bad upgrade | Rollback to snapshot |
| Container failure | Recreate container |
| Host failure | Reinstall OS, import pool |
| Disk failure | Restore from backup |

## File Recovery from Snapshot

### Access Snapshot Directory

```bash
ls /mnt/tank/nextcloud-data/.zfs/snapshot/
```

### Copy File Back

```bash
cp /mnt/tank/nextcloud-data/.zfs/snapshot/hourly-2024-01-15/file.txt \
   /mnt/tank/nextcloud-data/file.txt
```

## Dataset Rollback

!!! warning "Destructive"
    Rollback destroys all changes since the snapshot.

```bash
# Stop services using the dataset
docker compose down

# Rollback
sudo zfs rollback tank/nextcloud-data@before-upgrade

# Restart services
docker compose up -d
```

## Container Recovery

Containers are disposable. To recover:

```bash
# Pull latest image
docker compose pull

# Recreate containers
docker compose up -d --force-recreate
```

Data persists in ZFS bind mounts.

## Host Recovery

If the host OS fails but ZFS pool is intact:

1. Install fresh Ubuntu Server
2. Install ZFS:
   ```bash
   sudo apt install -y zfsutils-linux
   ```
3. Import pool:
   ```bash
   sudo zpool import tank
   ```
4. Reinstall Docker and services
5. Start containers with existing bind mounts

See [Rebuild Checklist](rebuild-checklist.md) for detailed steps.

## Disk Failure Recovery

### Single Disk Pool (No Redundancy)

If a disk fails, restore from backup:

1. Replace failed disk
2. Create new pool
3. Restore from remote backup:
   ```bash
   ssh backup-server zfs send backup/data@latest | zfs receive tank/data
   ```

### If You Had a Mirror

```bash
# Replace failed disk
zpool replace tank old-disk new-disk

# Monitor resilver progress
zpool status
```

## Database Recovery

### From Snapshot

```bash
sudo zfs rollback tank/db/nextcloud@pre-upgrade
docker compose restart db
```

### From SQL Dump

```bash
docker exec -i nextcloud-db mysql -u root -p nextcloud < backup.sql
```

## VM Recovery

### From Snapshot

```bash
sudo zfs rollback tank/vm@before-update
virsh start win11
```

### Corrupted VM Disk

Restore from backup or recreate from installation media.

## Recovery Testing

Schedule regular recovery drills:

- [ ] Monthly: Restore file from snapshot
- [ ] Quarterly: Clone dataset and verify service starts
- [ ] Yearly: Full rebuild test on spare hardware
