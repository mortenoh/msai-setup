# Virtual machines

Incus runs full virtual machines — QEMU/KVM guests with their own kernel and firmware — from the same CLI as containers. This page covers Incus VMs in general: creating them, allocating resources, virtio devices, and console access. The [Windows 11 VM](windows-vm.md) page builds on this with the TPM/Secure Boot/virtio-driver specifics that guest needs.

## When a VM instead of a container

Use a VM (not a system container) when the workload needs:

- **A different or its own kernel** — kernel modules, a non-matching kernel version, real `/boot`.
- **A non-Linux OS** — Windows 11 (the main case here), BSD.
- **Stronger isolation** — hardware-virtualized boundary rather than a shared kernel.
- **TPM 2.0 / Secure Boot / UEFI firmware** — VMs emulate these; containers can't.

Everything else — the Docker stacks, the ROCm inference containers — is a container, because containers are lighter and this host's iGPU stays with the host (so there's no GPU reason to put inference in a VM).

## Creating a VM

The only difference from a container at launch is the `--vm` flag:

```bash
# A Linux VM from a community VM image
incus launch images:ubuntu/24.04 builder --vm

# Create without starting, then configure, then start
incus init images:ubuntu/24.04 builder --vm
incus config set builder limits.cpu 4
incus config set builder limits.memory 8GiB
incus config device set builder root size=60GiB
incus start builder
```

!!! note "VM images are distinct from container images"
    On the `images:` remote, an image is published either as a container rootfs or a VM disk image (some as both). If `incus launch <image> --vm` complains the image has no VM variant, pick one that does — `incus image list images: type=virtual-machine` filters to VM-capable images. This matters because a container rootfs isn't a bootable disk.

### Resource allocation

VMs allocate CPU and memory the same way as containers, but the numbers are hard reservations of virtual hardware rather than cgroup limits:

```bash
incus config set builder limits.cpu 4               # 4 vCPUs
incus config set builder limits.cpu 0-7             # pin to host cores 0-7 (one CCX)
incus config set builder limits.memory 8GiB         # RAM presented to the guest
incus config device set builder root size=60GiB     # disk size (the backing zvol)
```

!!! warning "VM memory is committed differently than container memory"
    A container's `limits.memory` is a ceiling it may not reach; a VM's `limits.memory` is RAM the guest believes it has and will use. Budget VM memory against the whole-host plan — with ARC at 16 GiB and Ollama potentially claiming ~108 GB of GTT, a large VM can create real contention. See [capacity planning](../operations/capacity-planning.md). CPU pinning to a single CCX (`limits.cpu=0-7` or `8-15`) helps cache locality on this 2-CCX Zen 5 part.

CPU pinning and topology detail:

```bash
# Expose a specific socket/core/thread topology to the guest
incus config set builder limits.cpu 4
incus config set builder limits.cpu.pin '0-3'
```

## Storage — the VM disk is a zvol

A VM's root disk is a ZFS **zvol** under `hot/incus/virtual-machines/<name>.block` (see [Storage](storage.md)). Resize it:

```bash
incus config device set builder root size=100GiB
# The guest still has to grow its own partition/filesystem to use the new space
```

Add a second disk (another volume or a passed-through path):

```bash
# A new custom volume as a second disk
incus storage volume create default builder-data --type=block
incus config device add builder data disk pool=default source=builder-data
```

## Devices: virtio and the rest

Incus VMs use **virtio** paravirtualized devices by default — virtio-net for the NIC, virtio-blk/scsi for disks, virtio for the console — which is why modern Linux guests just work and why Windows needs the virtio driver ISO ([Windows VM](windows-vm.md)).

### Networking

A VM gets an `eth0` NIC from the `default` profile, on `incusbr0`, exactly like a container:

```bash
incus config device show builder | grep -A4 eth0
# nictype/network: incusbr0, type: nic
```

The [networking page](networking.md) applies unchanged — NAT by default, proxy devices or a bridged-to-LAN setup to expose services, UFW `route allow` for forwarding.

### TPM and Secure Boot (VM-only)

VMs support an emulated **TPM 2.0** and **UEFI Secure Boot** — the two features that make Windows 11 installable. Briefly (full detail on the [Windows VM page](windows-vm.md)):

```bash
# Add an emulated TPM 2.0 device (VM only; no path/pathrm keys for VMs)
incus config device add builder vtpm tpm

# Secure Boot is a config key, on by default for VMs
incus config get builder security.secureboot        # default: true
incus config set builder security.secureboot false  # disable if a guest needs it off
```

Both verified against the current Incus [TPM device](https://linuxcontainers.org/incus/docs/main/reference/devices_tpm/) and [instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/) docs — `security.secureboot` is a bool defaulting to `true`, VM-only.

!!! note "No GPU passthrough to VMs on this build"
    Incus VMs *can* take a `gpu` device, but this build keeps the iGPU on the host for ROCm and passes it to **containers** ([GPU passthrough](gpu-passthrough.md)), never to a VM. GPU-in-a-VM here would mean losing host ROCm, which defeats the box's purpose. VMs run headless/virtio-graphics only.

### Other devices

```bash
# Attach an ISO for installation (a disk device pointing at an image)
incus config device add builder install disk source=/path/to/os.iso boot.priority=10

# Pass a host directory into a Linux VM (shared via virtiofs)
incus config device add builder shared disk source=/tank/media path=/mnt/media
```

## Console and graphical access

VMs have no `incus exec` (there's no shared kernel to inject a process into) — you reach them via console or the network.

### Text console

```bash
# Attach to the VM's serial console (boot messages, a getty login)
incus console builder

# Detach: press Ctrl-a then q
```

### VGA / graphical console

For a graphical console (a Linux desktop, or Windows before RDP is up):

```bash
incus console builder --type=vga
```

This opens a graphical console via the local `remote-viewer`/SPICE viewer if available. On this headless host you'll usually drive the VM over the network once it's booted — SSH for Linux, [RDP for Windows](windows-vm.md) — rather than the VGA console day to day. The VGA console's main job is initial install and rescue.

### Agent-based exec (Linux guests)

Linux VM images that ship the **incus-agent** do support a limited `incus exec` over a virtio-vsock channel:

```bash
incus exec builder -- uname -a      # works if the guest runs incus-agent
```

Community Ubuntu/Debian VM images include the agent. Custom or Windows guests won't have it — use console/SSH/RDP instead.

## Lifecycle (same as containers)

```bash
incus start builder
incus stop builder                 # graceful ACPI shutdown
incus stop builder --force         # power off
incus restart builder
incus pause builder                # suspend
incus info builder                 # state, resources
incus snapshot create builder pre-change
incus delete builder --force       # destroys the VM and its zvol
```

Snapshots of a VM are snapshots of its zvol — see [Snapshots & backup](snapshots-backup.md). For a consistent snapshot of a running VM, prefer stopping it (or use the guest-agent's freeze if available); a hot zvol snapshot is crash-consistent at best.

## Verify

```bash
incus list                          # TYPE column shows VIRTUAL-MACHINE
incus info builder                  # vCPUs, memory, disk
incus config show builder           # effective config
incus console builder               # reach the console
```

## Next steps

- [Windows 11 VM](windows-vm.md) — TPM, Secure Boot, virtio drivers, RDP.
- [Storage](storage.md) — how VM zvols are laid out and snapshotted.
- [Networking](networking.md) — exposing VM services.
- [Snapshots & backup](snapshots-backup.md) — VM snapshot/export workflow.
