# Migration to Netplan

## Overview

Netplan replaced `/etc/network/interfaces` (ifupdown) and direct NetworkManager configuration in Ubuntu 18.04+. This guide covers migration from legacy systems.

## From /etc/network/interfaces

### Basic Interface

**Before (ifupdown):**

```
# /etc/network/interfaces
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 1.1.1.1 8.8.8.8
```

**After (netplan):**

```yaml
# /etc/netplan/00-config.yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
```

### DHCP Interface

**Before:**

```
auto eth0
iface eth0 inet dhcp
```

**After:**

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

### Multiple Addresses

**Before:**

```
auto eth0
iface eth0 inet static
    address 192.168.1.100/24
    gateway 192.168.1.1

auto eth0:0
iface eth0:0 inet static
    address 192.168.1.101/24

auto eth0:1
iface eth0:1 inet static
    address 192.168.1.102/24
```

**After:**

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - 192.168.1.101/24
        - 192.168.1.102/24
      routes:
        - to: default
          via: 192.168.1.1
```

### Bridge

**Before:**

```
auto br0
iface br0 inet static
    bridge_ports eth0
    bridge_stp off
    bridge_fd 0
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
```

**After:**

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        stp: false
        forward-delay: 0
```

### Bond

**Before:**

```
auto bond0
iface bond0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    bond-slaves eth0 eth1
    bond-mode 802.3ad
    bond-miimon 100
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4
```

**After:**

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
    eth1:
      dhcp4: false

  bonds:
    bond0:
      interfaces:
        - eth0
        - eth1
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        mode: 802.3ad
        mii-monitor-interval: 100
        lacp-rate: fast
        transmit-hash-policy: layer3+4
```

### VLAN

**Before:**

```
auto eth0.100
iface eth0.100 inet static
    address 10.100.0.1
    netmask 255.255.255.0
    vlan-raw-device eth0
```

**After:**

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false

  vlans:
    eth0.100:
      id: 100
      link: eth0
      addresses:
        - 10.100.0.1/24
```

## From NetworkManager Connections

### View Existing Connections

```bash
nmcli connection show
nmcli connection show "Wired connection 1"
```

### Static IP

**NetworkManager connection:**

```bash
nmcli connection show "My Connection" | grep -E "ipv4|gateway|dns"
```

**Netplan:**

```yaml
network:
  version: 2
  renderer: networkd  # or NetworkManager if needed

  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
```

### WiFi

**NetworkManager:**

```bash
nmcli connection show "MyWiFi" | grep -E "ssid|psk|802-11"
```

**Netplan:**

```yaml
network:
  version: 2
  renderer: NetworkManager  # Required for WiFi

  wifis:
    wlan0:
      access-points:
        "MyWiFi":
          password: "secretpassword"
      dhcp4: true
```

## Migration Process

### Step 1: Document Current Configuration

```bash
# Backup existing config
cp /etc/network/interfaces /etc/network/interfaces.backup
cp -r /etc/NetworkManager/system-connections /root/nm-backup/

# Document current state
ip addr show > /root/network-state.txt
ip route show >> /root/network-state.txt
cat /etc/resolv.conf >> /root/network-state.txt
```

### Step 2: Create Netplan Configuration

```bash
# Create netplan config
sudo nano /etc/netplan/00-config.yaml
```

### Step 3: Disable Old Configuration

```bash
# Comment out /etc/network/interfaces
sudo mv /etc/network/interfaces /etc/network/interfaces.disabled

# Remove NM connections (if switching to networkd)
# sudo rm /etc/NetworkManager/system-connections/*
```

### Step 4: Test Safely

```bash
# Validate syntax
sudo netplan generate

# Apply with rollback
sudo netplan try --timeout 120

# If it works, press ENTER
# If not, wait for rollback
```

### Step 5: Verify

```bash
# Check configuration applied
ip addr show
ip route show
resolvectl status

# Test connectivity
ping 8.8.8.8
ping google.com
```

## Rollback Procedure

If migration fails:

```bash
# Restore old interfaces file
sudo mv /etc/network/interfaces.disabled /etc/network/interfaces

# Remove netplan config
sudo rm /etc/netplan/00-config.yaml

# Restart old networking
sudo systemctl restart networking

# Or reboot
sudo reboot
```

## Common Migration Issues

### Interface Names Changed

Old: `eth0` → New: `enp5s0`

```yaml
# Use match to handle any name
ethernets:
  mainnic:
    match:
      macaddress: "aa:bb:cc:dd:ee:ff"
    set-name: eth0
    dhcp4: true
```

### DNS Not Working

Add nameservers explicitly:

```yaml
ethernets:
  eth0:
    dhcp4: true
    nameservers:
      addresses: [1.1.1.1, 8.8.8.8]
```

### Gateway Not Default Route

Use `routes` instead of deprecated `gateway4`:

```yaml
# Old (deprecated)
gateway4: 192.168.1.1

# New (correct)
routes:
  - to: default
    via: 192.168.1.1
```

### Bridge/Bond Members Keep Getting IPs

Ensure member interfaces have no DHCP/static:

```yaml
ethernets:
  eth0:
    dhcp4: false  # Important!
  eth1:
    dhcp4: false  # Important!

bonds:
  bond0:
    interfaces: [eth0, eth1]
    addresses: [192.168.1.100/24]  # IP on bond
```

## Version-Specific Notes

### Ubuntu 18.04 (Bionic)

- First version with netplan
- Some features missing
- May need `renderer: networkd` explicitly

### Ubuntu 20.04 (Focal)

- Mature netplan
- `gateway4` deprecated but works

### Ubuntu 22.04+ (Jammy+)

- `gateway4` removed - use `routes`
- Full feature support
- WireGuard native support

## Conversion Tools

### netplan migrate

For simple ifupdown conversions:

```bash
# Generate netplan from interfaces file
netplan migrate
```

### Manual Conversion

For complex setups, convert manually following examples above.

## Coexistence

During migration, you can have both:

```bash
# Keep some interfaces in /etc/network/interfaces
# With 'source-directory' or excluding specific interfaces

# And use netplan for others
# Just don't configure same interface in both
```

## Post-Migration Cleanup

After successful migration:

```bash
# Remove old config files
sudo rm /etc/network/interfaces.disabled
sudo rm -rf /root/nm-backup

# Clean up any unused packages
sudo apt autoremove

# Verify on next reboot
sudo reboot
```
