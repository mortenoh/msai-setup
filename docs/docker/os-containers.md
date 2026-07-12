# Running OS-like containers

The Docker pages elsewhere in this section describe *service* containers — one
image, one process, a `docker-compose.yml` per stack. This page covers the
adjacent question people reach Docker for and then get stuck on: "can I just
run a whole operating system in a container?" The honest answer is *sort of,
and only for the cases where a container is actually the right tool*. This
page walks the container-appropriate shapes — base-OS images, long-running
login-able containers, and desktop-in-a-container — and, at each step, points
you at [Incus](../incus/index.md) for the cases a container genuinely cannot
serve.

!!! note "Where this runs on the build"
    On the MS-S1 MAX, Docker itself runs *nested inside* an Incus system
    container, per [Docker in Incus](../incus/docker-in-incus.md) — there is
    no Docker daemon on the host. Everything on this page is a `docker`
    command you run *inside* that nesting container. The commands are
    identical to running Docker anywhere; they just sit one layer down. On a
    Mac dev machine the same commands run under Docker Desktop or
    [Apple Container](../apple-container/index.md) instead, with the
    differences called out below.

## Containers are not VMs

A Docker container is not a small computer. It shares the **host kernel** and
runs a single process tree inside namespaces and cgroups — there is no BIOS,
no bootloader, no init system unless you install one, and no kernel of its
own. `docker run ubuntu:24.04` does not boot Ubuntu; it unpacks Ubuntu's
*userland* (its `/bin`, `/usr`, `apt`, libraries) and runs one command against
the kernel that is already running underneath. This is exactly the "process
container vs system container" distinction laid out in
[Docker vs system containers](docker-vs-lxc.md), and it decides everything
below.

The consequences are concrete:

- **You cannot run a different kernel.** No custom kernel modules, no `systemd`
  cgroup-v1 quirks the host kernel doesn't support, no Windows.
- **You cannot boot from an ISO.** There is nothing to boot; the image *is*
  the filesystem.
- **Hardware isolation is weaker than a VM's.** Namespaces, not a hypervisor.

So the moment you want a full OS with its own kernel, an install-from-ISO
workflow, Windows, or hardware-virtualized isolation (TPM, Secure Boot), you
have left Docker's territory and want an Incus VM instead:

| You want | Use | Page |
|---|---|---|
| A full Linux to `ssh` into and live in | Incus **system container** | [Incus containers](../incus/containers.md) |
| A Linux VM with its own kernel, from an ISO | Incus **VM** | [Incus VMs](../incus/vms.md), [Fedora VM](../incus/fedora-vm.md) |
| Windows | Incus **VM** | [Windows 11 VM](../incus/windows-vm.md) |

Everything from here down is the part Docker *does* do well.

## Base-OS images

The base-OS images are userland-only distro rootfs images. They are the right
starting point when you are building your own image, need a throwaway shell in
a specific distro, or want to reproduce a bug against a particular userland.

```bash
# Drop into a shell in each distro's userland (host kernel underneath)
docker run -it --rm ubuntu:24.04 bash     # Ubuntu 24.04 LTS
docker run -it --rm debian:12 bash        # Debian 12 (bookworm)
docker run -it --rm fedora:41 bash        # Fedora 41 (uses dnf)
docker run -it --rm alpine:3.20 sh        # Alpine — musl libc, ~5 MB, ash not bash
```

Inside, package managers work as normal — you are installing into the
container's filesystem layer, not the host:

```bash
# Ubuntu / Debian
apt update && apt install -y curl vim

# Fedora
dnf install -y curl vim

# Alpine (apk, and packages are named differently)
apk add --no-cache curl vim
```

!!! note "This is userland, not a running OS"
    `uname -r` inside any of these prints the **host** kernel, not the
    distro's. `ubuntu:24.04` gives you Ubuntu's `apt` and libraries running on
    whatever kernel the host boots. On the Linux build that is the real host
    kernel; on macOS Docker Desktop it is the shared `linuxkit` VM's kernel
    (see the macOS note below). Multi-arch images resolve to your platform —
    on Apple Silicon and the Strix Halo box you get `aarch64` variants.

**Base image vs service image.** Reach for a raw base image (`ubuntu`,
`fedora`, …) when *you* are the one adding software — a Dockerfile `FROM`
line, an interactive debugging shell, a CI-style build sandbox. Reach for a
purpose-built service image (`postgres:16`, `nginx`, `ollama/ollama:rocm`)
when the upstream already packages the process you want; those come with the
software installed and a sensible entrypoint, and re-inventing them on top of
a base image is wasted effort. If what you actually want is "a persistent
Linux I keep and `apt upgrade` over months," that is a *pet*, and a pet
belongs in an [Incus system container](../incus/containers.md), not a Docker
image you rebuild.

## Login-able, long-running "server" containers and SSH

A container that stays up (a build agent, a dev environment, something you
poke at repeatedly) is fine. The question is how you get a shell into it. The
answer is almost always `docker exec`, not SSH:

```bash
# Start a long-running container (tail -f keeps PID 1 alive with nothing to do)
docker run -d --name devbox ubuntu:24.04 sleep infinity

# Get an interactive shell whenever you want one — no sshd, no port, no keys
docker exec -it devbox bash

# One-off command without an interactive session
docker exec devbox apt list --installed
```

`docker exec` is the native, correct way to "log in" to a container. It needs
no SSH daemon, no published port, no key management, and it is available even
when the container has no network. Use it by default.

Occasionally you have tooling that genuinely speaks SSH — a client that only
knows how to `scp`, an IDE remote that requires an SSH endpoint. Only then do
you put an `sshd` in the container. A minimal pattern:

```dockerfile
# Dockerfile — sshd in a container, only when a tool truly requires ssh
FROM ubuntu:24.04
RUN apt update && apt install -y openssh-server \
    && mkdir -p /run/sshd
# Inject an authorized key at build time (never bake in a password)
COPY authorized_keys /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys
EXPOSE 22
# sshd in the foreground becomes PID 1
CMD ["/usr/sbin/sshd", "-D", "-e"]
```

```bash
docker build -t sshbox .
# Publish 22 only to localhost or a Tailscale interface — never 0.0.0.0
docker run -d --name sshbox -p 127.0.0.1:2222:22 sshbox
ssh -p 2222 root@127.0.0.1
```

!!! warning "sshd-in-a-container is usually an anti-pattern"
    An SSH daemon means a second process to supervise, a key/credential
    surface, and a published port — the exact things Docker's one-process
    model exists to avoid, and a real exposure risk under this build's
    UFW/Tailscale posture (recall from [Docker Setup](setup.md#docker-and-ufw)
    that published ports bypass UFW). If what you actually want is "a full
    Linux I ssh into," that is precisely what a **system container** is for:
    it ships its own init and `sshd`, updates with `apt upgrade`, and is a
    ZFS-native instance you can snapshot. Use an
    [Incus system container](../incus/containers.md); the reasoning is spelled
    out in [Docker vs system containers](docker-vs-lxc.md). Keep sshd-in-Docker
    strictly for the "a tool demands an ssh endpoint" case, bound to localhost
    or Tailscale.

## Desktop-in-a-container (RDP / VNC / noVNC)

You can run a full graphical Linux desktop inside a container and reach it
from a browser or a VNC/RDP client. This does **not** give the container a
GPU-accelerated display or its own kernel — it runs a software X/Wayland
session plus a VNC server, streamed out over a port. It is genuinely useful
for a disposable browser, a throwaway GUI tool, or a per-user workspace. For a
*real* accelerated desktop with its own kernel, that is the Incus VM path
([Graphical access](../incus/graphical-access.md)), not this.

The best-known image family is **LinuxServer's Webtop**
(`linuxserver/webtop`), which serves a KDE / XFCE / MATE / i3 desktop over
KasmVNC straight to the browser — no client to install.

```yaml
# docker-compose.yml — a browser-accessible Linux desktop
services:
  webtop:
    image: lscr.io/linuxserver/webtop:latest
    container_name: webtop
    security_opt:
      - seccomp:unconfined        # some desktop bits need this
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
    volumes:
      - /mnt/tank/webtop/config:/config   # persist the home dir on ZFS
    ports:
      - "127.0.0.1:3000:3000"     # HTTP UI, localhost only — proxy/Tailscale in front
      - "127.0.0.1:3001:3001"     # HTTPS UI
    shm_size: "1gb"               # browsers inside need shared memory
    restart: unless-stopped
```

!!! warning "Verify the desktop tag against Docker Hub"
    `linuxserver/webtop` selects the desktop environment **via the image tag**
    (roughly `<distro>-<desktop>`, e.g. `ubuntu-kde`, `debian-xfce`,
    `fedora-mate`, `alpine-kde`), and the set of published tags changes over
    time — `latest` has historically pointed at an Alpine/XFCE build. Pick the
    exact tag from the current
    [tag list on Docker Hub / GHCR](https://hub.docker.com/r/linuxserver/webtop)
    rather than trusting the value above; treat the `:latest` here as a
    placeholder. The default HTTP/HTTPS ports (3000/3001) and the KasmVNC
    front end are stable across recent images, but confirm for your tag.

**Kasm Workspaces** (`kasmweb/...`) is the heavier, multi-user cousin:
containerized desktops and single-app streams behind a management plane, with
individual workspace images like `kasmweb/desktop` or
`kasmweb/core-ubuntu-jammy` that expose their session on port `6901` with a
default `kasm_user`. It is worth it when you want a managed workspace portal;
for a single throwaway desktop, Webtop is far less machinery. As with Webtop,
pin the exact image tag from Docker Hub — Kasm's image and default-credential
conventions are version-specific.

A generic `xrdp` or `TigerVNC` server baked into your own image is the
build-it-yourself alternative (install `xrdp`/`tigervnc-standalone-server` + a
desktop, run the daemon as PID 1, publish 3389/5901). It is more work than
Webtop and rarely worth it unless you need a very specific desktop.

!!! warning "Never expose a desktop container to the internet"
    A desktop container is a full interactive session; a weak or default VNC
    password on a public port is a direct foothold. Keep the published port
    bound to `127.0.0.1` or a **Tailscale** interface only, put it behind the
    reverse proxy with real auth, and never open it on the LAN broadcast or
    `0.0.0.0`. This is the same posture the [Docker Setup](setup.md#docker-and-ufw)
    page takes for every sensitive service — and it matters more here because
    the payload is a shell with a GUI. If you want a properly isolated,
    accelerated desktop, use a graphical Incus VM instead
    ([Graphical access](../incus/graphical-access.md)).

## GPU into containers (recap)

On the Linux build, ROCm reaches into a container by passing the AMD devices
and the right groups — nothing special beyond the flags:

```bash
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal:latest rocminfo | head
```

That is the short version. The full story — host ROCm install, the compose
`devices:`/`group_add:` form, `HSA_OVERRIDE_GFX_VERSION`, unified-memory
sizing, and troubleshooting — already lives in
[GPU Containers](../ai/containers/gpu-containers.md) and
[Resource Limits](resources.md#gpu-access); this page does not duplicate it.

Two boundaries to remember:

- **NVIDIA / CUDA does not apply on this build.** The Strix Halo iGPU is an
  AMD/ROCm device; `nvidia/cuda:*` images and `nvidia-container-toolkit` are
  not used here.
- **macOS Docker Desktop has no GPU passthrough** (verified locally):
  `docker run --gpus all ...` fails with *"no known GPU vendor found"*, and
  Metal is never exposed to a container. On the Mac, do GPU work **natively**
  (MLX, llama.cpp Metal) rather than in a container — see
  [Apple Container limitations](../apple-container/limitations.md).

## macOS Docker Desktop vs the Linux build

Because some of this gets tested on a Mac first, keep the two environments
straight — several behaviours differ:

| Behaviour | macOS Docker Desktop (verified) | Linux build (Docker in Incus) |
|---|---|---|
| Kernel under containers | One shared `linuxkit` VM (`6.12.76-linuxkit`) for *all* containers | The real host kernel (shared by containers in the nesting container) |
| Base images | `ubuntu:24.04`, `fedora:41` run fine (aarch64) | Same images, native `aarch64` |
| `docker run --gpus all` | Fails: *"no known GPU vendor found"* — no passthrough | N/A (AMD, not `--gpus`); ROCm via `--device=/dev/kfd` |
| GPU work | Run natively (MLX / llama.cpp Metal) | ROCm into the container |
| Native alternative | [Apple Container](../apple-container/index.md) (one microVM per container) | Incus is the substrate |

## Summary: container, or Incus instead?

| Use case | Docker container? | Or use Incus |
|---|---|---|
| Throwaway shell in a specific distro | Yes — `docker run -it ubuntu:24.04 bash` | — |
| Building your own image | Yes — base image + Dockerfile | — |
| A packaged service (Postgres, nginx, Ollama) | Yes — the upstream service image | — |
| Shell into a running container | Yes — `docker exec -it` | — |
| "A tool needs an ssh endpoint" | Yes, minimally — sshd bound to localhost | — |
| A full Linux to `ssh` into and keep | No | [Incus system container](../incus/containers.md) |
| Browser/throwaway graphical desktop | Yes — `linuxserver/webtop` (LAN/Tailscale only) | — |
| A real accelerated desktop, own kernel | No | [Graphical Incus VM](../incus/graphical-access.md) |
| Full OS installed from an ISO | No | [Incus VM](../incus/vms.md), [Fedora VM](../incus/fedora-vm.md) |
| Windows | No | [Windows 11 VM](../incus/windows-vm.md) |
| GPU-accelerated inference | Yes — ROCm devices | (or an Incus GPU instance) |

## Verify

```bash
# Base userland runs, and the kernel is the HOST's, not the image's
docker run --rm ubuntu:24.04 bash -c 'cat /etc/os-release | head -1; uname -r'
# -> Ubuntu userland, host kernel version — proof it is not a booted OS

# exec-based shell works with no sshd and no published port
docker run -d --name verify-devbox ubuntu:24.04 sleep infinity
docker exec -it verify-devbox bash -c 'echo shell-in && whoami'
docker rm -f verify-devbox

# Desktop container answers on localhost only (after `docker compose up -d`)
curl -sI http://127.0.0.1:3000 | head -1        # 200/302 from KasmVNC UI
ss -ltnp | grep ':3000'                          # bound to 127.0.0.1, not 0.0.0.0

# GPU recap (Linux build only): container sees the AMD iGPU
docker run --rm --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/rocm-terminal:latest rocminfo | grep -i gfx1151
```

## Next steps

- [Docker vs system containers](docker-vs-lxc.md) — the process-vs-system
  container model that decides container-or-Incus for every row above.
- [GPU Containers](../ai/containers/gpu-containers.md) and
  [Resource Limits](resources.md#gpu-access) — the full ROCm-into-containers
  detail this page only recaps.
- [Incus containers](../incus/containers.md) — when you want a full Linux to
  live in rather than an sshd bolted into Docker.
- [Incus VMs](../incus/vms.md), [Fedora VM](../incus/fedora-vm.md),
  [Windows 11 VM](../incus/windows-vm.md) — full OSes from an ISO, and Windows.
- [Graphical access](../incus/graphical-access.md) — a real accelerated
  desktop VM, versus the browser desktop containers here.
- [Apple Container](../apple-container/index.md) and its
  [limitations](../apple-container/limitations.md) — the Mac-native runtime and
  why GPU work there stays native.
