# Running containers

With the service up (see [Installation](installation.md)), running containers with Apple Container feels like Docker with a different last mile. This page covers pulling and running base images, detached containers, names, ports, volumes, `exec`, the **per-container IP** model, `--rosetta` for x86 images, an SSH-into-a-container pattern, and building your own images. The `container run` flags shown here are taken from `container run --help` on version 1.1.0 — where a command's output is quoted it was verified locally.

## Pull and run a base image

The registry defaults to **`docker.io`**, so ordinary image references just work. Both Ubuntu and Fedora were verified, and pulled images are **arm64-native** on Apple Silicon:

```bash
# Fully-qualified reference (docker.io is the default, so the prefix is optional)
container run docker.io/library/ubuntu:24.04 uname -r     # -> 6.12.28
container run docker.io/library/fedora:41 cat /etc/os-release

# The short form resolves against docker.io too
container run ubuntu:24.04 echo "hello from a microVM"
```

That `uname -r` output — **6.12.28** — is the headline: it is *this container's own kernel*, from its own Linux microVM, not a shared host kernel. Every container you start gets its own. Contrast Docker Desktop, where every container reports the one shared `6.12.76-linuxkit` kernel.

## Interactive shells and `exec`

```bash
# Interactive shell in a throwaway container (-i/-t like Docker; --rm auto-removes)
container run --rm -it ubuntu:24.04 bash

# Run a detached, named container, then exec into it
container run -d --name web docker.io/library/ubuntu:24.04 sleep infinity
container exec -it web bash

# One-off command in a running container
container exec web hostname -I        # prints the container's own IP (see below)
```

Verified management commands: `container ls`, `container ls -a`, `container inspect <name>`, `container stop <name>`, `container rm <name>`, and `container images ls`.

## The per-container IP model

Because each container is its own VM, each gets its **own IP** on a dedicated subnet — verified at `192.168.64.0/24`. A running container appeared as **`192.168.64.2/24`**, shown both in the **IP column** of `container ls` and via `hostname -I` inside the container:

```bash
container ls                          # note the IP column, e.g. 192.168.64.2
container exec web hostname -I        # 192.168.64.2  — same address, from inside
```

There is no shared `docker0`-style bridge fronting the containers with published-ports-only reachability. Containers are **first-class network peers**: you can reach one directly on its IP from the host (and from sibling containers) without publishing a port at all. This is closer to how instances behave on `incusbr0` under [Incus](../incus/networking.md) than to Docker Desktop's bridge.

!!! tip "You often don't need `-p` at all"
    On Docker you publish a port to reach a service. Here, if you just want to hit the container from your Mac, use its `192.168.64.x` address directly. Publishing (below) still matters when you want the service on `localhost` or a fixed host port.

## Ports and volumes

Verified `container run` flags include `-p/--publish`, `--publish-socket`, `-v/--volume`, and `--mount`:

```bash
# Publish a container port to the host
container run -d --name nginx -p 8080:80 docker.io/library/nginx:latest
# -> reachable at http://localhost:8080  (and directly at the container IP:80)

# Bind-mount a host directory into the container
container run --rm -it -v "$HOME/code:/work" ubuntu:24.04 bash

# --mount is the longer, explicit form for the same idea
container run --rm -it --mount source="$HOME/code",target=/work ubuntu:24.04 bash
```

Other verified `run` flags worth knowing: `-c/--cpus` and `-m/--memory` (resource caps), `-a/--arch` / `--platform` (image architecture selection), `--dns-search`, `--name`, `-d` (detach), and `--rm` (remove on exit).

```bash
# Cap CPUs and memory for a container
container run -d --name db -c 2 -m 2g docker.io/library/postgres:16
```

## Running x86 images with `--rosetta`

Images pull arm64-native by default, but sometimes you must run an **amd64** image or binary (a tool with no arm64 build, an x86-only base image). The verified `--rosetta` flag enables **Rosetta x86_64 translation inside the container** so amd64 code runs:

```bash
# Run an amd64 image with Rosetta translation inside the container
container run --rm -it --rosetta --platform linux/amd64 \
  docker.io/library/ubuntu:24.04 bash
# inside: uname -m now reports x86_64-class behaviour via Rosetta
```

Reach for `--rosetta` only when you actually need x86 — arm64-native is faster and the default for a reason.

## SSH into a container

Two patterns, depending on whether you want a real SSH daemon or just a shell.

**Usually you don't need SSH at all** — `container exec` gives you a shell directly:

```bash
container exec -it web bash        # the simplest "get into the container"
```

When you *do* want a genuine `sshd` (e.g. to test an SSH-based workflow, or use the container like a tiny remote host), install and run sshd in the container. Because the container has its **own IP**, you can SSH straight to that address — publishing port 22 is optional:

```bash
# Start a container, install and configure sshd inside it
container run -d --name sshbox docker.io/library/ubuntu:24.04 sleep infinity
container exec sshbox bash -lc '
  apt-get update && apt-get install -y openssh-server &&
  mkdir -p /run/sshd &&
  echo "root:changeme" | chpasswd &&
  sed -i "s/^#\?PermitRootLogin.*/PermitRootLogin yes/" /etc/ssh/sshd_config &&
  /usr/sbin/sshd -D &        # run the daemon
'

# SSH directly to the container's own IP (from `container ls`), no port publish needed
ssh root@192.168.64.2

# --- or, if you prefer localhost + a published port ---
# container run -d --name sshbox -p 2222:22 ... then: ssh -p 2222 root@localhost
```

!!! warning "That sshd recipe is a lab convenience, not a hardened setup"
    Password root login and a literal password are fine for a throwaway local container and nothing else. For anything you keep, use keys and a non-root user. And remember these containers are Apple-Silicon-local dev instances — the build's real remote-access conventions (Tailscale-gated, key-based) live under the server's [remote-desktop](../remote-desktop/rdp/windows-setup.md) and networking sections.

## Building images

`container build` builds from a **Dockerfile** or **Containerfile**, so your existing build files work unchanged:

```bash
# Build an image from ./Dockerfile in the current directory
container build -t myapp:dev .

# Run what you just built
container run --rm -it myapp:dev
```

Because the images are ordinary OCI images, something you build and test here can later run under [Docker in Incus](../incus/docker-in-incus.md) or as an [OCI application container](../incus/oci-containers.md) on the Linux server — the artifact is portable; only the runtime differs.

!!! note "Registry login and pushing"
    Pulling from public `docker.io` needs no auth. For private registries or pushing, use the tool's standard login/push flow (`container --help` lists the registry subcommands for your version). The exact syntax is version-dependent — check `container --help` and the [apple/container project](https://github.com/apple/container) rather than assuming Docker's exact `login`/`push` spelling.

## Verify

```bash
container run docker.io/library/ubuntu:24.04 uname -r     # 6.12.28 (its own kernel)
container run -d --name t docker.io/library/ubuntu:24.04 sleep infinity
container ls                                              # note IP column, e.g. 192.168.64.2
container exec t hostname -I                              # same IP, from inside
container stop t && container rm t                        # clean up
```

## Next steps

- [Limitations](limitations.md) — no GPU/Metal, Linux-only guests, and the full Docker/Incus comparison.
- [Installation](installation.md) — service management and the post-upgrade version-mismatch gotcha.
- [Docker in Incus](../incus/docker-in-incus.md) — where these same images run on the server.
