# Troubleshooting Overview

This section covers diagnosing and resolving common issues on Ubuntu Server 24.04 LTS.

## Troubleshooting Methodology

### Systematic Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    Problem Reported                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    1. Gather Information                     │
│         What changed? When did it start? What's affected?   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. Check Logs                             │
│           journalctl, /var/log/, dmesg                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. Verify Basics                          │
│           Service status, disk space, memory, network        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. Isolate the Issue                      │
│           Narrow down: hardware, software, config, network   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    5. Test Solutions                         │
│           Start with least invasive, document changes        │
└─────────────────────────────────────────────────────────────┘
```

## Section Contents

| Page | Description |
|------|-------------|
| [Boot Issues](boot-issues.md) | Boot failures, GRUB, recovery mode |
| [Network Issues](network-issues.md) | Connectivity, DNS, firewall problems |
| [Security Incidents](security-incidents.md) | Incident response basics |

## Quick Diagnostics

### System Health Check

```bash
#!/bin/bash
echo "=== System Health Check ==="

echo -e "\n--- Uptime & Load ---"
uptime

echo -e "\n--- Memory ---"
free -h

echo -e "\n--- Disk Usage ---"
df -h | grep -v tmpfs

echo -e "\n--- Failed Services ---"
systemctl --failed

echo -e "\n--- Recent Errors ---"
sudo journalctl -p err --since "1 hour ago" --no-pager | head -20

echo -e "\n--- Top Processes ---"
ps aux --sort=-%mem | head -10

echo -e "\n--- Network Status ---"
ip addr show | grep -E "^[0-9]|inet "

echo -e "\n--- Listening Ports ---"
sudo ss -tlnp | head -10
```

### Service Quick Check

```bash
# Check specific service
systemctl status service-name

# Service logs
sudo journalctl -u service-name --since "30 minutes ago"

# Service dependencies
systemctl list-dependencies service-name
```

## Common Log Locations

| Log | Location | Contents |
|-----|----------|----------|
| System | /var/log/syslog | General system messages |
| Auth | /var/log/auth.log | Authentication events |
| Kernel | /var/log/kern.log | Kernel messages |
| Boot | /var/log/boot.log | Boot messages |
| APT | /var/log/apt/history.log | Package changes |
| Journal | journalctl | Structured logs |

### Quick Log Searches

```bash
# Recent errors
sudo journalctl -p err --since today

# Specific service
sudo journalctl -u nginx -n 100

# Follow logs
sudo journalctl -f

# Kernel messages
dmesg | tail -50
sudo journalctl -k
```

## Essential Commands

### System Information

```bash
# System version
lsb_release -a
cat /etc/os-release

# Kernel
uname -a

# Hardware
lscpu
lsmem
lspci
lsblk
```

### Process Information

```bash
# All processes
ps aux

# Process tree
pstree -p

# Top processes by resource
top
htop

# Specific process
ps aux | grep nginx
pgrep -a nginx
```

### Resource Usage

```bash
# Memory
free -h
vmstat 1 5

# Disk
df -h
du -sh /var/log/*
iostat -x 1 5

# Network
ss -s
ss -tlnp
iftop  # requires install
```

## Common Issues Quick Fixes

### Service Won't Start

```bash
# Check status
systemctl status service

# Check logs
sudo journalctl -u service -n 50

# Check config syntax (service-specific)
nginx -t
apache2ctl configtest

# Check dependencies
systemctl list-dependencies service

# Try manual start
sudo /usr/sbin/service-binary --foreground
```

### Out of Disk Space

```bash
# Find large files
sudo du -ah / 2>/dev/null | sort -rh | head -20

# Clean APT cache
sudo apt clean

# Clean old kernels
sudo apt autoremove

# Clean journal
sudo journalctl --vacuum-size=500M

# Find large logs
sudo find /var/log -type f -size +100M
```

### High Memory Usage

```bash
# Check memory
free -h

# Top memory users
ps aux --sort=-%mem | head -10

# Check for memory leaks
cat /proc/meminfo

# Clear caches (safe)
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### High CPU Usage

```bash
# Top CPU users
top -o %CPU
ps aux --sort=-%cpu | head -10

# Check load average
uptime

# Check for runaway processes
ps aux | awk '$3 > 50 {print}'
```

### Can't SSH

```bash
# On console, check SSH service
systemctl status ssh

# Check if listening
ss -tlnp | grep 22

# Check firewall
sudo ufw status
sudo iptables -L -n | grep 22

# Check configuration
sudo sshd -t

# Check auth log
sudo tail -f /var/log/auth.log
```

## When to Escalate

### Hardware Issues

- Disk errors in dmesg
- Memory errors (MCE)
- Repeated crashes without software cause
- Hardware RAID alerts

### Data Loss

- Database corruption
- Filesystem errors
- Accidental deletion
- Encryption key loss

### Security Incidents

- Unauthorized access detected
- Malware found
- Data breach suspected
- Service compromise

## Best Practices

### Before Making Changes

1. **Document** - Note current state
2. **Backup** - Configuration and data
3. **Test** - In staging if possible
4. **Plan rollback** - Know how to undo
5. **Communicate** - Inform stakeholders

### During Troubleshooting

- Work methodically
- Change one thing at a time
- Document what you try
- Check logs after each change
- Don't assume

### After Resolution

- Document the fix
- Update runbooks
- Consider automation
- Review for prevention

## Quick Reference

### Essential Commands

```bash
# Logs
journalctl -f              # Follow
journalctl -u service      # By service
journalctl -p err          # Errors only
dmesg | tail               # Kernel

# Services
systemctl status service   # Status
systemctl restart service  # Restart
systemctl --failed         # Failed units

# Resources
free -h                    # Memory
df -h                      # Disk
top                        # CPU/memory
ss -tlnp                   # Listening

# Network
ip addr                    # IP addresses
ip route                   # Routes
ping host                  # Connectivity
curl -v url                # HTTP test
```

## Next Steps

Start with the specific troubleshooting section that matches your issue:

- [Boot Issues](boot-issues.md) - System won't boot or fails during boot
- [Network Issues](network-issues.md) - Network connectivity problems
- [Security Incidents](security-incidents.md) - Suspected compromise
