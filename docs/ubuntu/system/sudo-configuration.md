# sudo Configuration

sudo (superuser do) enables controlled privilege escalation. Proper configuration balances usability with security.

## sudo Fundamentals

### How sudo Works

```
┌─────────────────────────────────────────────────────────────┐
│                    User runs: sudo command                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PAM Authentication                              │
│         (verify user's password)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              sudoers Policy Check                            │
│         (is user authorized for this command?)               │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
              ┌─────────┐         ┌─────────┐
              │ Allowed │         │ Denied  │
              │ Execute │         │  Log &  │
              │ as root │         │ Reject  │
              └─────────┘         └─────────┘
```

### Default Ubuntu Configuration

Ubuntu uses the `sudo` group for administrative access:

```bash
# Members of sudo group get full root access
%sudo   ALL=(ALL:ALL) ALL
```

## The sudoers File

### File Location and Editing

The main sudoers file is `/etc/sudoers`. **Never edit directly**—always use visudo:

```bash
# Edit with syntax checking
sudo visudo

# Edit specific include file
sudo visudo -f /etc/sudoers.d/custom
```

!!! danger "Always Use visudo"
    Direct editing can create syntax errors that lock everyone out of sudo. visudo validates syntax before saving.

### sudoers Syntax

```
user    host=(runas_user:runas_group)    commands
```

| Field | Meaning | Example |
|-------|---------|---------|
| user | Username or %group | admin, %sudo |
| host | Hostname or ALL | ALL, webserver |
| runas_user | Target user | ALL, root, www-data |
| runas_group | Target group | ALL, www-data |
| commands | Allowed commands | ALL, /usr/bin/apt |

### Basic Examples

```sudoers
# User admin can run any command as any user
admin   ALL=(ALL:ALL) ALL

# Group wheel can run any command
%wheel  ALL=(ALL:ALL) ALL

# User backup can run specific commands without password
backup  ALL=(root) NOPASSWD: /usr/bin/rsync, /usr/bin/tar

# User deployer can restart specific service
deployer ALL=(root) /usr/bin/systemctl restart myapp.service

# User can run commands as www-data user
developer ALL=(www-data) /usr/bin/php
```

## Using sudoers.d Directory

### Modular Configuration

The `/etc/sudoers.d/` directory allows modular configuration:

```bash
# Create a new rules file
sudo visudo -f /etc/sudoers.d/developers
```

### File Requirements

| Requirement | Details |
|-------------|---------|
| No `.` or `~` in filename | Files with these are ignored |
| Mode 0440 | Correct permissions required |
| Valid syntax | Invalid files may break sudo |

```bash
# Check file permissions
ls -la /etc/sudoers.d/

# Fix permissions if needed
sudo chmod 440 /etc/sudoers.d/developers
```

### Example Organization

```
/etc/sudoers.d/
├── 00-defaults          # Default settings
├── 10-admin-users       # Admin group rules
├── 20-developers        # Developer rules
├── 30-backup            # Backup user rules
└── 90-monitoring        # Monitoring tools
```

## Security Best Practices

### Avoid NOPASSWD

NOPASSWD removes the authentication barrier:

```sudoers
# DANGEROUS: No password required
admin ALL=(ALL) NOPASSWD: ALL
```

!!! danger "NOPASSWD Risks"
    - If account is compromised, attacker gets instant root
    - No audit trail verification of who ran command
    - Accidental privilege escalation easier

    Only use NOPASSWD for:
    - Automated systems (CI/CD pipelines)
    - Specific, low-risk commands
    - Systems with other authentication (SSH keys + MFA)

### Restrict Commands

Grant only necessary commands:

```sudoers
# Instead of this (too broad):
developer ALL=(ALL) ALL

# Use this (specific commands):
developer ALL=(root) /usr/bin/systemctl restart myapp, \
                     /usr/bin/journalctl -u myapp
```

### Use Command Arguments

Restrict command arguments:

```sudoers
# Only allow restarting specific service
webadmin ALL=(root) /usr/bin/systemctl restart nginx

# Allow viewing but not editing
auditor ALL=(root) /usr/bin/cat /var/log/auth.log

# Allow specific mount point only
backup ALL=(root) /usr/bin/mount /dev/sdb1 /mnt/backup
```

### Prevent Shell Escape

Some commands can spawn shells. Restrict or avoid:

```sudoers
# DANGEROUS: vim can spawn shell with :!bash
admin ALL=(root) /usr/bin/vim

# SAFER: Use sudoedit for file editing
admin ALL=(root) sudoedit /etc/nginx/nginx.conf

# Or use restricted editor
Defaults editor=/usr/bin/rvim
```

Commands with shell escape potential:

| Command | Shell Escape |
|---------|--------------|
| vim/vi | `:!bash` or `:shell` |
| less | `!bash` |
| man | `!bash` |
| ftp | `!bash` |
| more | `!bash` |

### Use Aliases

Aliases make rules more readable and maintainable:

```sudoers
# Command aliases
Cmnd_Alias SERVICES = /usr/bin/systemctl start *, \
                      /usr/bin/systemctl stop *, \
                      /usr/bin/systemctl restart *

Cmnd_Alias LOGS = /usr/bin/journalctl, \
                  /usr/bin/tail -f /var/log/*

Cmnd_Alias PACKAGES = /usr/bin/apt update, \
                      /usr/bin/apt upgrade

# User aliases
User_Alias ADMINS = admin1, admin2, admin3
User_Alias DEVELOPERS = dev1, dev2, dev3

# Host aliases
Host_Alias WEBSERVERS = web1, web2, web3

# Apply rules
ADMINS ALL=(ALL) ALL
DEVELOPERS WEBSERVERS=(root) SERVICES, LOGS
```

## Default Options

### Useful Defaults

```sudoers
# Require password after 5 minutes of inactivity
Defaults timestamp_timeout=5

# Show asterisks when typing password
Defaults pwfeedback

# Require password for each terminal session
Defaults timestamp_type=tty

# Log to specific file
Defaults logfile=/var/log/sudo.log

# Log input/output (careful: may capture sensitive data)
Defaults log_input, log_output

# Require password for sudo -l
Defaults listpw=always

# Mail root when unauthorized sudo attempt
Defaults mail_badpass

# Set secure path
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Prevent environment variable injection
Defaults env_reset
Defaults env_check="COLORTERM DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS"
Defaults env_keep="EDITOR VISUAL"

# Lecture user on first use
Defaults lecture=once
```

### Security-Focused Defaults

```sudoers
# Require tty (prevents some automated attacks)
Defaults requiretty

# Don't preserve user environment (security)
Defaults always_set_home
Defaults set_home

# Limit authentication attempts
Defaults passwd_tries=3

# Lock out after failed attempts
Defaults insults
```

## Common sudo Commands

### For Users

```bash
# Run command as root
sudo command

# Run as different user
sudo -u www-data command

# Run with login shell
sudo -i

# Run shell as root
sudo -s

# List user's sudo permissions
sudo -l

# Edit file with sudo (safer than sudo vim)
sudoedit /etc/nginx/nginx.conf

# Extend sudo timeout
sudo -v

# Invalidate sudo timestamp (require password again)
sudo -k
```

### For Administrators

```bash
# Check sudoers syntax
sudo visudo -c

# Edit sudoers.d file safely
sudo visudo -f /etc/sudoers.d/custom

# Check specific user's permissions
sudo -l -U username

# Run command and preserve environment
sudo -E command
```

## Auditing sudo Usage

### Enable Logging

Add to sudoers:

```sudoers
Defaults logfile=/var/log/sudo.log
Defaults log_input, log_output
Defaults iolog_dir=/var/log/sudo-io
```

### View sudo Logs

```bash
# Traditional log
sudo tail -f /var/log/sudo.log

# Systemd journal
sudo journalctl -t sudo

# Auth log (includes sudo failures)
sudo tail -f /var/log/auth.log | grep sudo

# Replay I/O log
sudo sudoreplay -l
sudo sudoreplay <session_id>
```

### What to Monitor

| Event | Indicates |
|-------|-----------|
| Failed authentication | Wrong password or unauthorized user |
| NOPASSWD usage | Automated or misconfigured access |
| Unusual commands | Potential compromise |
| New users using sudo | Review authorization |

## Troubleshooting

### Common Issues

**"user is not in the sudoers file":**

```bash
# As root, add user to sudo group
usermod -aG sudo username
```

**"syntax error" after editing sudoers:**

```bash
# Boot to recovery mode
# Mount root filesystem read-write
mount -o remount,rw /
# Fix sudoers
visudo
```

**sudo asking for root password instead of user's:**

```bash
# Check targetpw setting
sudo grep -r "targetpw" /etc/sudoers*
# Remove or comment out: Defaults targetpw
```

**"sudo: command not found":**

```bash
# Use full path
/usr/bin/sudo command

# Or fix PATH
export PATH=$PATH:/usr/bin:/usr/sbin
```

### Verify Configuration

```bash
# Check syntax of all sudoers files
sudo visudo -c

# Test specific user's access
sudo -l -U testuser

# Verify a specific command
sudo -l -U testuser /usr/bin/systemctl restart nginx
```

## Example Configurations

### Web Server Administrator

```sudoers
# /etc/sudoers.d/webadmin
Cmnd_Alias WEB_SERVICES = /usr/bin/systemctl start nginx, \
                          /usr/bin/systemctl stop nginx, \
                          /usr/bin/systemctl restart nginx, \
                          /usr/bin/systemctl reload nginx

Cmnd_Alias WEB_CONFIG = /usr/bin/nginx -t, \
                        /usr/bin/certbot

webadmin ALL=(root) WEB_SERVICES, WEB_CONFIG
webadmin ALL=(root) sudoedit /etc/nginx/sites-available/*
```

### Database Administrator

```sudoers
# /etc/sudoers.d/dbadmin
Cmnd_Alias DB_SERVICES = /usr/bin/systemctl * postgresql, \
                         /usr/bin/systemctl * mysql

Cmnd_Alias DB_BACKUP = /usr/bin/pg_dump, \
                       /usr/bin/mysqldump

dbadmin ALL=(root) DB_SERVICES
dbadmin ALL=(postgres) ALL
dbadmin ALL=(root) DB_BACKUP
```

### CI/CD Pipeline

```sudoers
# /etc/sudoers.d/deployment
Cmnd_Alias DEPLOY = /usr/bin/systemctl restart myapp, \
                    /usr/bin/docker-compose -f /opt/myapp/docker-compose.yml *

# NOPASSWD acceptable for automated systems with other controls
deployer ALL=(root) NOPASSWD: DEPLOY
```

## Next Steps

Continue to [PAM Configuration](pam.md) to configure authentication modules and password policies.
