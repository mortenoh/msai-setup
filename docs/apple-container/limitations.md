# Limitations

Apple Container is excellent at one job — running Linux containers on the Mac with a strong per-container boundary — and it is honest about not being a general-purpose hypervisor. This page draws the boundaries plainly so you reach for the right tool: no GPU/Metal into containers, Linux-only guests, and where it sits relative to [Docker Desktop](../docker/index.md) and the server's [Incus](../incus/index.md) layer.

## No GPU / Metal passthrough

There is **no `--gpu` flag and no `--device` flag** — verified against `container run --help` on 1.1.0. Apple Container does **not** expose the Mac's GPU or Metal into a container. A container cannot see or use the Apple Silicon GPU, full stop.

This is not a gap unique to Apple Container. **Docker Desktop on the Mac can't expose Metal into containers either** — the same wall, documented on [GPU containers](../ai/containers/gpu-containers.md). Mac container runtimes are CPU-only from the guest's point of view.

The practical consequence for this build's LLM work:

- **GPU LLM work on the Mac runs natively, not in a container** — MLX or llama.cpp with the Metal backend, on the host, talking to the GPU directly.
- If you need **GPU inside a container**, that is the Linux server's job: the Radeon 8060S iGPU with ROCm, passed into an Incus instance — see [Incus GPU passthrough](../incus/gpu-passthrough.md).

!!! warning "Don't try to containerize Mac GPU inference"
    There is no flag, no workaround, and no plugin that gets Metal into an Apple Container (or a Docker Desktop) container on macOS. For local GPU inference on the Mac, run the model natively with MLX/llama.cpp Metal. For containerized GPU, use the ROCm-on-Incus path on the server. Trying to bridge the two just wastes time.

## Linux-only guests

Every Apple Container "container" is a small **Linux** VM. That means:

- **No Windows guest.** You cannot boot Windows in Apple Container. The build's Windows machine is the [Incus Windows 11 VM](../incus/windows-vm.md) on the server.
- **No macOS guest.** Apple Container does not run macOS VMs.
- **No full-OS install from an ISO**, no graphical desktop VM, no arbitrary operating system. There is no ISO-boot path at all — it runs OCI images, not installer media.

For those jobs on the Mac, use a real VM tool:

- **[tart](https://github.com/cirruslabs/tart)** — macOS and Linux VMs on Apple Silicon, purpose-built for CI-style workflows.
- **UTM** — QEMU-based, general-purpose VMs (including Windows-on-ARM and, with emulation, other architectures).
- **VirtualBox** — traditional desktop VMs (with the usual Apple-Silicon caveats).

And for a full-OS or Windows guest as part of *this* build, the answer is the server's [Incus VMs](../incus/vms.md), not the Mac at all.

## vs Docker Desktop, vs Incus

The one-glance version of where each tool wins:

| Dimension | Apple Container (Mac) | Docker Desktop (Mac) | Incus (Linux server) |
|---|---|---|---|
| Runs on | macOS 15+, Apple Silicon only | macOS / Windows / Linux | Ubuntu on the MS-S1 MAX |
| Isolation unit | One Linux microVM **per container** | Containers in **one shared** Linux VM | System container or full VM |
| Kernel sharing | Dedicated kernel per container | One shared linuxkit kernel for all | Host kernel (containers) / own (VMs) |
| Container IP | Own IP, 192.168.64.0/24, directly reachable | Shared bridge, published ports | Own IP on `incusbr0` |
| GPU into container | **No** (no Metal) | **No** on Mac (no Metal) | **Yes** — ROCm/AMD passthrough |
| Windows / macOS guest | **No** | **No** | Windows: **yes** (Win11 VM) |
| Full-OS from ISO | **No** | **No** | **Yes** |
| `--rosetta` x86 translation | Yes | Yes (Rosetta emulation) | N/A (native x86 host) |
| Registry default | `docker.io` | `docker.io` | `docker:` remote / `images:` |
| Role in this build | Mac-side Linux containers | Alternative Mac runtime | The one server virtualization layer |

Reading the table:

- **Apple Container vs Docker Desktop** — same job on the Mac (Linux OCI containers), different isolation. Apple Container gives each container its own VM and a directly-reachable IP; Docker Desktop packs everything into one shared VM behind a bridge. Neither can touch the GPU. Choose Apple Container for the stronger boundary and native Apple tooling; choose Docker Desktop when you need its ecosystem (Compose UI, extensions, cross-platform parity with colleagues).
- **Either Mac runtime vs Incus** — not really competitors. The Mac runtimes run Linux *containers* locally for development. [Incus](../incus/index.md) is the server's **one virtualization layer**: it runs containers *and* full VMs, does GPU passthrough, and hosts the [Windows 11 VM](../incus/windows-vm.md). Anything needing a real GPU, a non-Linux guest, or an OS installed from an ISO belongs on the server under Incus, not on the Mac.

!!! note "The honest summary"
    Apple Container is the best-fit tool for *Linux containers on the Apple Silicon Mac* — nothing more, and it doesn't pretend otherwise. GPU inference on the Mac is native (MLX/llama.cpp Metal). Windows, full-OS VMs, and GPU-in-a-container are the Linux server's job via Incus. Keep those lanes separate and each tool stays simple.

## Verify

```bash
container run --help | grep -E -- '--gpu|--device'   # no matches — no GPU/device passthrough
container run docker.io/library/ubuntu:24.04 uname -s # Linux — the only guest kind it runs
```

## Next steps

- [Section overview](index.md) — the microVM-per-container model and the full comparison.
- [Running containers](running-containers.md) — what it *does* do well, in practice.
- [Incus GPU passthrough](../incus/gpu-passthrough.md) — the containerized-GPU path, on the server.
- [GPU containers](../ai/containers/gpu-containers.md) — why Metal doesn't reach Mac containers, in depth.
