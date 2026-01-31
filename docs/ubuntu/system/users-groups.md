# Users and Groups

Proper user and group management is fundamental to system security. This page covers creating, managing, and securing user accounts on Ubuntu Server 24.04.

## User Management Fundamentals

### User Account Components

Each user account consists of:

| Component | Location | Purpose |
|-----------|----------|---------|
| Username | `/etc/passwd` | Login name |
| UID | `/etc/passwd` | Numeric identifier |
| Primary GID | `/etc/passwd` | Default group |
| Home directory | `/etc/passwd` | User's files |
| Shell | `/etc/passwd` | Login shell |
| Password hash | `/etc/shadow` | Encrypted password |

### UID Ranges

Ubuntu follows conventional UID allocation:

| Range | Purpose |
|-------|---------|
| 0 | root |
| 1-999 | System accounts |
| 1000+ | Regular users |
| 65534 | nobody (special) |

## Creating Users

### Interactive User Creation

```bash
# Create user with home directory and bash shell
sudo adduser newuser
```

The `adduser` command interactively prompts for:
- Password
- Full name (GECOS)
- Room number (optional)
- Phone numbers (optional)
- Other (optional)

### Non-Interactive User Creation

```bash
# Create user with specific options
sudo useradd -m -s /bin/bash -c "John Doe" johndoe

# Set password
sudo passwd johndoe
```

**useradd Options:**

| Option | Purpose |
|--------|---------|
| `-m` | Create home directory |
| `-s /bin/bash` | Set login shell |
| `-c "Comment"` | Set GECOS/full name |
| `-u 1500` | Specific UID |
| `-g users` | Primary group |
| `-G sudo,docker` | Additional groups |
| `-e 2025-12-31` | Account expiry date |
| `-d /custom/home` | Custom home directory |

### System User Creation

For service accounts that don't need login:

```bash
# Create system user without home or login shell
sudo useradd -r -s /usr/sbin/nologin -c "Service Account" serviceuser
```

| Option | Purpose |
|--------|---------|
| `-r` | System account (UID < 1000) |
| `-s /usr/sbin/nologin` | No shell access |
| `-M` | No home directory |

## Modifying Users

### Common Modifications

```bash
# Change shell
sudo usermod -s /bin/zsh username

# Add to additional groups (append)
sudo usermod -aG sudo,docker username

# Change primary group
sudo usermod -g newgroup username

# Lock account (disable login)
sudo usermod -L username

# Unlock account
sudo usermod -U username

# Set account expiry
sudo usermod -e 2025-06-30 username

# Change home directory
sudo usermod -d /new/home -m username
```

!!! warning "Group Modification"
    Using `-G` without `-a` **replaces** all secondary groups. Always use `-aG` to append groups.

### Password Management

```bash
# Change password
sudo passwd username

# Force password change on next login
sudo passwd -e username

# Set password expiry (90 days)
sudo chage -M 90 username

# View password expiry info
sudo chage -l username

# Set minimum days between password changes
sudo chage -m 7 username
```

## Deleting Users

### Remove User Account

```bash
# Delete user, keep home directory
sudo userdel username

# Delete user and home directory
sudo userdel -r username

# Delete user, home, and mail spool
sudo userdel -r -f username
```

!!! tip "Pre-Deletion Checklist"
    Before deleting a user:

    1. Check for running processes: `pgrep -u username`
    2. Check for cron jobs: `crontab -u username -l`
    3. Backup home directory if needed
    4. Review file ownership elsewhere: `find / -user username 2>/dev/null`

### Handle Orphaned Files

After deleting a user, files owned by their UID become orphaned:

```bash
# Find files owned by UID (not username)
sudo find / -uid 1001 -ls 2>/dev/null

# Change ownership
sudo chown -R newowner:newgroup /path/to/files
```

## Group Management

### Creating Groups

```bash
# Create standard group
sudo groupadd developers

# Create with specific GID
sudo groupadd -g 2000 developers
```

### Group Membership

```bash
# Add user to group
sudo gpasswd -a username groupname

# Remove user from group
sudo gpasswd -d username groupname

# Set group members (replaces all)
sudo gpasswd -M user1,user2,user3 groupname

# List group members
getent group groupname
```

### Common System Groups

| Group | Purpose | Example Usage |
|-------|---------|---------------|
| sudo | Administrative access | Full sudo rights |
| adm | Log access | Read system logs |
| docker | Docker daemon access | Run docker commands |
| libvirt | KVM/QEMU access | Manage VMs |
| www-data | Web server | Web application files |
| systemd-journal | Journal access | Read journalctl |

### Deleting Groups

```bash
# Delete group (must have no primary members)
sudo groupdel groupname
```

## Home Directory Security

### Default Permissions

Ubuntu 24.04 creates home directories with `755` by default. This may be too permissive.

```bash
# Check current home directory permissions
ls -la /home/

# Restrict to owner only
sudo chmod 700 /home/username
```

### Change Default for New Users

Edit `/etc/adduser.conf`:

```bash
# Set default home directory permissions
DIR_MODE=0700
```

Or with login.defs for useradd:

```bash
# In /etc/login.defs
UMASK 077
```

### Home Directory Skeleton

Files in `/etc/skel` are copied to new home directories:

```bash
# View skeleton contents
ls -la /etc/skel/

# Add custom files for all new users
sudo cp .bashrc.custom /etc/skel/.bashrc
```

## Shell Restrictions

### Restrict Shell Access

For accounts that shouldn't have interactive shell:

```bash
# Set to nologin
sudo usermod -s /usr/sbin/nologin username

# Set to restricted shell
sudo usermod -s /bin/rbash username
```

### Valid Login Shells

Only shells listed in `/etc/shells` are valid:

```bash
cat /etc/shells
# /bin/sh
# /bin/bash
# /usr/bin/bash
# /bin/rbash
# /usr/bin/rbash
# /bin/dash
# /usr/bin/dash
# /usr/bin/tmux
# /usr/bin/screen
```

### Restricted Bash (rbash)

rbash limits what users can do:

- Cannot change directories
- Cannot modify PATH
- Cannot use / in command names
- Cannot redirect output

```bash
# Create restricted user
sudo useradd -m -s /bin/rbash restricteduser
```

## Security Best Practices

### Account Policies

| Policy | Implementation |
|--------|----------------|
| Unique accounts | One account per person |
| No shared passwords | Individual authentication |
| Service accounts | Separate accounts for services |
| Account review | Regular audit of active accounts |
| Account expiry | Set end dates for temporary access |

### Password Requirements

Configure in `/etc/login.defs`:

```ini
# Password aging
PASS_MAX_DAYS   90
PASS_MIN_DAYS   7
PASS_WARN_AGE   14

# Minimum password length
PASS_MIN_LEN    12

# Encryption algorithm
ENCRYPT_METHOD  YESCRYPT
```

### Audit User Accounts

```bash
# List all users
getent passwd

# List users with login shells
grep -v nologin /etc/passwd | grep -v /bin/false

# Find users with UID 0 (should only be root)
awk -F: '$3 == 0 {print $1}' /etc/passwd

# Find users without passwords
sudo awk -F: '$2 == "" {print $1}' /etc/shadow

# Find accounts with no password expiry
sudo awk -F: '$5 == "" || $5 == 99999 {print $1}' /etc/shadow
```

### Lock Unused Accounts

```bash
# Lock account
sudo usermod -L username

# Lock and expire
sudo usermod -L -e 1 username

# Verify locked status
sudo passwd -S username
# Should show "L" for locked
```

## User Information Commands

### View User Details

```bash
# Current user info
id

# Specific user info
id username

# User's groups
groups username

# Detailed user info
getent passwd username

# Password status
sudo passwd -S username

# Password aging info
sudo chage -l username

# Last login
lastlog -u username

# Login history
last username
```

### Find User Files

```bash
# Files owned by user
find /home -user username -ls

# Find files by user in specific location
find /var/www -user www-data -type f

# Files with specific group
find /shared -group developers -ls
```

## Configuration Files Reference

### /etc/passwd Format

```
username:x:UID:GID:GECOS:home:shell
```

Example:
```
johndoe:x:1001:1001:John Doe,,,:/home/johndoe:/bin/bash
```

### /etc/shadow Format

```
username:password:lastchange:min:max:warn:inactive:expire:reserved
```

| Field | Meaning |
|-------|---------|
| password | Hashed password or `!`/`*` for locked |
| lastchange | Days since 1970-01-01 of last change |
| min | Minimum days between changes |
| max | Maximum days before change required |
| warn | Days before expiry to warn |
| inactive | Days after expiry before disable |
| expire | Account expiry date |

### /etc/group Format

```
groupname:x:GID:member1,member2
```

## Next Steps

With user management established, continue to [sudo Configuration](sudo-configuration.md) to control privilege escalation.
