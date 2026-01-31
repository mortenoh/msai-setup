# Network Namespaces

## What are Network Namespaces?

Network namespaces provide isolation of network resources. Each namespace has its own:

- Network interfaces
- IP addresses
- Routing tables
- Firewall rules (iptables/nftables)
- Sockets
- /proc/net

This is the foundation of container networking.

## Default Namespace

All processes start in the default (init) namespace:

```bash
# View processes in default namespace
ls -la /proc/1/ns/net

# Your processes share this namespace
ls -la /proc/$$/ns/net
```

## Creating Namespaces

### Using ip Command

```bash
# Create namespace
sudo ip netns add isolated

# List namespaces
ip netns list

# Delete namespace
sudo ip netns delete isolated
```

### Namespace Persistence

Created namespaces persist until deleted or system reboot:

```bash
# Namespaces are stored here
ls /var/run/netns/
```

## Executing Commands in Namespaces

```bash
# Run command in namespace
sudo ip netns exec isolated ip addr

# Interactive shell
sudo ip netns exec isolated bash

# Check current namespace
readlink /proc/$$/ns/net
```

## Network Interface Types

### VETH Pairs

Virtual ethernet pairs connect namespaces:

```
┌───────────────────┐          ┌───────────────────┐
│   Host Namespace  │          │ Container Namespace│
│                   │          │                    │
│   ┌─────────┐    │          │    ┌─────────┐    │
│   │  veth0  │◄───┼──────────┼───►│  veth1  │    │
│   └─────────┘    │          │    └─────────┘    │
│                   │          │                    │
└───────────────────┘          └───────────────────┘
```

```bash
# Create veth pair
sudo ip link add veth0 type veth peer name veth1

# Move one end to namespace
sudo ip link set veth1 netns isolated

# Configure host end
sudo ip addr add 10.0.0.1/24 dev veth0
sudo ip link set veth0 up

# Configure namespace end
sudo ip netns exec isolated ip addr add 10.0.0.2/24 dev veth1
sudo ip netns exec isolated ip link set veth1 up
sudo ip netns exec isolated ip link set lo up

# Test connectivity
ping 10.0.0.2
sudo ip netns exec isolated ping 10.0.0.1
```

### Bridge Connection

Multiple namespaces can connect to a bridge:

```
┌───────────────────────────────────────────────────┐
│                   Host Namespace                   │
│                                                    │
│   ┌────────────────────────────────────────────┐  │
│   │              br0 (bridge)                   │  │
│   │    ┌─────┐   ┌─────┐   ┌─────┐             │  │
│   │    │veth0│   │veth2│   │veth4│             │  │
│   └────┴──┬──┴───┴──┬──┴───┴──┬──┴─────────────┘  │
│           │         │         │                    │
└───────────┼─────────┼─────────┼────────────────────┘
            │         │         │
            ▼         ▼         ▼
      ┌─────────┐ ┌─────────┐ ┌─────────┐
      │  ns1    │ │  ns2    │ │  ns3    │
      │ veth1   │ │ veth3   │ │ veth5   │
      └─────────┘ └─────────┘ └─────────┘
```

```bash
# Create bridge
sudo ip link add br0 type bridge
sudo ip link set br0 up
sudo ip addr add 10.0.0.1/24 dev br0

# Create namespace and veth
sudo ip netns add ns1
sudo ip link add veth0 type veth peer name veth1

# Connect to bridge and namespace
sudo ip link set veth0 master br0
sudo ip link set veth0 up
sudo ip link set veth1 netns ns1
sudo ip netns exec ns1 ip addr add 10.0.0.2/24 dev veth1
sudo ip netns exec ns1 ip link set veth1 up
sudo ip netns exec ns1 ip link set lo up

# Add default route in namespace
sudo ip netns exec ns1 ip route add default via 10.0.0.1
```

## Internet Access from Namespace

### Enable Forwarding

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

### Add NAT

```bash
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

### Complete Example

```bash
#!/bin/bash

# Create isolated namespace with internet access
NAMESPACE="webserver"
BRIDGE="br-internal"
VETH_HOST="veth-${NAMESPACE}-h"
VETH_NS="veth-${NAMESPACE}"
IP_HOST="10.100.0.1"
IP_NS="10.100.0.2"
SUBNET="10.100.0.0/24"

# Create namespace
ip netns add $NAMESPACE

# Create bridge (if not exists)
ip link show $BRIDGE &>/dev/null || {
    ip link add $BRIDGE type bridge
    ip addr add ${IP_HOST}/24 dev $BRIDGE
    ip link set $BRIDGE up
}

# Create veth pair
ip link add $VETH_HOST type veth peer name $VETH_NS

# Connect host end to bridge
ip link set $VETH_HOST master $BRIDGE
ip link set $VETH_HOST up

# Move namespace end
ip link set $VETH_NS netns $NAMESPACE

# Configure namespace
ip netns exec $NAMESPACE ip addr add ${IP_NS}/24 dev $VETH_NS
ip netns exec $NAMESPACE ip link set $VETH_NS up
ip netns exec $NAMESPACE ip link set lo up
ip netns exec $NAMESPACE ip route add default via $IP_HOST

# Enable forwarding and NAT
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -s $SUBNET ! -o $BRIDGE -j MASQUERADE
iptables -A FORWARD -i $BRIDGE -j ACCEPT
iptables -A FORWARD -o $BRIDGE -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

echo "Namespace $NAMESPACE ready"
echo "Test: ip netns exec $NAMESPACE ping 8.8.8.8"
```

## Firewall Rules in Namespaces

Each namespace has its own iptables:

```bash
# View rules in namespace
sudo ip netns exec isolated iptables -L -n

# Add rule in namespace
sudo ip netns exec isolated iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# These are completely independent of host rules
```

## How Docker Uses Namespaces

Docker creates a namespace per container:

```bash
# Find container's namespace
CONTAINER_PID=$(docker inspect -f '{{.State.Pid}}' container_name)

# Enter container's network namespace
nsenter -t $CONTAINER_PID -n ip addr

# Or find namespace file
ls -la /proc/$CONTAINER_PID/ns/net
```

### Docker's Network Model

```
┌─────────────────────────────────────────────────────────────┐
│                      Host Namespace                          │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  docker0 bridge                        │  │
│  │     172.17.0.1/16                                     │  │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐              │  │
│  │   │veth1234 │  │veth5678 │  │veth9abc │              │  │
│  └───┴────┬────┴──┴────┬────┴──┴────┬────┴──────────────┘  │
│           │            │            │                       │
│           │            │            │                       │
│  ┌────────▼────────┐ ┌─▼──────────┐ ┌▼───────────────┐     │
│  │ Container1 NS   │ │Container2  │ │Container3 NS   │     │
│  │ eth0            │ │eth0        │ │eth0            │     │
│  │ 172.17.0.2      │ │172.17.0.3  │ │172.17.0.4      │     │
│  └─────────────────┘ └────────────┘ └────────────────┘     │
│                                                              │
│  NAT: 172.17.0.0/16 -> eth0 (masquerade)                    │
└─────────────────────────────────────────────────────────────┘
```

## How libvirt Uses Namespaces

VMs don't use network namespaces in the same way (they're fully isolated), but libvirt's NAT networking is similar:

```
┌─────────────────────────────────────────────────────────────┐
│                      Host Namespace                          │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  virbr0 bridge                         │  │
│  │     192.168.122.1/24                                   │  │
│  │   ┌─────────┐  ┌─────────┐                            │  │
│  │   │vnet0    │  │vnet1    │  (tap devices)             │  │
│  └───┴────┬────┴──┴────┬────┴────────────────────────────┘  │
│           │            │                                     │
│           │            │                                     │
│  ┌────────▼────────┐ ┌─▼──────────────┐                     │
│  │ VM1 (qemu)      │ │ VM2 (qemu)     │                     │
│  │ virtio-net      │ │ virtio-net     │                     │
│  │ 192.168.122.10  │ │ 192.168.122.11 │                     │
│  └─────────────────┘ └────────────────┘                     │
│                                                              │
│  NAT: 192.168.122.0/24 -> eth0 (masquerade)                 │
└─────────────────────────────────────────────────────────────┘
```

## How LXC Uses Namespaces

LXC containers use namespaces like Docker:

```bash
# List LXD containers with network info
lxc list

# Find container's namespace
lxc info container_name | grep PID
# Then use nsenter as with Docker
```

## Namespace Inspection Tools

### nsenter

```bash
# Enter all namespaces of a process
nsenter -t $PID -a

# Enter only network namespace
nsenter -t $PID -n

# Enter network namespace and run command
nsenter -t $PID -n ip addr
```

### lsns

```bash
# List all namespaces
lsns

# List network namespaces only
lsns -t net

# Show processes in namespace
lsns -t net -p $PID
```

### /proc/*/ns/

```bash
# Each process has namespace links
ls -la /proc/1/ns/

# Compare namespaces
readlink /proc/1/ns/net
readlink /proc/$$/ns/net

# If same, processes share namespace
```

## Troubleshooting

### Namespace Won't Delete

```bash
# Check for processes in namespace
ip netns pids namespace_name

# Force delete (may fail)
ip netns delete namespace_name

# If that fails, find and kill processes
for pid in $(ip netns pids namespace_name); do
    kill $pid
done
ip netns delete namespace_name
```

### Can't Ping from Namespace

```bash
# Check routes
ip netns exec ns1 ip route

# Check firewall
ip netns exec ns1 iptables -L

# Check host forwarding
cat /proc/sys/net/ipv4/ip_forward

# Check host NAT
iptables -t nat -L POSTROUTING -n -v
```

### Container Can't Reach Internet

```bash
# In container namespace:
# 1. Check IP
ip addr

# 2. Check gateway
ip route

# 3. Test gateway
ping <gateway_ip>

# 4. Test DNS
cat /etc/resolv.conf
nslookup google.com

# On host:
# 5. Check forwarding
sysctl net.ipv4.ip_forward

# 6. Check NAT
iptables -t nat -L -n -v

# 7. Check FORWARD chain
iptables -L FORWARD -n -v
```

## Security Implications

### Namespace Isolation

Namespaces provide isolation, not security:

- Processes can't see other namespaces' resources
- But CAP_NET_ADMIN in a namespace allows full control
- Root processes can access any namespace

### Firewall Independence

!!! warning "Important"
    Namespace firewall rules don't apply to traffic from the host or other namespaces.

Traffic flow:

1. Container sends packet
2. Leaves container namespace (container's iptables applies)
3. Enters host namespace via veth
4. Host's iptables applies
5. If forwarding, enters FORWARD chain
6. Exits via NAT (POSTROUTING)

### Bridge Filtering

```bash
# When bridge-nf-call-iptables is 1 (default):
# Bridged traffic is filtered by iptables FORWARD chain

cat /proc/sys/net/bridge/bridge-nf-call-iptables

# This is why Docker traffic goes through host iptables
# And why UFW rules don't work for containers by default
```
