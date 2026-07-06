# System containers in depth

This page is about Incus **system containers** — full Linux userlands sharing the host kernel — and the config that makes them useful on this build: nesting (for Docker), resource limits, and reusable profiles. VMs are [a separate page](vms.md); GPU passthrough is [its own page](gpu-passthrough.md).

## Creating and managing

### Launch

```bash
# Launch (create + start) a container from a community image
incus launch images:ubuntu/24.04 web

# Just create it, start later
incus init images:ubuntu/24.04 web
incus start web

# Launch with profiles, config, and a root size in one shot
incus launch images:ubuntu/24.04 web \
  --profile default --profile docker-nesting \
  -c limits.cpu=4 -c limits.memory=8GiB \
  -d root,size=40GiB
```

### Lifecycle

```bash
incus list                          # all instances, state, IPs
incus info web                      # detailed state, resource usage
incus start web
incus stop web                      # graceful
incus stop web --force              # hard stop
incus restart web
incus pause web / incus resume web  # freeze/thaw (cgroup freezer)
incus rename web web2
incus delete web --force            # destroy (also removes the ZFS dataset)
```

### Getting inside

```bash
# Run a command
incus exec web -- systemctl status

# Interactive shell
incus exec web -- bash

# As a specific user / with env
incus exec web --user 1000 --env TERM=xterm -- bash
```

!!! note "`incus exec` vs `incus console`"
    For **containers**, `incus exec` is what you want — it runs a process directly in the container's namespaces. `incus console` attaches to the container's console (PID 1's tty), useful for watching boot or recovering a container whose sshd/networking is broken, but it is not the day-to-day tool. `incus console` is more central for **VMs** (see [VMs](vms.md)), which have no `exec`.

### Pushing and pulling files

```bash
incus file push ./config.yaml web/etc/myapp/config.yaml
incus file pull web/var/log/app.log ./app.log
incus file push -r ./site/ web/srv/www/       # recursive
```

## Resource limits

Container limits are enforced via cgroups — set them as config keys, live-updatable in most cases.

### CPU

```bash
# Number of vCPUs (scheduler sees this many)
incus config set web limits.cpu 4

# Pin to specific host cores (this host is 16c/32t, 2 CCX — pin to one CCX for cache locality)
incus config set web limits.cpu 0-7

# CPU time allowance (soft cap: 50% of the allotted CPUs)
incus config set web limits.cpu.allowance 50%

# Priority under contention (0-10; higher wins)
incus config set web limits.cpu.priority 5
```

### Memory

```bash
# Hard ceiling
incus config set web limits.memory 8GiB

# Enforcement: hard (OOM-kill over limit) vs soft (reclaim under pressure)
incus config set web limits.memory.enforce hard

# Disable swap for this instance
incus config set web limits.memory.swap false
```

!!! note "Leave headroom for ARC, Ollama, and VMs"
    This host has 128 GB unified memory, but it is shared: ZFS ARC is capped at 16 GiB, ROCm/Ollama can claim ~108 GB of GTT (see [memory configuration](../ai/gpu/memory-configuration.md)), and VMs reserve theirs. Set container `limits.memory` deliberately rather than letting containers assume the whole box — an unbounded container competing with a running inference job is how you get OOM surprises. The [capacity planning](../operations/capacity-planning.md) page has the whole-host budget.

### Disk and processes

```bash
incus config device set web root size=40GiB    # root disk quota (ZFS refquota)
incus config set web limits.processes 4096       # PID limit
```

### Inspect live usage

```bash
incus info web --resources
incus config show web         # full effective config, including inherited profile keys
```

## Nesting — running Docker inside a container

The default pattern on this build: existing `docker-compose.yml` stacks run **inside an Incus system container** with nesting enabled, essentially unchanged.

### Enable nesting

```bash
incus config set web security.nesting true
```

`security.nesting` (bool, default `false`, container-only, **live-updatable**) allows running a nested container/OCI runtime — including Docker — inside the instance. Verified against the [Incus instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/): "Whether to support running Incus (nested) inside the instance." The same flag is what Docker-in-Incus relies on.

```bash
# A container purpose-built for Docker
incus launch images:ubuntu/24.04 docker-host -c security.nesting=true
incus exec docker-host -- bash
# inside the container:
#   curl -fsSL https://get.docker.com | sh
#   docker run hello-world
```

!!! note "Nesting is usually enough — avoid `security.privileged`"
    For running Docker inside an **unprivileged** container, `security.nesting=true` is typically sufficient on modern kernels — you do **not** need `security.privileged=true`. Privileged containers disable the UID/GID remapping that isolates the container's root from the host's root, which is a real security downgrade. Reach for privileged mode only if a specific workload provably needs it (some device or filesystem edge cases), and understand you're trading isolation for it. See the [Incus security explanation](https://linuxcontainers.org/incus/docs/main/explanation/security/).

!!! warning "Some Docker storage drivers misbehave nested on ZFS"
    Docker running inside a ZFS-backed Incus container sometimes struggles with its default storage driver (`overlay2` over an idmapped ZFS root has historically had rough edges). If Docker fails to start or images misbehave inside the container, forcing the `fuse-overlayfs` or `vfs` driver — or giving the container's `/var/lib/docker` its own dataset — is the usual fix. The full migration mechanics (relocating a compose stack, the storage-driver choice, bind-mounting host datasets for compose volumes) are the subject of [Docker in Incus](docker-in-incus.md); this page only covers *enabling* the capability.

### Verify nesting works

```bash
incus exec docker-host -- docker info | grep -i 'storage driver'
incus exec docker-host -- docker run --rm hello-world
```

## Unprivileged vs privileged containers

By default Incus containers are **unprivileged**: the container's root (UID 0) maps to a high, unprivileged UID on the host, so a container-root breakout lands as a nobody user on the host. This is the safe default and this build keeps it.

```bash
# Confirm a container is unprivileged (no security.privileged key set = default false)
incus config get web security.privileged        # empty or "false"
```

`security.privileged=true` disables that mapping. The trade-offs are covered above — the short version is **don't**, unless a workload provably requires it.

## Profiles for reuse

Rather than repeating `-c` flags on every launch, bundle common config into profiles. This build's standard profiles are detailed in [Profiles](profiles.md); the two most relevant to containers:

### A Docker-nesting profile

```bash
incus profile create docker-nesting
incus profile set docker-nesting security.nesting true
# optionally bake in sensible resource defaults
incus profile set docker-nesting limits.memory 8GiB

# Use it
incus launch images:ubuntu/24.04 media-stack --profile default --profile docker-nesting
```

### A resource-tier profile

```bash
incus profile create small
incus profile set small limits.cpu 2
incus profile set small limits.memory 2GiB

incus profile create large
incus profile set large limits.cpu 8
incus profile set large limits.memory 32GiB
```

Profiles stack — `--profile default --profile large --profile docker-nesting` composes all three, later ones winning on conflicts. See [Profiles](profiles.md) for the full set including the GPU profile.

## Autostart and boot ordering

Make a container come up on host boot, and control ordering:

```bash
incus config set web boot.autostart true
incus config set web boot.autostart.priority 10      # higher starts first
incus config set web boot.autostart.delay 5          # seconds to wait after starting
```

The [rebuild checklist](../operations/rebuild-checklist.md) relies on autostart so that, after `rpool` is imported and Incus re-adopts its datasets, the service containers come back without manual `incus start` for each.

## A worked example: the media stack container

Tying it together — a container to host the media `docker-compose.yml` stack:

```bash
# Create it: nesting for Docker, sensible limits, autostart, a decent root size
incus launch images:ubuntu/24.04 media \
  --profile default --profile docker-nesting \
  -c limits.cpu=6 -c limits.memory=16GiB \
  -c boot.autostart=true \
  -d root,size=30GiB

# Mount the media library dataset from the host (tank/media) read-write
incus config device add media library disk source=/tank/media path=/srv/media

# Install Docker inside and bring the stack up
incus exec media -- bash -c 'curl -fsSL https://get.docker.com | sh'
incus file push -r ./media-stack/ media/opt/media-stack/
incus exec media -- bash -c 'cd /opt/media-stack && docker compose up -d'
```

The container is disposable; the *data* lives on `tank/media` (host dataset, bind-mounted) and the compose files are in version control. Snapshot the container before changes with `incus snapshot create media before-upgrade`, and let sanoid cover `rpool/incus/containers/media` on schedule (see [Storage](storage.md)).

## Verification

```bash
incus list                                   # is it running?
incus config show media                      # effective config (limits, nesting, autostart)
incus exec media -- docker compose -f /opt/media-stack/compose.yaml ps
incus info media --resources                 # live CPU/mem
```

## Next steps

- [GPU passthrough](gpu-passthrough.md) — giving a container the iGPU for ROCm.
- [Profiles](profiles.md) — the reusable profiles this build standardizes on.
- [Networking](networking.md) — exposing a container's services.
- [Docker in Incus](docker-in-incus.md) — the full compose-stack migration guide.
