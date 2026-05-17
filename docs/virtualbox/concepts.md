# VirtualBox Concepts

The mental model. Skim this if you're new to virtualization; skip if you already know what a hypervisor is.

## What virtualization is

A hypervisor runs **guest** operating systems on top of the **host** OS by emulating hardware and trapping privileged instructions. The guest thinks it has its own CPU, RAM, disks, and network — really it's all serviced by the hypervisor on the underlying physical hardware.

Two flavours:

| Type | Where it runs | Examples |
|---|---|---|
| **Type 1 (bare-metal)** | Directly on the hardware; no host OS underneath | ESXi, Proxmox, KVM (technically a kernel module — boundary blurry) |
| **Type 2 (hosted)** | As an application on a normal OS | VirtualBox, VMware Workstation, Parallels |

VirtualBox is Type 2. On Linux it uses KVM under the hood when available; on macOS it uses the Hypervisor.framework (HVF) on Apple Silicon. The host OS continues to run normally; VirtualBox is just another application.

## What a "VM" actually is

A VirtualBox VM is two things:

1. **Configuration** — an XML file plus VirtualBox's registry. Specifies how much RAM, how many CPUs, which firmware, which storage controllers, which disks/ISOs are attached, networking settings, etc.
2. **Storage** — one or more virtual disk files (VDI/VMDK/VHD/etc.) on the host filesystem. These are the guest's "physical" disks.

When you `VBoxManage startvm`, VirtualBox reads the config, allocates the requested RAM, starts emulating the configured CPU/devices, and loads the boot device — which then boots the guest OS exactly as if it were on physical hardware.

On disk for a VM named `test`:

```
~/VirtualBox VMs/
  test/
    test.vbox          # XML config (current)
    test.vbox-prev     # backup of the previous config
    Logs/              # per-boot VBox.log files
    Snapshots/         # snapshot disk deltas (.vdi-typed)
    test.vdi           # the primary disk
    # (other disks may live elsewhere — they're referenced by path)
```

The VM is **registered** in VirtualBox's machine list; you can see it with `VBoxManage list vms`. Unregistering it (`VBoxManage unregistervm`) removes it from the list; the files only delete if you pass `--delete`.

## Virtual hardware

VirtualBox emulates a fairly fixed set of virtual hardware. The bits we care about:

### CPU

The guest sees emulated/virtualized CPUs. On Apple Silicon hosts, the guest CPU is ARM64; on x86 hosts, x86_64. VirtualBox uses hardware virtualization (VT-x on Intel, AMD-V on AMD, Apple's HVF on macOS ARM) so most instructions run natively at native speed — only privileged ones are trapped and emulated.

You configure: number of cores, whether the guest sees NUMA topology, PAE/NX, hardware virt for nested-VMs, etc. For lab VMs the defaults are fine — just set `--cpus` to a sensible count.

### Memory

Allocated from host RAM at VM start. Returned to the host when the VM stops. There's no overcommit by default — if you ask for 8 GiB and the host doesn't have it free, the VM won't start.

### Storage controllers

Virtual controllers the guest sees. The most useful:

| Controller | What it is | Guest sees | Use |
|---|---|---|---|
| **SATA** (`IntelAhci`) | Standard AHCI controller | `/dev/sda`, `/dev/sdb`, ... | Default for almost everything. Up to 30 ports. |
| **IDE** | Old PATA controller | `/dev/sda` (or hd) | Maximum-compatibility CD-ROMs on older OSes. |
| **NVMe** | NVM Express | `/dev/nvme0n1` | Realistic NVMe simulation; newer guests only. |
| **SCSI** (`LsiLogic` etc.) | Various SCSI HBAs | `/dev/sda` (SCSI numbering) | Compatibility with old enterprise OSes. |
| **USB** | USB controllers | USB devices | For USB pass-through. |

For Linux guests: **SATA is the default choice**. NVMe is fine too. IDE has compatibility quirks on ARM (the lab learned this the hard way — see [Apple Silicon](apple-silicon.md)).

### Disks

Virtual disks are files on the host. Formats:

| Format | Made by | Notes |
|---|---|---|
| **VDI** | VirtualBox | Native; supports snapshots, dynamic sizing. Default for new disks. |
| **VMDK** | VMware | Cross-VMware/VBox compatible. |
| **VHD/VHDX** | Microsoft | Hyper-V compatible. |
| **RAW** | (just a file) | No metadata; what `dd` would produce. |

Default is **VDI dynamic-allocated** — the file starts small and grows as the guest writes. Pre-allocated is faster on first write but takes the full size up front. For lab work, dynamic is fine.

### Networking

Per NIC, you pick a "type" that determines how the guest sees the network:

| Mode | Guest connectivity | Host can reach guest? | Other guests can reach guest? |
|---|---|---|---|
| **NAT** | Internet via host NAT (10.0.2.0/24, host = 10.0.2.2) | Only via port-forward | No (different NAT per VM) |
| **NAT Network** | Internet + shared subnet across VMs | Only via port-forward | Yes (shared NAT) |
| **Bridged** | Joins the host's LAN; gets a LAN IP | Yes (via the LAN IP) | Yes (same LAN) |
| **Host-only** | Isolated network with the host; no internet | Yes | Yes (same vboxnetN) |
| **Internal** | Isolated network without the host | No | Yes (same intnet name) |

For the lab: **NAT** with a host port-forward for SSH (`127.0.0.1:2222 -> guest:22`). This works on Apple Silicon and doesn't need to ask the LAN router for a DHCP lease.

### Display

In headless mode the display goes nowhere (a framebuffer exists for screenshot purposes only). Otherwise VBox exposes a window with the guest's framebuffer, plus optional VRDE (RDP) for remote access.

The graphics controller emulated to the guest (`vboxvga`, `vmsvga`, `qemuramfb`, etc.) determines what driver the guest loads. For ARM Linux guests, **only `qemuramfb` works** — the others crash with `VERR_PGM_RAM_CONFLICT`. For x86 Linux, `vmsvga` is the modern default.

## Snapshots

A snapshot freezes the **entire VM state** — disks, RAM (if running), the current settings — at a moment in time. After the snapshot, all subsequent writes go to a delta file; the original disk image stays untouched.

```
Before snapshot:     test.vdi  (all writes go here)

Snapshot taken:      test.vdi  (read-only base)
                     Snapshots/{uuid}.vdi  (writes go here now)
```

Restoring a snapshot discards the delta — the VM reverts to exactly the state when the snapshot was taken.

Snapshots can branch — after restoring snapshot S1, you can take a new snapshot S2 that creates a new branch in the tree. The lab uses snapshots heavily for "fresh-install, experiment, roll back, experiment again" cycles.

Trade-off: a snapshot chain that gets long (many snapshots in sequence) starts to slow down disk I/O — each read walks the chain looking for the most recent block. Periodically deleting old snapshots merges them back into the base.

## VBox vs the alternatives, briefly

| | VBox | Multipass | UTM | Tart | KVM/QEMU |
|---|---|---|---|---|---|
| Platform | mac/linux/win | mac/linux/win | mac only (UI), free | mac only, free | linux only |
| Apple Silicon ARM Linux | tech-preview-quality | great | great | great | n/a (mac) |
| Headless first-class | yes | yes | clunky | yes | yes |
| CLI automation | excellent (VBoxManage) | excellent (multipass) | OK | excellent | excellent (libvirt) |
| Snapshots | mature | basic | mature | yes | mature |
| Multiple disks per VM | trivial | hard (one default) | easy | easy | easy |
| Live VM migration | no | no | no | no | yes |
| Networking flexibility | high | medium | medium | medium | very high |

For this build's needs (cross-platform CLI scripting, multiple lab disks for ZFS, snapshots), VirtualBox is the right pick despite the Apple Silicon ARM quirks.

## A note about the "Extension Pack"

VirtualBox has two parts:

- **Base** (GPL): everything we use in the lab. Free.
- **Extension Pack** (proprietary, free for personal use): adds USB 2.0/3.0 pass-through, VRDE server (RDP for headless console), disk encryption, PXE boot ROM for Intel cards.

The lab uses **VRDE** (from the Extension Pack) when falling back to interactive install on ISOs the unattended templates don't support. If you don't install the Extension Pack, that fallback path doesn't work — but the main flow (unattended via our cloud-init ISO) does.

Install:

```bash
# macOS
brew install --cask virtualbox-extension-pack
# (or download from virtualbox.org)
```

## Where to go next

- [Installation](installation.md) — get VirtualBox installed
- [VBoxManage CLI](vboxmanage.md) — the actual commands
- [Apple Silicon](apple-silicon.md) — if you're on a Mac with ARM, read this before anything else
