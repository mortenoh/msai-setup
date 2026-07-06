# Incus — the one virtualization layer

This section is the deep dive on [Incus](https://linuxcontainers.org/incus/), the single container-and-VM manager this build runs directly on the host. Everything that isn't the base OS — Docker stacks, single-image services, the Windows 11 VM, GPU-accelerated inference containers — lives inside Incus.

!!! note "This supersedes the old Docker-direct decision"
    An earlier draft of this project ran Docker directly on the host and reached for LXC/LXD only for niche full-system-container needs (that thesis still lives, for now, in [`docker/docker-vs-lxc.md`](../docker/docker-vs-lxc.md), which a later pass will rewrite). The architecture has since flipped: **Incus is now the one virtualization layer**, and Docker workloads run *nested inside* Incus system containers. The pages in this section are what supersede that older decision — read [`START.md`](https://github.com/) at the repo root for the full architectural intent.

## What Incus is

Incus manages two kinds of instance from one CLI and one API:

- **System containers** — a full Linux userland (its own init, its own package manager, ssh-able if you want) sharing the host kernel. Think "a tiny VM without the virtualization overhead." This is where nested Docker stacks run.
- **Virtual machines** — QEMU/KVM guests with their own kernel, full hardware emulation, TPM 2.0 and Secure Boot support. This is where Windows 11 runs.

It also runs **OCI application containers** — launch a Docker/OCI image directly as an Incus instance without a nested Docker daemon (`incus launch docker:...`). That is a newer, less-proven path documented separately (see [OCI application containers](oci-containers.md)).

Under the hood Incus leans on the same primitives this build already uses elsewhere: Linux namespaces and cgroups for containers, KVM for VMs, and **ZFS** for storage — every instance is a native ZFS dataset under `rpool/incus`.

## Why Incus replaced Docker-direct plus bare KVM/libvirt

The original design ran two separate stacks: Docker directly on the host for services, and libvirt/`virt-install` for VMs. Incus collapses both into one tool:

| Concern | Old design | This build (Incus) |
|---|---|---|
| Service containers | Docker on the host | Docker nested inside an Incus system container, or a native OCI app container |
| VMs | libvirt / `virt-install` / `virsh` | Incus VM instances (`incus launch --vm`) |
| Per-instance storage | Docker bind mounts onto ZFS datasets | One ZFS dataset per instance, automatic, via Incus's ZFS driver |
| Snapshots | `zfs snapshot` on the bind-mounted dataset | `incus snapshot` (a ZFS snapshot under the hood) plus raw `zfs` still available |
| CLI surface | `docker`, `virsh`, `virt-install`, `qemu-img` | one `incus` client |
| Host attack surface | Docker daemon runs as root on the host | the host runs no Docker daemon; nesting is contained |

The wins that matter here:

- **One consistent management model** for "a thing that runs a workload," whether that thing is a container or a VM.
- **ZFS-native storage per instance** with zero bind-mount choreography — snapshots, clones, and `zfs send`/`receive` work per instance, composing directly with this build's sanoid/syncoid backup story.
- **The host stays clean.** No Docker daemon running as root on the host; Docker (when needed) is confined inside a nesting-enabled container. VMs are managed the same way as containers instead of via a second toolchain.
- **Rebuild is declarative.** Instance configuration is stored in Incus's database and reproducible from a preseed file; the datasets survive on `rpool/incus`.

Docker itself is not abandoned — the many services that ship as `docker-compose.yml` stacks keep running under Docker, just *inside* an Incus container. Incus is the host-level layer; Docker is a guest-level detail.

## How Incus relates to LXD — the fork history

Incus is a **community fork of [LXD](https://ubuntu.com/lxd)**, created in 2023.

- LXD began at Canonical as the "system container manager" built on top of LXC, adding a REST API, images, storage/network management, and clustering.
- In late 2023 Canonical **moved the LXD project under its own umbrella and required a Contributor License Agreement (CLA)** for contributions, and moved the repository out of the `linuxcontainers` community organization.
- In response, LXD's original lead maintainer and much of the community forked LXD into **Incus** under the Linux Containers project, license unchanged (Apache 2.0), **no CLA required**. Incus is now packaged in Debian and Ubuntu's own archives.

Practically, if you already know LXD, Incus is the same tool: the CLI is `incus` instead of `lxc` (avoiding the collision with the classic `lxc-*` tools), the config keys and concepts carry over, and there is a documented `lxd-to-incus` migration path. This build uses Incus, not LXD — it is the actively community-maintained line and ships in the distro.

!!! warning "`incus` the client vs `lxc` the LXD client vs `lxc-*` the classic tools"
    Three easily-confused things: **`incus`** (this build's client), **`lxc`** (the *LXD* client — a different fork's CLI), and **`lxc-create` / `lxc-start` / `lxc-attach`** (the low-level classic LXC tools). Every command in this section is the `incus` client. If a guide you find online uses `lxc network ...` or `lxc launch ...`, it is LXD documentation — the equivalent Incus command is almost always the same with `incus` swapped for `lxc`, but verify against the [Incus docs](https://linuxcontainers.org/incus/docs/main/) rather than assuming.

## The shape of this section

Read roughly in order — each page assumes the mental model built by the ones before it.

### Getting started
- [Installation](installation.md) — installing Incus on Ubuntu 26.04, `incus admin init`, pointing storage at `rpool/incus`.
- [Core concepts](concepts.md) — containers vs VMs, images, profiles, storage pools, networks, projects. Read this before anything below.

### The building blocks
- [Storage](storage.md) — the ZFS storage driver in depth: per-instance datasets, snapshots/clones, composing with sanoid/syncoid.
- [Networking](networking.md) — the `incusbr0` bridge, UFW forwarding integration (the Incus equivalent of `ufw-docker`), Netplan/systemd-networkd, Tailscale reachability.
- [Containers](containers.md) — system containers, nesting for Docker, resource limits, reusable profiles.
- [Docker in Incus](docker-in-incus.md) — migrating existing `docker-compose.yml` stacks into a nesting-enabled system container (the build default).
- [OCI application containers](oci-containers.md) — running a Docker/OCI image directly as an Incus instance, for simple single-image services.
- [GPU passthrough](gpu-passthrough.md) — the ROCm/AMD story: the `gpu` device plus an explicit `/dev/kfd` `unix-char` device, verifying `rocminfo` inside a container, render-group GID matching, troubleshooting.
- [Virtual machines](vms.md) — Incus VMs in general: creation, resources, virtio, `incus console`.
- [Windows 11 VM](windows-vm.md) — TPM 2.0 + Secure Boot, virtio drivers, RDP, iGPU stays with the host.
- [Profiles](profiles.md) — reusable profiles for this build (GPU-enabled, Docker-nesting, and more).

### Operations and reference
- [Snapshots & backup](snapshots-backup.md) — instance snapshots, export/import, how this fits the sanoid/syncoid/restic philosophy.
- [Troubleshooting](troubleshooting.md) — nesting, GPU devices, storage pools, networking/UFW.
- [Quick reference](reference/quick-reference.md) — command cheat sheet.

### Running Docker workloads

The two ways Docker-packaged software runs on this build:

- [Docker in Incus](docker-in-incus.md) — the full guide to relocating existing `docker-compose.yml` stacks into a nesting-enabled Incus system container. This is the default for anything already packaged as a compose stack.
- [OCI application containers](oci-containers.md) — running a Docker/OCI image directly as an Incus instance (`incus launch docker:...`), for simple single-image services where a full nested-Docker container is more machinery than needed.

The [Containers](containers.md) page covers *enabling* nesting; the migration mechanics and the OCI-vs-nested-Docker decision live in those two pages.

## Verification note

The exact `incus` command syntax in this section was checked against the [official Incus documentation](https://linuxcontainers.org/incus/docs/main/) at the time of writing. Incus moves fast — config key names and defaults do change between releases. Where a command is destructive or load-bearing, verify it against the current docs for your installed version (`incus version`) before running it.
