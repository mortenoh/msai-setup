# APT Package Management

APT (Advanced Package Tool) is Ubuntu's package management system. Understanding APT configuration is essential for maintaining a secure and stable server.

## APT Fundamentals

### APT Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Commands                             │
│              apt, apt-get, apt-cache                        │
├─────────────────────────────────────────────────────────────┤
│                    APT Library                               │
│           (Package resolution, downloads)                    │
├─────────────────────────────────────────────────────────────┤
│                     dpkg                                     │
│         (Low-level package installation)                     │
├─────────────────────────────────────────────────────────────┤
│                    Package Database                          │
│              /var/lib/dpkg/status                           │
└─────────────────────────────────────────────────────────────┘
```

### apt vs apt-get

| Command | Use Case |
|---------|----------|
| `apt` | Interactive use (progress bars, colors) |
| `apt-get` | Scripts, automation (stable output) |

## Repository Configuration

### sources.list

Main repository file: `/etc/apt/sources.list`

```bash
# Ubuntu 24.04 example
deb http://archive.ubuntu.com/ubuntu noble main restricted
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted
deb http://archive.ubuntu.com/ubuntu noble universe
deb http://archive.ubuntu.com/ubuntu noble-updates universe
deb http://archive.ubuntu.com/ubuntu noble multiverse
deb http://archive.ubuntu.com/ubuntu noble-updates multiverse
deb http://archive.ubuntu.com/ubuntu noble-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu noble-security main restricted
deb http://security.ubuntu.com/ubuntu noble-security universe
deb http://security.ubuntu.com/ubuntu noble-security multiverse
```

### Repository Format

```
deb [options] uri distribution component1 [component2] [...]
```

| Part | Example | Meaning |
|------|---------|---------|
| Type | deb | Binary packages (deb-src for source) |
| Options | [arch=amd64] | Architecture, signed-by, etc. |
| URI | http://archive.ubuntu.com/ubuntu | Repository URL |
| Distribution | noble | Ubuntu codename |
| Components | main restricted | Package categories |

### Repository Components

| Component | Description | Support |
|-----------|-------------|---------|
| main | Free software, Canonical supported | Full |
| restricted | Proprietary, Canonical supported | Full |
| universe | Free software, community maintained | Community |
| multiverse | Non-free software | Limited |

### Pocket Types

| Pocket | Description |
|--------|-------------|
| (none) | Release packages |
| -updates | Stable updates post-release |
| -security | Security patches |
| -backports | Newer versions backported |
| -proposed | Testing before -updates |

## Adding Repositories

### Using add-apt-repository

```bash
# Add PPA
sudo add-apt-repository ppa:user/ppa-name

# Add repository
sudo add-apt-repository "deb http://repo.example.com/ubuntu noble main"

# Remove repository
sudo add-apt-repository --remove ppa:user/ppa-name
```

### Manual Configuration

Create file in `/etc/apt/sources.list.d/`:

```bash
# Example: Docker repository
sudo nano /etc/apt/sources.list.d/docker.list
```

```
deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable
```

### GPG Keys

Modern method using keyrings:

```bash
# Create keyrings directory
sudo mkdir -p /etc/apt/keyrings

# Download and convert key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set permissions
sudo chmod 644 /etc/apt/keyrings/docker.gpg
```

Reference in sources list:

```
deb [signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable
```

## Common Operations

### Update and Upgrade

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade

# Upgrade with new dependencies
sudo apt full-upgrade

# Upgrade, remove obsolete packages
sudo apt dist-upgrade
```

### Installing Packages

```bash
# Install package
sudo apt install nginx

# Install specific version
sudo apt install nginx=1.24.0-1

# Install without recommended packages
sudo apt install --no-install-recommends nginx

# Install from .deb file
sudo apt install ./package.deb

# Reinstall package
sudo apt install --reinstall nginx
```

### Removing Packages

```bash
# Remove package (keep config)
sudo apt remove nginx

# Remove with configuration
sudo apt purge nginx

# Remove unused dependencies
sudo apt autoremove

# Clean package cache
sudo apt clean          # Remove all cached packages
sudo apt autoclean      # Remove obsolete cached packages
```

### Searching and Information

```bash
# Search packages
apt search nginx

# Show package info
apt show nginx

# List installed packages
apt list --installed

# List upgradable packages
apt list --upgradable

# Show package dependencies
apt depends nginx

# Show reverse dependencies
apt rdepends nginx
```

## Package Pinning

### Understanding Priorities

APT uses priority numbers to decide which version to install:

| Priority | Meaning |
|----------|---------|
| < 0 | Never install |
| 0-100 | Only install if not installed |
| 100-500 | Install if newer than installed |
| 500-990 | Default for target release |
| 990-1000 | Always install even if older |
| > 1000 | Force install, ignore conflicts |

### Pin Configuration

Create `/etc/apt/preferences.d/custom`:

```
# Pin all packages from security to higher priority
Package: *
Pin: release a=noble-security
Pin-Priority: 900

# Pin specific package to specific version
Package: nginx
Pin: version 1.24.*
Pin-Priority: 1001

# Block a package from being installed
Package: apache2
Pin: release *
Pin-Priority: -1

# Prefer packages from specific repository
Package: *
Pin: origin packages.example.com
Pin-Priority: 600
```

### View Pin Status

```bash
# Show pin priority for package
apt-cache policy nginx

# Output:
# nginx:
#   Installed: 1.24.0-1
#   Candidate: 1.24.0-1
#   Version table:
#  *** 1.24.0-1 500
#         500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages
```

## Holding Packages

Prevent packages from being upgraded:

```bash
# Hold package
sudo apt-mark hold nginx

# Unhold package
sudo apt-mark unhold nginx

# List held packages
apt-mark showhold

# Alternative: dpkg hold
echo "nginx hold" | sudo dpkg --set-selections
```

## APT Configuration

### Configuration Directory

APT configuration: `/etc/apt/apt.conf.d/`

Files are read in alphanumeric order.

### Common Configuration

Create `/etc/apt/apt.conf.d/99custom`:

```
// Don't install recommended packages
APT::Install-Recommends "false";

// Don't install suggested packages
APT::Install-Suggests "false";

// Keep downloaded packages
APT::Keep-Downloaded-Packages "true";

// Quiet updates
Acquire::Languages "none";

// HTTP proxy
// Acquire::http::Proxy "http://proxy:3128";

// HTTPS settings
// Acquire::https::Verify-Peer "true";
```

### Security Settings

```
// Require valid signatures
APT::Get::AllowUnauthenticated "false";

// Don't automatically remove packages
APT::Get::AutomaticRemove "false";

// Always prompt before removing
APT::Get::Remove "true";
```

## Proxy Configuration

### HTTP Proxy

Create `/etc/apt/apt.conf.d/95proxy`:

```
Acquire::http::Proxy "http://proxy.example.com:3128";
Acquire::https::Proxy "http://proxy.example.com:3128";
```

### Authenticated Proxy

```
Acquire::http::Proxy "http://user:password@proxy:3128";
```

### Per-Repository Proxy

```
Acquire::http::Proxy::archive.ubuntu.com "http://proxy:3128";
```

## Cache Management

### Cache Locations

| Path | Contents |
|------|----------|
| /var/cache/apt/archives/ | Downloaded .deb files |
| /var/lib/apt/lists/ | Package lists |

### Clean Cache

```bash
# Remove all cached packages
sudo apt clean

# Remove obsolete cached packages
sudo apt autoclean

# Check cache size
du -sh /var/cache/apt/archives/
```

### Limit Cache Size

In `/etc/apt/apt.conf.d/99clean`:

```
APT::Periodic::MaxAge "7";
APT::Periodic::MaxSize "500";
```

## Troubleshooting

### Fix Broken Packages

```bash
# Configure unconfigured packages
sudo dpkg --configure -a

# Fix broken dependencies
sudo apt --fix-broken install

# Force package reinstall
sudo apt install --reinstall package
```

### Lock File Issues

```bash
# If apt is locked
# Wait for other apt process to finish, or:
sudo rm /var/lib/apt/lists/lock
sudo rm /var/cache/apt/archives/lock
sudo rm /var/lib/dpkg/lock*
sudo dpkg --configure -a
```

### Repository Issues

```bash
# Skip broken repository
sudo apt update --ignore-missing

# Remove problematic repository
sudo rm /etc/apt/sources.list.d/problematic.list

# Clear lists and refresh
sudo rm -rf /var/lib/apt/lists/*
sudo apt update
```

### View Logs

```bash
# APT history
cat /var/log/apt/history.log

# APT term log (command output)
cat /var/log/apt/term.log

# dpkg log
cat /var/log/dpkg.log
```

## Security Considerations

### Verify Package Authenticity

```bash
# Check package signature
apt-key list

# Verify package integrity
debsums package-name
```

### Third-Party Repositories

!!! warning "Third-Party Risk"
    Third-party repositories can:

    - Introduce security vulnerabilities
    - Break system stability
    - Override official packages

    Only add trusted repositories.

### Secure Repository Configuration

```bash
# Always use HTTPS
deb https://repo.example.com/ubuntu noble main

# Always verify signatures
deb [signed-by=/etc/apt/keyrings/repo.gpg] https://repo.example.com/ubuntu noble main
```

## Quick Reference

### Essential Commands

```bash
# Update and upgrade
sudo apt update && sudo apt upgrade

# Install/remove
sudo apt install package
sudo apt remove package
sudo apt purge package

# Search
apt search keyword
apt show package

# Maintenance
sudo apt autoremove
sudo apt clean

# Package holds
sudo apt-mark hold package
sudo apt-mark unhold package
apt-mark showhold
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/apt/sources.list | Main repository config |
| /etc/apt/sources.list.d/*.list | Additional repositories |
| /etc/apt/apt.conf.d/*.conf | APT configuration |
| /etc/apt/preferences.d/* | Package pinning |
| /etc/apt/keyrings/ | GPG keys |
| /var/log/apt/history.log | Update history |

## Next Steps

Continue to [Unattended Upgrades](unattended-upgrades.md) to configure automatic security updates.
