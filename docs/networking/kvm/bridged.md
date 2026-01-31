# Bridged Networking

## Overview

Bridged networking places VMs directly on your physical network. VMs get IPs from your network's DHCP server and appear as regular hosts.

## When to Use Bridged Mode

- VMs need to be accessible from other network devices
- VMs need specific services (like DHCP server, DNS)
- Easier remote access without port forwarding
- Gaming VMs that need low latency

## Host Bridge Setup

### Create Bridge with Netplan

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    enp5s0:
      dhcp4: false
      # Physical interface - no IP here

  bridges:
    br0:
      interfaces: [enp5s0]
      dhcp4: true
      # Or static:
      # addresses:
      #   - 192.168.1.100/24
      # routes:
      #   - to: default
      #     via: 192.168.1.1
      # nameservers:
      #   addresses: [1.1.1.1]
      parameters:
        stp: false
        forward-delay: 0
```

### Apply Configuration

```bash
# Test first
sudo netplan try

# Apply
sudo netplan apply

# Verify
ip addr show br0
bridge link show
```

### Verify Bridge

```bash
# Bridge should have IP
ip addr show br0
# inet 192.168.1.100/24

# Physical interface should be enslaved
ip link show enp5s0
# master br0

# Bridge should be forwarding
cat /sys/class/net/br0/bridge/stp_state
# 0 (STP disabled) or 1 (STP enabled)
```

## libvirt Bridged Network

### Create Network Definition

```xml
<!-- bridged-network.xml -->
<network>
  <name>bridged</name>
  <forward mode="bridge"/>
  <bridge name="br0"/>
</network>
```

### Define and Start

```bash
virsh net-define bridged-network.xml
virsh net-start bridged
virsh net-autostart bridged
```

### Verify

```bash
virsh net-list --all
virsh net-info bridged
```

## Attach VM to Bridged Network

### New VM

```bash
virt-install \
    --name myvm \
    --ram 4096 \
    --vcpus 2 \
    --disk path=/var/lib/libvirt/images/myvm.qcow2,size=50 \
    --network network=bridged \
    --os-variant ubuntu22.04 \
    --cdrom /path/to/ubuntu.iso
```

### Existing VM

```bash
# Edit VM XML
virsh edit myvm
```

Change network interface:

```xml
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
</interface>
```

Or use network:

```xml
<interface type='network'>
  <source network='bridged'/>
  <model type='virtio'/>
</interface>
```

## VM Configuration

### DHCP (Recommended)

VM gets IP from network's DHCP server:

```bash
# Inside VM
ip addr show
# Should have IP from 192.168.1.x range
```

### Static IP

Configure inside VM:

```yaml
# /etc/netplan/00-config.yaml (inside VM)
network:
  version: 2
  ethernets:
    enp1s0:
      addresses:
        - 192.168.1.50/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
```

## UFW Considerations

### Traffic Flow

With bridged networking, VM traffic doesn't go through host's IP stack for forwarding:

```
External Host ──▶ br0 (bridge) ──▶ vnet0 ──▶ VM
                       │
                       └─ Host's IP stack (not involved in VM traffic)
```

### UFW Does NOT Filter Bridged Traffic

!!! warning "Important"
    UFW rules on the host do NOT apply to bridged VM traffic by default.

VM traffic crosses the bridge at Layer 2, bypassing the host's INPUT/OUTPUT chains.

### Bridge Filtering

To filter bridged traffic:

```bash
# Enable bridge filtering (may already be enabled)
echo 1 | sudo tee /proc/sys/net/bridge/bridge-nf-call-iptables

# Make permanent
echo "net.bridge.bridge-nf-call-iptables = 1" | sudo tee /etc/sysctl.d/99-bridge.conf
```

Now FORWARD chain rules apply to bridged traffic.

### Filtering Bridged VMs

With bridge-nf-call-iptables enabled:

```bash
# /etc/ufw/before.rules

# Block VM from accessing specific host service
-A ufw-before-forward -i br0 -d 192.168.1.100 -p tcp --dport 22 -j DROP

# Rate limit VM traffic
-A ufw-before-forward -i br0 -m limit --limit 1000/sec -j ACCEPT
-A ufw-before-forward -i br0 -j DROP
```

### VM Should Have Its Own Firewall

Since host UFW doesn't protect bridged VMs:

```bash
# Inside VM
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow ssh
```

## Multiple Bridges

### Different VLANs

```yaml
# /etc/netplan/00-config.yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false

  vlans:
    enp5s0.10:
      id: 10
      link: enp5s0
    enp5s0.20:
      id: 20
      link: enp5s0

  bridges:
    br-vlan10:
      interfaces: [enp5s0.10]
      addresses: [192.168.10.1/24]
    br-vlan20:
      interfaces: [enp5s0.20]
      addresses: [192.168.20.1/24]
```

### Create libvirt Networks

```xml
<!-- vlan10-network.xml -->
<network>
  <name>vlan10</name>
  <forward mode="bridge"/>
  <bridge name="br-vlan10"/>
</network>
```

## Macvtap Alternative

Direct connection without host bridge:

```xml
<interface type='direct'>
  <source dev='enp5s0' mode='bridge'/>
  <model type='virtio'/>
</interface>
```

Modes:
- `bridge` - Frames delivered directly
- `vepa` - Frames sent to external switch
- `private` - VMs can't communicate
- `passthrough` - Exclusive access to NIC

!!! note
    With macvtap, host and VM cannot communicate directly (use a separate management network).

## Troubleshooting

### VM Has No Network

```bash
# Check bridge
ip link show br0
bridge link show

# Check VM interface attached
virsh domiflist vmname

# Check in VM
ip addr
ip route
```

### VM Can't Reach Network

```bash
# Check physical interface is up
ip link show enp5s0

# Check cable/switch
ethtool enp5s0

# Check bridge forwarding
cat /sys/class/net/br0/bridge/stp_state
```

### VM Gets Wrong IP

```bash
# Check DHCP server
# VM should get IP from network's DHCP, not libvirt's

# Verify not using NAT network
virsh domiflist vmname
# Should show bridge/br0, not network/default
```

### Host Lost Network After Creating Bridge

```bash
# Bridge should have IP, not physical interface
ip addr show br0
ip addr show enp5s0

# If IP is on wrong interface, fix netplan config
```

## Performance Considerations

### virtio Driver

Always use virtio for best performance:

```xml
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
</interface>
```

### Multiqueue

For high-throughput VMs:

```xml
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
  <driver name='vhost' queues='4'/>
</interface>
```

Match queues to VM vCPU count.

### Disable STP

If only one bridge (no loops):

```yaml
bridges:
  br0:
    parameters:
      stp: false
      forward-delay: 0
```
