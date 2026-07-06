# Incus UFW integration

!!! note "Summary page — the full treatment is in Incus networking"
    This is the networking-section summary of the Incus-vs-UFW firewall
    problem. The **detailed strategy** — why it happens, the exact
    `ufw route allow` rules, the ordering trap, proxy devices, and the
    two-tier example — lives in
    [Incus networking → the firewall problem](../../incus/networking.md#the-firewall-problem-incus-vs-ufw).
    Read that for depth; this page is the short version.

    This build runs **[Incus](../../incus/index.md)** (the community fork of
    LXD). The commands are the `incus` client and the bridge is `incusbr0`.

## The same problem as Docker

Like Docker, **Incus writes its own firewall rules** when
`ipv4.firewall: true` on a managed bridge. On Ubuntu 26.04 the backend is
**nftables** (UFW uses the nftables backend too). The conflict runs both
ways:

1. **UFW's default `FORWARD` policy is DROP** — which can block forwarded
   traffic to and from `incusbr0`, so instances lose internet or
   inter-instance connectivity even though Incus "set up" the bridge.
2. **Incus's own NAT rules can bypass UFW's filter chains** — the same reason
   `ufw-docker` exists for Docker; a naively-forwarded port could be reachable
   despite UFW.

## The fix: let UFW own filtering

This build hands the *filtering* decision to UFW (its single firewall
front-end) and leaves Incus doing only NAT.

### Step 1 — stop Incus managing the bridge firewall

```bash
incus network set incusbr0 ipv4.firewall false
incus network set incusbr0 ipv6.firewall false
```

NAT (`ipv4.nat`) still works; only the filtering is handed off.

### Step 2 — allow the bridge in UFW

`ufw route allow` is the modern UFW way to permit **forwarded** traffic
without hand-editing `before.rules` — it's what gets past
`DEFAULT_FORWARD_POLICY="DROP"`:

```bash
sudo ufw allow in on incusbr0
sudo ufw route allow in on incusbr0
sudo ufw route allow out on incusbr0
```

To be more restrictive, allow only what instances need from the host (DHCP +
DNS) and rely on `route allow` for the rest:

```bash
sudo ufw allow in on incusbr0 to any port 67 proto udp    # IPv4 DHCP
sudo ufw allow in on incusbr0 to any port 53              # DNS
```

### Step 3 — ensure IP forwarding is on

```bash
echo "net.ipv4.conf.all.forwarding=1" | sudo tee /etc/sysctl.d/99-incus-forwarding.conf
sudo systemctl restart systemd-sysctl
sysctl net.ipv4.conf.all.forwarding      # should be 1
```

### Step 4 — reload and verify

```bash
sudo ufw reload
sudo ufw status verbose

incus exec web -- ping -c2 1.1.1.1
```

!!! warning "Order matters — disable Incus's firewall before trusting UFW"
    If you add the UFW `route allow` rules but leave `ipv4.firewall: true`,
    two systems write forwarding/NAT rules for the same bridge and the
    interaction is hard to reason about. Do step 1 *before* relying on the
    UFW rules. Confirm with `sudo nft list ruleset` that Incus is no longer
    adding filter chains for `incusbr0`.

## Exposing a port: proxy device with `bind=host`

The recommended way to expose an instance service and keep it under UFW is a
**proxy device bound on the host** — the listener runs in the host's network
namespace, so standard UFW rules apply:

```bash
incus config device add web http proxy \
    listen=tcp:0.0.0.0:8080 \
    connect=tcp:127.0.0.1:80 \
    bind=host

sudo ufw allow from 192.168.0.0/24 to any port 8080 proto tcp
```

Prefer this over any direct-exposure trick — it's the one pattern that keeps
port exposure under UFW's control.

## Two-tier example (public front-end, internal back-end)

```bash
# Public web instance on incusbr0, exposed via a host-bound proxy
incus launch images:ubuntu/24.04 webserver
incus config device add webserver http proxy \
    listen=tcp:0.0.0.0:80 connect=tcp:127.0.0.1:80 bind=host
sudo ufw allow 80/tcp

# Internal-only DB tier (NAT off = no internet, no LAN)
incus network create backend ipv4.address=10.20.0.1/24 ipv4.nat=false ipv4.firewall=false
incus launch images:ubuntu/24.04 database
incus config device override database eth0 network=backend
# No proxy device = not reachable from outside
```

## Troubleshooting

```bash
# Instance can't reach the internet
incus network get incusbr0 ipv4.nat        # expect true
sysctl net.ipv4.conf.all.forwarding        # expect 1
sudo ufw status verbose                     # look for the route allow rules

# Two firewalls fighting
sudo nft list ruleset | less                # confirm no incus filter chains for incusbr0

# Proxy not reachable
incus config device show web | grep -A5 proxy
sudo ss -tlnp | grep 8080                   # host is listening (bind=host)
sudo ufw status | grep 8080
```

## See also

- [Incus networking](../../incus/networking.md) - the full firewall/bridge/Tailscale story.
- [Incus network overview](overview.md) - bridge, network types, exposing services.
- [UFW configuration](../ufw/configuration.md) - the host firewall this integrates with.
