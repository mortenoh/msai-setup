# CLI Reference

## Overview

The `tailscale` CLI provides complete control over Tailscale:

```bash
tailscale --help
```

## Connection Commands

### tailscale up

Connect to Tailscale network:

```bash
tailscale up [flags]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--accept-dns` | Accept DNS configuration from admin |
| `--accept-routes` | Accept subnet routes from other nodes |
| `--advertise-exit-node` | Offer to be an exit node |
| `--advertise-routes=` | Routes to advertise (CIDR) |
| `--advertise-tags=` | ACL tags to request |
| `--auth-key=` | Auth key for automated setup |
| `--exit-node=` | Use specified exit node |
| `--exit-node-allow-lan-access` | Allow LAN access when using exit node |
| `--force-reauth` | Force reauthentication |
| `--hostname=` | Hostname to use |
| `--login-server=` | Custom coordination server |
| `--netfilter-mode=` | Netfilter mode (on/nodivert/off) |
| `--operator=` | Unix user to allow operations |
| `--reset` | Reset unspecified options to default |
| `--shields-up` | Block incoming connections |
| `--ssh` | Run SSH server |
| `--timeout=` | Connection timeout |

**Examples:**

```bash
# Basic connection
sudo tailscale up

# Server with SSH and routes
sudo tailscale up --ssh --advertise-routes=192.168.1.0/24

# Client using exit node
sudo tailscale up --exit-node=my-exit-server

# Automated with auth key
sudo tailscale up --auth-key=tskey-auth-xxxxx
```

### tailscale down

Disconnect from Tailscale:

```bash
sudo tailscale down
```

Keeps authentication, just disconnects.

### tailscale logout

Log out and remove authentication:

```bash
sudo tailscale logout
```

Requires re-authentication on next `tailscale up`.

### tailscale login

Authenticate with custom options:

```bash
tailscale login [flags]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--auth-key=` | Use auth key |
| `--login-server=` | Custom control server |
| `--timeout=` | Login timeout |

## Status Commands

### tailscale status

Show network status:

```bash
tailscale status [flags]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |
| `--peers` | Show only peers |
| `--self` | Show only self |
| `--active` | Show only active peers |
| `--browser` | Open admin console |

**Examples:**

```bash
# Basic status
tailscale status

# JSON output
tailscale status --json | jq '.Peer | keys'

# Just active connections
tailscale status --active
```

### tailscale ip

Show Tailscale IP addresses:

```bash
tailscale ip [flags] [peer]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `-1` | Only show first IP |
| `-4` | Only show IPv4 |
| `-6` | Only show IPv6 |

**Examples:**

```bash
# Your IPs
tailscale ip

# Your IPv4 only
tailscale ip -4

# Peer's IP
tailscale ip my-server
```

### tailscale whois

Look up who owns an IP:

```bash
tailscale whois <ip>
```

**Example:**

```bash
tailscale whois 100.100.100.5
```

## Network Commands

### tailscale ping

Ping a peer through Tailscale:

```bash
tailscale ping [flags] <hostname-or-ip>
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--c=` | Number of pings |
| `--timeout=` | Ping timeout |
| `--tsmp` | Use TSMP ping |
| `--peerapi` | Ping via peerapi |
| `--until-direct` | Ping until direct connection |
| `--verbose` | Verbose output |

**Examples:**

```bash
# Basic ping
tailscale ping my-server

# Multiple pings
tailscale ping --c=10 my-server

# Wait for direct connection
tailscale ping --until-direct my-server
```

### tailscale netcheck

Check network connectivity:

```bash
tailscale netcheck [flags]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--verbose` | Detailed output |
| `--every=` | Repeat interval |

**Example:**

```bash
tailscale netcheck --verbose
```

### tailscale dns

Manage DNS configuration:

```bash
tailscale dns [subcommand]
```

**Subcommands:**

```bash
tailscale dns status    # Show DNS status
tailscale dns query     # Query DNS
```

## Configuration Commands

### tailscale set

Persistently set configuration:

```bash
tailscale set [flags]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--accept-dns` | Accept DNS |
| `--accept-routes` | Accept routes |
| `--advertise-exit-node` | Advertise as exit node |
| `--advertise-routes=` | Advertise routes |
| `--auto-update` | Enable auto-updates |
| `--exit-node=` | Set exit node |
| `--hostname=` | Set hostname |
| `--operator=` | Set operator user |
| `--shields-up` | Enable shields |
| `--ssh` | Enable SSH |

**Examples:**

```bash
# Enable auto-updates
sudo tailscale set --auto-update

# Set operator
sudo tailscale set --operator=myuser

# Enable SSH
sudo tailscale set --ssh
```

### tailscale switch

Switch between Tailscale accounts:

```bash
tailscale switch [account]
```

**Examples:**

```bash
# List accounts
tailscale switch --list

# Switch to account
tailscale switch work@example.com
```

## File Transfer

### tailscale file

Transfer files between devices:

```bash
tailscale file [subcommand]
```

**Subcommands:**

```bash
tailscale file cp <files> <peer>:    # Send files
tailscale file get [directory]        # Receive files
```

**Examples:**

```bash
# Send file
tailscale file cp document.pdf my-laptop:

# Send multiple files
tailscale file cp *.jpg my-laptop:

# Receive files
tailscale file get ~/Downloads/
```

## SSH Commands

### tailscale ssh

SSH into a peer using Tailscale authentication:

```bash
tailscale ssh [flags] user@host [command]
```

Uses Tailscale identity instead of SSH keys.

**Example:**

```bash
tailscale ssh user@my-server
```

## Certificate Commands

### tailscale cert

Manage TLS certificates:

```bash
tailscale cert [flags] <domain>
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--cert-file=` | Certificate output file |
| `--key-file=` | Key output file |

**Example:**

```bash
tailscale cert my-server.tailnet.ts.net
```

## Funnel and Serve

### tailscale serve

Expose local services on your tailnet:

```bash
tailscale serve [flags] {port|path|url}
```

**Examples:**

```bash
# Serve local port
tailscale serve 3000

# Serve with HTTPS
tailscale serve https / http://localhost:3000

# Serve static files
tailscale serve / /var/www/html
```

### tailscale funnel

Expose services to the public internet:

```bash
tailscale funnel [flags] {port|target}
```

**Examples:**

```bash
# Expose port publicly
tailscale funnel 443

# View funnel status
tailscale funnel status
```

## Debug Commands

### tailscale debug

Various debugging commands:

```bash
tailscale debug [subcommand]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `prefs` | Show preferences |
| `netmap` | Show network map |
| `portmap` | Show port mappings |
| `derp-map` | Show DERP map |
| `metrics` | Show metrics |
| `component-logs` | Enable component logging |
| `capture` | Capture network traffic |

**Examples:**

```bash
# Show current preferences
tailscale debug prefs

# Show network map
tailscale debug netmap

# Show DERP servers
tailscale debug derp-map
```

### tailscale bugreport

Generate a bug report:

```bash
tailscale bugreport
```

Outputs a URL with diagnostic information for support.

## Lock Commands

### tailscale lock

Manage Tailscale Lock (network lock):

```bash
tailscale lock [subcommand]
```

**Subcommands:**

```bash
tailscale lock status              # Show lock status
tailscale lock init                # Initialize lock
tailscale lock sign <nodekey>      # Sign a node
tailscale lock disable             # Disable lock
tailscale lock add <keys>          # Add signing keys
tailscale lock remove <keys>       # Remove signing keys
```

## Update Commands

### tailscale update

Update Tailscale:

```bash
tailscale update [flags]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would update |
| `--yes` | Skip confirmation |
| `--track=` | Release track (stable/unstable) |

**Example:**

```bash
# Check for updates
tailscale update --dry-run

# Update
sudo tailscale update --yes
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |

## JSON Output

Many commands support `--json`:

```bash
# Parse with jq
tailscale status --json | jq '.Self.HostName'

# Get all peer IPs
tailscale status --json | jq -r '.Peer[] | .TailscaleIPs[0]'

# Get DNS name
tailscale status --json | jq -r '.Self.DNSName'
```
