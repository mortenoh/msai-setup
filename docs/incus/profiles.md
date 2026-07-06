# Profiles

A **profile** is a reusable bundle of config keys and devices that instances inherit. Profiles are how this build avoids retyping the same `-c security.nesting=true` and GPU device flags on every launch. This page defines the standard profiles for this build and the mechanics of composing them.

## How profiles compose

- Every instance gets **`default`** unless told otherwise.
- An instance can have **multiple** profiles; they apply in order, later overriding earlier.
- **Instance-local config** (set directly on the instance) overrides all profiles.

```
default  ->  profile B  ->  profile C  ->  instance-local config
(lowest precedence)                        (highest precedence)
```

```bash
incus profile list
incus profile show default

# Launch with a stack of profiles
incus launch images:ubuntu/24.04 ai-box --profile default --profile gpu --profile docker-nesting

# Add/remove on a running instance
incus profile add ai-box small
incus profile remove ai-box small
```

!!! note "Keep `default` minimal"
    The `default` profile should carry only what *every* instance needs — the root disk (on the `default` storage pool) and the `eth0` NIC (on `incusbr0`). Resist stuffing GPU devices or nesting into `default`; those belong in purpose-built profiles you opt into, so a plain container stays plain. `incus admin init` already set `default` up correctly (see [installation](installation.md)).

## The `default` profile (already created)

For reference, what init created:

```yaml
name: default
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

Every profile below is meant to be layered *on top of* this.

## Profile: `gpu` — ROCm access

Bundles the two devices from [GPU passthrough](gpu-passthrough.md) so any container is one flag away from the iGPU. Substitute your host's `render` group GID (`getent group render`).

```bash
incus profile create gpu

# /dev/dri render nodes via the gpu device (gputype=physical is the default)
incus profile device add gpu gpu0 gpu gputype=physical id=0 gid=<render-gid>

# /dev/kfd (ROCm compute) via a unix-char device — the piece the gpu device omits
incus profile device add gpu dev_kfd unix-char source=/dev/kfd path=/dev/kfd gid=<render-gid>
```

Usage:

```bash
incus launch images:ubuntu/24.04 ai-box --profile default --profile gpu
incus exec ai-box -- rocminfo | grep gfx1151      # verify (after installing rocminfo inside)
```

!!! warning "The `gpu` profile only makes sense for containers"
    This build passes the iGPU to containers, never VMs ([Windows VM](windows-vm.md) explains why). Don't apply `gpu` to a VM instance. Also remember the group-membership step inside the container — the profile presents the devices with the right GID, but the container's user still has to be *in* that group (see [GPU passthrough](gpu-passthrough.md)).

## Profile: `docker-nesting` — run Docker inside

Enables nesting so a system container can host a `docker-compose.yml` stack.

```bash
incus profile create docker-nesting
incus profile set docker-nesting security.nesting true
```

Usage:

```bash
incus launch images:ubuntu/24.04 media --profile default --profile docker-nesting
incus exec media -- bash -c 'curl -fsSL https://get.docker.com | sh'
```

This is the default deployment shape for existing compose stacks on this build. The migration mechanics (relocating stacks, storage-driver choices) are in [Docker in Incus](docker-in-incus.md); this profile is just the capability toggle.

## Profile: `ai-stack` — GPU + Docker + generous limits

A composite for the AI containers — most inference containers want the GPU *and* Docker *and* real resources. You can either apply three profiles or bake a single one:

```bash
incus profile create ai-stack
incus profile set ai-stack security.nesting true
incus profile set ai-stack limits.cpu 8
incus profile set ai-stack limits.memory 32GiB
incus profile device add ai-stack gpu0 gpu gputype=physical id=0 gid=<render-gid>
incus profile device add ai-stack dev_kfd unix-char source=/dev/kfd path=/dev/kfd gid=<render-gid>
```

```bash
incus launch images:ubuntu/24.04 ollama --profile default --profile ai-stack
```

Prefer the composite when the combination is always used together (the AI containers); prefer separate `gpu` + `docker-nesting` profiles when you mix and match.

## Profiles: resource tiers

Small/medium/large templates so you size instances by name, not by remembering numbers. Budget against the [whole-host memory plan](../operations/capacity-planning.md) — this box shares 128 GB across ARC, Ollama/GTT, VMs, and containers.

```bash
incus profile create small
incus profile set small limits.cpu 2
incus profile set small limits.memory 2GiB

incus profile create medium
incus profile set medium limits.cpu 4
incus profile set medium limits.memory 8GiB

incus profile create large
incus profile set large limits.cpu 8
incus profile set large limits.memory 32GiB
```

```bash
incus launch images:ubuntu/24.04 web --profile default --profile small
incus launch images:ubuntu/24.04 db  --profile default --profile medium
```

## Profile: `autostart` — come up on boot

For service instances that should return automatically after a reboot (which the [rebuild checklist](../operations/rebuild-checklist.md) relies on):

```bash
incus profile create autostart
incus profile set autostart boot.autostart true
incus profile set autostart boot.autostart.priority 10
```

```bash
incus launch images:ubuntu/24.04 media \
  --profile default --profile docker-nesting --profile autostart
```

## Profile: `lan` — bridged onto the physical network

For an instance that needs a real LAN IP instead of NAT (see [Networking](networking.md), pattern 2). Assumes a host bridge defined in Netplan.

```bash
incus profile create lan
incus profile device add lan eth0 nic nictype=bridged parent=<host-bridge>
```

Because this profile redefines `eth0`, apply it *after* `default` so it overrides the `incusbr0` NIC:

```bash
incus launch images:ubuntu/24.04 appliance --profile default --profile lan
```

## Inspecting and editing profiles

```bash
incus profile list
incus profile show gpu
incus profile device show gpu

# Edit a profile in $EDITOR (full YAML)
incus profile edit gpu

# Which instances use a profile?
incus profile show gpu | grep -A20 used_by
```

!!! warning "Editing a profile changes every instance using it"
    Profiles are live — changing `gpu`'s device GID or `large`'s memory limit takes effect on **all** instances that reference it (config keys usually apply immediately; device changes may need an instance restart). That's the point (fix once, fixed everywhere) but also the risk (a bad edit hits everything). For a one-off change to a single instance, set it **instance-local** (`incus config set <instance> ...`) instead of editing the shared profile.

## Copying profiles (for a rebuild)

Profiles are part of the reproducible config captured by the [preseed file](installation.md). To export/import individually:

```bash
# Dump a profile to YAML
incus profile show gpu > gpu-profile.yaml

# Recreate it elsewhere
incus profile create gpu
incus profile edit gpu < gpu-profile.yaml
```

For a full rebuild, the [preseed YAML](installation.md) plus these profile definitions (kept in version control) reconstruct the whole Incus configuration; the datasets come back with `rpool` (see [Storage](storage.md)).

## This build's profile summary

| Profile | Purpose | Key contents |
|---|---|---|
| `default` | baseline (init-created) | root disk on `default` pool, `eth0` on `incusbr0` |
| `gpu` | ROCm access | `gpu` device (`/dev/dri`) + `unix-char` (`/dev/kfd`) |
| `docker-nesting` | run Docker inside | `security.nesting=true` |
| `ai-stack` | GPU + Docker + resources | nesting + GPU devices + generous limits |
| `small`/`medium`/`large` | resource tiers | `limits.cpu` / `limits.memory` |
| `autostart` | boot with the host | `boot.autostart=true` |
| `lan` | real LAN IP | bridged `eth0` on a host bridge |

## Next steps

- [Containers](containers.md) — where these profiles get applied.
- [GPU passthrough](gpu-passthrough.md) — the devices behind the `gpu` profile.
- [Quick reference](reference/quick-reference.md) — profile commands at a glance.
