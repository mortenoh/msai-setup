# Recovery — scenario router

A short list of "something broke; what do I do?" with pointers to the canonical procedure for each scenario. Most of the actual content lives in the [Backup &amp; Recovery](backup.md), [Rebuild Checklist](rebuild-checklist.md), or the ZFS [Operations](../zfs/operations.md) / [Troubleshooting](../zfs/troubleshooting.md) pages — this page is the way in.

## Pick your scenario

| Scenario | First action | Canonical procedure |
|---|---|---|
| Accidentally deleted a file or directory | Find the most recent snapshot, copy it back | [ZFS Snapshots → Reading from a snapshot](../zfs/snapshots.md#reading-from-a-snapshot) |
| Bad service upgrade — Nextcloud / Authentik / etc. | Stop service, rollback its dataset, restart | [Docker Integration → Snapshot before risky operations](../zfs/docker-integration.md#snapshot-before-risky-operations) |
| Bad VM-side change — Windows Update broke the guest | Stop VM, rollback its dataset, start | [VM Storage → When the VM corrupts its filesystem](../zfs/vm-storage.md#when-the-vm-corrupts-its-filesystem) |
| Container won't start | `docker compose down && up --force-recreate` — data is on ZFS, not in the container | [Docker Integration](../zfs/docker-integration.md) |
| ZFS pool reports DEGRADED / disk error | Read `zpool status -v`, plan disk replacement | [ZFS Operations → Disk replacement](../zfs/operations.md#disk-replacement) |
| ZFS pool won't import after reboot | Manual `zpool import`, check zfs-import services | [ZFS Troubleshooting → I rebooted and the pool isn't there](../zfs/troubleshooting.md#i-rebooted-and-the-pool-isnt-there) |
| Host OS broken; ZFS pool fine | Reinstall Ubuntu, re-import pool, restore services | [Rebuild Checklist](rebuild-checklist.md) |
| Disk failure on the no-redundancy pool | Replace disk, restore from off-host backup | [Backup &amp; Recovery → Off-site target](backup.md#off-site-target) + [Rebuild Checklist](rebuild-checklist.md) |
| Pool metadata corruption (FAULTED) | Try read-only import; rewind with `-F`; restore from backup if needed | [ZFS Troubleshooting → Pool is FAULTED / UNAVAIL](../zfs/troubleshooting.md#pool-is-faulted--unavail) |
| Lost ZFS encryption passphrase | No recovery is possible | [ZFS Encryption → Lost passphrase](../zfs/encryption.md#lost-passphrase) |
| Database (Postgres / MariaDB) corruption | Rollback DB dataset, or restore from SQL dump | See [Database from snapshot](#database-from-snapshot-or-sql-dump) below |
| Forgot SSH access (locked out) | Console-rescue path or single-user GRUB boot | See [Locked-out recovery](#locked-out-of-ssh) below |
| Tailscale stopped working | Re-auth, check ACLs | [Tailscale Troubleshooting](../tailscale/troubleshooting/index.md) |

## Database from snapshot or SQL dump

Two paths depending on what's available.

### From ZFS snapshot (fastest)

```bash
# Stop the container so it isn't writing during rollback
cd /path/to/compose/dir
docker compose stop postgres

# Rollback the DB dataset
sudo zfs rollback tank/db/postgres@before-upgrade-2026-05-17

# Start again
docker compose start postgres
docker compose logs --tail=50 postgres
```

The rollback is point-in-time-consistent (matches the txg at which the snapshot was taken). Postgres will recover from its WAL on next start.

### From SQL dump (slower, more portable)

If you took a `pg_dump` / `mysqldump` before the bad change:

```bash
# Postgres
docker exec -i postgres-container psql -U user database < /mnt/tank/backups/db-2026-05-17.sql

# MariaDB / MySQL
docker exec -i mariadb-container mysql -u root -p database < /mnt/tank/backups/db-2026-05-17.sql
```

For Postgres specifically, use `pg_restore` for custom-format dumps:

```bash
docker exec -i postgres-container pg_restore -U user -d database < /mnt/tank/backups/db.dump
```

## Locked out of SSH

If `ssh user@host` stops working after a config change:

1. **Try from a different source IP / Tailscale.** Lockouts (e.g. fail2ban, pam_faillock) are usually per-source IP.
2. **Reach the box on its single HDMI output + keyboard.** Use a recovery shell to undo the change:

   ```bash
   # Reset PAM faillock for root (and others)
   sudo faillock --user root --reset

   # Or roll back ssh config
   sudo cp /etc/ssh/sshd_config.bak /etc/ssh/sshd_config
   sudo systemctl restart ssh
   ```
3. **Boot via GRUB recovery mode** if the SSH service won't start. Edit the kernel cmdline at GRUB to append `single` or `init=/bin/bash`, drop to a root shell, fix the config.
4. **As a last resort, boot from a Ubuntu live USB**, mount the root filesystem, and edit `/etc/ssh/sshd_config` directly.

See [PAM → Recovery if root gets locked out](../ubuntu/system/pam.md) for the faillock specifics.

## Recovery drill schedule

Pick a cadence and stick to it. Skipping drills is how you find out your backups didn't actually work the day you really need them.

- **Monthly**: restore a single file from the most recent snapshot. Five minutes.
- **Quarterly**: clone a dataset to a new mountpoint and start the service against it — verifies the snapshot is actually usable, not just present.
- **Quarterly**: test the off-site backup by listing it and restoring one file.
- **Annually**: walk through the [Rebuild Checklist](rebuild-checklist.md) on spare hardware or a VirtualBox lab (see [ZFS VirtualBox Lab](../zfs/virtualbox-lab.md)). Time how long it takes; that's your real RTO.

A drill that doesn't end in "I successfully read the data" doesn't count.
