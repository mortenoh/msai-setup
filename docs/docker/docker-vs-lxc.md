# Docker vs system containers on the MS-S1 MAX

This used to be a "Docker vs LXC, pick one for bare metal" decision. It
isn't anymore. This build's architecture pivoted: **[Incus](../incus/index.md)
is now the one virtualization and container layer on the host**, and both
"Docker" and "system container" are now things that run *inside* Incus, not
choices you make on bare metal.

So this page is no longer a decision aid for what to install on the host —
that decision is made (Incus). What it still is: an explanation of the
genuine technical difference between a Docker container's process-level
model and a system container's full-userland model, because that difference
is exactly what tells you, *within Incus*, whether to nest Docker or use an
Incus-native container for a given service.

!!! note "What changed, and where the current story lives"
    An earlier draft of this project ran Docker directly on the host and
    reached for LXC only for niche "small VM" needs. The host now runs
    **no Docker daemon and no bare libvirt** — everything is an Incus
    instance. The canonical current pages are:

    - [Incus — the one virtualization layer](../incus/index.md) — why the
      architecture flipped, and the whole section index.
    - [Docker in Incus](../incus/docker-in-incus.md) — relocating existing
      `docker-compose.yml` stacks into a nesting-enabled Incus system
      container. This is where the compose-based services documented across
      this site actually run now.
    - [Incus OCI containers](../incus/oci-containers.md) — running a single
      OCI/Docker image directly as an Incus instance, with no nested Docker
      daemon.

    The old "Docker on bare metal by default" reasoning is preserved below
    as historical context where it still teaches something, not erased.

## TL;DR for this build (post-pivot)

> **Incus is the substrate. Nothing runs on bare metal except Incus itself.
> Inside Incus you have three shapes for a workload — pick by how the
> upstream ships and how much machinery the service needs.**

| Workload shape | Runs as | When |
|---|---|---|
| Compose-style multi-container stack | Docker, nested inside an Incus **system container** (`security.nesting=true`) | The service already ships a `docker-compose.yml` (Nextcloud, the media stack, monitoring, the AI stack) — keep it essentially unchanged, just inside Incus |
| Single OCI image, simple | Incus **OCI application container** (`incus launch docker:...`) | One image, one process, no compose orchestration — a full nested Docker daemon is more than the service needs |
| Full Linux userland to log into | Incus **system container** directly (no Docker inside) | A build sandbox, a per-tenant Linux, a system pet you `apt upgrade` slowly |
| Own kernel / non-Linux / TPM / Secure Boot | Incus **VM** | Windows 11, or anything needing hardware-virtualized isolation — see [Incus VMs](../incus/vms.md) |

The rest of this page is the "why" behind the first three rows — the
container-model differences that make the choice.

## The distinction that still matters: process container vs system container

This is the genuinely-useful, still-accurate part of the old comparison.
A Docker container and a system container use the same kernel primitives
(namespaces, cgroups) but model an "isolated unit" differently, and that
difference is unchanged by the pivot — it just now plays out *inside* Incus
instead of on bare metal.

| Aspect | Docker (process container) | System container (Incus, LXC-style) |
|--------|----------------------------|--------------------------------------|
| Mental model | One process the image launches | Full system: init, sshd, package manager |
| Image format | OCI images from a registry | Distro rootfs images (Debian, Ubuntu, Alpine) |
| Operate via | `docker compose up`, inside a nesting container | `incus exec`, or ssh into it |
| Update cadence | Pull a new image | `apt upgrade` inside the container |
| Persistent data | Bind mount from the container's filesystem | Lives in the instance's ZFS dataset (or a bind mount) |
| ZFS integration | Bind-mount a host path into the Docker container | Automatic — every Incus instance *is* a ZFS dataset under `rpool/incus` |
| Snapshots | Snapshot the underlying dataset | `incus snapshot` — a ZFS snapshot under the hood |
| GPU passthrough | `--device=/dev/kfd --device=/dev/dri` in compose | Incus `gpu` device + explicit `/dev/kfd` `unix-char` device |
| Best for | Services the upstream packages as images | A whole Linux to live in, or the host for nested Docker |

A Docker container is "the one process this image launches" with everything
else stripped out. A system container is "a complete userland, just without
its own kernel." That was true when the choice was "which runs on bare
metal"; it's still true now that the choice is "which shape inside Incus."

## How the old reasoning maps onto the new architecture

The old page's arguments were mostly right about the *containers* — it just
assumed one of them ran directly on the host. Re-read through the pivot:

- **"Every stack ships a first-class Docker image; there's no upstream LXC
  story."** Still true, and it's exactly why Docker didn't go away — the
  compose stacks keep running under Docker. What changed is *where*: inside
  an Incus system container with nesting enabled, not on the host. See
  [Docker in Incus](../incus/docker-in-incus.md).
- **"ZFS bind-mount workflows are wired into the Docker pages."** Still the
  pattern *inside* the nesting container for the Docker case. But note Incus
  gives you a cleaner option the old design couldn't: an Incus instance is
  natively a ZFS dataset, so `incus snapshot` and `zfs send`/`receive` work
  per instance with no bind-mount choreography at that layer. See
  [Incus storage](../incus/storage.md).
- **"LXC's strength is a small-VM feel — apt, sshd, its own init."** Still
  its strength, and now it's a first-class, default-supported thing: that's
  what an Incus **system container** *is*. You no longer reach for a separate
  toolchain to get it.
- **"LXC's ZFS storage backend gives one dataset per container with zero
  glue."** This is now simply how Incus works for *every* instance — the
  thing that used to be LXC's niche advantage is the substrate's default.

The one claim that fully flipped is the headline: "use Docker on bare metal
by default." The host runs no Docker daemon at all now — that's a deliberate
attack-surface decision (see [why Incus](../incus/index.md#why-incus-replaced-docker-direct-plus-bare-kvmlibvirt)).

## Nested Docker vs Incus-native OCI: the choice you actually make now

Given a single containerized service, the live question is no longer
"Docker or LXC" but "nest a Docker daemon, or launch the image as an Incus
OCI instance." Short version:

- **Nest Docker** when the service is a multi-container `docker-compose.yml`
  stack, depends on Docker-specific features (compose networks, healthchecks,
  an existing operational muscle-memory), or you want to keep the upstream's
  packaging verbatim. One nesting-enabled system container can host a whole
  compose stack. Full walkthrough: [Docker in Incus](../incus/docker-in-incus.md).
- **Use an Incus OCI container** when it's one image, one process, and you'd
  rather not run a Docker daemon inside a container just to run one image.
  Incus pulls the OCI image and runs it as a native instance. Details and the
  trade-offs: [Incus OCI containers](../incus/oci-containers.md).

Neither of those is "bare metal Docker," which no longer exists on this box.

## Docker on ZFS, inside the nesting container {#docker-on-zfs-the-pattern-used-in-these-docs}

The ZFS bind-mount pattern the Docker pages describe hasn't gone away — it
just operates one layer in, inside the nesting-enabled Incus system
container. Persistent data still lives on a ZFS dataset that's bind-mounted
into the Docker container:

```yaml
# docker-compose.yml, running inside the Incus nesting container
services:
  ollama:
    image: ollama/ollama:rocm
    volumes:
      - /data/ollama:/root/.ollama   # a path backed by ZFS
```

What's different post-pivot is that the *outer* layer is now a ZFS-native
Incus instance: the system container itself is a dataset under `rpool/incus`,
so `incus snapshot` captures the whole thing (Docker daemon state included),
while raw `zfs snapshot` on the inner data dataset is still available for
per-service granularity. See [Incus storage](../incus/storage.md) and
[Docker in Incus](../incus/docker-in-incus.md) for how the two layers of
dataset nest, and [ZFS Datasets](../zfs/datasets.md) for the layout.

## GPU and device passthrough (now via Incus) {#gpu-and-device-passthrough}

Both container shapes can still reach the AMD Strix Halo iGPU — but the
device plumbing is now Incus's job, not the host Docker daemon's.

- For the **nested-Docker** case, the Incus system container gets the GPU
  devices via Incus (`gpu` device plus a `/dev/kfd` `unix-char` device), and
  Docker inside it then sees `/dev/kfd` and `/dev/dri` and can hand them to
  its own containers the usual way (`devices:` in compose). The canonical
  device recipe is [Incus GPU passthrough](../incus/gpu-passthrough.md); the
  container-inner compose fragment lives with the [GPU containers](../ai/containers/gpu-containers.md)
  docs.
- For an **Incus-native** container, you attach the GPU with Incus's device
  types directly and skip Docker entirely.

The old page hand-wrote `lxc.cgroup2.devices.allow` lines for this — Incus's
`gpu` and `unix-char` device abstractions replace that hand-editing, which is
the same ergonomics win Docker's `--device` flags once had, now at the Incus
layer.

## A pragmatic recipe for this box (post-pivot)

1. **Install Incus on the host** — the one host-level container/VM tool.
   See [Incus installation](../incus/installation.md).
2. **Compose stacks → a nesting-enabled Incus system container.** The AI,
   media, observability, and identity stacks keep their `docker-compose.yml`
   files, just running inside Incus. [Docker in Incus](../incus/docker-in-incus.md).
3. **Simple single-image services → Incus OCI containers.** No nested daemon.
   [Incus OCI containers](../incus/oci-containers.md).
4. **A Linux to tinker in → an Incus system container directly.** `apt install`
   freely; snapshot it with `incus snapshot` before you break it.
5. **VMs (Windows 11, etc.) → Incus VM instances.** [Incus VMs](../incus/vms.md).

You don't juggle Docker-on-host vs LXD-on-host vs libvirt anymore — Incus is
the single front door, and these are just instance shapes behind it.

## See also

- [Incus — the one virtualization layer](../incus/index.md) — the section
  that supersedes the old Docker-direct decision.
- [Docker in Incus](../incus/docker-in-incus.md) — nesting compose stacks.
- [Incus OCI containers](../incus/oci-containers.md) — native single-image
  services.
- [Incus containers](../incus/containers.md) — system containers, nesting,
  profiles, resource limits.
- [Docker Setup](setup.md) / [Docker Compose](compose.md) — how the compose
  stacks themselves are declared (now run inside the nesting container).
- [ZFS Datasets](../zfs/datasets.md) — the storage layout underneath it all.
- [GPU Containers](../ai/containers/gpu-containers.md) — ROCm device
  passthrough into the containers that need it.
