# Incus network overview

!!! note "This build uses Incus — the fuller networking guide is in the Incus section"
    This page is the networking-section summary of how container/VM
    networking works on this build. The **detailed, canonical treatment** —
    the `incusbr0` bridge, UFW forwarding integration (the `ufw-docker`
    equivalent), Netplan/systemd-networkd ownership, Tailscale reachability —
    lives in [Incus networking](../../incus/networking.md). Read that for
    depth; this page is the quick orientation and points into it.

    An earlier draft of these pages was written against LXD (and blurred LXD
    with classic LXC's `lxc-*` tools). This build runs **[Incus](../../incus/index.md)**,
    the community fork of LXD. The commands here are the `incus` client
    accordingly — same concepts LXD used, `incus` in place of `lxc`.

## The one tool, the one bridge

Incus manages instance networking through a **managed bridge**, created by
`incus admin init` and named **`incusbr0`** on this build. It NATs instances
out to the internet and runs a built-in DHCP/DNS server on the bridge, so
instances get an address automatically and resolve each other by name.

```bash
incus network list
incus network show incusbr0
```

```yaml
name: incusbr0
type: bridge
config:
  ipv4.address: 10.x.x.1/24     # auto-generated subnet
  ipv4.nat: "true"
  ipv6.address: none
  ipv4.firewall: "true"          # Incus manages firewall rules for this bridge
managed: true
status: Created
```

With `ipv4.nat: true`, instances reach the internet but are **not reachable
from the LAN** unless you forward ports (see [exposing a service](#exposing-a-service),
below).

## Network types

### Managed bridge (default)

```text
┌──────────────────────────────────────────────────────────────┐
│                            Host                                │
│                                                               │
│   ┌──────────────────────────────────────────────────────┐   │
│   │              incusbr0 bridge                          │   │
│   │              10.x.x.1/24  (managed by Incus)          │   │
│   │              built-in DHCP + DNS                      │   │
│   │    ┌────────┐  ┌────────┐                            │   │
│   │    │ veth0  │  │ veth1  │                            │   │
│   └────┴───┬────┴──┴───┬────┴────────────────────────────┘   │
│            │           │                                      │
│   ┌────────v────────┐ ┌v───────────────┐                     │
│   │   Instance 1    │ │   Instance 2   │                     │
│   │   10.x.x.10     │ │   10.x.x.11    │                     │
│   └─────────────────┘ └────────────────┘                     │
│                                                               │
│   uplink (10GbE) ────────────────────────> Internet          │
│   NAT: 10.x.x.0/24 masquerade                                │
└──────────────────────────────────────────────────────────────┘
```

### Bridged onto the LAN

To give an instance its own LAN IP (from your router's DHCP) instead of NAT,
attach it to a bridge over the physical interface rather than `incusbr0`. On
this build the host-side bridge should be defined in **Netplan** and attached
to by Incus as an unmanaged bridge, so Netplan and Incus don't both try to
own the same L2 interface. The full pattern is in
[Incus networking → bridged onto the LAN](../../incus/networking.md#pattern-2-bridged-onto-the-lan-instance-gets-a-lan-ip).

### Internal-only (no internet)

For a database tier or an air-gapped experiment, create a network with NAT
off:

```bash
incus network create internal ipv4.address=10.20.0.1/24 ipv4.nat=false ipv4.firewall=false
incus config device override db eth0 network=internal
```

Instances on `internal` reach each other but not the internet or the LAN.

## Managing networks

```bash
# List / inspect
incus network list
incus network show incusbr0
incus network info incusbr0          # live state, DHCP leases

# Create a managed bridge with explicit config
incus network create mynet \
    ipv4.address=10.20.0.1/24 \
    ipv4.nat=true \
    ipv6.address=none

# Edit
incus network edit incusbr0
incus network set incusbr0 ipv4.address 10.x.x.1/24

# Delete
incus network delete mynet
```

## Attaching instances

Instances inherit an `eth0` NIC on `incusbr0` from the `default` profile.
To attach explicitly or add a second interface:

```bash
# At launch, onto a specific network
incus launch images:ubuntu/24.04 web --network incusbr0

# Add a second NIC on another network
incus config device add web eth1 nic network=mynet

# Override a static IP on the inherited NIC
incus config device override web eth0 ipv4.address=10.x.x.50
```

## Exposing a service

By default NAT means instances are outbound-only. The recommended way to
reach an instance service from the LAN is a **proxy device with
`bind=host`** — the listener runs in the host's network namespace, so UFW
rules apply to it and you keep one firewall front-end:

```bash
incus config device add web http proxy \
    listen=tcp:0.0.0.0:8080 \
    connect=tcp:127.0.0.1:80 \
    bind=host

sudo ufw allow from 192.168.0.0/24 to any port 8080 proto tcp
```

This, and the UFW forwarding rules the bridge needs, are covered in depth on
the [Incus networking page](../../incus/networking.md) and summarized in
[UFW integration](ufw-integration.md).

## DNS resolution

Instances on `incusbr0` resolve each other by name through Incus's built-in
DNS:

```bash
incus exec web -- ping -c1 db          # short name resolves on the bridge
```

## Troubleshooting quick hits

```bash
# Instance has no network — check its devices and the bridge
incus config device show web
incus network list

# From inside the instance
incus exec web -- ip addr
incus exec web -- ip route

# NAT / forwarding (the usual culprits)
incus network get incusbr0 ipv4.nat
sysctl net.ipv4.conf.all.forwarding    # must be 1
```

Full networking troubleshooting — including the UFW `DEFAULT_FORWARD_POLICY`
trap — is in [Incus networking](../../incus/networking.md#troubleshooting-quick-hits)
and [Incus troubleshooting](../../incus/troubleshooting.md).

## See also

- [Incus networking](../../incus/networking.md) - the full bridge/UFW/Netplan/Tailscale story.
- [UFW integration](ufw-integration.md) - the firewall-specific summary.
- [Incus containers](../../incus/containers.md) - building the instances that attach to the bridge.
