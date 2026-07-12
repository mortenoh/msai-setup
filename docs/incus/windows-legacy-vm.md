# Windows legacy VM (9x / 2000 / XP)

This page covers **pre-UEFI, pre-virtio** Windows — Windows 95/98/ME, Windows 2000, and Windows XP — as Incus VMs. Unlike [Windows 11](windows-vm.md) and [Windows 7/10](windows-7-10-vm.md), these releases predate almost everything Incus's VM defaults assume: they want legacy BIOS instead of UEFI, IDE/SATA disks instead of virtio, an emulated legacy NIC instead of virtio-net, and (for 9x) have no Remote Desktop at all. Getting them running is a retro/hobby exercise, not a supported build path.

!!! warning "This is a retro exercise — expect fiddliness, and don't rely on it"
    Windows 9x/2000/XP are **out of support**, receive no security fixes, and were built for hardware nothing like a modern QEMU q35 machine. Nothing here is guaranteed to boot on the first try: firmware, disk bus, and NIC all need overrides away from Incus's defaults, and the exact overrides are **version-dependent**. Treat every command below as a starting point to verify against the Incus and QEMU docs for your installed versions, not a copy-paste recipe. Keep these VMs on the LAN/Tailscale only, snapshot aggressively, and assume you'll iterate.

!!! note "The iGPU stays with the host — 2D emulated graphics only"
    As with every Windows VM on this build, the Radeon 8060S iGPU stays with the **host** for ROCm; there is no passthrough. These guests render to an emulated VGA/cirrus adapter streamed over SPICE. That's actually a *good* fit here — legacy Windows has no virtio-gpu driver and expects a plain VGA card anyway.

## Why the defaults don't fit

Incus VMs default to a **modern machine**: UEFI (OVMF) firmware on a QEMU **q35** machine type, with **virtio** disk, NIC, and graphics. Modern Linux and Windows 10/11 thrive on that. Legacy Windows chokes on all three layers:

| Layer | Incus default | What 9x / 2000 / XP need |
|---|---|---|
| Firmware / machine | UEFI (OVMF), q35 | Legacy BIOS (SeaBIOS / CSM), i440fx-style |
| Boot disk | virtio-scsi / virtio-blk | IDE (or SATA/AHCI for XP with F6) |
| NIC | virtio-net | Emulated rtl8139 or e1000 |
| Graphics | virtio-gpu | std VGA / cirrus |
| Guest agent | incus-agent / spice-vdagent | none (period tools only) |

The rest of this page is how to override each layer.

## Firmware and machine type

The documented Incus knob is **`security.csm`** — a VM-only bool (**default `false`**) described in the [instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/) as enabling "a firmware that supports UEFI-incompatible operating systems." That is the Compatibility Support Module (legacy-BIOS) firmware these OSes need. The docs also state `security.secureboot` should be `false` when CSM is on:

```bash
incus init win2000 --vm --empty \
  -c limits.cpu=1 -c limits.memory=512MiB -d root,size=10GiB

# Legacy-BIOS firmware + no Secure Boot — the two documented, first-class knobs
incus config set win2000 security.csm true
incus config set win2000 security.secureboot false
```

For many legacy guests `security.csm=true` is enough to get a bootable BIOS environment. Where it is **not** enough — a guest that specifically needs an older **i440fx** machine type rather than q35, or a legacy PIC/ACPI configuration — the escape hatch is `raw.qemu` / `raw.qemu.conf`, which inject arguments into (or override settings in) the VM's generated QEMU command line and config:

```bash
# CONCEPTUAL — verify the exact machine string against your QEMU before using.
# raw.qemu appends raw args to the QEMU command line (see Incus instance options).
# The machine type and its options are QEMU-version-specific: enumerate them with
#   qemu-system-x86_64 -machine help
# and confirm raw.qemu / raw.qemu.conf semantics in the Incus docs before committing.
incus config set win2000 raw.qemu -- '-machine pc-i440fx-<VERSION>'
```

!!! warning "Do not treat the raw.qemu machine string as a fixed value — verify it"
    The exact machine type name (`pc`, `pc-i440fx-<version>`, `q35`, …) and which options it accepts are **QEMU-version-dependent** and change between releases. Incus also constructs much of the QEMU command line itself, so a `raw.qemu -machine ...` override can conflict with what Incus already generates. Enumerate valid machines with `qemu-system-x86_64 -machine help`, read the [Incus `raw.qemu` documentation](https://linuxcontainers.org/incus/docs/main/reference/instance_options/), and expect trial and error. This guide deliberately does **not** hard-code a machine string, because doing so would be inventing a value that won't be right for your version. Prefer `security.csm` first; reach for `raw.qemu` only when it isn't enough.

## Disk — legacy Windows has no virtio-blk driver

Incus's disk `io.bus` property accepts **`virtio-scsi`** (default), **`virtio-blk`**, **`nvme`**, and **`usb`** — verified against the [disk device docs](https://linuxcontainers.org/incus/docs/main/reference/devices_disk/). Notably it does **not** offer an `ide` or `sata` value. That's a problem: 9x/2000/XP ship no virtio-blk driver, so the default virtio disk is invisible to their installers.

Two ways around it:

- **Windows XP:** XP *can* load a storage driver from a floppy at the classic **F6 "press F6 to install a third-party SCSI or RAID driver"** prompt, so a virtio-blk (`viostor`) disk is technically possible. Simpler and more reliable, though, is a plain **IDE** disk that XP sees natively with zero drivers.
- **9x / ME / 2000:** realistically these want an **IDE** boot disk — there's no clean F6 virtio path.

Because Incus's `io.bus` has no IDE/SATA option, an IDE/SATA boot disk means expressing the controller and disk through `raw.qemu` rather than a native Incus disk property:

```bash
# CONCEPTUAL ONLY — the exact -drive/-device args are QEMU-version-specific.
# Intent: attach the VM's disk on an IDE (or AHCI/SATA) controller instead of virtio.
# Verify device names with `qemu-system-x86_64 -device help` and confirm how this
# composes with the disk Incus already defines. Do NOT assume these strings verbatim.
#   e.g. an IDE controller is typically implicit on an i440fx/pc machine;
#        an AHCI controller is added with a device such as `-device ich9-ahci`.
```

!!! warning "IDE/SATA for the boot disk is a raw.qemu exercise, not an Incus disk property"
    There is no `incus config device set <vm> root io.bus=ide` — `ide`/`sata` are not accepted `io.bus` values. Getting a legacy-visible boot disk means either accepting virtio-blk + an F6 driver floppy (XP only) or constructing an IDE/AHCI disk via `raw.qemu`, whose exact arguments you must verify against `qemu-system-x86_64 -device help` and the Incus `raw.qemu` docs. This is the fiddliest part of legacy Windows on Incus — budget time for it.

## NIC — emulated rtl8139 or e1000

There are no virtio-net drivers for 9x/2000/XP out of the box, so the default virtio NIC won't work. These OSes *do* have (or can easily get) drivers for the classic emulated cards QEMU provides — **rtl8139** (Realtek 8139, the traditional 9x/2000 choice) and **e1000** (Intel, works well for XP). Incus's `nic` device doesn't expose a legacy model selector, so this is again a `raw.qemu` override:

```bash
# CONCEPTUAL — verify against `qemu-system-x86_64 -device help` and the raw.qemu docs.
# Intent: give the guest an emulated legacy NIC instead of virtio-net.
#   rtl8139 — best for Windows 9x / 2000
#   e1000   — best for Windows XP
# Do not assume Incus's own NIC device and a raw.qemu NIC won't collide; you may need
# to omit the default NIC and define networking entirely through raw.qemu.
```

Windows 98/ME may need a vendor driver disk for the RTL8139; Windows 2000 and XP recognise both cards from their in-box driver set in most cases.

## Secure Boot and TPM — off and absent

Straightforward: no Secure Boot, no TPM.

```bash
incus config set winxp security.secureboot false   # required for legacy firmware/CSM
# Do NOT add a vtpm device — these OSes have no concept of a TPM
```

## Graphics and console — SPICE VGA only

Legacy Windows has no virtio-gpu driver, so you rely on the **SPICE VGA console** with an emulated **std VGA** or **cirrus** adapter — exactly the adapters these OSes have built-in drivers for:

```bash
incus start winxp
incus console winxp --type=vga        # the SPICE VGA console — drive Setup and the desktop here
```

See [Graphical access](graphical-access.md) for the SPICE stack, forcing a specific emulated VGA model via `raw.qemu` (e.g. `-vga std` or `-vga cirrus`), reaching the console remotely, and the harmless `GSpice-CRITICAL usbredir` warning. Because there's no guest SPICE agent for these OSes, expect a fixed resolution, no clipboard sharing, and a doubled/offset cursor — all normal for pre-agent Windows.

!!! note "Remote access: 9x has no RDP; 2000/XP Pro do but it's insecure"
    Windows **95/98/ME** have **no Remote Desktop** at all — your options are the SPICE VGA console or a period **VNC server** installed inside the guest (e.g. an old TightVNC/RealVNC build), tunnelled out. Windows **2000 Server** (Terminal Services) and **Windows XP Professional** (Remote Desktop) do have RDP, but it's an ancient, weak implementation — no NLA, obsolete crypto. If you enable it, gate it to LAN/Tailscale only with the same proxy-device + UFW pattern used for [Windows 11](windows-vm.md#reach-rdp-from-your-client), and never expose it further:

```bash
# XP Pro / Win2000 RDP, LAN/Tailscale only — same pattern as the modern pages
incus config device add winxp rdp proxy \
  listen=tcp:0.0.0.0:3389 connect=tcp:127.0.0.1:3389 bind=host
sudo ufw allow from 192.168.0.0/24 to any port 3389 proto tcp
```

## Per-OS notes

### Windows 98 / ME

- **RAM ceiling:** Windows 98/ME are unstable or won't boot with large RAM — keep the guest to roughly **512 MiB or less** (some builds need workarounds even above ~512 MiB). Start small (256–512 MiB).
- **ACPI/APIC:** legacy ACPI support is flaky; if the installer hangs, disabling ACPI/APIC in the emulated firmware (a `raw.qemu` machine option — verify the exact flag) is a common fix.
- **NIC:** RTL8139 with a vendor driver disk; no in-box virtio.
- **RDP:** none — use the VGA console or a period VNC server.

### Windows 2000

- **RAM:** comfortable at **512 MiB – 1 GiB**; more brings little.
- **ACPI:** better than 9x but still old — install with ACPI enabled if it's stable, otherwise fall back to Standard PC HAL.
- **Disk:** IDE boot disk; virtio-blk isn't practical.
- **RDP:** available via **Terminal Services** on 2000 Server (not Professional). Insecure — Tailscale/LAN only.

### Windows XP

- **RAM:** 32-bit XP addresses up to ~**3.2 GB usable**; 1–2 GiB is plenty for a VM.
- **Disk:** IDE is simplest; XP can F6-load `viostor` for virtio-blk if you prefer.
- **NIC:** **e1000** is the smoothest choice; XP recognises it in-box.
- **RDP:** **Remote Desktop** is present in **XP Professional** (not Home). Old and insecure — gate it.
- **x64 exists:** **Windows XP Professional x64 Edition** exists (a Server 2003-derived kernel) if you need 64-bit; it's a different, less common install with its own driver quirks.

## Installing

The managed-volume ISO workflow is the same restricted-`user-1000`-project path used everywhere in this build — raw host-path disk sources are forbidden, so import the ISO as an iso-type volume and attach it:

```bash
# Import the legacy Windows installer ISO as a managed iso-type volume on the lab pool
incus storage volume import lab /data/iso/WinXP.iso winxp-iso --type=iso

# Attach it, boot.priority high so the BIOS firmware boots the installer first
incus config device add winxp install disk \
  pool=lab source=winxp-iso boot.priority=10

incus start winxp
incus console winxp --type=vga        # drive the text-mode + GUI installer over SPICE
```

!!! warning "Managed-volume ISO import is mandatory in this project"
    `--type=iso` and `pool=lab` both matter; the raw-host-path `source=/path/to.iso` form generic guides use will **not** attach in the `user-1000` project. List imported ISOs with `incus storage volume list lab type=iso`. Same gotcha as the [VMs](vms.md) and [Windows 11](windows-vm.md) pages.

Install to the **IDE disk** (the raw.qemu-defined one, or the virtio disk after an F6 driver load on XP). After the OS is up, detach the install media so the VM boots from disk:

```bash
incus stop winxp
incus config device remove winxp install
incus start winxp
incus storage volume delete lab winxp-iso    # reclaim the managed volume when no VM needs it
```

## Verify

```bash
incus list                                  # target VM, VIRTUAL-MACHINE, RUNNING
incus config get winxp security.csm         # true (legacy-BIOS firmware)
incus config get winxp security.secureboot  # false
incus config show winxp | grep -A3 raw.qemu # your IDE/NIC/machine overrides, if any
incus console winxp --type=vga              # the VGA console shows the guest
```

## Next steps

- [Windows 7 and Windows 10 VM](windows-7-10-vm.md) — the next tier up; where `security.csm` / Secure-Boot-off first appears for a still-bootable Windows.
- [Windows 11 VM](windows-vm.md) — the modern flow these pages diverge from.
- [VMs](vms.md) — the general VM model, managed-volume ISO imports, `raw.qemu` context.
- [Graphical access](graphical-access.md) — the SPICE/VGA console, forcing an emulated VGA model, remote access.
- [Windows RDP Setup](../remote-desktop/rdp/windows-setup.md) — the RDP convention (for XP Pro / Win2000, insecure — gate it).
