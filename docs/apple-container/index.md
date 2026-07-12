# Apple Container — Linux containers on the Mac

This section is the **Mac-side companion** to the Linux box's container story. The primary build runs [Incus](../incus/index.md) as the one virtualization layer with [Docker](../docker/index.md) nested inside it — that is all Linux, on the MS-S1 MAX. But day-to-day development happens on an **Apple Silicon Mac (M2 Max, macOS 26)**, and the tool that plays the Incus/Docker role there is **[Apple Container](https://github.com/apple/container)** — Apple's native macOS container runtime, driven by the `container` CLI.

Apple Container runs standard **OCI Linux containers** on macOS, the same images you'd run under Docker or push into an Incus OCI instance. What makes it interesting — and worth its own section rather than a footnote on the Docker page — is *how* it runs them: not one shared Linux VM for everything, but **one lightweight Linux microVM per container**, each with its own kernel. That is a genuinely different isolation model from Docker Desktop, and it changes how you reason about the containers you run.

!!! note "This is the Mac dev machine, not the server"
    Nothing in this section runs on the MS-S1 MAX. The Linux home server uses Incus (host layer) and Docker (nested), documented under [Incus](../incus/index.md) and [Docker](../docker/index.md). Apple Container is the local, Apple-Silicon-only tool for spinning up Linux containers on macOS without Docker Desktop. Where a comparison sharpens the picture, this section links back to those pages.

## What Apple Container is

Apple Container is an open-source command-line tool (`container`) plus a background service that runs OCI images as containers on macOS. Under the hood it uses Apple's **Virtualization.framework** and the **Containerization** Swift package to boot a minimal Linux VM for each container. It requires **macOS 15+ on Apple Silicon** — there is no Intel-Mac path, and no Linux or Windows build; it is a macOS-native tool by design.

From the outside it feels like Docker: you `container run` an image, `container exec` into it, `container build` from a Dockerfile, `container ls` to see what's running. The registry defaults to `docker.io`, so `container run ubuntu:24.04` pulls the same Ubuntu image Docker would. The verified CLI at the time of writing is **`container` version 1.1.0**.

## The microVM-per-container model — the key differentiator

This is the whole reason Apple Container is architecturally distinct, and it was verified locally:

- Launch an `ubuntu:24.04` container and run `uname -r` inside it: the kernel is **6.12.28** — a dedicated Linux kernel belonging to *that container's* VM.
- Docker Desktop, by contrast, runs **one shared `linuxkit` VM** (its kernel reports as `6.12.76-linuxkit`) and every container you start is a process inside that single VM, sharing that one kernel.

So the mental model is:

- **Apple Container** = one microVM per container, each with its own kernel. Stronger isolation boundary — a container is a VM, not just a namespaced process next to your other containers.
- **Docker Desktop** = one shared VM, many containers inside it, all on the same kernel.

This mirrors, on the Mac, the same instinct the Linux box follows with Incus: prefer a real isolation boundary per workload. On the server that boundary is an Incus system container or VM; on the Mac, Apple Container gives each container its own VM for free.

!!! tip "Networking follows from the model"
    Because each container is its own VM, each gets its **own IP** on a dedicated subnet — verified at `192.168.64.0/24`, with a running container showing `192.168.64.2/24` in the `container ls` IP column and via `hostname -I` inside. There is no shared `docker0`-style bridge with port-only reachability; containers are **first-class network peers** you can address directly by IP. See [Running containers](running-containers.md) for what that enables.

## How it relates to Docker Desktop and to Incus

| Dimension | Apple Container (Mac) | Docker Desktop (Mac) | Incus (Linux server) |
|---|---|---|---|
| Where it runs | macOS 15+, Apple Silicon only | macOS / Windows / Linux | Ubuntu on the MS-S1 MAX |
| Isolation unit | One Linux microVM **per container** | One shared Linux VM, containers inside | System container (shared host kernel) or full VM |
| Kernel | Dedicated per container (6.12.28 seen) | One shared linuxkit kernel | Host kernel (containers) / own kernel (VMs) |
| Container networking | Per-container IP on 192.168.64.0/24 | Shared bridge, published ports | `incusbr0` bridge, per-instance IP |
| Registry default | `docker.io` | `docker.io` | `docker:` remote / `images:` |
| GPU passthrough | **None** (no Metal into containers) | **None** on Mac (no Metal into containers) | ROCm/AMD passthrough to instances |
| Full-OS / Windows guests | No — Linux containers only | No | Yes — VMs incl. [Windows 11](../incus/windows-vm.md) |
| Role in this build | Mac-side Linux containers | Alternative Mac runtime | The one server virtualization layer |

The short version: on the Mac, Apple Container and Docker Desktop are **alternatives** for the same job (running Linux containers), with Apple Container trading a shared VM for a stronger per-container boundary and native Apple tooling. Neither is the server. On the server, [Incus](../incus/index.md) is the one virtualization layer and does things neither Mac runtime can — full-OS VMs from an ISO, a Windows guest, real GPU passthrough.

## When to reach for it on the Mac

- You want to run or test a **Linux container** locally on the Mac without installing Docker Desktop.
- You want **stronger isolation** between containers than a shared VM gives — each container is its own VM.
- You are on **Apple Silicon** and want arm64-native images, with `--rosetta` available when you must run an amd64 image.
- You are prototyping something you'll eventually run under [Docker in Incus](../incus/docker-in-incus.md) on the server — the images are the same OCI images.

## The matrix reality — what it does and does not do

Apple Container is excellent at running Linux containers on the Mac. It is **not** a general-purpose hypervisor:

- **Great for**: Linux OCI containers (Ubuntu, Fedora, Alpine, language runtimes, dev databases) on Apple Silicon.
- **N/A for**: booting a full OS from an ISO, running a **Windows** or macOS guest, or a graphical desktop VM. There is no ISO-install path and no non-Linux guest. For those on the Mac you use **[tart](https://github.com/cirruslabs/tart)**, **UTM**, or **VirtualBox**; for a real Windows guest on this build, that's the [Incus Windows 11 VM](../incus/windows-vm.md) on the server.
- **No GPU/Metal** into containers — see [Limitations](limitations.md). Local LLM GPU work on the Mac runs **natively** (MLX / llama.cpp Metal), not in a container.

## The shape of this section

Read in order — each page assumes the model built by the one before it.

- [Installation](installation.md) — installing Apple Container, `container system start/status/stop`, and the version-mismatch gotcha that bites after an upgrade.
- [Running containers](running-containers.md) — pulling and running Ubuntu/Fedora and other images, detached runs, names, ports, volumes, `exec`, the per-container IP model, `--rosetta` for x86 images, SSH-into-a-container, and building images.
- [Limitations](limitations.md) — no GPU/Metal passthrough, Linux-only guests, and a clear comparison against Docker Desktop and against Incus on the server.

## Verification note

The commands and behaviours called out as **verified/tested** in this section were run on the author's M2 Max under macOS 26.5.2 with `container` 1.1.0. Everything else (installer specifics, log syntax, registry login) is described as standard usage — verify it against `container --help` and the [apple/container project](https://github.com/apple/container) for your installed version, since a fast-moving tool changes flags and defaults between releases.
