# Netplan Renderers

## What is a Renderer?

A renderer is the backend system that actually configures the network. Netplan generates configuration files for the chosen renderer.

```
Netplan YAML
     │
     ▼
┌─────────────────────────────────────────────────┐
│              Netplan Parser                      │
│    Reads YAML, validates, generates config      │
└─────────────────────────────────────────────────┘
     │
     ├──────────────────────┬─────────────────────┐
     ▼                      ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  networkd   │      │NetworkManager│     │  (sriov)    │
└─────────────┘      └─────────────┘      └─────────────┘
```

## Available Renderers

### systemd-networkd

**Default for Ubuntu Server**

Characteristics:
- Lightweight, minimal dependencies
- Designed for servers and headless systems
- Integrated with systemd
- No GUI

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: true
```

### NetworkManager

**Default for Ubuntu Desktop**

Characteristics:
- Full-featured network management
- GUI integration (nm-applet, GNOME Settings)
- Better for laptops (roaming, WiFi management)
- More complex

```yaml
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    eth0:
      dhcp4: true
```

## Choosing a Renderer

### Use systemd-networkd When

- Running a server (headless)
- Need minimal resource usage
- Configuration is static
- No GUI needed
- Managing VMs/containers

### Use NetworkManager When

- Running a desktop
- Need GUI configuration
- Frequently changing networks (laptop)
- Need VPN integration (NetworkManager plugins)
- Using mobile broadband

## Renderer Comparison

| Feature | systemd-networkd | NetworkManager |
|---------|------------------|----------------|
| Resource usage | Low | Higher |
| GUI support | No | Yes |
| WiFi roaming | Limited | Excellent |
| VPN support | Limited | Extensive |
| Server recommended | Yes | No |
| Desktop recommended | No | Yes |
| Configuration | Files only | Files + GUI + CLI |

## Setting the Renderer

### Global Default

```yaml
network:
  version: 2
  renderer: networkd  # or NetworkManager
```

### Per-Interface

```yaml
network:
  version: 2
  renderer: networkd  # Default for all

  ethernets:
    eth0:
      dhcp4: true
      # Uses default renderer (networkd)

  wifis:
    wlan0:
      renderer: NetworkManager  # Override for this interface
      access-points:
        "MyNetwork":
          password: "secret"
```

## systemd-networkd Details

### Service Management

```bash
# Check status
systemctl status systemd-networkd

# Restart
sudo systemctl restart systemd-networkd

# View logs
journalctl -u systemd-networkd
```

### Generated Files

```bash
# .network files (configuration)
/run/systemd/network/10-netplan-eth0.network

# .netdev files (virtual devices)
/run/systemd/network/10-netplan-br0.netdev

# .link files (link configuration)
/run/systemd/network/10-netplan-eth0.link
```

### Example Generated File

```ini
# /run/systemd/network/10-netplan-eth0.network
[Match]
Name=eth0

[Network]
DHCP=ipv4
LinkLocalAddressing=ipv6

[DHCP]
RouteMetric=100
UseMTU=true
```

### networkctl Commands

```bash
# List interfaces
networkctl list

# Show interface status
networkctl status eth0

# Show all details
networkctl status

# Reconfigure interface
networkctl reconfigure eth0

# Reload configuration
networkctl reload
```

### systemd-resolved Integration

networkd integrates with systemd-resolved for DNS:

```bash
# Check resolver status
resolvectl status

# Per-interface DNS
resolvectl dns eth0

# Query DNS
resolvectl query example.com
```

## NetworkManager Details

### Service Management

```bash
# Check status
systemctl status NetworkManager

# Restart
sudo systemctl restart NetworkManager

# View logs
journalctl -u NetworkManager
```

### Generated Files

```bash
# Connection files
/run/NetworkManager/system-connections/netplan-eth0.nmconnection
```

### nmcli Commands

```bash
# List connections
nmcli connection show

# Show interface status
nmcli device status

# Show connection details
nmcli connection show "netplan-eth0"

# Activate connection
nmcli connection up "netplan-eth0"

# Deactivate
nmcli connection down "netplan-eth0"
```

### nmtui

Text-based UI for NetworkManager:

```bash
nmtui
```

## Mixed Renderer Setup

You can use different renderers for different interfaces:

```yaml
network:
  version: 2

  ethernets:
    eth0:
      renderer: networkd
      dhcp4: true

  wifis:
    wlan0:
      renderer: NetworkManager
      access-points:
        "Office":
          password: "secret"
```

**Use case:** Server with Ethernet (networkd) but occasional WiFi for maintenance (NetworkManager).

## Switching Renderers

### From NetworkManager to networkd

```bash
# 1. Update netplan config
sudo nano /etc/netplan/01-netcfg.yaml
# Set: renderer: networkd

# 2. Generate new config
sudo netplan generate

# 3. Disable NetworkManager
sudo systemctl disable --now NetworkManager

# 4. Enable networkd
sudo systemctl enable --now systemd-networkd

# 5. Apply
sudo netplan apply
```

### From networkd to NetworkManager

```bash
# 1. Install NetworkManager
sudo apt install network-manager

# 2. Update netplan config
sudo nano /etc/netplan/01-netcfg.yaml
# Set: renderer: NetworkManager

# 3. Generate new config
sudo netplan generate

# 4. Disable networkd (optional, can coexist)
# sudo systemctl disable --now systemd-networkd

# 5. Enable NetworkManager
sudo systemctl enable --now NetworkManager

# 6. Apply
sudo netplan apply
```

## Troubleshooting Renderer Issues

### networkd Not Applying Configuration

```bash
# Check service
systemctl status systemd-networkd

# Check for errors
journalctl -u systemd-networkd -p err

# Regenerate
sudo netplan generate
sudo netplan apply

# Force reconfigure
networkctl reconfigure eth0
```

### NetworkManager Ignoring Netplan

```bash
# Check if NM is managing the interface
nmcli device status

# Ensure netplan generated NM files
ls /run/NetworkManager/system-connections/

# Reload connections
nmcli connection reload
```

### Interface Managed by Wrong Renderer

```yaml
# Force specific renderer
ethernets:
  eth0:
    renderer: networkd  # Explicit
    dhcp4: true
```

### Both Renderers Trying to Manage

```bash
# Check what's managing eth0
networkctl status eth0  # Shows if networkd manages it
nmcli device status     # Shows if NM manages it

# One should show "unmanaged"
```

## Renderer-Specific Features

### networkd-Only Features

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      route-metric: 100
      use-domains: true
    networkd:  # networkd-specific passthrough
      RequiredForOnline: no
```

### NetworkManager-Only Features

```yaml
ethernets:
  eth0:
    dhcp4: true
    networkmanager:  # NM-specific passthrough
      uuid: "12345678-1234-1234-1234-123456789012"
      passthrough:
        connection.autoconnect-priority: 100
```

## Server Recommendation

For the MS-S1 MAX server setup:

```yaml
network:
  version: 2
  renderer: networkd  # Recommended for servers

  ethernets:
    enp5s0:
      dhcp4: true
```

**Reasons:**
- Lower resource usage
- Better systemd integration
- Designed for static configurations
- No unnecessary GUI components
