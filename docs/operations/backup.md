# Backup & Recovery

This page covers backup strategies, recovery testing, and disaster recovery procedures.

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

## Recovery Testing

Regular recovery testing validates that backups are actually restorable.

### Test Schedule

| Test | Frequency | Duration |
|------|-----------|----------|
| File restore from snapshot | Monthly | 15 min |
| Clone dataset and verify service | Quarterly | 1 hour |
| Full rebuild on test hardware | Yearly | 4+ hours |

### Monthly: File Restore Test

Verify you can restore individual files from snapshots:

```bash
# List available snapshots
ls /mnt/tank/nextcloud-data/.zfs/snapshot/

# Pick a recent snapshot and verify file access
ls /mnt/tank/nextcloud-data/.zfs/snapshot/hourly-$(date +%Y-%m-%d)/

# Copy a file to verify
cp /mnt/tank/nextcloud-data/.zfs/snapshot/hourly-$(date +%Y-%m-%d)/test-file.txt /tmp/

# Log the test
echo "$(date): File restore test PASSED" >> /var/log/recovery-tests.log
```

### Quarterly: Service Restore Test

Clone a dataset and verify the service starts:

```bash
# Stop services to avoid conflicts
cd ~/docker/nextcloud && docker compose down

# Clone the current snapshot
sudo zfs snapshot tank/nextcloud-data@restore-test
sudo zfs clone tank/nextcloud-data@restore-test tank/restore-test

# Verify data integrity
ls /mnt/tank/restore-test

# Start service with cloned data (modify compose to use clone path)
# ... verify service works ...

# Cleanup
sudo zfs destroy tank/restore-test
sudo zfs destroy tank/nextcloud-data@restore-test

# Restart production
docker compose up -d

# Log the test
echo "$(date): Quarterly service restore test PASSED" >> /var/log/recovery-tests.log
```

### Yearly: Full Rebuild Test

On spare or test hardware:

1. Install fresh Ubuntu Server
2. Install ZFS and import pool (or restore from backup)
3. Follow [Rebuild Checklist](rebuild-checklist.md)
4. Verify all services operational
5. Document any issues encountered

### Test Result Logging

Maintain a log of all recovery tests:

```bash
# /var/log/recovery-tests.log format
# DATE: Test type - PASSED/FAILED - Notes

2024-01-15: Monthly file restore - PASSED
2024-02-15: Monthly file restore - PASSED
2024-03-01: Quarterly service clone - PASSED
2024-03-15: Monthly file restore - PASSED
```

## Disaster Scenarios

### Scenario 1: Single Disk Failure

**Symptoms**: ZFS pool shows degraded or faulted disk

**Recovery**:

1. Identify failed disk:
   ```bash
   zpool status tank
   ```

2. If mirrored, replace the disk:
   ```bash
   sudo zpool replace tank /dev/old-disk /dev/new-disk
   sudo zpool status  # Monitor resilver
   ```

3. If no redundancy, restore from backup:
   ```bash
   # Replace disk, create new pool
   sudo zpool create tank /dev/new-disk

   # Restore from remote backup
   ssh backup-server "zfs send -R backup/tank@latest" | sudo zfs receive -F tank
   ```

**Estimated Recovery Time**: 1-4 hours (mirror) or 4-24 hours (full restore)

### Scenario 2: Complete Host Loss

**Symptoms**: Hardware failure, cannot boot, physical damage

**Recovery**:

1. If disks are intact:
   - Install fresh Ubuntu on new hardware
   - Import existing pool: `sudo zpool import tank`
   - Follow [Rebuild Checklist](rebuild-checklist.md)

2. If disks are lost:
   - Restore from offsite backup
   - Follow full recovery procedure below

**Estimated Recovery Time**: 4-8 hours (disks intact) or 24+ hours (full restore)

### Scenario 3: Data Corruption Discovery

**Symptoms**: Files unreadable, checksum errors, application errors

**Recovery**:

1. Run ZFS scrub to identify extent:
   ```bash
   sudo zpool scrub tank
   zpool status tank  # Check for errors
   ```

2. For corrupted files, restore from snapshot:
   ```bash
   # Find snapshot before corruption
   ls /mnt/tank/data/.zfs/snapshot/

   # Copy clean version
   cp /mnt/tank/data/.zfs/snapshot/daily-2024-01-14/corrupted-file \
      /mnt/tank/data/corrupted-file
   ```

3. For widespread corruption, rollback dataset:
   ```bash
   sudo zfs rollback tank/data@last-good-snapshot
   ```

**Estimated Recovery Time**: 1-4 hours

### Scenario 4: Ransomware Recovery

**Symptoms**: Files encrypted, ransom notes present

**Recovery**:

1. **Immediately**: Disconnect from network
   ```bash
   sudo ip link set eth0 down
   ```

2. Do NOT pay ransom

3. Assess damage:
   - Which datasets are affected?
   - When did encryption start?

4. Rollback to pre-infection snapshot:
   ```bash
   # Find clean snapshot (before infection date)
   zfs list -t snapshot -o name,creation

   # Rollback affected datasets
   sudo zfs rollback tank/data@pre-infection
   ```

5. Before reconnecting:
   - Investigate infection vector
   - Patch vulnerabilities
   - Change all credentials

**Estimated Recovery Time**: 4-24 hours

## Recovery Runbooks

### Runbook: Nextcloud Restore

**Prerequisites**: SSH access to server, ZFS snapshots available

1. Stop Nextcloud:
   ```bash
   cd ~/docker/nextcloud
   docker compose down
   ```

2. Rollback datasets:
   ```bash
   sudo zfs rollback tank/nextcloud-data@backup
   sudo zfs rollback tank/nextcloud-app@backup
   sudo zfs rollback tank/db/nextcloud@backup
   ```

3. Start Nextcloud:
   ```bash
   docker compose up -d
   ```

4. Verify:
   - Access web UI
   - Check file listing
   - Verify recent files exist

### Runbook: Database Restore from Dump

**Prerequisites**: SQL dump file available

1. Stop application:
   ```bash
   docker compose stop nextcloud
   ```

2. Restore database:
   ```bash
   docker exec -i nextcloud-db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" nextcloud < backup.sql
   ```

3. Restart application:
   ```bash
   docker compose start nextcloud
   ```

4. Run maintenance:
   ```bash
   docker exec -u www-data nextcloud php occ maintenance:repair
   docker exec -u www-data nextcloud php occ files:scan --all
   ```

### Runbook: Full System Recovery

**Prerequisites**: Backup server accessible, new hardware ready

1. Install Ubuntu Server (minimal)

2. Install ZFS:
   ```bash
   sudo apt update && sudo apt install -y zfsutils-linux
   ```

3. Create pool (if restoring from backup):
   ```bash
   sudo zpool create tank /dev/nvme0n1p3
   ```

4. Restore data:
   ```bash
   # Full recursive restore
   ssh backup-server "zfs send -R backup/tank@latest" | sudo zfs receive -F tank
   ```

5. Follow [Rebuild Checklist](rebuild-checklist.md) for:
   - Docker installation
   - Container configuration
   - Network setup
   - Service verification

### Required Access and Credentials

Keep secure, offline copies of:

| Item | Location |
|------|----------|
| SSH keys | Password manager, printed |
| Root/admin passwords | Password manager |
| Backup server credentials | Password manager |
| Docker .env files | In ZFS snapshot, password manager |
| BIOS password | Printed, secure location |
| Encryption keys (if applicable) | Multiple secure locations |

!!! warning "Credential Storage"
    Recovery is impossible without access credentials. Store them in multiple secure locations.
