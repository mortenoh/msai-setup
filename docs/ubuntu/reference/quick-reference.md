# Quick Reference

Command and configuration cheat sheet for Ubuntu Server 24.04 LTS administration.

## System Information

```bash
# Ubuntu version
lsb_release -a
cat /etc/os-release

# Kernel
uname -a
uname -r

# Hostname
hostname
hostnamectl

# Uptime
uptime

# Hardware
lscpu           # CPU
lsmem           # Memory
lsblk           # Block devices
lspci           # PCI devices
lsusb           # USB devices
dmidecode       # BIOS/hardware info
```

## User Management

```bash
# Add user
sudo adduser username
sudo useradd -m -s /bin/bash username

# Modify user
sudo usermod -aG sudo username    # Add to group
sudo usermod -L username          # Lock
sudo usermod -U username          # Unlock
sudo usermod -s /sbin/nologin username  # Disable shell

# Delete user
sudo userdel username
sudo userdel -r username          # With home dir

# Password
sudo passwd username
sudo passwd -e username           # Force change
sudo chage -l username            # Show expiry

# Groups
sudo groupadd groupname
sudo gpasswd -a user group
groups username
```

## Service Management

```bash
# Status
systemctl status service
systemctl is-active service
systemctl is-enabled service

# Control
sudo systemctl start service
sudo systemctl stop service
sudo systemctl restart service
sudo systemctl reload service

# Enable/disable
sudo systemctl enable service
sudo systemctl disable service
sudo systemctl enable --now service

# List
systemctl list-units --type=service
systemctl list-unit-files --type=service
systemctl --failed

# Logs
journalctl -u service
journalctl -u service -f           # Follow
journalctl -u service --since today
```

## Package Management

```bash
# Update
sudo apt update
sudo apt upgrade
sudo apt full-upgrade

# Install/remove
sudo apt install package
sudo apt remove package
sudo apt purge package             # With config
sudo apt autoremove                # Unused deps

# Search
apt search keyword
apt show package
apt list --installed
apt list --upgradable

# Hold
sudo apt-mark hold package
sudo apt-mark unhold package
apt-mark showhold
```

## Network

```bash
# Interface
ip link show
ip addr show
ip route show

# Configure (Netplan)
sudo nano /etc/netplan/00-config.yaml
sudo netplan try                   # Test (reverts)
sudo netplan apply

# DNS
resolvectl status
dig domain.com
nslookup domain.com

# Connections
ss -tlnp                          # Listening TCP
ss -ulnp                          # Listening UDP
ss -anp                           # All connections
ss -s                             # Summary

# Testing
ping host
traceroute host
curl -I http://host
```

## Firewall (UFW)

```bash
# Status
sudo ufw status
sudo ufw status verbose

# Enable/disable
sudo ufw enable
sudo ufw disable

# Rules
sudo ufw allow 22/tcp
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24
sudo ufw allow from 192.168.1.0/24 to any port 22
sudo ufw deny 80/tcp
sudo ufw delete allow 80/tcp

# Defaults
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

## Disk and Storage

```bash
# Disk usage
df -h
du -sh /path
du -h --max-depth=1 /var

# Block devices
lsblk
blkid

# Mount
mount
sudo mount /dev/sdb1 /mnt
sudo umount /mnt

# LVM
sudo pvs                          # Physical volumes
sudo vgs                          # Volume groups
sudo lvs                          # Logical volumes
sudo lvextend -L +10G /dev/vg/lv  # Extend
sudo resize2fs /dev/vg/lv         # Resize filesystem
```

## Logs

```bash
# journalctl
journalctl -f                     # Follow
journalctl -b                     # This boot
journalctl -b -1                  # Last boot
journalctl --since "1 hour ago"
journalctl -p err                 # Errors only
journalctl -u service             # By service
journalctl --disk-usage           # Size
journalctl --vacuum-size=500M     # Clean

# Traditional logs
tail -f /var/log/syslog
tail -f /var/log/auth.log
cat /var/log/apt/history.log
dmesg | tail
```

## Processes

```bash
# View
ps aux
ps auxf                           # Tree
top
htop

# Control
kill PID
kill -9 PID                       # Force
pkill processname
killall processname

# Background
command &
nohup command &
jobs
fg
bg
```

## File Operations

```bash
# Permissions
chmod 755 file
chmod u+x file
chmod -R 755 dir
chown user:group file
chown -R user:group dir

# Find
find /path -name "*.txt"
find /path -mtime -7              # Modified last 7 days
find /path -size +100M
find /path -type f -perm -4000    # SUID

# Archive
tar -czvf archive.tar.gz dir/
tar -xzvf archive.tar.gz
zip -r archive.zip dir/
unzip archive.zip
```

## SSH

```bash
# Connect
ssh user@host
ssh -p 2222 user@host
ssh -i keyfile user@host

# Key management
ssh-keygen -t ed25519
ssh-copy-id user@host
ssh-add keyfile

# Config test
sudo sshd -t

# Tunnel
ssh -L 8080:localhost:80 user@host   # Local
ssh -R 8080:localhost:80 user@host   # Remote
ssh -D 1080 user@host                # SOCKS
```

## Cron

```bash
# Edit crontab
crontab -e
sudo crontab -e
crontab -l

# Format: minute hour day month weekday command
# 0 2 * * * /script.sh            # 2 AM daily
# */5 * * * * /script.sh          # Every 5 min
# 0 0 * * 0 /script.sh            # Weekly

# System cron
ls /etc/cron.*
cat /etc/crontab
```

## systemd Timers

```bash
# List timers
systemctl list-timers

# Create timer (replace cron)
# /etc/systemd/system/mytask.service
# /etc/systemd/system/mytask.timer

# Enable
sudo systemctl enable --now mytask.timer
```

## Security

```bash
# Fail2ban
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo fail2ban-client set sshd banip IP
sudo fail2ban-client set sshd unbanip IP

# AppArmor
sudo aa-status
sudo aa-enforce /path/to/profile
sudo aa-complain /path/to/profile

# Audit
sudo auditctl -l                  # List rules
sudo ausearch -k keyname          # Search by key
sudo aureport --summary           # Summary

# Updates
sudo unattended-upgrade --dry-run
sudo unattended-upgrade
```

## Common Configuration Files

| File | Purpose |
|------|---------|
| /etc/hostname | System hostname |
| /etc/hosts | Host mappings |
| /etc/fstab | Filesystem mounts |
| /etc/netplan/*.yaml | Network config |
| /etc/ssh/sshd_config | SSH server |
| /etc/sudoers | sudo config |
| /etc/apt/sources.list | APT repositories |
| /etc/systemd/system/ | Custom units |
| /etc/ufw/ | Firewall config |
| /etc/fail2ban/jail.local | Fail2ban config |

## Useful Paths

| Path | Contents |
|------|----------|
| /var/log/ | Log files |
| /var/log/journal/ | systemd journal |
| /etc/ | Configuration |
| /home/ | User homes |
| /tmp/ | Temporary files |
| /var/www/ | Web content |
| /opt/ | Optional software |
| /usr/local/ | Local software |

## Keyboard Shortcuts (Console)

| Shortcut | Action |
|----------|--------|
| Ctrl+C | Cancel command |
| Ctrl+Z | Suspend process |
| Ctrl+D | Exit/logout |
| Ctrl+L | Clear screen |
| Ctrl+R | Search history |
| Ctrl+A | Start of line |
| Ctrl+E | End of line |
| Ctrl+U | Clear line |
| Ctrl+W | Delete word |
| Tab | Autocomplete |

## Tmux Quick Reference

```bash
# Sessions
tmux                              # Start
tmux new -s name                  # Named session
tmux ls                           # List
tmux attach -t name               # Attach
tmux kill-session -t name         # Kill

# Inside tmux (prefix = Ctrl+B)
Ctrl+B d                          # Detach
Ctrl+B c                          # New window
Ctrl+B n                          # Next window
Ctrl+B p                          # Previous window
Ctrl+B %                          # Split vertical
Ctrl+B "                          # Split horizontal
Ctrl+B arrow                      # Move between panes
```
