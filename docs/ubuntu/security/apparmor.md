# AppArmor

AppArmor is Ubuntu's mandatory access control (MAC) system. It confines programs to a limited set of resources, reducing the damage from compromised applications.

## Understanding AppArmor

### What AppArmor Does

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Request                       │
│              (e.g., read /etc/passwd)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AppArmor Policy Check                     │
│                                                              │
│  Profile: /usr/sbin/nginx                                   │
│  Rule: /etc/passwd r,    ← Read allowed                     │
│  Rule: /etc/shadow deny, ← Explicitly denied                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
            ▼                                   ▼
      ┌─────────┐                        ┌─────────┐
      │ Allowed │                        │ Denied  │
      │ Access  │                        │ + Log   │
      └─────────┘                        └─────────┘
```

### AppArmor vs SELinux

| Feature | AppArmor | SELinux |
|---------|----------|---------|
| Default in | Ubuntu, SUSE | RHEL, Fedora |
| Policy style | Path-based | Label-based |
| Complexity | Lower | Higher |
| Learning curve | Easier | Steeper |
| Flexibility | Good | Very high |

### Profile Modes

| Mode | Behavior |
|------|----------|
| **Enforce** | Policy enforced, violations blocked and logged |
| **Complain** | Policy not enforced, violations only logged |
| **Disabled** | Profile not loaded |

## Check AppArmor Status

### System Status

```bash
# Check if AppArmor is enabled
sudo aa-status

# Or shorter
sudo apparmor_status

# Output shows:
# - Number of loaded profiles
# - Profiles in enforce/complain mode
# - Processes with profiles
```

### Service Status

```bash
# AppArmor service
sudo systemctl status apparmor

# Verify kernel support
cat /sys/module/apparmor/parameters/enabled
# Should output: Y
```

## Managing Profiles

### Profile Locations

| Location | Purpose |
|----------|---------|
| `/etc/apparmor.d/` | Main profiles |
| `/etc/apparmor.d/local/` | Local customizations |
| `/etc/apparmor.d/disable/` | Disabled profiles (symlinks) |
| `/etc/apparmor.d/abstractions/` | Common rule sets |
| `/etc/apparmor.d/tunables/` | Variables |

### List Profiles

```bash
# All profiles
ls /etc/apparmor.d/

# Profiles by status
sudo aa-status --enabled
sudo aa-status --profiled
```

### Profile Operations

```bash
# Reload all profiles
sudo systemctl reload apparmor

# Reload specific profile
sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx

# Set profile to enforce mode
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx

# Set profile to complain mode
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx

# Disable profile
sudo aa-disable /etc/apparmor.d/usr.sbin.nginx

# Remove profile from kernel
sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.nginx
```

## Profile Syntax

### Basic Structure

```
# /etc/apparmor.d/usr.bin.example

#include <tunables/global>

profile example /usr/bin/example {
  #include <abstractions/base>

  # Allow reading own binary
  /usr/bin/example mr,

  # Allow reading config
  /etc/example.conf r,

  # Allow writing logs
  /var/log/example.log w,

  # Deny access to sensitive files
  deny /etc/shadow r,
}
```

### Permission Flags

| Flag | Permission |
|------|------------|
| `r` | Read |
| `w` | Write |
| `a` | Append |
| `x` | Execute (inherit profile) |
| `ix` | Execute (inherit profile) |
| `px` | Execute (transition to profile) |
| `Px` | Execute (transition or fail) |
| `ux` | Execute (unconfined) |
| `cx` | Execute (child profile) |
| `m` | Memory map executable |
| `k` | File locking |
| `l` | Link |

### Common Patterns

```
# Exact path
/path/to/file r,

# Wildcard - single directory component
/path/to/dir/* r,

# Recursive - all subdirectories
/path/to/dir/** r,

# Pattern matching
/var/log/*.log w,
/home/*/.config r,

# Owner condition
owner /home/*/.ssh/* r,

# Deny explicitly
deny /etc/shadow r,
```

### Abstractions

Abstractions provide common rule sets:

```
# Include common patterns
#include <abstractions/base>           # Basic system access
#include <abstractions/nameservice>    # DNS, passwd lookups
#include <abstractions/openssl>        # SSL/TLS libraries
#include <abstractions/ssl_certs>      # Certificate files
#include <abstractions/python>         # Python interpreter
```

Available in `/etc/apparmor.d/abstractions/`.

## Creating Custom Profiles

### Generate Profile with aa-genprof

```bash
# Install utilities
sudo apt install apparmor-utils

# Generate profile interactively
sudo aa-genprof /usr/bin/myapp
```

Then:
1. Run myapp in another terminal
2. Exercise all functionality
3. Return to aa-genprof and press 'S' to scan logs
4. Accept/deny actions as prompted
5. Press 'F' to finish

### Generate Profile with aa-autodep

```bash
# Create basic profile
sudo aa-autodep /usr/bin/myapp

# Profile created at /etc/apparmor.d/usr.bin.myapp
# Start in complain mode
sudo aa-complain /etc/apparmor.d/usr.bin.myapp

# Run application, then check logs
sudo aa-logprof
```

### Manual Profile Creation

```bash
# /etc/apparmor.d/usr.local.bin.myapp

#include <tunables/global>

profile myapp /usr/local/bin/myapp {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Binary
  /usr/local/bin/myapp mr,

  # Libraries
  /usr/lib/** mr,
  /lib/x86_64-linux-gnu/** mr,

  # Configuration
  /etc/myapp/ r,
  /etc/myapp/** r,

  # Data
  /var/lib/myapp/ rw,
  /var/lib/myapp/** rw,

  # Logs
  /var/log/myapp/ rw,
  /var/log/myapp/** w,

  # PID file
  /var/run/myapp.pid rw,

  # Network
  network inet stream,
  network inet dgram,

  # Deny sensitive areas
  deny /etc/shadow r,
  deny /root/** rw,
}
```

Load profile:

```bash
sudo apparmor_parser -r /etc/apparmor.d/usr.local.bin.myapp
```

## Network Rules

### Network Access Control

```
# Allow specific network types
network inet stream,     # TCP over IPv4
network inet dgram,      # UDP over IPv4
network inet6 stream,    # TCP over IPv6
network unix stream,     # Unix sockets

# Deny all network
deny network,
```

## Capability Rules

### Linux Capabilities

```
# Allow specific capabilities
capability net_bind_service,   # Bind to ports < 1024
capability chown,              # Change file ownership
capability dac_override,       # Bypass permission checks
capability setuid,             # Set UID
capability setgid,             # Set GID

# Deny all capabilities
deny capability,
```

## Debugging and Troubleshooting

### View Denials

```bash
# Real-time denials
sudo dmesg -w | grep apparmor

# From audit log
sudo grep apparmor /var/log/audit/audit.log

# From syslog
sudo grep apparmor /var/log/syslog

# Parse and display denials
sudo aa-notify -s 1 -v
```

### Analyze Denials

```bash
# Interactive profile update
sudo aa-logprof

# This reads recent denials and offers to:
# - Add rules to profiles
# - Set permissions
# - Update abstractions
```

### Common Issues

**Application fails with "Permission denied":**

```bash
# Check if confined
sudo aa-status | grep <process>

# Look for denials
sudo dmesg | grep -i apparmor | grep DENIED

# Temporarily set to complain mode
sudo aa-complain /etc/apparmor.d/profile

# Run application, then analyze
sudo aa-logprof
```

**Profile not loading:**

```bash
# Check syntax
sudo apparmor_parser -p /etc/apparmor.d/profile

# View errors
sudo apparmor_parser -r /etc/apparmor.d/profile 2>&1
```

## Example Profiles

### Nginx Web Server

```
# /etc/apparmor.d/usr.sbin.nginx

#include <tunables/global>

profile nginx /usr/sbin/nginx {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/openssl>

  # Binary
  /usr/sbin/nginx mr,

  # Libraries
  /usr/lib/nginx/modules/** mr,

  # Configuration
  /etc/nginx/ r,
  /etc/nginx/** r,

  # SSL certificates
  /etc/ssl/certs/** r,
  /etc/ssl/private/** r,

  # Web content (adjust path as needed)
  /var/www/** r,

  # Logs
  /var/log/nginx/ rw,
  /var/log/nginx/** w,

  # PID and lock
  /run/nginx.pid rw,
  /var/lib/nginx/ rw,
  /var/lib/nginx/** rw,

  # Temp files
  /var/cache/nginx/ rw,
  /var/cache/nginx/** rw,

  # Network
  capability net_bind_service,
  network inet stream,
  network inet6 stream,

  # Worker processes
  capability setuid,
  capability setgid,
  capability dac_override,
}
```

### Custom Application

```
# /etc/apparmor.d/local/usr.local.myapp

#include <tunables/global>

profile myapp /usr/local/bin/myapp flags=(attach_disconnected) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Own binary
  /usr/local/bin/myapp mr,

  # Config
  /etc/myapp.conf r,

  # Data directory
  owner /var/lib/myapp/ rw,
  owner /var/lib/myapp/** rw,

  # Logs
  /var/log/myapp.log w,

  # Temporary files
  /tmp/myapp.* rw,

  # Network (restrict to localhost)
  network inet stream,
  network inet dgram,

  # Deny sensitive
  deny /etc/shadow r,
  deny /etc/gshadow r,
  deny /root/** rw,
  deny /home/** rw,
}
```

## Local Customizations

### Override Without Modifying Package Profiles

```bash
# Create local override
sudo nano /etc/apparmor.d/local/usr.sbin.nginx
```

```
# Local additions for nginx
# Include from main profile with:
# #include <local/usr.sbin.nginx>

# Allow additional content directory
/srv/www/** r,
```

Add include to main profile:

```
profile nginx /usr/sbin/nginx {
  ...
  #include <local/usr.sbin.nginx>
}
```

## Ubuntu Default Profiles

Ubuntu includes profiles for many applications:

```bash
# View installed profiles
dpkg -L apparmor-profiles
dpkg -L apparmor-profiles-extra

# Install additional profiles
sudo apt install apparmor-profiles apparmor-profiles-extra
```

Common default profiles:

| Application | Profile Status |
|-------------|----------------|
| Firefox | Shipped but not enabled |
| LibreOffice | Shipped but not enabled |
| cups-browsed | Enabled |
| man | Enabled |
| tcpdump | Enabled |

## Best Practices

### Profile Development

1. Start in complain mode
2. Exercise all application functionality
3. Use aa-logprof to add necessary rules
4. Review and minimize permissions
5. Test in enforce mode
6. Monitor for denials

### Security Guidelines

| Practice | Reason |
|----------|--------|
| Use abstractions | Consistent, maintained rule sets |
| Minimize permissions | Only allow what's needed |
| Use owner keyword | Restrict to file owner |
| Deny sensitive explicitly | Document security intentions |
| Audit deny rules | Log denied access attempts |

### Maintenance

```bash
# After package updates, reload profiles
sudo systemctl reload apparmor

# Periodically check for denials
sudo aa-notify -s 7 -v

# Review and update profiles
sudo aa-logprof
```

## Quick Reference

### Commands

```bash
# Status
sudo aa-status
sudo apparmor_status

# Profile management
sudo aa-enforce /path/to/profile
sudo aa-complain /path/to/profile
sudo aa-disable /path/to/profile

# Profile generation
sudo aa-genprof /path/to/binary
sudo aa-logprof

# Reload
sudo systemctl reload apparmor
sudo apparmor_parser -r /path/to/profile

# Debugging
sudo dmesg | grep apparmor
sudo aa-notify -s 1 -v
```

## Next Steps

Continue to [Fail2ban](fail2ban.md) to set up intrusion prevention.
