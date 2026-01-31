# libvirt Network Overview

## KVM/libvirt Networking

libvirt provides network management for QEMU/KVM virtual machines. It supports multiple networking modes to fit different use cases.

## Network Types

### NAT (Default)

VMs get private IPs and access external networks through NAT:

```
┌─────────────────────────────────────────────────────────────┐
│                          Host                                │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              virbr0 bridge                           │   │
│   │              192.168.122.1/24                        │   │
│   │                                                      │   │
│   │    ┌────────┐  ┌────────┐                           │   │
│   │    │ vnet0  │  │ vnet1  │                           │   │
│   └────┴───┬────┴──┴───┬────┴───────────────────────────┘   │
│            │           │                                     │
│   ┌────────▼────────┐ ┌▼───────────────┐                    │
│   │      VM1        │ │     VM2        │                    │
│   │  192.168.122.10 │ │ 192.168.122.11 │                    │
│   └─────────────────┘ └────────────────┘                    │
│                                                              │
│   eth0 ────────────────────────────────────▶ Internet       │
│   NAT: 192.168.122.0/24 ──▶ masquerade                     │
└─────────────────────────────────────────────────────────────┘
```

### Bridged

VMs get IPs on the physical network:

```
┌─────────────────────────────────────────────────────────────┐
│                          Host                                │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                 br0 bridge                           │   │
│   │              192.168.1.100/24                        │   │
│   │                                                      │   │
│   │   ┌────────┐ ┌────────┐ ┌────────┐                  │   │
│   │   │  eth0  │ │ vnet0  │ │ vnet1  │                  │   │
│   └───┴───┬────┴─┴───┬────┴─┴───┬────┴──────────────────┘   │
│           │          │          │                            │
│           │   ┌──────▼──────┐ ┌─▼────────────┐              │
│           │   │    VM1      │ │    VM2       │              │
│           │   │ 192.168.1.50│ │192.168.1.51  │              │
│           │   └─────────────┘ └──────────────┘              │
│           │                                                  │
│           └────────────────────────────────▶ Network        │
└─────────────────────────────────────────────────────────────┘
```

### Isolated

VMs can communicate with each other but not outside:

```
┌─────────────────────────────────────────────────────────────┐
│                          Host                                │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           virbr1 (isolated)                          │   │
│   │              10.0.0.1/24                             │   │
│   │           No NAT, No external                        │   │
│   │                                                      │   │
│   │    ┌────────┐  ┌────────┐                           │   │
│   │    │ vnet0  │  │ vnet1  │                           │   │
│   └────┴───┬────┴──┴───┬────┴───────────────────────────┘   │
│            │           │                                     │
│   ┌────────▼────────┐ ┌▼───────────────┐                    │
│   │      VM1        │ │     VM2        │                    │
│   │    10.0.0.10    │ │   10.0.0.11    │                    │
│   └─────────────────┘ └────────────────┘                    │
│                                                              │
│   eth0 ─────────▶ Internet (VMs cannot access)             │
└─────────────────────────────────────────────────────────────┘
```

### Routed

VMs are on a separate subnet that's routed (not NAT'd):

```
External router knows 192.168.100.0/24 → Host
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│   Host (192.168.1.100)                                      │
│   Routes 192.168.100.0/24 via virbr0                       │
│                                                              │
│   virbr0 ─────▶ VM1 (192.168.100.10)                       │
│             └──▶ VM2 (192.168.100.11)                       │
└─────────────────────────────────────────────────────────────┘
```

## Managing Networks

### List Networks

```bash
virsh net-list --all
```

### View Network Details

```bash
virsh net-info default
virsh net-dumpxml default
```

### Network XML

Default network configuration:

```xml
<network>
  <name>default</name>
  <uuid>...</uuid>
  <forward mode='nat'>
    <nat>
      <port start='1024' end='65535'/>
    </nat>
  </forward>
  <bridge name='virbr0' stp='on' delay='0'/>
  <mac address='52:54:00:xx:xx:xx'/>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.122.2' end='192.168.122.254'/>
    </dhcp>
  </ip>
</network>
```

## Creating Networks

### NAT Network

```xml
<!-- nat-network.xml -->
<network>
  <name>nat-network</name>
  <forward mode='nat'/>
  <bridge name='virbr1'/>
  <ip address='10.0.0.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.0.0.100' end='10.0.0.200'/>
    </dhcp>
  </ip>
</network>
```

```bash
virsh net-define nat-network.xml
virsh net-start nat-network
virsh net-autostart nat-network
```

### Isolated Network

```xml
<!-- isolated-network.xml -->
<network>
  <name>isolated</name>
  <bridge name='virbr2'/>
  <!-- No forward mode = isolated -->
  <ip address='10.10.0.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.10.0.2' end='10.10.0.254'/>
    </dhcp>
  </ip>
</network>
```

### Bridged Network (Using Host Bridge)

```xml
<!-- bridged-network.xml -->
<network>
  <name>bridged</name>
  <forward mode='bridge'/>
  <bridge name='br0'/>
</network>
```

Requires host bridge to exist first (see [Bridged Networking](bridged.md)).

### Routed Network

```xml
<!-- routed-network.xml -->
<network>
  <name>routed</name>
  <forward mode='route'/>
  <bridge name='virbr3'/>
  <ip address='192.168.100.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.100.2' end='192.168.100.254'/>
    </dhcp>
  </ip>
</network>
```

## DHCP Configuration

### Static Leases

```xml
<ip address='192.168.122.1' netmask='255.255.255.0'>
  <dhcp>
    <range start='192.168.122.100' end='192.168.122.200'/>
    <host mac='52:54:00:aa:bb:cc' name='vm1' ip='192.168.122.10'/>
    <host mac='52:54:00:dd:ee:ff' name='vm2' ip='192.168.122.11'/>
  </dhcp>
</ip>
```

### Custom DHCP Options

```xml
<dhcp>
  <range start='192.168.122.100' end='192.168.122.200'/>
  <bootp file='/pxelinux.0' server='192.168.122.1'/>
</dhcp>
```

## DNS Configuration

libvirt runs dnsmasq for each NAT network:

### View dnsmasq Process

```bash
ps aux | grep dnsmasq
```

### DNS Forwarding

VMs use the host as DNS server (192.168.122.1).
Host dnsmasq forwards to system DNS.

### Custom DNS Entries

```xml
<dns>
  <host ip='192.168.122.10'>
    <hostname>vm1.local</hostname>
  </host>
  <host ip='192.168.122.11'>
    <hostname>vm2.local</hostname>
  </host>
</dns>
```

## Network Operations

### Start/Stop

```bash
virsh net-start default
virsh net-destroy default
```

### Autostart

```bash
virsh net-autostart default
virsh net-autostart default --disable
```

### Modify Network

```bash
# Edit (requires restart)
virsh net-edit default

# Or undefine and redefine
virsh net-destroy default
virsh net-undefine default
virsh net-define new-default.xml
virsh net-start default
```

### Delete Network

```bash
virsh net-destroy mynetwork
virsh net-undefine mynetwork
```

## VM Network Attachment

### At Creation

```bash
virt-install \
    --name myvm \
    --network network=default \
    ...
```

### Multiple NICs

```bash
virt-install \
    --name myvm \
    --network network=default \
    --network network=isolated \
    ...
```

### Attach to Running VM

```bash
virsh attach-interface myvm network default --model virtio --live
```

### Detach Interface

```bash
virsh detach-interface myvm network --mac 52:54:00:xx:xx:xx
```

## Troubleshooting

### Network Won't Start

```bash
# Check for errors
virsh net-start default 2>&1

# Check if bridge exists
ip link show virbr0

# Check dnsmasq
systemctl status libvirtd
journalctl -u libvirtd | grep dnsmasq
```

### VM Has No Network

```bash
# In VM, check interface
ip addr
ip route

# Check if connected to network
virsh domiflist myvm

# Check bridge
brctl show virbr0
```

### DNS Not Working in VM

```bash
# Check dnsmasq is running
ps aux | grep dnsmasq

# Test from host
dig @192.168.122.1 google.com

# Check VM's resolv.conf
cat /etc/resolv.conf
```
