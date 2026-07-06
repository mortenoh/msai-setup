# Installing Incus

This page installs Incus on Ubuntu Server 26.04, does the first-run initialization, and points Incus's storage backend at the `rpool/incus` dataset created during [disk partitioning](../ubuntu/installation/disk-partitioning.md).

Incus must be installed **directly on the host** — it needs the real kernel's namespaces, cgroups, and KVM. It is not nested inside anything itself.

## Package availability on 26.04

!!! note "Incus is in the Ubuntu archive on 24.04 and later"
    A native `incus` package ships in the Ubuntu archive from **24.04 LTS onward**, so on 26.04 `sudo apt install incus` is the default path — no third-party repository required. The [Zabbly repo](#alternative-zabblys-upstream-repo) below is only needed if you want upstream's newer builds or a feature the archive package was compiled without.

Verify what the archive offers before deciding:

```bash
apt policy incus
# Shows the candidate version available from the Ubuntu archive
```

### Default path — Ubuntu archive

```bash
sudo apt update
sudo apt install incus

# VM support needs QEMU as well — the archive incus package does not pull it in
sudo apt install qemu-system-x86 qemu-utils
```

`incus` (the daemon plus the CLI client) is enough for containers. VMs additionally need `qemu-system-x86` on this amd64 host; without it, `incus launch ... --vm` fails at start with a "QEMU not found" style error.

Enable and start the daemon socket:

```bash
sudo systemctl enable --now incus.socket
# On some packagings the unit is incus.service; check which exists:
systemctl list-unit-files | grep incus
```

### Alternative — Zabbly's upstream repo

[Zabbly](https://github.com/zabbly/incus) is the upstream project's own package repository, maintained by Incus's lead developer. Use it if the archive version lags a feature you need (OCI improvements and newer VM features land there first).

```bash
# Add Zabbly's signing key
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://pkgs.zabbly.com/key.asc -o /etc/apt/keyrings/zabbly.asc

# Add the repo (stable channel). Verify the current recommended snippet at
# https://github.com/zabbly/incus — the codename and channel format do change.
sudo sh -c 'cat > /etc/apt/sources.list.d/zabbly-incus-stable.sources <<EOF
Enabled: yes
Types: deb
URIs: https://pkgs.zabbly.com/incus/stable
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: main
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/zabbly.asc
EOF'

sudo apt update
sudo apt install incus
```

!!! warning "Verify the Zabbly snippet against upstream before pasting"
    Repository codenames, the `Suites` value, and the channel names on Zabbly change over time, and a 26.04 (`resolute`) suite may lag the release. Treat the block above as a template — pull the current exact instructions from [github.com/zabbly/incus](https://github.com/zabbly/incus). Do not mix the archive package and the Zabbly package; pick one source and stick to it, or `apt` dependency conflicts follow.

## Non-root access — the `incus-admin` group

By default only root can talk to the Incus daemon. Access control is by group membership: members of **`incus-admin`** get full control of the daemon.

```bash
# The package usually creates the group; create it if missing
getent group incus-admin || sudo groupadd incus-admin

# Add your admin user
sudo usermod -aG incus-admin "$USER"

# Apply the new group in the current shell without logging out
newgrp incus-admin

# Confirm you can reach the daemon without sudo
incus info | head
```

!!! danger "`incus-admin` is effectively root on the host"
    A member of `incus-admin` can launch privileged containers, add device passthroughs, and mount host paths — that is root-equivalent power. Grant it only to trusted admin accounts, exactly as you would `sudo`. There is also a read-only `incus` group in some packagings for restricted access; `incus-admin` is the full-control one.

## First-run initialization

`incus admin init` is the interactive setup wizard: it creates the initial storage pool, the default network bridge, and the `default` profile. Run it once after install.

```bash
sudo incus admin init
```

The interactive prompts, and the answers this build wants:

| Prompt | Answer for this build | Why |
|---|---|---|
| Would you like to use clustering? | `no` | single host |
| Do you want to configure a new storage pool? | `yes` | |
| Name of the new storage pool | `default` | |
| Name of the storage backend to use | `zfs` | native ZFS integration |
| Create a new ZFS pool? | **`no`** | reuse the existing `rpool` — see below |
| Name of the existing ZFS pool or dataset | `rpool/incus` | the dataset from disk-partitioning |
| Would you like to create a new network bridge? | `yes` | creates `incusbr0` |
| What IPv4 address should be used? | `auto` (or a fixed subnet) | see [Networking](networking.md) |
| What IPv6 address should be used? | `none` | this build is IPv4-internal for instances |
| Would you like the server to be available over the network? | `no` (manage via socket + Tailscale) | see note below |
| Would you like stale cached images to be updated automatically? | `yes` | |
| Would you like a YAML "incus admin init" preseed to be printed? | `yes` | keep it for rebuilds |

!!! note "Answer `no` to 'create a new ZFS pool'"
    This is the single most important answer. `rpool` already exists (it holds root and hot data), and the `rpool/incus` dataset was created for exactly this purpose in [disk partitioning](../ubuntu/installation/disk-partitioning.md). You are pointing Incus at an **existing dataset**, not asking it to create a new pool on a raw disk. Answering `yes` here would try to hand Incus a whole block device.

### The equivalent preseed file

For a reproducible rebuild, drive the same setup non-interactively. Save this as `incus-preseed.yaml`:

```yaml
config:
  images.auto_update_interval: "6"
storage_pools:
  - name: default
    driver: zfs
    config:
      source: rpool/incus
networks:
  - name: incusbr0
    type: bridge
    config:
      ipv4.address: auto
      ipv4.nat: "true"
      ipv6.address: none
profiles:
  - name: default
    devices:
      root:
        path: /
        pool: default
        type: disk
      eth0:
        name: eth0
        network: incusbr0
        type: nic
```

Apply it:

```bash
cat incus-preseed.yaml | sudo incus admin init --preseed
```

Keep this file in version control (it is the "recreate my Incus setup" artifact referenced by the [rebuild checklist](../operations/rebuild-checklist.md)). The `source: rpool/incus` line is what re-attaches Incus to its preserved datasets after a host rebuild — see [Storage](storage.md).

!!! warning "Managing Incus over the network"
    The wizard offers to bind the Incus API to a network address (`core.https_address`). This build declines it — Incus is managed through its **local Unix socket** on the host (reachable over SSH/Tailscale), never exposed as a network API on the LAN or internet. If you ever do enable it, bind it to the Tailscale interface only and require client certificates; a wide-open Incus API is a full host takeover. See [Networking](networking.md).

## Verify the install

```bash
# Daemon version and environment (storage backends, kernel features)
incus version
incus info

# The storage pool points at rpool/incus
incus storage list
incus storage show default

# The bridge exists
incus network list

# The default profile references the pool and bridge
incus profile show default

# Kernel is ready for containers (all should say available/enabled)
incus info | grep -iA20 'kernel_features'
```

Confirm the ZFS side agrees — Incus should have created its internal dataset layout under `rpool/incus`:

```bash
zfs list -r rpool/incus
# Expect child datasets like rpool/incus/containers, rpool/incus/virtual-machines,
# rpool/incus/images, rpool/incus/custom appearing as instances are created
```

## Smoke test

Launch a throwaway container, confirm it runs, then delete it:

```bash
incus launch images:ubuntu/24.04 smoke-test
incus list
incus exec smoke-test -- cat /etc/os-release
incus delete --force smoke-test
```

If that round-trips cleanly, Incus, the storage pool, and the bridge all work. Move on to [Core concepts](concepts.md).

## Next steps

- [Core concepts](concepts.md) — the mental model before you build anything real.
- [Storage](storage.md) — how `rpool/incus` becomes per-instance datasets.
- [Networking](networking.md) — reconciling `incusbr0` with UFW and Netplan.
