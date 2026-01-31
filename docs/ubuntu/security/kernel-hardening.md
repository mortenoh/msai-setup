# Kernel Hardening

The Linux kernel provides many security features that are not enabled by default. Proper kernel hardening reduces the attack surface and mitigates exploitation attempts.

## Understanding sysctl

### What sysctl Controls

sysctl modifies kernel parameters at runtime:

```
┌─────────────────────────────────────────────────────────────┐
│                    Kernel Space                              │
├─────────────────────────────────────────────────────────────┤
│  /proc/sys/kernel/  │  /proc/sys/net/  │  /proc/sys/fs/    │
│  • Core kernel      │  • Networking    │  • Filesystem     │
│  • Security         │  • IPv4/IPv6     │  • File handles   │
│  • Randomization    │  • Protocols     │  • Quotas         │
└─────────────────────────────────────────────────────────────┘
```

### sysctl Basics

```bash
# View all parameters
sysctl -a

# View specific parameter
sysctl kernel.randomize_va_space

# Set parameter temporarily
sudo sysctl kernel.randomize_va_space=2

# Apply from config files
sudo sysctl --system
```

### Configuration Files

| Location | Priority | Purpose |
|----------|----------|---------|
| `/etc/sysctl.conf` | Lowest | Main config (legacy) |
| `/etc/sysctl.d/*.conf` | By filename | Modular configs |
| `/usr/lib/sysctl.d/*.conf` | Package defaults | Vendor settings |
| `/run/sysctl.d/*.conf` | Runtime | Temporary overrides |

Create custom hardening in `/etc/sysctl.d/99-security.conf`:

```bash
sudo nano /etc/sysctl.d/99-security.conf
```

## Memory Protection

### Address Space Layout Randomization (ASLR)

ASLR randomizes memory locations to make exploitation harder:

```ini
# Full ASLR (recommended)
kernel.randomize_va_space = 2
```

| Value | Effect |
|-------|--------|
| 0 | Disabled |
| 1 | Stack, VDSO, shared libraries randomized |
| 2 | Full randomization (includes heap) |

### Restrict Kernel Pointer Exposure

Prevent kernel address leaks:

```ini
# Hide kernel pointers from non-privileged users
kernel.kptr_restrict = 2

# Restrict dmesg to privileged users
kernel.dmesg_restrict = 1

# Restrict perf events
kernel.perf_event_paranoid = 3
```

### Exec-Shield Protection

```ini
# Restrict mmap in lower addresses
vm.mmap_min_addr = 65536

# Randomize mmap base
vm.mmap_rnd_bits = 32
vm.mmap_rnd_compat_bits = 16
```

### Core Dump Restrictions

```ini
# Disable core dumps for SUID programs
fs.suid_dumpable = 0
```

## Network Hardening

### IPv4 Security

```ini
# Disable IP forwarding (unless router/firewall)
net.ipv4.ip_forward = 0

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# Don't send ICMP redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Enable reverse path filtering (anti-spoofing)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log martian packets (impossible source addresses)
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Ignore ICMP echo to broadcast
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Enable TCP SYN cookies (SYN flood protection)
net.ipv4.tcp_syncookies = 1

# TCP timestamps (can leak system uptime, but helps with TCP performance)
net.ipv4.tcp_timestamps = 1
```

### IPv6 Security

```ini
# Disable IPv6 if not used
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# If IPv6 is used, harden it:
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
```

### TCP Hardening

```ini
# Enable TCP RFC 1337
net.ipv4.tcp_rfc1337 = 1

# Reduce TCP FIN timeout (faster cleanup)
net.ipv4.tcp_fin_timeout = 30

# Reduce keepalive time
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
```

## Filesystem Security

### Protect Hard/Soft Links

Prevent symlink/hardlink attacks:

```ini
# Restrict hardlink creation
fs.protected_hardlinks = 1

# Restrict symlink following
fs.protected_symlinks = 1

# Protect FIFO files
fs.protected_fifos = 2

# Protect regular files
fs.protected_regular = 2
```

### File Handle Limits

```ini
# Maximum open file handles
fs.file-max = 65535
```

## Process Security

### ptrace Restrictions

Limit process tracing (prevents some debugging attacks):

```ini
# Restrict ptrace
kernel.yama.ptrace_scope = 2
```

| Value | Effect |
|-------|--------|
| 0 | Classic ptrace (any process can trace) |
| 1 | Restricted (only parent can trace) |
| 2 | Admin-only (CAP_SYS_PTRACE required) |
| 3 | No ptrace (disabled entirely) |

### SysRq Key

Restrict Magic SysRq key (physical access issue):

```ini
# Disable SysRq (or restrict to specific functions)
kernel.sysrq = 0
```

| Value | Functions Allowed |
|-------|-------------------|
| 0 | Disabled |
| 1 | All functions |
| 176 | Sync + reboot only |

### Kernel Module Loading

```ini
# Restrict module loading (careful - may break hardware support)
# kernel.modules_disabled = 1  # Permanent until reboot
```

## Complete Hardening Configuration

### /etc/sysctl.d/99-security.conf

```ini
# Ubuntu 24.04 Kernel Hardening
# Apply with: sudo sysctl --system

#########################################
# Memory Protection
#########################################

# Enable full ASLR
kernel.randomize_va_space = 2

# Restrict kernel pointer exposure
kernel.kptr_restrict = 2

# Restrict dmesg access
kernel.dmesg_restrict = 1

# Restrict perf events
kernel.perf_event_paranoid = 3

# Minimum mmap address
vm.mmap_min_addr = 65536

# Disable core dumps for SUID
fs.suid_dumpable = 0

#########################################
# Network Security - IPv4
#########################################

# Disable IP forwarding (enable for routers/containers)
net.ipv4.ip_forward = 0

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Enable reverse path filtering
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Ignore broadcast ICMP
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Enable SYN cookies
net.ipv4.tcp_syncookies = 1

# Enable TCP RFC 1337
net.ipv4.tcp_rfc1337 = 1

#########################################
# Network Security - IPv6
#########################################

# If not using IPv6, disable it:
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1

# If using IPv6, harden:
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

#########################################
# Filesystem Protection
#########################################

# Protect hardlinks
fs.protected_hardlinks = 1

# Protect symlinks
fs.protected_symlinks = 1

# Protect FIFOs
fs.protected_fifos = 2

# Protect regular files
fs.protected_regular = 2

#########################################
# Process Security
#########################################

# Restrict ptrace
kernel.yama.ptrace_scope = 2

# Disable SysRq
kernel.sysrq = 0
```

## Apply Configuration

```bash
# Apply all sysctl settings
sudo sysctl --system

# Verify settings
sysctl kernel.randomize_va_space
sysctl net.ipv4.tcp_syncookies
```

## Boot-Time Kernel Parameters

### GRUB Configuration

Some security features require boot parameters.

Edit `/etc/default/grub`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX="init_on_alloc=1 init_on_free=1 page_alloc.shuffle=1 pti=on vsyscall=none"
```

| Parameter | Purpose |
|-----------|---------|
| init_on_alloc=1 | Zero memory on allocation |
| init_on_free=1 | Zero memory on free |
| page_alloc.shuffle=1 | Randomize page allocator freelist |
| pti=on | Page Table Isolation (Meltdown mitigation) |
| vsyscall=none | Disable vsyscall mapping |
| slab_nomerge | Prevent slab merging (security) |
| slub_debug=FZP | SLUB allocator debugging |

Apply:

```bash
sudo update-grub
sudo reboot
```

### Verify Boot Parameters

```bash
cat /proc/cmdline
```

## Kernel Lockdown

Ubuntu supports kernel lockdown mode for high-security environments:

```bash
# Check current status
cat /sys/kernel/security/lockdown

# Enable via boot parameter (in GRUB)
# GRUB_CMDLINE_LINUX="lockdown=integrity"
# or
# GRUB_CMDLINE_LINUX="lockdown=confidentiality"
```

| Mode | Restrictions |
|------|--------------|
| none | No restrictions |
| integrity | Prevents unsigned kernel modules, /dev/mem access |
| confidentiality | Integrity + restricts features that could leak kernel data |

## Verify Hardening

### Check Current Settings

```bash
# Create verification script
cat << 'EOF' > check-hardening.sh
#!/bin/bash
echo "=== Kernel Hardening Status ==="

echo -e "\n--- Memory Protection ---"
sysctl kernel.randomize_va_space
sysctl kernel.kptr_restrict
sysctl kernel.dmesg_restrict
sysctl fs.suid_dumpable

echo -e "\n--- Network (IPv4) ---"
sysctl net.ipv4.ip_forward
sysctl net.ipv4.tcp_syncookies
sysctl net.ipv4.conf.all.rp_filter
sysctl net.ipv4.conf.all.accept_redirects
sysctl net.ipv4.conf.all.log_martians

echo -e "\n--- Filesystem ---"
sysctl fs.protected_hardlinks
sysctl fs.protected_symlinks

echo -e "\n--- Process ---"
sysctl kernel.yama.ptrace_scope
sysctl kernel.sysrq

echo -e "\n--- Boot Parameters ---"
cat /proc/cmdline
EOF
chmod +x check-hardening.sh
./check-hardening.sh
```

### Security Score Tools

```bash
# Install and run Lynis
sudo apt install lynis
sudo lynis audit system
```

## Considerations for Specific Workloads

### Docker/Container Hosts

Enable IP forwarding:

```ini
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
```

### KVM/Virtualization Hosts

Enable IP forwarding:

```ini
net.ipv4.ip_forward = 1
```

May need to adjust ptrace for debugging:

```ini
kernel.yama.ptrace_scope = 1
```

### High-Performance Servers

Some hardening may impact performance:

```ini
# Consider less strict rp_filter for asymmetric routing
net.ipv4.conf.all.rp_filter = 2
```

## Troubleshooting

### Common Issues

**Network connectivity problems after hardening:**

```bash
# Check if IP forwarding is needed
cat /proc/sys/net/ipv4/ip_forward

# Check for blocked martians in logs
sudo dmesg | grep martian
```

**Application crashes after ptrace restrictions:**

```bash
# Temporarily allow ptrace for debugging
sudo sysctl kernel.yama.ptrace_scope=1
```

**Dmesg access denied:**

```bash
# Users can't run dmesg - expected with dmesg_restrict=1
# Use sudo dmesg instead
```

## Next Steps

Continue to [SSH Hardening](ssh-hardening.md) for securing remote access.
