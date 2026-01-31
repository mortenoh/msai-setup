# KVM/libvirt Network Integration

## Overview

KVM virtual machines need network connectivity. Netplan provides the host network foundation that libvirt builds upon.

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Host System                               │
│                                                                      │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐                │
│  │    VM 1    │    │    VM 2    │    │    VM 3    │                │
│  │ 192.168.122│    │ 192.168.122│    │ 192.168.1. │                │
│  │    .50     │    │    .51     │    │    150     │                │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘                │
│        │                 │                 │                        │
│        └────────┬────────┘                 │                        │
│                 │                          │                        │
│          virbr0 (NAT)                 br0 (Bridged)                │
│        192.168.122.1             192.168.1.100                     │
│                 │                          │                        │
│                 └────────────┬─────────────┘                        │
│                              │                                      │
│                         eth0 (netplan)                              │
│                         192.168.1.100                               │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                          Physical Network
```

## Network Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| NAT (default) | VMs share host IP | Simple setups, outbound-only |
| Bridged | VMs get IPs from network | Production, direct access |
| Isolated | VMs only talk to each other | Testing, security |
| Macvtap | Direct device access | Performance, SR-IOV |

## NAT Networking (Default)

libvirt's default network (virbr0):

```bash
# Check default network
virsh net-list
virsh net-dumpxml default
```

Default provides:
- Network: 192.168.122.0/24
- Gateway: 192.168.122.1
- DHCP: 192.168.122.2-254
- NAT to host interface

### Netplan for NAT Mode

Minimal netplan - libvirt handles VM networking:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

## Bridged Networking

VMs get IPs directly from physical network.

### Create Bridge with Netplan

```yaml
# /etc/netplan/00-kvm-bridge.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: false
      dhcp6: false

  bridges:
    br0:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
      parameters:
        stp: false
        forward-delay: 0
```

### Configure libvirt to Use Bridge

Create network definition:

```xml
<!-- /tmp/host-bridge.xml -->
<network>
  <name>host-bridge</name>
  <forward mode="bridge"/>
  <bridge name="br0"/>
</network>
```

```bash
# Define and start network
virsh net-define /tmp/host-bridge.xml
virsh net-start host-bridge
virsh net-autostart host-bridge
```

### Attach VM to Bridge

```xml
<!-- VM interface configuration -->
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
</interface>
```

Or with virsh:

```bash
virsh attach-interface --domain vm-name --type bridge \
  --source br0 --model virtio --config
```

## Multiple Networks

### Separate Management and VM Networks

```yaml
# /etc/netplan/00-multi-network.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Management NIC
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1]

    # VM NIC (no host IP)
    eth1:
      dhcp4: false

  bridges:
    br-vms:
      interfaces:
        - eth1
      parameters:
        stp: false
        forward-delay: 0
```

VMs connect to `br-vms` and get IPs from network DHCP.

### VLANs for VMs

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: false

  vlans:
    eth0.10:
      id: 10
      link: eth0

    eth0.20:
      id: 20
      link: eth0

  bridges:
    br-mgmt:
      interfaces:
        - eth0.10
      addresses:
        - 10.10.0.100/24
      routes:
        - to: default
          via: 10.10.0.1

    br-vms:
      interfaces:
        - eth0.20
      # No IP - VMs use their own
      parameters:
        stp: false
```

## Bonded Bridge for VMs

High-availability VM networking:

```yaml
network:
  version: 2
  renderer: networkd

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
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4

  bridges:
    br0:
      interfaces:
        - bond0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        stp: false
        forward-delay: 0
```

## Isolated Networks

VMs can only communicate with each other:

### libvirt Isolated Network

```xml
<network>
  <name>isolated</name>
  <bridge name="virbr1"/>
  <ip address="10.0.0.1" netmask="255.255.255.0">
    <dhcp>
      <range start="10.0.0.2" end="10.0.0.254"/>
    </dhcp>
  </ip>
</network>
```

No `<forward>` element = isolated.

## Macvtap (Direct Device)

High-performance direct access:

```bash
# VM config
virsh attach-interface --domain vm-name \
  --type direct \
  --source eth0 \
  --model virtio \
  --config
```

Or in XML:

```xml
<interface type='direct'>
  <source dev='eth0' mode='bridge'/>
  <model type='virtio'/>
</interface>
```

Modes:
- `bridge`: VMs can communicate
- `vepa`: Traffic goes through switch
- `private`: VMs isolated
- `passthrough`: Exclusive access

## SR-IOV

For maximum performance with supported NICs:

### Enable SR-IOV

```bash
# Check support
lspci -vvv | grep -i "single root"

# Enable VFs
echo 4 > /sys/class/net/eth0/device/sriov_numvfs
```

### Netplan with VFs

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24

    # VF interfaces appear as separate
    eth0v0:
      dhcp4: false
    eth0v1:
      dhcp4: false
```

### Attach VF to VM

```xml
<interface type='hostdev'>
  <source>
    <address type='pci' domain='0x0000' bus='0x03' slot='0x10' function='0x0'/>
  </source>
</interface>
```

## Port Forwarding to VMs

For NAT mode, forward ports from host to VM:

### Using iptables

```bash
# Forward port 80 to VM
iptables -t nat -A PREROUTING -p tcp --dport 80 \
  -j DNAT --to-destination 192.168.122.50:80

# Allow forwarded traffic
iptables -A FORWARD -p tcp -d 192.168.122.50 --dport 80 -j ACCEPT
```

### Using libvirt Hook

Create `/etc/libvirt/hooks/qemu`:

```bash
#!/bin/bash
VM_NAME=$1
ACTION=$2

if [ "$VM_NAME" = "webserver" ] && [ "$ACTION" = "start" ]; then
    iptables -t nat -A PREROUTING -p tcp --dport 80 \
      -j DNAT --to-destination 192.168.122.50:80
fi
```

## VM DNS Resolution

### VM Using Host DNS

VMs in NAT mode use host as DNS (192.168.122.1).

### VM Using Network DNS

For bridged mode, VMs get DNS from DHCP or static config.

### libvirt DNS

```xml
<network>
  <name>default</name>
  <forward mode="nat"/>
  <bridge name="virbr0"/>
  <dns>
    <forwarder addr="1.1.1.1"/>
    <forwarder addr="8.8.8.8"/>
  </dns>
  <ip address="192.168.122.1" netmask="255.255.255.0">
    <dhcp>
      <range start="192.168.122.2" end="192.168.122.254"/>
    </dhcp>
  </ip>
</network>
```

## Troubleshooting

### VM Has No Network

```bash
# Check bridge exists
ip link show br0

# Check VM interface attached
virsh domiflist vm-name

# Check bridge has VM interface
bridge link show

# Check VM has IP
virsh domifaddr vm-name
```

### VM Can't Reach Internet

```bash
# Check host IP forwarding
cat /proc/sys/net/ipv4/ip_forward

# Check NAT rules (for NAT mode)
iptables -t nat -L -n -v

# Check default route on VM
# (from VM console)
ip route show
```

### Bridged VM Not Getting IP

```bash
# Check DHCP server reachable
# From host:
tcpdump -i br0 port 67 or port 68

# Check promiscuous mode
ip link show br0 | grep PROMISC

# Check STP isn't blocking
bridge link show
```

### Performance Issues

```bash
# Check for packet drops
ip -s link show br0

# Use virtio drivers
virsh dumpxml vm-name | grep model

# Consider macvtap or SR-IOV for high throughput
```

## Best Practices

1. **Use bridges for production** - Bridged networking provides direct access
2. **Use virtio drivers** - Best performance for VM NICs
3. **Disable STP on simple bridges** - Faster interface activation
4. **Separate networks** - Management vs. VM traffic
5. **Use VLANs** - Segment different VM groups
6. **Consider bonds** - Redundancy for critical VMs
7. **Plan IP addressing** - Avoid conflicts
8. **Document network topology** - Complex setups need documentation
