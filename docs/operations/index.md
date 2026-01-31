# Operations

This section covers monitoring, power management, backup, recovery, and maintenance procedures.

## Philosophy

- **ZFS snapshots** protect against accidental deletion and bad upgrades
- **Backups** protect against disk failure and host loss
- **Host is rebuildable** without touching ZFS data
- **Proactive monitoring** catches issues before they become failures

## Sections

- [Capacity Planning](capacity-planning.md) - System-wide resource allocation strategy
- [Monitoring](monitoring.md) - Hardware health and alerting
- [Power Management](power-management.md) - APU power and thermal control
- [Backup & Recovery](backup.md) - Snapshot, backup, and recovery procedures
- [Recovery](recovery.md) - Detailed recovery scenarios
- [Rebuild Checklist](rebuild-checklist.md) - Host reinstallation steps
