# Backup

## Backup Strategy

### Two Layers of Protection

| Layer | Protects Against | Tool |
|-------|------------------|------|
| Snapshots | Accidental deletion, bad upgrades | ZFS snapshots |
| Backups | Disk failure, host loss | zfs send/receive |

## ZFS Snapshots

### Automated Snapshots

Install zfs-auto-snapshot:

```bash
sudo apt install -y zfs-auto-snapshot
```

Default retention:

- Frequent: 4 (every 15 min)
- Hourly: 24
- Daily: 31
- Weekly: 8
- Monthly: 12

### Disable for Disposable Data

```bash
sudo zfs set com.sun:auto-snapshot=false tank/containers
```

### Manual Snapshots

Before major changes:

```bash
sudo zfs snapshot -r tank@pre-upgrade-$(date +%Y%m%d)
```

## Remote Backups

### Send to Remote Server

Initial full send:

```bash
zfs send tank/nextcloud-data@latest | \
    ssh backup-server zfs receive backup/nextcloud-data
```

Incremental sends:

```bash
zfs send -i @previous @latest tank/nextcloud-data | \
    ssh backup-server zfs receive backup/nextcloud-data
```

### Automated with Sanoid/Syncoid

Install sanoid:

```bash
sudo apt install -y sanoid
```

Configure `/etc/sanoid/sanoid.conf`:

```ini
[tank/nextcloud-data]
    use_template = production

[template_production]
    frequently = 0
    hourly = 24
    daily = 30
    monthly = 6
    yearly = 0
    autosnap = yes
    autoprune = yes
```

Run syncoid for replication:

```bash
syncoid tank/nextcloud-data backup-server:backup/nextcloud-data
```

## Database Backups

### MariaDB Dump

```bash
docker exec nextcloud-db mysqldump -u root -p nextcloud > \
    /mnt/tank/backups/nextcloud-db-$(date +%Y%m%d).sql
```

### Before Container Updates

Always snapshot before updating:

```bash
sudo zfs snapshot tank/db/nextcloud@pre-update
docker compose pull
docker compose up -d
```

## Backup Verification

### Test Restore Regularly

1. Clone snapshot to temporary dataset
2. Start service against clone
3. Verify data integrity
4. Destroy clone

```bash
# Clone
zfs clone tank/nextcloud-data@backup tank/test-restore

# Verify
ls /mnt/tank/test-restore

# Cleanup
zfs destroy tank/test-restore
```

## Backup Schedule

| Data | Snapshot Frequency | Remote Backup |
|------|-------------------|---------------|
| nextcloud-data | Hourly | Daily |
| nextcloud-app | Daily | Weekly |
| db | Hourly | Daily |
| media | Weekly | Monthly |
| vm | Manual (pre-change) | Weekly |
