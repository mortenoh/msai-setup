# Network Performance Tuning

## Overview

Network performance tuning optimizes throughput, latency, and reliability. Key areas:

- MTU and jumbo frames
- Ring buffers
- Offload features
- TCP/IP stack tuning
- Interrupt handling

## MTU Configuration

### Standard MTU

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      mtu: 1500            # Standard Ethernet MTU
```

### Jumbo Frames

For high-performance storage/backup networks:

```yaml
network:
  version: 2
  ethernets:
    # Standard for internet traffic
    eth0:
      addresses:
        - 192.168.1.100/24
      mtu: 1500

    # Storage network with jumbo frames
    eth1:
      addresses:
        - 10.0.0.100/24
      mtu: 9000
```

!!! warning "Jumbo Frame Requirements"
    All devices in the path must support the same MTU:
    - Network switches
    - All hosts
    - Any bridges/bonds

### Testing MTU

```bash
# Test if jumbo frames work
ping -M do -s 8972 10.0.0.1

# -M do = don't fragment
# -s 8972 = 9000 - 28 (IP + ICMP headers)
```

### Path MTU Discovery

```bash
# Find optimal MTU to destination
tracepath 10.0.0.1 | grep pmtu
```

## Ring Buffers

Increase network buffer sizes for high traffic:

### Check Current Settings

```bash
ethtool -g eth0
```

### Configure in Netplan

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      receive-buffer-size: 4096
      transmit-buffer-size: 4096
```

### Alternative: ethtool

```bash
# Set ring buffers
ethtool -G eth0 rx 4096 tx 4096
```

## Hardware Offloading

Let the NIC handle certain operations:

### Check Current Offload Settings

```bash
ethtool -k eth0
```

### Configure Offloading

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      # Checksum offloading
      receive-checksum-offload: true
      transmit-checksum-offload: true
      # Segmentation offloading
      tcp-segmentation-offload: true
      generic-segmentation-offload: true
      # Receive offloading
      generic-receive-offload: true
      large-receive-offload: false    # Often causes issues
```

### When to Disable Offloading

Disable for:
- Packet capture/analysis
- Some virtualization scenarios
- When debugging network issues

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      receive-checksum-offload: false
      transmit-checksum-offload: false
      tcp-segmentation-offload: false
```

## TCP/IP Stack Tuning

### Sysctl Network Settings

Create `/etc/sysctl.d/60-network-performance.conf`:

```ini
# Increase socket buffer sizes
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 31457280
net.core.wmem_default = 31457280

# TCP buffer sizes
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# Increase connection tracking
net.core.netdev_max_backlog = 30000
net.core.somaxconn = 65535

# TCP congestion control
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# Enable TCP window scaling
net.ipv4.tcp_window_scaling = 1

# Reduce TIME_WAIT connections
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# Increase local port range
net.ipv4.ip_local_port_range = 1024 65535

# Disable slow start after idle
net.ipv4.tcp_slow_start_after_idle = 0

# Enable TCP Fast Open
net.ipv4.tcp_fastopen = 3
```

Apply:

```bash
sysctl -p /etc/sysctl.d/60-network-performance.conf
```

### BBR Congestion Control

Better bottleneck bandwidth:

```bash
# Check available algorithms
sysctl net.ipv4.tcp_available_congestion_control

# Enable BBR (if available)
echo "net.ipv4.tcp_congestion_control = bbr" >> /etc/sysctl.d/60-network-performance.conf
echo "net.core.default_qdisc = fq" >> /etc/sysctl.d/60-network-performance.conf
sysctl -p
```

## Interrupt Handling

### Check Interrupt Affinity

```bash
# View interrupts per CPU
cat /proc/interrupts | grep eth0

# Check current affinity
cat /proc/irq/*/smp_affinity_list | head
```

### Distribute Interrupts

For multi-queue NICs:

```bash
# Set affinity for each queue to different CPUs
echo 1 > /proc/irq/IRQ_NUMBER_1/smp_affinity_list
echo 2 > /proc/irq/IRQ_NUMBER_2/smp_affinity_list
echo 3 > /proc/irq/IRQ_NUMBER_3/smp_affinity_list
echo 4 > /proc/irq/IRQ_NUMBER_4/smp_affinity_list
```

### Use irqbalance

Let the system balance automatically:

```bash
# Install and enable
apt install irqbalance
systemctl enable --now irqbalance
```

## Network Queue Configuration

### Check Queues

```bash
# Number of queues
ethtool -l eth0

# Current queue settings
ethtool -n eth0
```

### Set Queue Count

```bash
# Set to number of CPUs
ethtool -L eth0 combined $(nproc)
```

### Flow Steering (RFS)

```bash
# Enable RFS
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries

# Per-queue setting
for i in /sys/class/net/eth0/queues/rx-*/rps_flow_cnt; do
    echo 32768 > $i
done
```

## Bond Performance

### LACP with Hash Policy

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
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        transmit-hash-policy: layer3+4    # Best load distribution
        mii-monitor-interval: 100
```

### Hash Policies

| Policy | Distribution Based On |
|--------|----------------------|
| layer2 | Source/dest MAC |
| layer2+3 | MAC + IP |
| layer3+4 | IP + port (best for most cases) |
| encap2+3 | Inner MAC + IP |
| encap3+4 | Inner IP + port |

## Benchmark and Testing

### iperf3

```bash
# Server
iperf3 -s

# Client
iperf3 -c server-ip

# Parallel streams
iperf3 -c server-ip -P 10

# Reverse mode
iperf3 -c server-ip -R

# UDP test
iperf3 -c server-ip -u -b 10G
```

### netperf

```bash
# Install
apt install netperf

# Server
netserver

# Client - TCP throughput
netperf -H server-ip

# Latency test
netperf -H server-ip -t TCP_RR
```

### ethtool Statistics

```bash
# View interface statistics
ethtool -S eth0

# Watch specific counters
watch -n 1 'ethtool -S eth0 | grep -E "rx_|tx_|err|drop"'
```

## Monitoring Performance

### Real-time Bandwidth

```bash
# Install nload
apt install nload
nload eth0

# Or iftop
apt install iftop
iftop -i eth0

# Or bmon
apt install bmon
bmon
```

### Interface Statistics

```bash
# Quick view
ip -s link show eth0

# Per-second rates
sar -n DEV 1

# Historical data
vnstat -i eth0
```

### Check for Errors

```bash
# Errors and drops
netstat -i
ip -s link show eth0 | grep -E "errors|dropped|overrun"

# Detailed
ethtool -S eth0 | grep -i error
```

## Performance Troubleshooting

### High CPU on Network

```bash
# Check softirq load
cat /proc/softirqs | head

# Check for single CPU bottleneck
mpstat -P ALL 1

# Solution: Enable RSS/RFS or irqbalance
```

### Packet Drops

```bash
# Check ring buffer overruns
ethtool -S eth0 | grep -i drop

# Solution: Increase ring buffers
ethtool -G eth0 rx 4096 tx 4096
```

### High Latency

```bash
# Check for bufferbloat
ping -f target     # Flood ping

# Check TCP congestion
ss -tin

# Solution: Enable BBR, tune buffers
```

### Low Throughput

```bash
# Check for negotiated speed
ethtool eth0 | grep Speed

# Check MTU matches
ping -M do -s 1472 target

# Check for errors
ethtool -S eth0 | grep err
```

## Complete Performance Config

```yaml
# /etc/netplan/00-performance.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Internet-facing (standard MTU)
    enp5s0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      mtu: 1500
      receive-checksum-offload: true
      transmit-checksum-offload: true
      tcp-segmentation-offload: true
      generic-segmentation-offload: true
      generic-receive-offload: true

    # Storage network (jumbo frames)
    enp6s0:
      addresses:
        - 10.0.0.100/24
      mtu: 9000
      receive-checksum-offload: true
      transmit-checksum-offload: true
      tcp-segmentation-offload: true
      generic-segmentation-offload: true
      generic-receive-offload: true
```

Combined with sysctl tuning for maximum performance.
