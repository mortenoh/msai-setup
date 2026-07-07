# Core concepts

This page is the mental model. The rest of the section assumes you understand these seven ideas: **instances** (containers and VMs), **images**, **profiles**, **storage pools**, **networks**, **devices**, and **projects**. Skim it once before building anything real.

## Instances: containers vs VMs

An **instance** is the unit Incus manages. There are two types, and one CLI drives both.

### System containers

A **system container** is a full Linux userland — its own init (systemd), its own package manager, its own users, ssh-able if you install `sshd` — that **shares the host kernel**. It is not a single-process sandbox like a Docker container; it looks and feels like a small VM you can `apt install` inside.

- Near-zero overhead (no hypervisor, no guest kernel).
- Boots in well under a second.
- Cannot run a different kernel from the host, cannot boot a non-Linux OS.
- This is where **nested Docker** stacks run on this build (see [Containers](containers.md)).

```bash
incus launch images:ubuntu/24.04 web        # a system container named "web"
```

### Virtual machines

A **VM** is a QEMU/KVM guest with its own kernel and emulated hardware. Full isolation, can run Windows or a different Linux kernel, supports TPM 2.0 and Secure Boot.

- Real hardware virtualization overhead (modest on this Zen 5 host).
- Boots like a real machine (firmware, bootloader, kernel).
- Runs any OS: Windows 11, a Linux desktop, BSD.
- This is where the [Windows 11 VM](windows-vm.md) lives.

```bash
incus launch images:ubuntu/24.04 builder --vm    # the --vm flag makes it a VM
```

!!! note "Same CLI, one flag apart"
    `incus launch <image> <name>` creates a container; add `--vm` and it creates a VM. Almost every management command (`start`, `stop`, `snapshot`, `config`, `exec`/`console`, `delete`) works identically on both. This uniformity is the main reason this build consolidated on Incus instead of running Docker plus libvirt side by side.

### Which to use here

| Use it for | Instance type |
|---|---|
| A `docker-compose.yml` stack (Nextcloud, media, monitoring, AI) | system container with nesting |
| A single-image service that doesn't need a Docker daemon | OCI application container (a container from a Docker image) |
| Windows 11 | VM |
| A Linux desktop, or anything needing its own kernel/kernel modules | VM |
| A ROCm inference container reaching the host iGPU | system container with GPU devices |

## Images

An **image** is the read-only template an instance is created from. Incus pulls images from **remotes** (image servers) and caches them locally.

```bash
# Configured image remotes
incus remote list

# Browse images on the default community remote
incus image list images:ubuntu
incus image list images:debian/12

# Local image cache
incus image list
```

The important remotes:

| Remote | Contents |
|---|---|
| `images:` | the community image server ([images.linuxcontainers.org](https://images.linuxcontainers.org)) — Ubuntu, Debian, Alpine, and many more, for both containers and VMs |
| `local:` | your host's own image cache |

To run **Docker/OCI images** as Incus instances, you add an OCI-protocol remote (documented in full on the [OCI application containers](oci-containers.md) page):

```bash
incus remote add docker https://docker.io --protocol=oci
incus launch docker:nginx my-nginx      # an OCI application container
```

Images are cached on first use and can auto-update (`images.auto_update_interval`, set during [init](installation.md)).

## Profiles

A **profile** is a reusable bundle of configuration and devices that instances inherit. Profiles are how you avoid repeating yourself — define "a GPU-enabled container" once, apply it everywhere.

- Every instance gets the **`default`** profile unless told otherwise.
- An instance can have **multiple profiles**; they stack in order, later ones overriding earlier ones.
- Instance-specific config (set directly on the instance) overrides all profiles.

```bash
incus profile list
incus profile show default

# Launch with extra profiles layered on
incus launch images:ubuntu/24.04 ai-box --profile default --profile gpu

# Add/remove a profile on a running instance
incus profile add ai-box docker-nesting
incus profile remove ai-box docker-nesting
```

The precedence chain, lowest to highest:

```
default profile  ->  additional profiles (in order)  ->  instance-local config
```

This build defines a handful of purpose-built profiles — a GPU profile, a Docker-nesting profile, resource-limit templates — covered in [Profiles](profiles.md).

## Storage pools

A **storage pool** is where instance data lives. On this build there is one pool, backed by the **ZFS driver**, pointed at the existing `hot/incus` dataset.

- Each instance's root disk is a **dataset** inside the pool (`hot/incus/containers/<name>`, `hot/incus/virtual-machines/<name>`).
- Snapshots and clones are native ZFS operations.
- You can also create **custom storage volumes** for shared data between instances.

```bash
incus storage list
incus storage show default
incus storage info default              # usage and backing

# Custom volumes (e.g. shared model files)
incus storage volume list default
incus storage volume create default models
```

The full ZFS integration — how the dataset tree maps, snapshots vs `zfs snapshot`, and the sanoid/syncoid interaction — is [Storage](storage.md).

## Networks

A **network** connects instances. The default is a **managed bridge** called `incusbr0`: Incus runs a bridge on the host, hands instances private IPs via built-in DHCP, and NATs their traffic out.

```bash
incus network list
incus network show incusbr0
incus network info incusbr0
```

- Instances attach to a network through a **`nic` device** (usually inherited from the `default` profile as `eth0`).
- The default bridge does NAT, so instances reach the internet but aren't reachable from the LAN unless you forward ports.
- Reconciling this with UFW (Incus's own firewall rules vs UFW's) is the subject of [Networking](networking.md) — it is the Incus equivalent of the `ufw-docker` problem.

## Devices

A **device** is anything attached to an instance beyond its root disk and default NIC: extra disks, extra NICs, GPU passthrough, `/dev/kfd`, a TPM, a proxy (port forward), or a bind-mounted host path.

```bash
incus config device list <instance>
incus config device show <instance>

# Add a device (general form)
incus config device add <instance> <device-name> <device-type> [key=value ...]
```

Device types used in this build:

| Type | Purpose | Where covered |
|---|---|---|
| `disk` | root disk, extra volumes, host bind mounts | [Storage](storage.md) |
| `nic` | network interfaces | [Networking](networking.md) |
| `gpu` | GPU passthrough (`/dev/dri`) | [GPU passthrough](gpu-passthrough.md) |
| `unix-char` | raw char device — used for `/dev/kfd` (ROCm) | [GPU passthrough](gpu-passthrough.md) |
| `tpm` | emulated TPM 2.0 for VMs | [Windows VM](windows-vm.md) |
| `proxy` | forward a host port to an instance port | [Networking](networking.md) |

Devices can be set **on a profile** (shared by every instance using it) or **on an instance** (specific to that one). The GPU and nesting profiles in [Profiles](profiles.md) are just bundles of these devices plus config keys.

## Projects

A **project** is an isolation boundary for instances, profiles, images, and networks — a way to keep unrelated sets of workloads from seeing each other's resources. Everything lives in the `default` project unless you create others.

```bash
incus project list
incus project create sandbox
incus project switch sandbox
incus launch images:ubuntu/24.04 test    # created inside "sandbox"
incus project switch default
```

!!! note "Projects are optional on a single-admin homelab"
    For this build, the `default` project is enough — one admin, one purpose. Projects earn their keep when you want hard separation (a "throwaway experiments" project whose instances and profiles can't collide with production, or per-tenant isolation). They are mentioned here so the concept isn't a surprise; you can ignore them until you have a reason not to.

## Config keys

Instance and profile behavior is controlled by **config keys** — dotted strings like `security.nesting`, `limits.cpu`, `security.secureboot`. Set them on an instance or a profile:

```bash
incus config set <instance> <key> <value>
incus config get <instance> <key>
incus config show <instance>            # full effective config

# On a profile instead
incus profile set <profile> <key> <value>
```

The keys this build relies on:

| Key | Applies to | Meaning |
|---|---|---|
| `security.nesting` | container | allow running Docker/Incus nested inside (default `false`) |
| `security.privileged` | container | run privileged — avoid unless necessary (default `false`) |
| `security.secureboot` | VM | enforce UEFI Secure Boot with MS keys (default `true`) |
| `limits.cpu` | both | CPU count or pinned set |
| `limits.memory` | both | memory ceiling |

These are introduced in context in [Containers](containers.md), [VMs](vms.md), and [Windows VM](windows-vm.md), and collected in the [Quick reference](reference/quick-reference.md).

## Putting it together

A concrete example that touches every concept — a GPU-enabled, Docker-nesting container for the AI stack:

```bash
# One instance ...
incus launch images:ubuntu/24.04 ai-stack \
  --profile default \        # storage pool + incusbr0 NIC (network + storage pool)
  --profile gpu \            # gpu device + /dev/kfd unix-char (devices)
  --profile docker-nesting   # security.nesting=true (config key)

# ... created from an image, on the ZFS pool, on the bridge, with GPU devices,
#     nesting enabled — all inherited from profiles.
```

Everything after this page is filling in those pieces in depth. Continue to [Storage](storage.md).
