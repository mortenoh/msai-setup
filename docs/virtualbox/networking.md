# Networking

VirtualBox supports up to eight NICs per VM. For each NIC you pick a "type" that determines how the guest sees the network. This page covers all the modes, when to use each, and the operational details (port forwarding, DHCP, interface naming) you actually hit.

## NIC modes at a glance

| Mode | Guest reaches internet? | Host reaches guest? | Other guests reach guest? | Needs |
|---|---|---|---|---|
| **NAT** | Yes (via host NAT) | Only via port-forward | No (each NAT instance is private) | nothing |
| **NAT Network** | Yes | Only via port-forward | Yes (shared NAT) | `natnetwork` configured |
| **Bridged** | Yes (LAN router) | Yes (LAN IP) | Yes (same LAN) | Bridgeable host interface |
| **Host-only** | No | Yes | Yes (same vboxnetN) | host-only adapter configured |
| **Internal** | No | No | Yes (same intnet name) | nothing |
| **NAT Network** | Yes | Only via port-forward | Yes (shared) | named natnetwork |
| **Generic** | depends on plugin | depends | depends | a generic driver |
| **null/none** | No | No | No | nothing |

For the MS-S1 MAX lab on a Mac: **NAT** with port-forwarding. It works everywhere, doesn't require LAN cooperation, and doesn't expose VMs to the rest of your network by accident.

## NAT (default)

The simplest mode. Each NIC gets its own private NAT environment.

```bash
VBoxManage modifyvm test --nic1 nat
```

What the guest sees:

```
guest IP:        10.0.2.15           (assigned via DHCP)
gateway:         10.0.2.2            (the NAT, hosted by VirtualBox)
DNS:             10.0.2.3            (also VirtualBox; forwards to host's DNS)
file-share host: 10.0.2.4            (the host's filesystem, via Shared Folders)
host loopback:   10.0.2.2            (the host's loopback as seen from the guest)
```

The guest can reach the internet — VBox NATs outbound traffic via the host's regular networking. The host can NOT reach the guest directly — there's no IP on the host for "the NAT side of NIC1".

**To reach the guest you need a port-forward.**

### NAT port-forwarding

```bash
# Add a forward
VBoxManage modifyvm <vm> --natpf<N> "name,proto,host-ip,host-port,guest-ip,guest-port"
#                                    ^      ^     ^       ^         ^         ^
#                                    label  tcp/udp  ip on host (empty=all)  destination
```

Examples:

```bash
# SSH (local-host only, the lab's default)
VBoxManage modifyvm test --natpf1 "ssh,tcp,127.0.0.1,2222,,22"

# HTTP on all host interfaces
VBoxManage modifyvm test --natpf1 "http,tcp,,8080,,80"

# UDP — DNS for example
VBoxManage modifyvm test --natpf1 "dns,udp,127.0.0.1,15353,,53"

# Forward to a specific guest IP (rare — you usually leave the guest IP empty)
VBoxManage modifyvm test --natpf1 "rdp,tcp,127.0.0.1,3389,10.0.2.15,3389"
```

Delete:

```bash
VBoxManage modifyvm test --natpf1 delete ssh
```

View:

```bash
VBoxManage showvminfo test --machinereadable | grep '^Forwarding'
# Forwarding(0)="ssh,tcp,127.0.0.1,2222,,22"
```

Port-forwards work **while the VM is running** — no need to stop the VM to add or remove rules.

### NAT limitations

- Outbound only: a guest can connect outward, but other machines on your LAN can't connect inward without help.
- Bind to `127.0.0.1` (the lab default) so the forward isn't exposed on your other network interfaces.
- ICMP works for outbound ping but not all reply codes; UDP is fine.
- DHCP lease comes from VirtualBox; the guest's IP doesn't change between VBox restarts but isn't predictable.

## NAT Network

Like NAT, but multiple VMs share the same NAT instance and can talk to each other on a defined subnet.

```bash
# Create a NAT network
VBoxManage natnetwork add \
    --netname lab-net \
    --network 10.10.10.0/24 \
    --enable --dhcp on

# Attach a VM to it
VBoxManage modifyvm test --nic1 natnetwork --nat-network1 lab-net

# Port-forward (per network, not per VM):
VBoxManage natnetwork modify --netname lab-net \
    --port-forward-4 "ssh,tcp,127.0.0.1,2222,,22"

# Multiple VMs attached to lab-net can ping each other
```

Use this if you want a "private subnet" of multiple lab VMs that can talk to each other but still reach the internet. For a single lab VM, regular NAT is simpler.

## Bridged

The VM joins the host's LAN as if it were a physical machine — gets a real LAN IP via the LAN's DHCP server, visible to every other LAN client.

```bash
# Find a bridgeable interface
VBoxManage list bridgedifs | head -20

# Attach
VBoxManage modifyvm test \
    --nic1 bridged \
    --bridgeadapter1 "en0: Wi-Fi (AirPort)"   # macOS interface name
```

Pros:

- VM is reachable from anywhere on your LAN (or via VPN to your LAN).
- Multiple VMs can talk to each other and to the host with no extra config.
- Closer to "real hardware" semantics.

Cons:

- VM gets a LAN IP (random, from your router); on Wi-Fi some routers refuse bridged VBox NICs.
- Anyone on your LAN can probe the VM. Make sure UFW is on inside the guest.
- Apple Silicon + Wi-Fi can be flaky with bridged mode; wired works better.

For the lab: stick with NAT unless you specifically want LAN visibility (e.g. testing a service that other LAN clients connect to). Then bridged + UFW inside the VM.

## Host-only

A private network between the host and a set of VMs, with no internet connectivity.

```bash
# Create a host-only adapter
VBoxManage hostonlyif create
# Created host-only adapter 'vboxnet0'

# Configure its IP/subnet
VBoxManage hostonlyif ipconfig vboxnet0 \
    --ip 192.168.56.1 --netmask 255.255.255.0

# Attach VM
VBoxManage modifyvm test --nic1 hostonly --hostonlyadapter1 vboxnet0
```

The guest gets a 192.168.56.x address (via DHCP if `--dhcp on` was set, otherwise static config inside the guest).

Use case: VMs that the host needs to reach but that should NOT have internet access (sensitive test environments).

You can combine NIC1=NAT (for internet) and NIC2=hostonly (for host-direct access) to get both.

## Internal

Like host-only but the host itself is also excluded. Multiple VMs on the same internal-network name talk only to each other.

```bash
VBoxManage modifyvm vm1 --nic1 intnet --intnet1 my-private
VBoxManage modifyvm vm2 --nic1 intnet --intnet1 my-private
```

Use case: simulating air-gapped networks, multi-VM lab topologies (e.g. a fake "DMZ" + "internal" pair).

## Multiple NICs

A VM can have up to 8 NICs, each in its own mode:

```bash
VBoxManage modifyvm test \
    --nic1 nat \                          # internet
    --natpf1 "ssh,tcp,127.0.0.1,2222,,22" \
    --nic2 hostonly --hostonlyadapter2 vboxnet0 \   # host-direct
    --nic3 intnet --intnet3 fake-dmz       # internal sim
```

The guest sees three interfaces (`enp0s3`, `enp0s8`, `enp0s9` or similar — VirtualBox-only PCI slot numbering). Configure routing inside the guest to taste.

## NIC types (the chip emulated)

Per NIC, you can pick the virtual hardware:

```bash
VBoxManage modifyvm test --nictype1 virtio
```

| Type | What | Use |
|---|---|---|
| `Am79C970A` | AMD PCnet PCI II (old) | Very old guests |
| `Am79C973` | AMD PCnet-FAST III | Old guests |
| `82540EM` | Intel PRO/1000 MT Desktop | Default; works everywhere |
| `82543GC` | Intel PRO/1000 T Server | (rare) |
| `82545EM` | Intel PRO/1000 MT Server | Some Windows variants |
| `virtio` | virtio-net | **Best perf** on modern Linux guests |

For lab Linux VMs: `virtio` if you want max throughput. The default (`82540EM`) works everywhere and is fine for SSH-and-Ansible loads.

## Inside the guest — interface naming

Modern Ubuntu uses `systemd-networkd` predictable interface names:

| Old (kernel-assigned) | systemd-predictable | What |
|---|---|---|
| `eth0` | `enp0s3` | First VirtualBox NIC (PCI slot 3) |
| `eth1` | `enp0s8` | Second VBox NIC |
| `eth2` | `enp0s9` | Third VBox NIC |

The lab's cloud-init `user-data` configures **both** `enp0s3` and `eth0` to DHCP, so it works regardless of which name the guest's networking stack uses.

## Operational tips

### See the VM's actual IP

NAT mode: the guest has 10.0.2.15 but the host can't ping it directly (no route). Inside the VM:

```bash
ip -br addr
hostname -I
```

Bridged / host-only mode: same as the LAN-IP world. `ip addr` inside the VM, or VBox can tell you from outside:

```bash
VBoxManage guestproperty get test /VirtualBox/GuestInfo/Net/0/V4/IP
# (requires Guest Additions in the guest)
```

### Test connectivity from outside

```bash
# NAT + port-forward: hit the host port
curl http://127.0.0.1:8080

# Bridged / host-only: hit the LAN IP directly
curl http://192.168.1.123
```

### Cap NIC bandwidth (rare)

```bash
VBoxManage modifyvm test --nicbandwidthgroup1 limit10mbps
VBoxManage bandwidthctl test add limit10mbps --type network --limit 10M
```

Useful for testing bandwidth-sensitive software in degraded conditions.

## Lab network setup (reference)

`msai create` configures the simplest workable setup:

```
NIC 1:  NAT
        Port forward: 127.0.0.1:2222 -> guest 22 (SSH)
NIC 2-8: not configured
```

This is enough for everything the lab does. The VM can:

- Reach the internet (apt update, docker pull, anything).
- Be reached on host port 2222 for SSH (the `msai ssh` command).
- NOT be reached from your LAN (intentional — lab VMs are throwaway, don't expose them).

If you wanted to test "real" services from your LAN, switch NIC 1 to bridged. The Ansible playbooks don't care which mode you use — they target whatever the inventory says the host IP is.

## See also

- [VMs](vms.md) — modifyvm flags for NIC configuration
- [Headless operation](headless.md) — VRDE uses similar IP-binding concepts
- [Apple Silicon](apple-silicon.md) — Wi-Fi + bridged mode caveat on macOS
