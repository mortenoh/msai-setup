# SFTP - SSH File Transfer Protocol

## Overview

SFTP is an interactive file transfer protocol that runs over SSH. Unlike FTP, it uses a single encrypted connection.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          SFTP Session                                     │
│                                                                           │
│   Local Machine                              Remote Server                │
│   ┌─────────────────┐                       ┌─────────────────┐          │
│   │                 │    SSH Connection     │                 │          │
│   │  SFTP Client    │◀─────────────────────▶│  SFTP Server    │          │
│   │                 │    (Port 22)          │                 │          │
│   │  • Browse       │    Encrypted          │  • /home/user   │          │
│   │  • Upload       │    Authenticated      │  • /var/www     │          │
│   │  • Download     │                       │                 │          │
│   │  • Manage       │                       │                 │          │
│   └─────────────────┘                       └─────────────────┘          │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Basic Connection

### Connect

```bash
sftp user@host
sftp -P 2222 user@host    # Custom port
sftp -i ~/.ssh/key user@host    # Specific key
```

### Using SSH Config

```bash
# ~/.ssh/config
Host myserver
    HostName server.example.com
    User admin
    IdentityFile ~/.ssh/key
```

```bash
sftp myserver
```

## Interactive Commands

### Navigation

```bash
sftp> pwd          # Remote working directory
sftp> lpwd         # Local working directory
sftp> cd /path     # Change remote directory
sftp> lcd /path    # Change local directory
sftp> ls           # List remote files
sftp> lls          # List local files
```

### File Transfer

```bash
sftp> get file.txt           # Download file
sftp> get file.txt local.txt # Download with rename
sftp> get -r directory/      # Download directory

sftp> put file.txt           # Upload file
sftp> put file.txt remote.txt # Upload with rename
sftp> put -r directory/      # Upload directory

sftp> mget *.txt             # Download multiple files
sftp> mput *.txt             # Upload multiple files
```

### File Management

```bash
sftp> mkdir newdir           # Create directory
sftp> rmdir emptydir         # Remove empty directory
sftp> rm file.txt            # Delete file
sftp> rename old.txt new.txt # Rename file
sftp> chmod 755 script.sh    # Change permissions
sftp> chown user file.txt    # Change owner
sftp> chgrp group file.txt   # Change group
sftp> ln -s target link      # Create symlink
```

### Information

```bash
sftp> ls -la                 # Detailed listing
sftp> df -h                  # Disk space
sftp> !command               # Run local command
sftp> help                   # Show commands
sftp> ?                      # Show commands
```

### Session Control

```bash
sftp> bye                    # Exit
sftp> exit                   # Exit
sftp> quit                   # Exit
```

## Non-Interactive Mode

### Single Command

```bash
sftp user@host <<< "get file.txt"
```

### Batch Mode

```bash
sftp -b commands.txt user@host
```

```bash
# commands.txt
cd /var/www
get index.html
get styles.css
bye
```

### Script Example

```bash
#!/bin/bash
sftp user@host << EOF
cd /backup
put database.sql
put config.tar.gz
bye
EOF
```

## Progress and Options

### Show Progress

```bash
sftp> progress      # Toggle progress display
```

### Preserve Timestamps

```bash
sftp> get -p file.txt
sftp> put -p file.txt
```

### Resume Transfer

```bash
sftp> reget largefile.iso    # Resume download
sftp> reput largefile.iso    # Resume upload
```

### Bandwidth Limit

```bash
sftp -l 1000 user@host    # Limit in Kbit/s
```

## Directory Synchronization

### Download Directory

```bash
sftp> get -r /remote/dir/
```

### Upload Directory

```bash
sftp> put -r /local/dir/
```

### Mirror (Requires Script)

```bash
#!/bin/bash
# Simple mirror using sftp

sftp user@host << EOF
lcd /local/path
cd /remote/path
mget *
bye
EOF
```

For true synchronization, use rsync instead.

## GUI Clients

### FileZilla

1. File → Site Manager
2. Protocol: SFTP
3. Host, Port, User
4. Logon Type: Key file
5. Connect

### WinSCP (Windows)

1. New Site
2. Protocol: SFTP
3. Enter credentials
4. Advanced → SSH → Authentication → Private key file
5. Login

### Cyberduck (macOS)

1. Open Connection
2. SFTP (SSH File Transfer Protocol)
3. Enter server details
4. Connect

### Nautilus/Dolphin (Linux)

Address bar:
```
sftp://user@host/path
```

## Mounting with SSHFS

Mount remote filesystem locally:

### Install

```bash
# Debian/Ubuntu
apt install sshfs

# macOS
brew install sshfs
```

### Mount

```bash
sshfs user@host:/remote/path /local/mountpoint
```

### With Options

```bash
sshfs user@host:/path /mnt/remote \
    -o IdentityFile=~/.ssh/key \
    -o reconnect \
    -o ServerAliveInterval=15 \
    -o allow_other
```

### Unmount

```bash
fusermount -u /local/mountpoint   # Linux
umount /local/mountpoint          # macOS
```

### fstab Entry

```bash
# /etc/fstab
user@host:/remote/path /local/mount fuse.sshfs noauto,x-systemd.automount,_netdev,users,idmap=user,IdentityFile=/home/user/.ssh/key,allow_other,reconnect 0 0
```

## SFTP-Only Users

### Server Configuration

```bash
# /etc/ssh/sshd_config
Subsystem sftp internal-sftp

Match User sftpuser
    ChrootDirectory /data/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
```

### Directory Setup

```bash
# Create user
useradd -m -s /usr/sbin/nologin sftpuser

# Create chroot directory (must be owned by root)
mkdir -p /data/sftp/sftpuser/files
chown root:root /data/sftp/sftpuser
chmod 755 /data/sftp/sftpuser

# Writable directory for user
chown sftpuser:sftpuser /data/sftp/sftpuser/files
```

## Troubleshooting

### Connection Failed

```bash
# Test SSH first
ssh user@host

# Check SFTP subsystem
ssh user@host "which sftp-server"
grep Subsystem /etc/ssh/sshd_config
```

### Permission Denied

```bash
# Check remote permissions
sftp> ls -la

# Check user owns files
sftp> !id
```

### Transfer Stalls

```bash
# Enable keep-alive
sftp -o ServerAliveInterval=60 user@host
```

### Chroot Not Working

```bash
# Directory must be owned by root
ls -la /data/sftp/
# drwxr-xr-x root root sftpuser

# Check sshd config syntax
sshd -t
```

## SFTP vs FTP/FTPS

| Feature | SFTP | FTP | FTPS |
|---------|------|-----|------|
| Encryption | Always | No | Optional |
| Port | 22 | 21 | 21/990 |
| Firewall friendly | Yes | No | Sometimes |
| Authentication | SSH keys/password | Password | Password/certs |
| Resume support | Yes | Yes | Yes |
| Complexity | Low | Medium | High |

## Automation Example

### Backup Script

```bash
#!/bin/bash
# backup-to-sftp.sh

REMOTE_HOST="backup.example.com"
REMOTE_USER="backup"
REMOTE_DIR="/backups/$(hostname)"
LOCAL_DIR="/var/backups"
DATE=$(date +%Y%m%d)

sftp -b - ${REMOTE_USER}@${REMOTE_HOST} << EOF
mkdir ${REMOTE_DIR}
cd ${REMOTE_DIR}
put ${LOCAL_DIR}/database-${DATE}.sql.gz
put ${LOCAL_DIR}/files-${DATE}.tar.gz
bye
EOF

if [ $? -eq 0 ]; then
    echo "Backup completed successfully"
else
    echo "Backup failed"
    exit 1
fi
```

### Watch and Upload

```bash
#!/bin/bash
# watch-upload.sh

inotifywait -m -e close_write /local/dir |
while read path action file; do
    sftp user@host << EOF
put "${path}${file}" /remote/dir/
bye
EOF
done
```
