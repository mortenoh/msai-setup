# Networking — the bridge, UFW, and Netplan

Incus's default networking is a managed bridge (`incusbr0`) that NATs instances out to the internet. That bridge has to be reconciled with three things this build already runs: **UFW** (nftables backend), **Netplan with the systemd-networkd renderer**, and **Tailscale** as the management plane. This page is the Incus equivalent of the `ufw-docker` problem — Incus, like Docker, inserts its own firewall rules, and you have to make UFW and Incus agree on who filters what.

## The default bridge: `incusbr0`

`incus admin init` created a managed bridge named `incusbr0`:

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
  ipv4.firewall: "true"          # <- Incus manages firewall rules for this bridge
  ipv6.firewall: "true"
```

What "managed" means:

- Incus runs a bridge interface `incusbr0` on the host.
- Instances attach to it via their `eth0` `nic` device (inherited from the `default` profile).
- Incus runs a built-in **DHCP + DNS** server (dnsmasq-style) on the bridge — instances get an IP automatically and resolve each other by name.
- With `ipv4.nat: true`, instance traffic is **masqueraded** out the host's uplink — instances reach the internet, but are **not reachable from the LAN** unless you forward ports.

```bash
# Watch an instance get a bridge IP
incus launch images:ubuntu/24.04 web
incus list                       # shows web's 10.x.x.x address
incus network info incusbr0      # bridge state, leases
```

## The firewall problem — Incus vs UFW

Just like Docker, **Incus writes its own firewall rules** when `ipv4.firewall: true`. On 26.04 the backend is **nftables** (UFW itself uses the nftables backend too). Incus's rules handle bridge forwarding, NAT masquerade, and letting instances reach the DHCP/DNS server.

The conflict, in both directions:

1. **UFW's default `FORWARD` policy is DROP.** If UFW is dropping forwarded traffic, it can block traffic to and from the Incus bridge — instances lose internet or inter-instance connectivity even though Incus "set up" the bridge.
2. **Incus's own NAT rules can bypass UFW's filter chains** — the same reason `ufw-docker` exists for Docker. A naively-forwarded instance port could be reachable despite UFW.

There are two clean strategies. This build uses **strategy A** (let UFW own filtering) because UFW is already this build's single firewall front-end.

### Inspect what Incus created

```bash
# See Incus's nftables rules
sudo nft list ruleset | less
# Look for an 'incus' table / chains handling incusbr0 forwarding and NAT

# UFW's forward policy (the usual culprit)
sudo grep DEFAULT_FORWARD_POLICY /etc/default/ufw
# DEFAULT_FORWARD_POLICY="DROP"  <- blocks bridge forwarding until you allow it
```

## Strategy A — let UFW own filtering (recommended)

Disable Incus's per-bridge firewall generation, then add explicit UFW rules for the bridge. This mirrors exactly how the [LXD UFW integration](../networking/lxc/ufw-integration.md) and [Docker UFW solutions](../networking/docker/ufw-solutions.md) pages handle the equivalent problem.

### Step 1 — stop Incus managing the bridge firewall

```bash
incus network set incusbr0 ipv4.firewall false
incus network set incusbr0 ipv6.firewall false
```

This tells Incus **not** to generate filtering rules for `incusbr0`. NAT (`ipv4.nat`) still works — you're only handing the *filtering* decision to UFW. (If you prefer, you can also disable Incus NAT and write the MASQUERADE rule yourself in `before.rules`, but leaving `ipv4.nat: true` and just disabling the firewall is simpler and is what this build does.)

### Step 2 — allow the bridge in UFW

These are the exact commands from the [official Incus firewall howto](https://linuxcontainers.org/incus/docs/main/howto/network_bridge_firewalld/):

```bash
# Allow traffic to the host on the bridge, and allow forwarding in/out of it
sudo ufw allow in on incusbr0
sudo ufw route allow in on incusbr0
sudo ufw route allow out on incusbr0
```

`ufw route allow` is the modern UFW way to permit **forwarded** traffic (the `FORWARD` chain) without hand-editing `before.rules` — it's the piece that gets past `DEFAULT_FORWARD_POLICY="DROP"`.

If you want to be more restrictive than "allow everything on the bridge," permit only what instances actually need from the host (DHCP + DNS) and rely on `route allow` for the rest:

```bash
sudo ufw allow in on incusbr0 to any port 67 proto udp    # IPv4 DHCP
sudo ufw allow in on incusbr0 to any port 547 proto udp   # IPv6 DHCP (if used)
sudo ufw allow in on incusbr0 to any port 53              # DNS (TCP + UDP)
```

### Step 3 — confirm forwarding is enabled

NAT needs kernel IP forwarding. Netplan/systemd-networkd may or may not have it on; set it explicitly:

```bash
echo "net.ipv4.conf.all.forwarding=1" | sudo tee /etc/sysctl.d/99-incus-forwarding.conf
sudo systemctl restart systemd-sysctl
sysctl net.ipv4.conf.all.forwarding      # should be 1
```

### Step 4 — reload and verify

```bash
sudo ufw reload
sudo ufw status verbose

# From inside an instance, confirm outbound works
incus exec web -- ping -c2 1.1.1.1
incus exec web -- getent hosts example.com
```

!!! warning "Order matters: disable Incus's firewall before trusting UFW"
    If you add the UFW `route allow` rules but leave `ipv4.firewall: true`, you have two systems writing forwarding/NAT rules for the same bridge and the interaction is hard to reason about. Do step 1 (disable Incus's per-bridge firewall) *before* relying on the UFW rules in step 2. Verify with `sudo nft list ruleset` that Incus is no longer adding its own filter chains for `incusbr0`.

## Exposing an instance service to the LAN

By default, NAT means instances are outbound-only. To reach an instance's service from the LAN there are two patterns.

### Pattern 1 — proxy device (recommended)

A `proxy` device forwards a host port to an instance port. With `bind=host`, the listener runs in the **host's** network namespace, so **UFW rules apply to it** — you keep one firewall front-end.

```bash
# Forward host port 8080 to the container's port 80
incus config device add web http proxy \
  listen=tcp:0.0.0.0:8080 \
  connect=tcp:127.0.0.1:80 \
  bind=host

# Now gate it with UFW like any host port
sudo ufw allow from 192.168.0.0/24 to any port 8080 proto tcp
```

Because the proxy binds on the host, this is the pattern that keeps port exposure *under UFW's control* — the direct analog of the [LXD proxy-device approach](../networking/lxc/ufw-integration.md). Prefer it for anything you deliberately expose.

### Pattern 2 — bridged onto the LAN (instance gets a LAN IP)

Instead of NAT, put the instance directly on the physical LAN so it gets its own DHCP address from your router. Attach the instance's NIC to a bridge over the physical interface rather than `incusbr0`:

```bash
# Create a bridge network parented to the host's LAN interface
# (interface name from `ip link` — this host has 10GbE Realtek ports)
incus network create lanbr --type=bridge \
  bridged.parent=<lan-iface> ipv4.dhcp=false ipv6.dhcp=false

# Or, more commonly, attach to an existing host bridge via a macvlan/bridged nic:
incus config device override web eth0 nictype=bridged parent=<host-bridge>
```

!!! note "Bridged-to-LAN reconciles with Netplan, not against it"
    If you go the bridged route, the cleanest arrangement on this build is to define the **host bridge in Netplan** (systemd-networkd renderer) and have Incus attach instances to it as an *unmanaged* bridge, rather than letting Incus and Netplan both try to own the same L2 interface. See [Netplan bridges](../netplan/interfaces/bridges.md) for the host-side bridge definition and [Netplan + LXD/LXC](../netplan/integration/lxd.md) for the integration pattern (it applies to Incus unchanged — same bridge semantics). For most services, the NAT-plus-proxy pattern above is less work and keeps everything behind UFW; reach for bridged-to-LAN only when an instance genuinely needs to be a first-class LAN citizen (e.g. it runs its own DHCP-dependent service discovery).

## Netplan and systemd-networkd

This build renders networking with **Netplan → systemd-networkd** (no NetworkManager). Incus's managed `incusbr0` is created and owned by **Incus**, not Netplan — the two don't fight as long as you let each own its own interfaces:

- **Netplan owns** the physical uplinks (the 10GbE ports), any host-level LAN bridge, and the host's own addressing. See [ubuntu/networking.md](../ubuntu/networking.md).
- **Incus owns** `incusbr0` and any Incus-managed bridge — do not declare `incusbr0` in Netplan.

The one seam is IP forwarding (handled in [strategy A step 3](#strategy-a-let-ufw-own-filtering-recommended) above) and, if you use a bridged-to-LAN setup, the host bridge — which *should* live in Netplan so it survives reboots and reconfigures predictably.

```bash
# Confirm who owns what
networkctl status                    # systemd-networkd's view (uplinks, host bridge)
incus network list                   # Incus's view (incusbr0)
ip -brief link                       # everything, together
```

## Tailscale reachability for instances

Tailscale is this build's [remote-management plane](../tailscale/index.md). Two ways instances become reachable over the tailnet:

### Option A — Tailscale on the host, subnet-router the bridge

Run Tailscale on the **host** (as this build already does) and advertise the `incusbr0` subnet as a [subnet route](../tailscale/features/subnet-routers.md). Tailnet peers can then reach instance IPs directly:

```bash
# On the host — advertise the Incus bridge subnet (use incusbr0's actual CIDR)
sudo tailscale up --advertise-routes=10.x.x.0/24
# Approve the route in the Tailscale admin console
```

Combined with the host's forwarding and the UFW `route allow` rules above, tailnet clients reach `10.x.x.<instance>` as if on the LAN. This is the lowest-effort option and keeps Tailscale in one place (the host).

### Option B — Tailscale inside an instance

For an instance that should be a first-class tailnet node (its own MagicDNS name, its own ACLs), install Tailscale *inside* it. A container needs `/dev/net/tun`, which nesting/appropriate config provides; the [Tailscale-in-containers guide](../tailscale/installation/containers.md) covers the device and userspace-networking options. Use this when an instance genuinely warrants its own tailnet identity (e.g. exposing a service via [Tailscale Serve](../tailscale/features/funnel-serve.md)); otherwise Option A is simpler.

!!! note "Manage Incus over Tailscale without exposing the API"
    You reach Incus remotely by **SSHing to the host over Tailscale** and running `incus` there against its local socket — *not* by binding the Incus HTTPS API to the network. This build deliberately left `core.https_address` unset (see [installation](installation.md)). The management plane is "Tailscale → SSH → host → `incus` on the local socket," which keeps the Incus API off every network.

## Multiple / isolated networks

For an instance (or group) that should have **no** internet access — a database tier, an air-gapped experiment — create a network with NAT off:

```bash
# Internal-only network: no NAT, no route out
incus network create internal ipv4.address=10.20.0.1/24 ipv4.nat=false ipv4.firewall=false

# Attach an instance to it instead of incusbr0
incus config device override db eth0 network=internal
```

Instances on `internal` can talk to each other but cannot reach the internet (no NAT) or the LAN. Pair a public front-end on `incusbr0` (with a proxy device) and a private back-end on `internal` for a classic two-tier split — the same structure as the [LXD complete example](../networking/lxc/ufw-integration.md).

## Troubleshooting quick hits

| Symptom | Check |
|---|---|
| Instance has no internet | `sysctl net.ipv4.conf.all.forwarding` (must be 1); `incus network get incusbr0 ipv4.nat` |
| Instance can't be reached even with a proxy | `sudo ufw status` for the host port; `bind=host` on the proxy device |
| Traffic blocked despite Incus "working" | UFW `DEFAULT_FORWARD_POLICY="DROP"` — add `ufw route allow in/out on incusbr0` |
| Two firewalls fighting | `sudo nft list ruleset` — confirm `ipv4.firewall false` on `incusbr0` |
| `incusbr0` vanished after reboot | it's Incus-managed, not Netplan — `incus network list`, restart `incus` |

Full networking troubleshooting is in [Troubleshooting](troubleshooting.md).

## Next steps

- [Containers](containers.md) — building the system containers that attach to this bridge.
- [Troubleshooting](troubleshooting.md) — networking failures in depth.
- [UFW configuration](../networking/ufw/configuration.md) — the host firewall this integrates with.
- [Tailscale subnet routers](../tailscale/features/subnet-routers.md) — reaching instances over the tailnet.
