# Operations

This section covers backup, recovery, and maintenance procedures.

## Philosophy

- **ZFS snapshots** protect against accidental deletion and bad upgrades
- **Backups** protect against disk failure and host loss
- **Host is rebuildable** without touching ZFS data

## Sections

- [Capacity Planning](capacity-planning.md) - System-wide resource allocation strategy
- [Backup](backup.md) - Snapshot and backup strategies
- [Recovery](recovery.md) - Disaster recovery procedures
- [Rebuild Checklist](rebuild-checklist.md) - Host reinstallation steps
