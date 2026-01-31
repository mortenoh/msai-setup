# PAM Configuration

Pluggable Authentication Modules (PAM) provide a flexible framework for authentication on Linux systems. Proper PAM configuration enforces password policies, account lockout, and access controls.

## PAM Fundamentals

### What PAM Does

PAM sits between applications and authentication methods:

```
┌─────────────────────────────────────────────────────────────┐
│             Applications (sshd, sudo, login)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        PAM Library                           │
│                    (libpam.so)                               │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      ┌──────────┐     ┌──────────┐     ┌──────────┐
      │pam_unix  │     │pam_ldap  │     │pam_google │
      │(local)   │     │(LDAP)    │     │(2FA)     │
      └──────────┘     └──────────┘     └──────────┘
```

### PAM Module Types

| Type | Purpose | Example |
|------|---------|---------|
| **auth** | Verify identity | Password check, 2FA |
| **account** | Access authorization | Account expiry, time restrictions |
| **password** | Password changes | Complexity requirements |
| **session** | Session setup/teardown | Mount home, set limits |

### Control Flags

| Flag | Behavior |
|------|----------|
| `required` | Must succeed, but continue checking other modules |
| `requisite` | Must succeed, fail immediately if not |
| `sufficient` | If succeeds, stop checking (unless required failed) |
| `optional` | Only matters if it's the only module |
| `include` | Include another PAM configuration |

## Configuration Files

### File Locations

```
/etc/pam.d/
├── common-auth          # Authentication
├── common-account       # Account management
├── common-password      # Password changes
├── common-session       # Session management
├── common-session-noninteractive
├── login                # Console login
├── sshd                 # SSH daemon
├── sudo                 # sudo command
└── su                   # su command
```

### Configuration Format

```
# type    control    module    [arguments]
auth      required   pam_unix.so nullok
account   required   pam_unix.so
```

## Password Policies

### Install Password Quality Module

```bash
sudo apt install libpam-pwquality
```

### Configure Password Complexity

Edit `/etc/security/pwquality.conf`:

```ini
# Minimum password length
minlen = 14

# Require at least one digit
dcredit = -1

# Require at least one uppercase
ucredit = -1

# Require at least one lowercase
lcredit = -1

# Require at least one special character
ocredit = -1

# Maximum consecutive same characters
maxrepeat = 3

# Maximum consecutive characters from same class
maxclassrepeat = 4

# Check for words from GECOS field
gecoscheck = 1

# Disallow usernames in passwords
usercheck = 1

# Dictionary check (requires cracklib-runtime)
dictcheck = 1

# Minimum difference from old password
difok = 5

# Number of recent passwords to remember
remember = 12

# Reject passwords containing dictionary words
enforcing = 1
```

### Enable in PAM

Verify `/etc/pam.d/common-password` includes:

```
password    requisite    pam_pwquality.so retry=3
password    [success=1 default=ignore]    pam_unix.so obscure use_authtok try_first_pass yescrypt remember=12
```

### Password Aging

Configure in `/etc/login.defs`:

```ini
# Maximum days before password must be changed
PASS_MAX_DAYS   90

# Minimum days between password changes
PASS_MIN_DAYS   7

# Days before expiry to warn user
PASS_WARN_AGE   14
```

Apply to existing users:

```bash
# Set for specific user
sudo chage -M 90 -m 7 -W 14 username

# View current settings
sudo chage -l username
```

## Account Lockout

### Install Faillock Module

Ubuntu 24.04 uses `pam_faillock` (replaced `pam_tally2`):

```bash
# Already included in Ubuntu 24.04
```

### Configure Lockout Policy

Create `/etc/security/faillock.conf`:

```ini
# Number of failed attempts before lockout
deny = 5

# Lockout duration in seconds (600 = 10 minutes)
unlock_time = 600

# Time window for counting failures (seconds)
fail_interval = 900

# Also lock root account
even_deny_root = true

# Lockout duration for root
root_unlock_time = 60

# Audit failed attempts
audit

# Silent mode (don't reveal account existence)
silent

# Directory for failure records
dir = /var/run/faillock
```

### Enable Faillock in PAM

Edit `/etc/pam.d/common-auth`:

```
# Add before pam_unix
auth    required    pam_faillock.so preauth
auth    [success=1 default=ignore]    pam_unix.so nullok
# Add after pam_unix
auth    [default=die]    pam_faillock.so authfail
auth    sufficient    pam_faillock.so authsucc
```

Edit `/etc/pam.d/common-account`:

```
account    required    pam_faillock.so
```

### Manage Locked Accounts

```bash
# View failed login attempts
sudo faillock --user username

# Reset failed count (unlock)
sudo faillock --user username --reset

# View all users with failed attempts
sudo faillock
```

## Access Time Restrictions

### Configure Time-Based Access

Edit `/etc/security/time.conf`:

```
# Format: services;ttys;users;times

# Allow login only during business hours
login;*;!admin;Al0800-1800

# Restrict specific user
sshd;*;contractor;Wk0900-1700

# Allow admin anytime
*;*;admin;Al0000-2400
```

### Enable Time Module

Add to `/etc/pam.d/common-auth`:

```
account    required    pam_time.so
```

### Time Format

| Code | Meaning |
|------|---------|
| Su | Sunday |
| Mo | Monday |
| Tu | Tuesday |
| We | Wednesday |
| Th | Thursday |
| Fr | Friday |
| Sa | Saturday |
| Wk | Weekdays |
| Wd | Weekend |
| Al | All days |

## Resource Limits

### Configure Limits

Edit `/etc/security/limits.conf`:

```ini
# Limit maximum processes
*               soft    nproc           1024
*               hard    nproc           2048

# Limit open files
*               soft    nofile          4096
*               hard    nofile          65535

# Limit memory (KB)
*               soft    as              4194304
*               hard    as              8388608

# Core dumps
*               soft    core            0
*               hard    core            0

# Specific user limits
developer       soft    nproc           4096
developer       hard    nproc           8192

# Group limits (prefix @)
@developers     soft    nofile          8192
```

### Enable Limits in PAM

Usually already enabled in `/etc/pam.d/common-session`:

```
session    required    pam_limits.so
```

### Common Limit Types

| Type | Description |
|------|-------------|
| nproc | Max user processes |
| nofile | Max open files |
| memlock | Max locked memory |
| as | Max address space |
| core | Core dump size (0 disables) |
| cpu | CPU time limit |
| fsize | Max file size |

## Session Security

### Configure Session Options

Edit `/etc/pam.d/common-session`:

```
# Log session open/close
session    required    pam_unix.so

# Set resource limits
session    required    pam_limits.so

# Set environment
session    required    pam_env.so

# Create home directory if missing
session    optional    pam_mkhomedir.so skel=/etc/skel umask=077

# Last login notification
session    optional    pam_lastlog.so showfailed

# Notify on new mail
session    optional    pam_mail.so standard
```

### umask for New Sessions

Set default umask in `/etc/pam.d/common-session`:

```
session    optional    pam_umask.so umask=027
```

Or in `/etc/login.defs`:

```
UMASK    027
```

## Two-Factor Authentication

### Google Authenticator

Install the module:

```bash
sudo apt install libpam-google-authenticator
```

Configure for each user:

```bash
# As the user, run setup
google-authenticator
```

Answer prompts:
- Time-based tokens: yes
- Update .google_authenticator: yes
- Disallow multiple uses: yes
- Increase time skew: no
- Rate limiting: yes

Enable in PAM (e.g., `/etc/pam.d/sshd`):

```
auth    required    pam_google_authenticator.so
```

Update SSH configuration `/etc/ssh/sshd_config`:

```
ChallengeResponseAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
```

### U2F/FIDO2

Install the module:

```bash
sudo apt install libpam-u2f
```

Register key:

```bash
# Create config directory
mkdir -p ~/.config/Yubico

# Register U2F key
pamu2fcfg > ~/.config/Yubico/u2f_keys
# Touch the key when prompted
```

Enable in PAM:

```
auth    required    pam_u2f.so
```

## Debugging PAM

### Enable Debug Logging

Temporarily add `debug` to module arguments:

```
auth    required    pam_unix.so nullok debug
```

### View PAM Logs

```bash
# Authentication logs
sudo tail -f /var/log/auth.log

# System messages
sudo journalctl -f | grep pam
```

### Test PAM Configuration

```bash
# Test SSH PAM config
sudo pamtester sshd username authenticate

# Test sudo PAM config
sudo pamtester sudo username authenticate acct_mgmt
```

### Common Issues

**"Authentication failure" despite correct password:**

```bash
# Check PAM configuration syntax
# Look for typos in /etc/pam.d/ files
grep -r "required" /etc/pam.d/ | head

# Check module exists
ls -la /lib/x86_64-linux-gnu/security/pam_unix.so
```

**"Module is unknown":**

```bash
# Module not installed
sudo apt install libpam-<module>

# Check available modules
ls /lib/x86_64-linux-gnu/security/
```

## Security Recommendations

### PAM Best Practices

| Practice | Implementation |
|----------|----------------|
| Strong passwords | pam_pwquality with strict requirements |
| Account lockout | pam_faillock with reasonable thresholds |
| Audit logging | pam_tty_audit for command logging |
| Resource limits | pam_limits to prevent DoS |
| 2FA for sensitive access | pam_google_authenticator or pam_u2f |

### Avoid Common Mistakes

| Mistake | Risk |
|---------|------|
| nullok without reason | Allows blank passwords |
| sufficient before required | May skip required checks |
| Missing modules | Silent authentication bypass |
| Overly strict lockout | Self-DoS vulnerability |

### Test Changes Carefully

Before deploying PAM changes:

1. Keep an active root session open
2. Test in a secondary terminal
3. Have recovery plan (boot media)
4. Document changes

## Quick Reference

### Common Modules

| Module | Purpose |
|--------|---------|
| pam_unix | Traditional Unix authentication |
| pam_pwquality | Password complexity |
| pam_faillock | Account lockout |
| pam_limits | Resource limits |
| pam_time | Time-based access |
| pam_env | Environment variables |
| pam_mkhomedir | Create home directories |
| pam_google_authenticator | TOTP 2FA |
| pam_u2f | U2F/FIDO2 authentication |

### Key Files

| File | Purpose |
|------|---------|
| /etc/pam.d/* | Service-specific PAM config |
| /etc/security/pwquality.conf | Password complexity |
| /etc/security/faillock.conf | Lockout policy |
| /etc/security/limits.conf | Resource limits |
| /etc/security/time.conf | Access time restrictions |
| /etc/login.defs | Login defaults |

## Next Steps

Continue to [systemd](systemd.md) to learn about service management and hardening.
