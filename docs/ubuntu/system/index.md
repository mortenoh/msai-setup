# System Configuration Overview

This section covers fundamental system configuration for Ubuntu Server 24.04 LTS with a focus on security and manageability.

## Core Concepts

A well-configured system follows the **principle of least privilege**: users and processes should have only the minimum permissions necessary to perform their tasks.

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    User Applications                         │
├─────────────────────────────────────────────────────────────┤
│              User Accounts & Groups                          │
│         (Who can access what resources)                      │
├─────────────────────────────────────────────────────────────┤
│              sudo & PAM Configuration                        │
│         (How privileges are escalated)                       │
├─────────────────────────────────────────────────────────────┤
│              systemd Service Management                      │
│         (How services run and are isolated)                  │
├─────────────────────────────────────────────────────────────┤
│              Kernel & Hardware                               │
└─────────────────────────────────────────────────────────────┘
```

## Section Contents

| Page | Description |
|------|-------------|
| [Users & Groups](users-groups.md) | User account management, groups, home directories |
| [sudo Configuration](sudo-configuration.md) | Privilege escalation, sudoers best practices |
| [PAM](pam.md) | Pluggable Authentication Modules, password policies |
| [systemd](systemd.md) | Service management and unit configuration |
| [Time Sync](time-sync.md) | NTP/chrony configuration for accurate time |

## Key Topics

### User Management

- Creating and managing user accounts
- Group-based access control
- Home directory security
- Shell restrictions

### Privilege Escalation

- sudo configuration
- Avoiding NOPASSWD misuse
- Using sudoers.d for modular configuration
- Auditing privilege use

### Authentication Security

- PAM module configuration
- Password complexity requirements
- Account lockout policies
- Failed login handling

### Service Management

- systemd unit files
- Service hardening options
- Resource limits
- Dependency management

### Time Synchronization

- Why accurate time matters for security
- chrony vs systemd-timesyncd
- NTP server configuration
- Time-based authentication

## Quick Reference

### Essential Commands

```bash
# User management
useradd -m -s /bin/bash username     # Create user
usermod -aG sudo username            # Add to sudo group
passwd username                      # Set password
userdel -r username                  # Delete user and home

# Group management
groupadd groupname                   # Create group
gpasswd -a user groupname            # Add user to group
groups username                      # List user's groups

# sudo
sudo -l                              # List sudo permissions
sudo -u user command                 # Run as different user
visudo                               # Edit sudoers safely

# systemd
systemctl status service             # Service status
systemctl enable --now service       # Enable and start
systemctl cat service                # View unit file
journalctl -u service                # View service logs

# Time
timedatectl                          # Time/timezone status
chronyc tracking                     # NTP sync status
```

## Configuration Files

| File | Purpose |
|------|---------|
| `/etc/passwd` | User account information |
| `/etc/shadow` | Encrypted passwords |
| `/etc/group` | Group definitions |
| `/etc/sudoers` | sudo configuration |
| `/etc/sudoers.d/` | Modular sudo rules |
| `/etc/pam.d/` | PAM configuration |
| `/etc/security/` | Security limits and policies |
| `/etc/systemd/system/` | Custom service units |
| `/etc/chrony/chrony.conf` | NTP configuration |

## Best Practices Summary

### User Accounts

| Practice | Reason |
|----------|--------|
| Unique accounts per person | Accountability, audit trail |
| No shared passwords | Individual responsibility |
| Disable unused accounts | Reduce attack surface |
| Regular access reviews | Remove stale permissions |

### Privilege Management

| Practice | Reason |
|----------|--------|
| Avoid NOPASSWD | Maintains authentication barrier |
| Use sudo groups | Easier management than individual rules |
| Restrict commands | Only allow necessary operations |
| Log all sudo use | Audit trail |

### Service Hardening

| Practice | Reason |
|----------|--------|
| Run as non-root | Limit damage from compromise |
| Use systemd sandboxing | Process isolation |
| Disable unnecessary services | Reduce attack surface |
| Set resource limits | Prevent DoS |

## Next Steps

Start with [Users & Groups](users-groups.md) to establish proper account management, then proceed through each section to build a hardened system configuration.
