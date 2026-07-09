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

More detail on both:

- The emulated TPM is backed by **swtpm** (present on this host); Incus wires it to the VM's firmware so the guest sees a TPM 2.0. TPM devices **cannot be hot-plugged** — add the `tpm` device while the VM is **stopped**.
- `security.secureboot=true` enforces UEFI Secure Boot with the default Microsoft keys, which is exactly what a stock Windows 11 install wants. A common mistake is copying a Linux recipe that turns it *off* and then wondering why the Win11 installer rejects the machine — leave it at its `true` default unless a specific unsigned bootloader needs it off.
- These two features are the whole reason Windows 11 is installable here; the [Windows VM](windows-vm.md) page walks the full `vtpm` + Secure Boot + autounattend flow.

!!! note "No GPU passthrough to VMs on this build"
    Incus VMs *can* take a `gpu` device, but this build keeps the iGPU on the host for ROCm and passes it to **containers** ([GPU passthrough](gpu-passthrough.md)), never to a VM. GPU-in-a-VM here would mean losing host ROCm, which defeats the box's purpose. VMs run headless/virtio-graphics only.

### Other devices

```bash
# Pass a host directory into a Linux VM (shared via virtiofs)
#   NOTE: blocked in the restricted user-1000 project — see the ISO/storage
#   caveat below; share via a managed volume instead of a raw host path.
incus config device add builder shared disk source=/data/media path=/mnt/media
```

Attaching an **install ISO** is also a `disk` device, but in this build's restricted project it needs the managed-volume route — see the next section.

## Installing a VM from an ISO

The community `images:` remote gives you ready-to-boot Linux VM images, but for a Windows guest, a custom distro, or anything not on `images:`, you create a **blank** VM and boot it from an installation ISO.

```bash
# A blank VM with no OS — just firmware, a disk, and (soon) an ISO to boot
incus init installer-vm --vm --empty \
  -c limits.cpu=4 -c limits.memory=8GiB -d root,size=60GiB
```

### The restricted-project ISO gotcha (managed volumes)

This build runs instances in the **`user-1000` project**, a restricted unprivileged project. Restricted projects **forbid raw host-path disk devices** — you cannot do `incus config device add vm install disk source=/data/iso/foo.iso` and have it attach; the project policy rejects a host path as a disk source. Instead, **import the ISO as a managed storage volume** of type `iso`, then attach *that volume*:

```bash
# 1. Import the ISO file into the 'lab' pool as an iso-type storage volume
incus storage volume import lab /data/iso/ubuntu-24.04.iso ubuntu-iso --type=iso

# 2. Attach the managed ISO volume as a boot device, boot.priority high so it boots first
incus config device add installer-vm install disk \
  pool=lab source=ubuntu-iso boot.priority=10

# 3. Start and open the graphical console to run the installer
incus start installer-vm
incus console installer-vm --type=vga
```

!!! warning "`--type=iso` matters, and so does the pool name"
    The volume must be imported `--type=iso` — a plain custom volume won't be treated as bootable optical media. The pool here is **`lab`** (this build's ZFS pool, source dataset `lab/incus`), not `default`. List imported ISOs with `incus storage volume list lab type=iso`. This managed-volume path is *mandatory* in the `user-1000` project — the raw-host-path `source=/path/to.iso` form you'll see in generic Incus guides simply will not attach here.

### `boot.priority` — booting the ISO before the disk

`boot.priority` sets device boot order (higher boots first). Give the install ISO a high priority (e.g. `10`) so firmware boots the installer, not the empty disk:

```bash
incus config device set installer-vm install boot.priority 10
```

### Detach the ISO after install

Once the OS is installed to the root disk, **remove the install ISO** so the VM boots from disk on the next start (otherwise it may re-enter the installer):

```bash
incus stop installer-vm
incus config device remove installer-vm install
incus start installer-vm

# Optionally reclaim the imported ISO volume once no VM needs it
incus storage volume delete lab ubuntu-iso
```

## Unattended / autoinstall

Clicking through an installer over the SPICE console is fine once; for reproducibility you want a **fully unattended** install. For Ubuntu that means **autoinstall** (the Subiquity/cloud-init-driven installer) fed a `user-data` seed.

### The one-confirmation-prompt problem

There is a specific trap: Ubuntu's autoinstall, when it finds an autoinstall config, still shows a **single interactive confirmation prompt** ("this will erase the disk, continue?") *unless* you pass `autoinstall` on the kernel command line. Providing the seed alone is not enough — without the `autoinstall` kernel arg you get one prompt that defeats the whole point of an unattended install. The fix is to boot the installer with `autoinstall` on the kernel cmdline, which suppresses that confirmation.

Because you cannot easily edit the kernel cmdline of a managed ISO volume at boot in a headless flow, the robust pattern is to **repack the ISO** with the `autoinstall` kernel argument baked into the bootloader config, plus a **NoCloud** seed carrying the `user-data`.

### A minimal Ubuntu autoinstall `user-data`

```yaml
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  keyboard:
    layout: us
  identity:
    hostname: ubuntu-vm
    # password hash: `mkpasswd --method=SHA-512` (do not commit a real hash to git)
    username: morten
    password: "$6$rounds=4096$REPLACE_WITH_A_REAL_HASH"
  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - "ssh-ed25519 AAAA... your-key"
  storage:
    layout:
      name: direct          # whole-disk, single root — simplest for a VM
  packages:
    - qemu-guest-agent
  late-commands:
    # Ensure the incus-agent / cloud-init finalization runs; install a desktop later if wanted
    - curtin in-target --target=/target -- systemctl enable ssh
  user-data:
    disable_root: true
```

### Wiring the seed to the ISO (NoCloud + kernel arg)

Two moving parts: the **NoCloud datasource** (where the installer reads `user-data`) and the **kernel argument** (which suppresses the confirmation prompt).

- **NoCloud seed**: place `user-data` and an empty `meta-data` where the installer looks. The common repack approach embeds a seed directory on the ISO and points the kernel at it with `ds=nocloud;s=/cdrom/server/` (or serves it over HTTP with `ds=nocloud-net;s=http://.../`).
- **Kernel argument**: add `autoinstall` (and the `ds=` above) to the GRUB/isolinux kernel line inside the repacked ISO.

A common toolchain for the repack is `cloud-localds` (to build the seed) plus a manual ISO remaster, or Incus's `distrobuilder` for image builds. Sketch:

```bash
# Build a NoCloud seed image from user-data + meta-data
cloud-localds seed.iso user-data meta-data

# Repack the Ubuntu ISO: extract, edit GRUB to add:
#   linux /casper/vmlinuz ... autoinstall ds=nocloud;s=/cdrom/nocloud/
# then rebuild the ISO (xorriso), import it as a managed volume, and boot it.
incus storage volume import lab ubuntu-autoinstall.iso ubuntu-auto --type=iso
incus config device add installer-vm install disk pool=lab source=ubuntu-auto boot.priority=10
```

!!! note "Why the kernel arg, not just the seed"
    Repeating the crux because it wastes the most time: a NoCloud seed *alone* still triggers the interactive "continue and erase?" confirmation. The `autoinstall` **kernel argument** is what makes the install truly hands-off. If your unattended install hangs on one prompt at the SPICE console, the missing kernel arg is why. For Windows, the equivalent fully-unattended mechanism is `autounattend.xml` — see [Windows VM](windows-vm.md).

## Console and graphical access

VMs have no namespace-injected `incus exec` (there's no shared kernel) — you reach them via the console channels, the agent, or the network. The full treatment — the SPICE stack, local vs remote access, virtual GPU options, clipboard/resolution/USB, and troubleshooting — is its own page: **[Graphical access](graphical-access.md)**. The essentials:

### Text console

```bash
# Attach to the VM's serial console (boot messages, a getty login)
incus console builder

# Detach: press Ctrl-a then q  (this does NOT stop the VM)
```

### VGA / graphical console

For a graphical console (a Linux desktop, or Windows before RDP is up):

```bash
incus console builder --type=vga     # opens a local remote-viewer/SPICE window
```

On this headless host you'll usually drive the VM over the network once it's booted — SSH for Linux, [RDP for Windows](windows-vm.md) — rather than the VGA console day to day. The VGA console's main jobs are **initial install** and **rescue**. See [Graphical access](graphical-access.md) for reaching it remotely (SSH socket-forwarding or a remote Incus client), the virtual-GPU/no-hardware-accel reality on this box, and every graphics knob.

### The incus agent (Linux guests)

Linux VM images from `images:` ship the **incus-agent**, a guest daemon that talks to the host over **virtio-vsock**. It is what makes `incus exec` and `incus file` work on a VM (unlike a container, there's no shared kernel to inject into — the agent is the bridge):

```bash
incus exec builder -- uname -a               # works only if incus-agent is running
incus exec builder -- systemctl status incus-agent
incus file push ./file builder/root/file     # agent-backed file transfer
```

Community Ubuntu/Debian VM images include the agent; custom-built and Windows guests won't have the Linux agent (Windows has its own agent in spice-guest-tools). If `incus exec` fails but `incus console` works, the agent is missing/stopped — that split is diagnostic. The agent is **separate from the graphical console**: you can have a working desktop and a dead agent, or vice versa ([Graphical access -> the incus agent](graphical-access.md#the-incus-agent-in-vms)).

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

- [Graphical access](graphical-access.md) — the SPICE/VGA console in depth, remote desktop access, virtual GPU, clipboard/resolution, troubleshooting.
- [Windows 11 VM](windows-vm.md) — TPM, Secure Boot, virtio drivers, autounattend, RDP.
- [Storage](storage.md) — how VM zvols are laid out and snapshotted.
- [Networking](networking.md) — exposing VM services.
- [Snapshots & backup](snapshots-backup.md) — VM snapshot/export workflow.
