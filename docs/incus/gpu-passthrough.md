# GPU passthrough — ROCm into containers

This is the page that makes local LLM inference work from inside an Incus container. The host owns the AMD Radeon 8060S iGPU (`gfx1151`) for ROCm; containers reach it through **two** device passthroughs that must both be present:

1. a **`gpu` device** — wires up `/dev/dri` (the render nodes), and
2. an explicit **`unix-char` device for `/dev/kfd`** — the ROCm compute interface.

The single most common mistake is adding only the `gpu` device and expecting ROCm to work. The `gpu` device alone gives you `/dev/dri` but **not** `/dev/kfd`, so `rocminfo` fails even though `/dev/dri/renderD128` is present inside the container. Both devices, every time.

!!! note "Containers only — the iGPU stays with the host, VMs get nothing"
    This whole page is about **containers**. This build deliberately does **not** pass the iGPU to any VM (host ROCm and VM passthrough are mutually exclusive, and the box's primary purpose is host-side inference — see `START.md` and the [Windows VM page](windows-vm.md)). ROCm-in-a-VM is not a path here. Containers share the host kernel and its amdgpu driver, which is exactly why device passthrough (not full GPU virtualization) is all that's needed.

## Prerequisites on the host

ROCm must already work **on the host** before any container can use it. Confirm:

```bash
# On the HOST
rocminfo | grep -i gfx            # should show gfx1151
rocm-smi                          # should show the GPU
ls -l /dev/kfd /dev/dri/          # both must exist; note the group on renderD128 and kfd
```

If the host side isn't working, fix that first — see [ROCm installation](../ai/gpu/rocm-installation.md). A container can only reach a GPU the host already drives.

### Find the render group GID — this is the crux

The `/dev/kfd` and `/dev/dri/renderD*` nodes are owned by the **`render`** group (and `video` for some nodes). Inside an unprivileged container, UIDs and GIDs are remapped, so the container needs the device presented with a **GID that maps to the right group inside the container** — otherwise the device appears but is unreadable, and ROCm gets "permission denied."

Get the host's `render` group GID:

```bash
# On the HOST
getent group render
# render:x:993:youruser        <- the number (e.g. 993) is what you pass as gid=
getent group video
```

Note both numbers. On this build, `render` is the one ROCm compute needs; you'll pass its GID to the `/dev/kfd` device.

## The two devices

### 1. The `gpu` device (`/dev/dri`)

Verified against the [Incus GPU device reference](https://linuxcontainers.org/incus/docs/main/reference/devices_gpu/): the default `gputype` is `physical`, and for a single-GPU host you can add it by ID.

```bash
# Add the iGPU's /dev/dri render nodes to the container.
# gputype=physical is the default; id=0 selects the first (only) GPU.
incus config device add ai-box gpu0 gpu gputype=physical id=0 gid=<render-gid>
```

- `gputype=physical` (default) passes the GPU's DRM/render nodes through.
- `id=0` selects the card by DRM ID (this host has one GPU, so `0`).
- `gid=<render-gid>` sets the group owner of the passed-in device nodes *inside the container* — set it to the host `render` GID so the nodes are group-accessible.

This gets you `/dev/dri/card0` and `/dev/dri/renderD128` inside the container. It does **not** get you `/dev/kfd`.

### 2. The `unix-char` device (`/dev/kfd`)

Verified against the [Incus unix-char device reference](https://linuxcontainers.org/incus/docs/main/reference/devices_unix_char/). `/dev/kfd` is the ROCm kernel-fusion-driver compute interface; the `gpu` device does not include it, so pass it explicitly as a raw character device:

```bash
incus config device add ai-box dev_kfd unix-char \
  source=/dev/kfd \
  path=/dev/kfd \
  gid=<render-gid>
```

- `source=/dev/kfd` — the host device node.
- `path=/dev/kfd` — where it appears inside the container.
- `gid=<render-gid>` — group owner inside the container, matching `render` so ROCm can open it.

!!! danger "This is the device everyone forgets"
    If `rocminfo` inside the container says something like "ROCk module is NOT loaded" or "no permission to access /dev/kfd", or `hipGetDeviceCount` returns 0 while `/dev/dri` clearly exists, the missing `/dev/kfd` `unix-char` device is almost always why. `/dev/dri` working and `/dev/kfd` missing is the signature failure. Add the device, restart the container, re-test.

### Group membership inside the container

The device nodes now carry the right GID, but the *process* inside the container must be **in** the `render` (and usually `video`) group to use that group access. Inside the container:

```bash
# Inside the container — create the groups with the SAME GIDs as the host, add the user
incus exec ai-box -- groupadd -g <render-gid> render 2>/dev/null || true
incus exec ai-box -- groupadd -g <video-gid> video 2>/dev/null || true
incus exec ai-box -- usermod -aG render,video <container-user>
```

Matching the GID numbers is what ties "the device node's group" to "a group the container user belongs to." If the container distro already has `render`/`video` at different GIDs, either recreate them at the host's numbers or add the user to whatever group holds the passed-in GID. Mismatched GIDs are the second most common cause of permission failures after a missing `/dev/kfd`.

## Verifying inside the container

```bash
# Devices are present
incus exec ai-box -- ls -l /dev/kfd /dev/dri/

# Install ROCm userspace tools inside the container (matching the host ROCm major version)
incus exec ai-box -- bash -c 'apt update && apt install -y rocminfo rocm-smi'

# The real test — ROCm sees the GPU
incus exec ai-box -- rocminfo | grep -iA4 gfx1151
incus exec ai-box -- rocm-smi
```

Expected: `rocminfo` lists `gfx1151` as an agent, exactly as it does on the host ([ROCm installation](../ai/gpu/rocm-installation.md) shows the expected output). If you see the agent and `rocm-smi` reports the GPU, passthrough works and you can run llama.cpp (HIP build) or Ollama inside the container.

!!! note "Match ROCm userspace to the host kernel driver"
    The container brings its own ROCm *userspace* (rocminfo, HIP libraries, the inference engine), but it uses the **host's** amdgpu kernel driver via the passed-in devices. Keep the container's ROCm version compatible with the host's kernel driver — the same major version is safest. You do **not** install amdgpu-dkms inside the container (there's no separate kernel there); only the runtime/userspace. This sidesteps the [DKMS build failures](../ai/gpu/rocm-installation.md) entirely for containers.

## A reusable GPU profile

Rather than adding both devices by hand every time, bundle them into a profile (full profile catalog in [Profiles](profiles.md)):

```bash
incus profile create gpu

# /dev/dri via the gpu device
incus profile device add gpu gpu0 gpu gputype=physical id=0 gid=<render-gid>

# /dev/kfd via unix-char
incus profile device add gpu dev_kfd unix-char source=/dev/kfd path=/dev/kfd gid=<render-gid>

# Apply to any container that needs the iGPU
incus launch images:ubuntu/24.04 ai-box --profile default --profile gpu
```

Now every AI container is one `--profile gpu` away from ROCm access. If you also run the inference stack *inside Docker inside the container*, layer `--profile docker-nesting` too — the devices are visible to Docker containers via `--device /dev/kfd --device /dev/dri` and `--group-add render` (exactly as the [GPU containers](../ai/containers/gpu-containers.md) page describes), because the nested Docker sees the devices the Incus container was given.

## Troubleshooting

### `/dev/dri` present but `/dev/kfd` missing

The classic. You added the `gpu` device but not the `unix-char` device for `/dev/kfd`.

```bash
incus config device show ai-box                 # is there a unix-char device for /dev/kfd?
incus exec ai-box -- ls -l /dev/kfd             # missing?
# Fix: add it
incus config device add ai-box dev_kfd unix-char source=/dev/kfd path=/dev/kfd gid=<render-gid>
incus restart ai-box
```

### Devices present but "permission denied" from ROCm

GID mismatch — the device's group inside the container isn't a group the process belongs to.

```bash
# What GID do the devices carry inside the container?
incus exec ai-box -- stat -c '%g %n' /dev/kfd /dev/dri/renderD128
# What groups is the user in?
incus exec ai-box -- id <container-user>
# Fix: ensure a group at that GID exists and the user is in it (see "Group membership" above)
```

### `rocminfo` shows "ROCk module is NOT loaded"

The container is trying to talk to the kernel driver but can't — usually the missing `/dev/kfd`, occasionally the host's amdgpu module not actually being loaded (check on the host with `lsmod | grep amdgpu`). The kernel side is the host's job; the container never loads amdgpu itself.

### Works on the host, not in the container, devices look right

Check for an unprivileged-container idmap issue: the raw device number vs remapped GID. As a diagnostic *only*, testing with `security.privileged=true` temporarily tells you whether it's a mapping problem (works privileged, fails unprivileged = GID mapping) — but **don't leave it privileged**; fix the GID matching instead and turn privileged back off.

```bash
# Diagnostic only — revert afterward
incus config set ai-box security.privileged true && incus restart ai-box
incus exec ai-box -- rocminfo | grep gfx1151
incus config set ai-box security.privileged false && incus restart ai-box
```

### `rocm-smi` works but inference is slow / falls back to CPU

That's an inference-engine build/target issue, not a passthrough issue — confirm the engine was built for `gfx1151` (e.g. llama.cpp with `-DAMDGPU_TARGETS=gfx1151`, see [ROCm installation](../ai/gpu/rocm-installation.md)) and that GTT memory is configured ([memory configuration](../ai/gpu/memory-configuration.md)). If `rocminfo` sees `gfx1151`, passthrough is done.

## Verify checklist

```bash
# On host: ROCm works, note render GID
rocminfo | grep gfx1151 && getent group render

# Container has BOTH devices
incus config device show ai-box | grep -E 'gpu|unix-char|kfd|dri'
incus exec ai-box -- ls -l /dev/kfd /dev/dri/

# ROCm works inside
incus exec ai-box -- rocminfo | grep gfx1151
incus exec ai-box -- rocm-smi
```

## Next steps

- [Profiles](profiles.md) — the `gpu` profile in the full catalog.
- [ROCm installation](../ai/gpu/rocm-installation.md) — the host-side ROCm stack these containers depend on.
- [GPU containers](../ai/containers/gpu-containers.md) — ROCm inside Docker (which itself runs inside an Incus container here).
- [Memory configuration](../ai/gpu/memory-configuration.md) — GTT/unified-memory tuning for inference.
