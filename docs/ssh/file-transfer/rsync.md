# Rsync over SSH

## Overview

Rsync is the most efficient tool for file synchronization and transfer. When used with SSH, it provides:

- Delta transfers (only changed parts)
- Resume support
- Compression
- Preservation of permissions, ownership, timestamps
- Bandwidth limiting

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Rsync Delta Transfer                              │
│                                                                           │
│   Source                                     Destination                  │
│   ┌─────────────────┐                       ┌─────────────────┐          │
│   │ File: 100 MB    │                       │ File: 100 MB    │          │
│   │                 │    Only Changed       │ (older version) │          │
│   │ ████████░░░░░░░ │───────────────────────▶│ ████████████████ │          │
│   │                 │    Blocks (~1 MB)     │                 │          │
│   │ (10% changed)   │                       │ (updated)       │          │
│   └─────────────────┘                       └─────────────────┘          │
│                                                                           │
│   Traditional copy: 100 MB                                               │
│   Rsync delta:      ~10 MB                                               │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Basic Syntax

```bash
rsync [options] source destination
```

## Common Options

| Option | Description |
|--------|-------------|
| `-a` | Archive mode (preserves everything) |
| `-v` | Verbose |
| `-z` | Compress during transfer |
| `-P` | Progress + partial (resume) |
| `--delete` | Delete extraneous files from dest |
| `-n` | Dry run (show what would happen) |
| `-e ssh` | Use SSH (default on modern rsync) |

## Basic Transfers

### Local to Remote

```bash
rsync -avz /local/path/ user@host:/remote/path/
```

### Remote to Local

```bash
rsync -avz user@host:/remote/path/ /local/path/
```

### With Progress

```bash
rsync -avzP /local/path/ user@host:/remote/path/
```

## Important: Trailing Slashes

```bash
# With trailing slash: copy CONTENTS of dir
rsync -av /source/ /dest/
# Result: /dest/file1, /dest/file2

# Without trailing slash: copy dir ITSELF
rsync -av /source /dest/
# Result: /dest/source/file1, /dest/source/file2
```

## SSH Options

### Custom Port

```bash
rsync -avz -e "ssh -p 2222" /local/ user@host:/remote/
```

### Specific Key

```bash
rsync -avz -e "ssh -i ~/.ssh/mykey" /local/ user@host:/remote/
```

### Through Jump Host

```bash
rsync -avz -e "ssh -J jumphost" /local/ user@internal:/remote/
```

### Multiple SSH Options

```bash
rsync -avz -e "ssh -p 2222 -i ~/.ssh/key -o StrictHostKeyChecking=no" /local/ user@host:/remote/
```

## Synchronization

### Mirror (Delete Extra Files)

```bash
rsync -avz --delete /local/ user@host:/remote/
```

!!! warning "Dangerous"
    `--delete` removes files from destination that don't exist in source. Use with caution.

### Dry Run First

```bash
rsync -avzn --delete /local/ user@host:/remote/
# Shows what WOULD happen without doing it
```

### One-Way Sync

```bash
rsync -avz --delete /source/ /dest/
```

### Exclude Files

```bash
rsync -avz --exclude='*.log' --exclude='cache/' /local/ user@host:/remote/
```

### Exclude from File

```bash
rsync -avz --exclude-from='exclude.txt' /local/ user@host:/remote/
```

```text
# exclude.txt
*.log
*.tmp
cache/
.git/
node_modules/
```

### Include/Exclude Patterns

```bash
# Only sync *.php and *.html
rsync -avz --include='*.php' --include='*.html' --exclude='*' /local/ user@host:/remote/
```

## Resume Transfers

### Partial Files

```bash
rsync -avzP /local/largefile.iso user@host:/remote/
# -P = --partial --progress
# If interrupted, run same command to resume
```

### Partial Directory

```bash
rsync -avz --partial-dir=.rsync-partial /local/ user@host:/remote/
```

## Bandwidth Control

### Limit Speed

```bash
rsync -avz --bwlimit=1000 /local/ user@host:/remote/
# Limit in KB/s (1000 KB/s = ~1 MB/s)
```

## Preserve Options

### Archive Mode (-a)

Equivalent to: `-rlptgoD`
- `-r` Recursive
- `-l` Preserve symlinks
- `-p` Preserve permissions
- `-t` Preserve times
- `-g` Preserve group
- `-o` Preserve owner
- `-D` Preserve devices and specials

### Additional Preservation

```bash
rsync -avzP --acls --xattrs /local/ user@host:/remote/
# Also preserve ACLs and extended attributes
```

### Hard Links

```bash
rsync -avzH /local/ user@host:/remote/
# -H preserves hard links
```

## Comparison Options

### Skip Based on Checksum

```bash
rsync -avzc /local/ user@host:/remote/
# -c uses checksum instead of time/size (slower but accurate)
```

### Update Only (Skip Newer)

```bash
rsync -avzu /local/ user@host:/remote/
# -u skip files that are newer on receiver
```

### Ignore Existing

```bash
rsync -avz --ignore-existing /local/ user@host:/remote/
```

## Backup Strategies

### Simple Backup

```bash
rsync -avz /data/ user@backup:/backups/$(date +%Y%m%d)/
```

### Incremental with Hard Links

```bash
rsync -avz --link-dest=/backups/latest /data/ user@backup:/backups/$(date +%Y%m%d)/
ln -sfn /backups/$(date +%Y%m%d) /backups/latest
```

Space-efficient: unchanged files are hard-linked.

### Backup with Rotation

```bash
#!/bin/bash
# backup.sh

DEST="user@backup:/backups"
LINK_DEST="--link-dest=../latest"

# Rotate
ssh user@backup "rm -rf /backups/backup.3"
ssh user@backup "mv /backups/backup.2 /backups/backup.3 2>/dev/null"
ssh user@backup "mv /backups/backup.1 /backups/backup.2 2>/dev/null"
ssh user@backup "mv /backups/latest /backups/backup.1 2>/dev/null"

# New backup
rsync -avz --delete $LINK_DEST /data/ $DEST/latest/
```

## Logging

### Verbose Output to File

```bash
rsync -avz /local/ user@host:/remote/ | tee rsync.log
```

### Log File Option

```bash
rsync -avz --log-file=rsync.log /local/ user@host:/remote/
```

### Statistics

```bash
rsync -avz --stats /local/ user@host:/remote/
```

## Common Use Cases

### Website Deployment

```bash
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.env' \
    /local/project/ user@web:/var/www/site/
```

### Database Backup Sync

```bash
rsync -avzP \
    --bwlimit=5000 \
    /var/backups/mysql/ user@backup:/backups/mysql/
```

### Photo/Media Sync

```bash
rsync -avzP \
    --include='*.jpg' \
    --include='*.mp4' \
    --include='*/' \
    --exclude='*' \
    /media/photos/ user@nas:/photos/
```

### Home Directory Backup

```bash
rsync -avz \
    --exclude='.cache' \
    --exclude='Downloads' \
    --exclude='.local/share/Trash' \
    ~/ user@backup:/backups/home/
```

## Troubleshooting

### Permission Errors

```bash
# Check user has write permission
ssh user@host "ls -la /remote/path"

# Or use --no-perms
rsync -avz --no-perms /local/ user@host:/remote/
```

### Slow Initial Scan

```bash
# Disable delta for first sync of large files
rsync -avz --whole-file /local/ user@host:/remote/
```

### Connection Timeout

```bash
rsync -avz -e "ssh -o ServerAliveInterval=60" /local/ user@host:/remote/
```

### Character Encoding

```bash
rsync -avz --iconv=UTF-8,UTF-8 /local/ user@host:/remote/
```

### Debugging

```bash
rsync -avvvz /local/ user@host:/remote/
# Extra v's for more detail
```

## Rsync Daemon Mode

For better performance (no SSH overhead):

### Server Setup

```bash
# /etc/rsyncd.conf
[backup]
    path = /data/backup
    read only = no
    auth users = backupuser
    secrets file = /etc/rsyncd.secrets
```

```bash
# /etc/rsyncd.secrets
backupuser:secretpassword
```

### Client Usage

```bash
rsync -avz /local/ backupuser@host::backup/
```

!!! note "Security"
    Rsync daemon mode isn't encrypted. Use SSH for security, or only on trusted networks.

## Comparison

| Feature | rsync | scp | sftp |
|---------|-------|-----|------|
| Delta transfer | ✅ | ❌ | ❌ |
| Resume | ✅ | ❌ | ✅ |
| Progress | ✅ | ✅ | ✅ |
| Sync/delete | ✅ | ❌ | ❌ |
| Bandwidth limit | ✅ | ✅ | ✅ |
| Preserve perms | ✅ | ✅ | ✅ |
| Complexity | Medium | Low | Low |
