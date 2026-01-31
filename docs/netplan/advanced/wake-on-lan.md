# Wake-on-LAN

## Overview

Wake-on-LAN (WoL) allows powering on a computer remotely by sending a special network packet (magic packet). Essential for:

- Remote server management
- Power management/scheduling
- Emergency access
- Home lab automation

## How WoL Works

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  Client                           Server (powered off)           │
│  ┌──────────┐                    ┌──────────────────────┐       │
│  │          │   Magic Packet     │                      │       │
│  │ Wake     │ ──────────────────▶│  NIC (still powered) │       │
│  │ Tool     │   FF FF FF FF FF   │  detects packet      │       │
│  │          │   AA:BB:CC:DD:EE   │  triggers power on   │       │
│  └──────────┘   (MAC x 16)       └──────────────────────┘       │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

The magic packet contains:
- 6 bytes of 0xFF
- Target MAC address repeated 16 times

## Enable WoL in Netplan

### Basic Configuration

```yaml
network:
  version: 2
  ethernets:
    eth0:
      wakeonlan: true
      dhcp4: true
```

### With Static IP

```yaml
network:
  version: 2
  ethernets:
    eth0:
      wakeonlan: true
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
```

## Prerequisites

### 1. BIOS/UEFI Support

Enable in firmware:

- Look for "Wake on LAN" or "Power On by PCI-E"
- May be under "Power Management" or "Advanced"
- Also enable "Power On after Power Failure" for UPS scenarios

### 2. Network Card Support

Check if NIC supports WoL:

```bash
# Check WoL capabilities
ethtool eth0 | grep -i wake

# Example output:
#         Supports Wake-on: pumbg
#         Wake-on: g

# Legend:
# p - PHY activity
# u - Unicast messages
# m - Multicast messages
# b - Broadcast messages
# g - Magic packet (the one we need)
```

### 3. Verify WoL is Enabled

```bash
# Check current WoL setting
ethtool eth0 | grep "Wake-on:"

# Should show 'g' for magic packet:
# Wake-on: g
```

## Apply and Verify

```bash
# Apply netplan
sudo netplan apply

# Verify WoL is enabled
ethtool eth0 | grep "Wake-on:"
```

## Sending Magic Packets

### Using wakeonlan

```bash
# Install
sudo apt install wakeonlan

# Send magic packet
wakeonlan AA:BB:CC:DD:EE:FF
```

### Using etherwake

```bash
# Install
sudo apt install etherwake

# Send (requires specifying interface)
sudo etherwake -i eth0 AA:BB:CC:DD:EE:FF
```

### Using wol (Python)

```bash
# Install
pip install wakeonlan

# Usage
wakeonlan AA:BB:CC:DD:EE:FF
```

### From PowerShell (Windows)

```powershell
# PowerShell function
function Send-WakeOnLan {
    param([string]$MacAddress)
    $MacBytes = $MacAddress -split '[:-]' | ForEach-Object { [byte]('0x' + $_) }
    $MagicPacket = [byte[]](,0xFF * 6) + ($MacBytes * 16)
    $UdpClient = New-Object System.Net.Sockets.UdpClient
    $UdpClient.Connect([System.Net.IPAddress]::Broadcast, 9)
    $UdpClient.Send($MagicPacket, $MagicPacket.Length)
    $UdpClient.Close()
}

# Usage
Send-WakeOnLan "AA:BB:CC:DD:EE:FF"
```

## Remote WoL (Across Subnets)

Magic packets are broadcast and don't cross routers by default.

### Option 1: Directed Broadcast

```bash
# Send to subnet broadcast address
wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF
```

Router must allow directed broadcasts (often disabled for security).

### Option 2: WoL Relay/Proxy

Set up a relay on the target network:

```bash
#!/bin/bash
# /usr/local/bin/wol-relay.sh
# Listen on port 9 and forward magic packets

socat UDP4-RECVFROM:9,fork EXEC:"/usr/local/bin/wol-handler.sh"
```

### Option 3: VPN

Send WoL through VPN connected to target network:

```bash
# From VPN client
wakeonlan -i 10.0.0.255 AA:BB:CC:DD:EE:FF
```

## Secure WoL

### SecureOn (WoL with Password)

Some NICs support password-protected WoL:

```bash
# Enable SecureOn password (if supported)
ethtool -s eth0 wol s

# Set password
ethtool -s eth0 sopass 11:22:33:44:55:66
```

### WoL via SSH Jump Host

Instead of exposing WoL, SSH to a always-on host:

```bash
# SSH to jump host, then wake target
ssh jumphost "wakeonlan AA:BB:CC:DD:EE:FF"
```

### Firewall Considerations

WoL uses UDP port 7 or 9 (port 9 is more common):

```bash
# Allow WoL packets (if firewall is running before wake)
ufw allow 9/udp
```

## Troubleshooting

### WoL Not Working

```bash
# 1. Check BIOS/UEFI setting
# Reboot and check firmware settings

# 2. Check NIC support
ethtool eth0 | grep -i wake

# 3. Check current setting
ethtool eth0 | grep "Wake-on:"
# Must show 'g'

# 4. Enable manually if needed
sudo ethtool -s eth0 wol g

# 5. Check cable is connected
# WoL requires physical link

# 6. Try from local network first
# Then try remote
```

### WoL Resets After Reboot

Netplan should persist settings, but if not:

```bash
# Check systemd-networkd is managing interface
networkctl status eth0

# Check generated config includes WoL
grep -i wol /run/systemd/network/*.network
```

### NIC Not Powered in Shutdown

Some systems power off NICs completely:

- Check BIOS for "ErP Ready" or "Deep Sleep" - disable these
- Check for "LAN Power" or similar settings

### Wrong Interface

```bash
# Find correct interface with MAC
ip link show | grep -B1 "aa:bb:cc"

# Use that interface name in netplan
```

## WoL with Bonds/Bridges

### Bond Interface

WoL must be set on physical interfaces:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      wakeonlan: true      # On physical NIC
      dhcp4: false
    eth1:
      wakeonlan: true      # On physical NIC
      dhcp4: false

  bonds:
    bond0:
      interfaces:
        - eth0
        - eth1
      addresses:
        - 192.168.1.100/24
```

### Bridge Interface

Same principle - enable on physical:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      wakeonlan: true      # Physical NIC
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
```

## Automation Examples

### Scheduled Wake

```bash
# Cron to wake server at 8 AM
0 8 * * * /usr/bin/wakeonlan AA:BB:CC:DD:EE:FF
```

### Wake Before Backup

```bash
#!/bin/bash
# /usr/local/bin/backup-server.sh

# Wake the server
wakeonlan AA:BB:CC:DD:EE:FF

# Wait for it to come up
sleep 120

# Run backup
rsync -av server:/data /backup/

# Shutdown server (optional)
ssh server "sudo shutdown -h now"
```

### Monitor and Wake

```bash
#!/bin/bash
# Wake server if needed service is down

if ! ping -c 1 192.168.1.100 > /dev/null; then
    echo "Server down, waking..."
    wakeonlan AA:BB:CC:DD:EE:FF
fi
```

## Getting MAC Address

### On the Target Server

```bash
# Get MAC address
ip link show eth0 | grep ether

# Or
cat /sys/class/net/eth0/address
```

### From Network

```bash
# If server is on (ping first)
ping 192.168.1.100
arp -a | grep 192.168.1.100
```

### From DHCP Server

```bash
# Check DHCP leases
cat /var/lib/dhcp/dhcpd.leases | grep -A 5 "192.168.1.100"
```

## Best Practices

1. **Document MACs** - Keep a list of server MAC addresses
2. **Test regularly** - Verify WoL works before you need it
3. **Have backup access** - IPMI/iLO/iDRAC as fallback
4. **Secure your network** - WoL packets could be spoofed
5. **Use always-on management** - IPMI is more reliable for critical servers
6. **Consider power draw** - NICs in WoL mode use some power
