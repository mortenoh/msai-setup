# Netplan Basics

## Configuration Files

### Location

Netplan configuration files are stored in:

```
/etc/netplan/
├── 00-installer-config.yaml    # Created by Ubuntu installer
├── 01-netcfg.yaml              # Custom configuration
└── 99-custom.yaml              # Override file
```

### Processing Order

Files are processed in **lexicographical order**:
- `00-*` files process first
- `99-*` files process last
- Later files can override earlier settings

### Naming Convention

```
/etc/netplan/
├── 00-installer-config.yaml    # Base from installer
├── 50-cloud-init.yaml          # Cloud-init generated
├── 60-bridge.yaml              # Custom bridge config
└── 90-local.yaml               # Local overrides
```

## Basic Structure

### Minimal Configuration

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: true
```

### Structure Breakdown

```yaml
network:                    # Root key (required)
  version: 2                # Schema version (required)
  renderer: networkd        # Backend (optional, has default)

  ethernets:                # Ethernet devices
    eth0:                   # Interface name or match pattern
      dhcp4: true           # Configuration options

  bridges:                  # Bridge devices
    br0:
      interfaces: [eth0]

  bonds:                    # Bond devices
    bond0:
      interfaces: [eth0, eth1]

  vlans:                    # VLAN devices
    vlan100:
      id: 100
      link: eth0

  wifis:                    # Wireless devices
    wlan0:
      access-points:
        "MyNetwork":
          password: "secret"
```

## Commands

### netplan generate

Generates backend configuration without applying:

```bash
sudo netplan generate

# Files created in:
# /run/systemd/network/   (for networkd)
# /run/NetworkManager/    (for NetworkManager)
```

### netplan apply

Applies configuration immediately:

```bash
sudo netplan apply
```

!!! warning "Remote Access Risk"
    `netplan apply` can disconnect you if configuration is wrong. Use `netplan try` for remote administration.

### netplan try

Applies configuration with automatic rollback:

```bash
# Default 120 second timeout
sudo netplan try

# Custom timeout
sudo netplan try --timeout 60
```

Press ENTER to confirm changes. If you don't (or can't because you lost connectivity), configuration reverts automatically.

### netplan get

Show current configuration:

```bash
# All configuration
sudo netplan get

# Specific interface
sudo netplan get ethernets.eth0

# Output as YAML
sudo netplan get --root-dir=/
```

### netplan set

Modify configuration from command line:

```bash
# Set DHCP
sudo netplan set ethernets.eth0.dhcp4=true

# Set static IP
sudo netplan set ethernets.eth0.addresses='[192.168.1.100/24]'

# Then apply
sudo netplan apply
```

### netplan status

Show current network status (Ubuntu 23.04+):

```bash
sudo netplan status
sudo netplan status eth0
```

### netplan info

Show Netplan version and features:

```bash
netplan info
```

## Interface Identification

### By Name

Direct interface name:

```yaml
ethernets:
  enp5s0:
    dhcp4: true
```

### By Match

Match multiple interfaces:

```yaml
ethernets:
  ethernet-dhcp:
    match:
      driver: e1000
    dhcp4: true
```

### Match Options

```yaml
ethernets:
  matched:
    match:
      name: "enp*"           # Glob pattern
      macaddress: "aa:bb:cc:dd:ee:ff"
      driver: "virtio*"
    set-name: eth0           # Rename matched interface
```

## Common Interface Names

### Predictable Names (Default)

| Pattern | Meaning |
|---------|---------|
| `enp5s0` | Ethernet, PCI bus 5, slot 0 |
| `ens3` | Ethernet, slot 3 |
| `eno1` | Onboard Ethernet 1 |
| `enx...` | Ethernet by MAC address |
| `wlp2s0` | Wireless, PCI bus 2, slot 0 |

### Finding Your Interface

```bash
# List all interfaces
ip link show

# Show detailed info
networkctl list

# Show status
networkctl status enp5s0
```

## Configuration Validation

### Syntax Check

```bash
# Check YAML syntax
sudo netplan generate

# Debug output
sudo netplan --debug generate
```

### Common Errors

**Invalid YAML:**

```yaml
# WRONG - tabs instead of spaces
network:
	version: 2    # Tab character!

# CORRECT - spaces only
network:
  version: 2      # Two spaces
```

**Missing Required Fields:**

```yaml
# WRONG - missing version
network:
  ethernets:
    eth0:
      dhcp4: true

# CORRECT
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

**Invalid IP Format:**

```yaml
# WRONG - missing CIDR notation
addresses:
  - 192.168.1.100

# CORRECT
addresses:
  - 192.168.1.100/24
```

## Backend Files

### systemd-networkd Files

Generated in `/run/systemd/network/`:

```bash
ls -la /run/systemd/network/

# Example files:
# 10-netplan-eth0.network
# 10-netplan-br0.netdev
# 10-netplan-br0.network
```

### NetworkManager Files

Generated in `/run/NetworkManager/system-connections/`:

```bash
ls -la /run/NetworkManager/system-connections/
```

## Persistence

### Configuration Persistence

- YAML files in `/etc/netplan/` persist across reboots
- Generated files in `/run/` are recreated at boot

### When Changes Take Effect

| Action | Effect |
|--------|--------|
| Edit YAML | No immediate effect |
| `netplan generate` | Creates backend files |
| `netplan apply` | Applies to running system |
| Reboot | Re-generates and applies |

## Minimal vs Full Configuration

### Minimal (DHCP)

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

### Complete (Static)

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - 192.168.1.101/24
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.0.0.0/8
          via: 192.168.1.254
      nameservers:
        search: [example.com, local]
        addresses: [192.168.1.1, 1.1.1.1]
      mtu: 1500
      optional: false
```
