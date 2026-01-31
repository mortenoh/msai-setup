# Basic Setup

## First-Time Setup

### Starting Tailscale

```bash
# Start Tailscale and authenticate
sudo tailscale up
```

This outputs a URL:

```
To authenticate, visit:

    https://login.tailscale.com/a/1234567890abcdef
```

Open the URL in a browser to authenticate with your identity provider.

### Post-Authentication

```bash
# Verify connection
tailscale status

# Example output:
# 100.100.100.1  my-laptop     linux   -
# 100.100.100.2  my-server     linux   active; direct 203.0.113.1:41641
```

### Check Your IP

```bash
# IPv4 address
tailscale ip -4
# 100.100.100.1

# IPv6 address
tailscale ip -6
# fd7a:115c:a1e0::1

# Both
tailscale ip
```

## Common Setup Options

### Enable SSH

Tailscale SSH allows passwordless SSH through the Tailscale network:

```bash
sudo tailscale up --ssh
```

Then SSH using the Tailscale hostname:

```bash
ssh my-server  # Uses MagicDNS name
```

### Accept DNS

Enable MagicDNS to resolve Tailscale hostnames:

```bash
sudo tailscale up --accept-dns
```

### Accept Routes

Accept subnet routes advertised by other nodes:

```bash
sudo tailscale up --accept-routes
```

### Hostname Override

Set a custom hostname:

```bash
sudo tailscale up --hostname=my-custom-name
```

### Combined Options

```bash
sudo tailscale up \
  --ssh \
  --accept-dns \
  --accept-routes \
  --hostname=production-server
```

## Tailscale Up Options

### Full Reference

```bash
tailscale up --help
```

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--ssh` | Enable Tailscale SSH server | Off |
| `--accept-dns` | Accept MagicDNS configuration | On |
| `--accept-routes` | Accept subnet routes | Off |
| `--advertise-routes` | Advertise subnet routes | None |
| `--advertise-exit-node` | Act as exit node | Off |
| `--exit-node` | Use specified exit node | None |
| `--hostname` | Set device hostname | System hostname |
| `--shields-up` | Block incoming connections | Off |
| `--auth-key` | Use auth key instead of browser | None |
| `--reset` | Reset to default settings | N/A |
| `--force-reauth` | Force reauthentication | N/A |
| `--operator` | Allow non-root user to manage | None |

### Examples

```bash
# Server setup with SSH and subnet routing
sudo tailscale up \
  --ssh \
  --advertise-routes=192.168.1.0/24 \
  --hostname=home-server

# Exit node
sudo tailscale up \
  --advertise-exit-node \
  --ssh

# Client using exit node
sudo tailscale up \
  --exit-node=home-server \
  --exit-node-allow-lan-access

# Locked down client
sudo tailscale up \
  --shields-up \
  --accept-dns
```

## Tailscale Set (Persistent)

Use `tailscale set` for persistent configuration changes:

```bash
# Enable auto-updates
sudo tailscale set --auto-update

# Set operator user
sudo tailscale set --operator=$USER

# Configure SSH
sudo tailscale set --ssh

# Set hostname
sudo tailscale set --hostname=my-server
```

!!! info "set vs up"
    `tailscale set` changes persist across restarts. `tailscale up` options may need to be repeated.

## Network Check

Verify network connectivity:

```bash
tailscale netcheck
```

Output shows:

```
Report:
    * UDP: true
    * IPv4: yes, 203.0.113.1:41641
    * IPv6: yes, 2001:db8::1
    * MappingVariesByDestIP: false
    * HairPinning: false
    * PortMapping: UPnP
    * Nearest DERP: New York City
    * DERP latency:
        - nyc: 15.2ms
        - sfo: 62.1ms
        - ...
```

### Understanding Results

| Field | Good Value | Issue If |
|-------|------------|----------|
| UDP | true | false = firewall blocking |
| IPv4/IPv6 | yes | no = NAT issues |
| MappingVariesByDestIP | false | true = symmetric NAT |
| PortMapping | UPnP/NAT-PMP | none = may relay |
| Nearest DERP | < 100ms | high = relay latency |

## Ping and Connectivity

### Test Connection to Peer

```bash
tailscale ping my-server
```

Output:

```
pong from my-server (100.100.100.2) via 203.0.113.1:41641 in 15ms
```

### Connection Types

| Output | Meaning |
|--------|---------|
| `via <IP:port>` | Direct connection |
| `via DERP(region)` | Relayed connection |

### Verbose Ping

```bash
tailscale ping --verbose my-server
```

## Status and Diagnostics

### Full Status

```bash
tailscale status
```

### JSON Output

```bash
tailscale status --json | jq .
```

### Specific Information

```bash
# Just peers
tailscale status --peers

# Self info
tailscale status --self

# Active connections
tailscale status --active
```

## DNS Configuration

### Check Current DNS

```bash
tailscale dns status
```

### Override System DNS

If MagicDNS isn't working:

```bash
# Check DNS is enabled
tailscale up --accept-dns

# Verify resolv.conf
cat /etc/resolv.conf
```

### Split DNS

Configure in admin console for domain-specific resolution.

## Logout and Disconnect

### Disconnect (Keep Auth)

```bash
sudo tailscale down
```

Device stays authenticated but disconnects.

### Reconnect

```bash
sudo tailscale up
```

### Logout (Remove Auth)

```bash
sudo tailscale logout
```

Requires re-authentication to reconnect.

## Operator Mode

Allow non-root users to manage Tailscale:

```bash
# Set operator
sudo tailscale set --operator=$USER

# Now user can run without sudo
tailscale status
tailscale ping server
```

!!! warning "Security"
    Operator can modify Tailscale configuration. Only grant to trusted users.

## Re-authentication

### Key Expiry

By default, keys expire periodically. Re-authenticate:

```bash
sudo tailscale up --force-reauth
```

### Disable Key Expiry

In admin console, disable key expiry for specific devices (servers):

1. Go to **Machines**
2. Click on the machine
3. Click **Disable key expiry**

## Machine Settings

### From CLI

```bash
# View current settings
tailscale status --json | jq '.Self'

# Modify settings
sudo tailscale set --hostname=new-name
```

### From Admin Console

1. Go to [login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines)
2. Click on the machine
3. Modify settings:
   - Disable key expiry
   - Apply tags
   - Modify routes

## Quick Setup Examples

### Home Server

```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Configure
sudo tailscale up \
  --ssh \
  --advertise-routes=192.168.1.0/24 \
  --advertise-exit-node \
  --hostname=home-server

# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

### Laptop

```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Configure
sudo tailscale up --accept-routes --accept-dns

# Set operator for convenience
sudo tailscale set --operator=$USER
```

### Headless Server

```bash
# Generate auth key in admin console first
sudo tailscale up \
  --auth-key=tskey-auth-xxxxx \
  --ssh \
  --hostname=prod-server-01
```
