# Docker vs LXC on the MS-S1 MAX

You're picking how the services on this box are packaged. Both Docker
and LXC use the same Linux kernel primitives (namespaces, cgroups), but
they make different trade-offs about what an isolated unit should look
like and how you operate it day-to-day. This page is a practical
decision aid for *this* build (Ubuntu Server 26.04 + ZFS), not a generic
comparison.

## TL;DR for this build

> **Use Docker by default. Reach for LXC when you need a full-system
> container (own init, package manager, ssh-able, looks like a tiny VM).**

Reasons:

- Every application stack in these docs (Ollama, llama.cpp,
  Open WebUI, Jellyfin, Nextcloud, Prometheus + Grafana, etc.) ships
  first-class Docker images. There is no upstream LXC story for most of
  them.
- ZFS bind-mount workflows are already wired into the Docker pages.
- LXC's strength is when you want a "small VM" — and on the MS-S1 MAX
  the AI workloads we care about don't need that.

The interesting cases for LXC are below.

!!! note "This page is about containers, not full VMs"
    Everything below compares Docker containers to LXC/LXD *system
    containers* — both share the host kernel. It has nothing to do with
    this build's use of full virtual machines (Windows 11, optionally a
    Linux desktop) via KVM/QEMU + libvirt, documented in
    [Virtualization](../virtualization/index.md) — that decision is
    unaffected by anything on this page.

    Worth calling out explicitly since it's a common mix-up: modern LXD
    (4.0+) can *also* launch real VMs (`lxc launch <image> --vm`,
    QEMU-backed under the hood), not just system containers. This build
    still uses KVM/libvirt directly for VMs rather than LXD's VM mode —
    the entire [Windows 11 VM](../virtualization/windows-vm.md) guide
    (TPM 2.0, OVMF, virtio-gpu, RDP) is already built around
    virt-manager/libvirt, whose tooling is more mature for Windows
    guests than LXD's newer VM feature, and there's no benefit to
    consolidating VMs and service containers under one tool here.

## Where the categories actually differ

| Aspect | Docker | LXC |
|--------|--------|-----|
| Mental model | One process per container | Full system: init, sshd, package manager |
| Image format | OCI images from a registry | Distro rootfs templates (Debian, Ubuntu, Alpine) |
| Operate via | `docker compose up` | `lxc-start`, `lxc-attach`, or run sshd inside |
| Update cadence | Pull a new image | `apt upgrade` inside the container |
| Networking | Bridge + overlay; per-port forwards | Bridge + plain Linux networking |
| Persistent data | Bind mount or named volume | Lives inside the rootfs (or bind mount) |
| ZFS integration | Bind mount a dataset into the container | Use the ZFS storage backend (one dataset per container, automatic) |
| Snapshots | Snapshot the bind-mounted dataset | `lxc-snapshot` (uses ZFS clone under the hood) |
| GPU passthrough | `--device=/dev/kfd --device=/dev/dri` | Pass devices through in the container config |
| Resource limits | `deploy.resources.limits` in Compose | cgroup config in the container's `config` |
| Ecosystem | Massive — almost every app has an official image | Smaller — you build the rootfs yourself |
| Best for | Services where the upstream packages images for you | Per-tenant Linux systems, dev sandboxes, legacy stacks |

A Docker container = "the one process this image launches" with
everything else stripped out. An LXC container = "a complete userland,
just without its own kernel."

## When to pick LXC anyway

Pick LXC for a service when **at least one** of these is true:

- **You want a full Linux system to log into and `apt install` things
  in.** Examples: a build sandbox, an "experimental tinker" machine,
  a tenant Linux you give to someone else, a system pet you want to
  upgrade slowly.
- **You're packaging a stack that doesn't ship as an OCI image and
  doesn't want to be re-architected** — old multi-process daemons
  with their own service supervisor, weird systemd dependencies, etc.
- **You want ZFS-native snapshots per container with zero glue.** The
  LXC ZFS storage backend creates one dataset per container, and
  `lxc-snapshot` becomes a zfs snapshot operation.
- **You want a closer-to-VM feel** without paying VM overhead. Each
  container has its own init, its own networking namespace, its own
  PID 1 — you can `ssh` into it.

If none of those apply, the Docker path will be lower-friction.

## When to pick Docker (most things on this box)

Pick Docker when **any** of these are true:

- The upstream project publishes a Docker image (almost universal for
  the AI / media / observability stacks documented here).
- You want declarative, version-controlled service definitions
  (`docker-compose.yml` in git) over ad-hoc rootfs munging.
- You want one-line "blow away and recreate from image" semantics.
- The "one image = one app" model fits the service.

This is essentially every service mentioned in this site outside of
this page.

## ZFS interaction

Both work well with ZFS — but differently.

### Docker on ZFS (the pattern used in these docs)

Use ZFS for persistent data, bind it into containers:

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:rocm
    volumes:
      - /mnt/tank/ai/ollama:/root/.ollama  # bind to ZFS dataset
```

Snapshot the dataset, not the container:

```bash
zfs snapshot tank/ai/ollama@before-upgrade
```

Containers stay disposable; data stays on ZFS.

### LXC on ZFS (LXC storage backend)

Configure LXC to put each container in its own ZFS dataset:

```bash
# /etc/lxc/default.conf or container config
lxc.rootfs.path = zfs:tank/lxc/<name>
```

Now `lxc-create` provisions the dataset, `lxc-snapshot` is a
`zfs snapshot`, and `lxc-clone` is a `zfs clone`. Fast, atomic, and
the container's "image" lives natively on ZFS without bind-mount
choreography.

This is the case where LXC's ZFS integration genuinely beats Docker's
storage drivers.

## GPU and device passthrough

Both paths can hand the AMD Strix Halo iGPU to a container.

### Docker

```yaml
services:
  llama-server:
    image: ghcr.io/ggml-org/llama.cpp:server-rocm
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
```

See [GPU Containers](../ai/containers/gpu-containers.md) for the full
flow.

### LXC

In the container's `config`:

```
lxc.cgroup2.devices.allow = c 226:* rwm   # /dev/dri/*
lxc.cgroup2.devices.allow = c 240:* rwm   # /dev/kfd
lxc.mount.entry = /dev/dri  dev/dri  none bind,optional,create=dir
lxc.mount.entry = /dev/kfd  dev/kfd  none bind,optional,create=file
```

This works, but you're hand-writing what Docker handles in two lines.
Unless you already need LXC for other reasons, this is friction for no
gain.

## A pragmatic recipe for this box

The pattern that works on the MS-S1 MAX:

1. **Docker for every "service" in the documented stacks** (AI,
   observability, media, identity). Bind-mounted onto ZFS datasets.
2. **LXC, if at all, for tinker / per-tenant Linux systems** — a
   sandbox where you `apt install` freely and don't care about the
   image stability story.

You don't need both running at once for most home-server use. If you
end up using LXC, isolate its bridge from Docker's so the two
networking models don't argue.

## Decision flow

```
Does the upstream project publish an official OCI image?
  yes -> Docker
  no  -> can you trivially port it?
           yes -> Docker
           no  -> Do you want a "small VM" feel (ssh, apt, systemd inside)?
                    yes -> LXC
                    no  -> wrap it in a Dockerfile and use Docker
```

## See also

- [Docker Setup](setup.md) - install + daemon config
- [Docker Compose](compose.md) - the way services are declared on
  this build
- [ZFS Datasets](../zfs/datasets.md) - the layout the Docker bind
  mounts assume
- [GPU Containers](../ai/containers/gpu-containers.md) - ROCm device
  passthrough into containers
