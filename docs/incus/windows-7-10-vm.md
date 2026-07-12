# Windows 7 and Windows 10 VM

Windows 10 and Windows 7 run as Incus VM instances the same way [Windows 11](windows-vm.md) does — the flow, the virtio-driver problem, and the SPICE-to-RDP switch are all identical. What differs is the **firmware gate**: these older releases predate the TPM 2.0 / Secure Boot requirements Windows 11 enforces, so you create them *without* a `vtpm` device and, for Windows 7, with Secure Boot turned off. This page is the "older Windows" companion to the [Windows 11 page](windows-vm.md); read that first, because everything not called out below is the same.

!!! note "The iGPU stays with the host — no passthrough to these VMs either"
    Unchanged from the [Windows 11 build](windows-vm.md): the Radeon 8060S iGPU stays with the **host** for ROCm, and is **not** passed to any Windows VM. Host ROCm and GPU passthrough are mutually exclusive, and this box exists for local LLM inference on the host, so these Windows VMs run on virtio graphics / 2D only (fine for RDP, Office, general desktop use). If you need GPU-accelerated Windows, that's a different machine — see `START.md`'s "intentionally avoids" list.

## Prerequisites

```bash
# QEMU must be installed for VM support (from the installation page)
dpkg -l | grep qemu-system

# The virtio-win driver ISO — Windows can't see virtio disks/NICs without it.
# Download the stable ISO from Fedora's virtio-win project onto the host.
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso \
  -O /data/iso/virtio-win.iso

# A Windows 10 (or Windows 7) installation ISO placed somewhere on the host
ls /data/iso/Win10.iso
```

!!! warning "Windows 7 may need an *older* virtio-win ISO"
    The current virtio-win drivers are signed with SHA-2 certificates. A stock Windows 7 that hasn't taken the **SHA-2 code-signing update (KB4474419)** will refuse to load them with a driver-signature error. Either slipstream KB4474419 first, or use an **older virtio-win release** whose drivers Windows 7 accepts as-is. See the [Windows 7 section](#windows-7) below.

## The virtio-driver problem is the same as Windows 11

Windows Setup ships **no virtio drivers**, and Incus presents the disk and NIC as virtio devices, so a stock ISO boots to an installer that sees **no disk**. The two fixes are exactly those on the [Windows 11 page](windows-vm.md#the-virtio-driver-problem-and-distrobuilder-repack-windows):

1. **Load the driver manually during Setup** — click *Load driver*, point at the virtio-win ISO, load `viostor` for your Windows version. The per-OS driver folder is the only thing that changes: `amd64\w10` for Windows 10, `amd64\w7` for Windows 7 (vs `amd64\w11` for 11).
2. **Repack the ISO with the drivers baked in** using `distrobuilder repack-windows` — the clean path for repeatable or unattended installs:

```bash
# distrobuilder injects virtio-win drivers (and can inject an answer file) into a Windows ISO
sudo distrobuilder repack-windows /data/iso/Win10.iso /data/iso/Win10-virtio.iso \
  --drivers=/data/iso/virtio-win.iso
```

The repacked `Win10-virtio.iso` boots straight to a disk-visible installer, which is what makes a hands-off `autounattend.xml` install possible.

## Windows 10

Windows 10 has **no TPM 2.0 and no Secure Boot requirement**. That single fact removes the two pieces of ceremony the Windows 11 page spends most of its length on: you create the VM with **no `vtpm` device**, and you can leave Secure Boot at its default or turn it off — see the tradeoff below. Everything else mirrors Windows 11.

### 1. Initialize the VM (no TPM)

The community `images:` server rarely carries a ready Windows image (licensing), so the reliable path is a **blank** VM installed from the Microsoft ISO:

```bash
incus init win10 --vm --empty \
  -c limits.cpu=8 \
  -c limits.memory=8GiB \
  -d root,size=80GiB
```

Note there is **no `incus config device add win10 vtpm tpm`** step — Windows 10 doesn't check for a TPM, so adding one is pointless (harmless, but pointless). Contrast the [Windows 11 flow](windows-vm.md#2-add-the-emulated-tpm-20), which *requires* it.

### 2. Secure Boot — leave it on, or turn it off

`security.secureboot` is a VM-only bool that **defaults to `true`** (verified against the [Incus instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/)). A normal retail Windows 10 ISO boots fine under Secure Boot, so usually you do nothing:

```bash
incus config get win10 security.secureboot        # expect: true (default)
```

Turn it off only if a specific image needs it — an unsigned bootloader, a custom or heavily-modified ISO, or certain older media that predates the Microsoft-signed boot chain:

```bash
# Only if your Win10 media won't boot under Secure Boot
incus config set win10 security.secureboot false
```

!!! note "The tradeoff: Secure Boot on is stricter but more compatible with modern media"
    Leaving Secure Boot **on** enforces the Microsoft-signed boot chain — good hygiene, and every mainstream Windows 10 retail ISO satisfies it. The reason to turn it **off** is purely media compatibility: a modded, very old, or non-Microsoft-signed installer may fail to boot with it on. Unlike Windows 11 there is no *requirement* either way, so the rule is: leave it on, and only disable it if the VM won't boot the installer.

### 3. Attach install media and virtio drivers (managed volumes)

This build runs Windows in the restricted **`user-1000` project**, which **forbids raw host-path disk devices**. Import each ISO as a managed **iso-type storage volume** on the `lab` pool, then attach the volumes — identical to the [Windows 11 procedure](windows-vm.md#4-attach-install-media-and-virtio-drivers-managed-volumes):

```bash
# Import the Windows installer ISO (repacked with virtio drivers if you did that above)
incus storage volume import lab /data/iso/Win10-virtio.iso win10-iso --type=iso

# Import the virtio-win driver ISO (needed if you did NOT repack the installer)
incus storage volume import lab /data/iso/virtio-win.iso virtio-iso --type=iso

# Attach the installer ISO, boot.priority high so firmware boots it first
incus config device add win10 install disk \
  pool=lab source=win10-iso boot.priority=10

# Attach the driver ISO as a second optical device (skip if you repacked)
incus config device add win10 drivers disk \
  pool=lab source=virtio-iso
```

!!! warning "Managed-volume ISO import is mandatory in this project"
    `--type=iso` and `pool=lab` both matter, and the raw-host-path form (`source=/path/to.iso`) you'll see in generic Windows-on-Incus guides will **not** attach in the `user-1000` project. List imported ISOs with `incus storage volume list lab type=iso`. This is the same restricted-project gotcha documented on the [VMs page](vms.md).

### 4. Install Windows 10

```bash
incus start win10
incus console win10 --type=vga        # SPICE VGA console — your only view of Setup
```

The SPICE VGA console is your only window into Setup — Windows has no network or RDP yet. See [Graphical access](graphical-access.md) for the SPICE stack, reaching this console remotely, and the harmless `GSpice-CRITICAL usbredir` warning. During setup:

1. **"Where do you want to install Windows?"** shows *no drives* — the disk is a virtio block device with no driver loaded yet.
2. Click **Load driver**, browse the virtio-win ISO, and load **viostor** from `amd64\w10`. The disk appears.
3. Continue the install as normal.
4. After install, from inside Windows, run the virtio-win **guest tools installer** (same ISO) for the NetKVM network driver, balloon, and the rest — the NIC won't come up until NetKVM is installed.

There is no "This PC can't run Windows" gate on Windows 10, so if the disk shows up and Setup proceeds, you're done — no TPM/Secure Boot troubleshooting needed.

### 5. autounattend.xml — same shape, minus the LabConfig bypass

The [Windows 11 answer file](windows-vm.md#a-complete-autounattendxml) works almost verbatim for Windows 10, with two changes:

- **Drop the LabConfig `Bypass*` keys.** Those exist to skip the Windows 11 TPM/Secure-Boot/CPU/RAM hardware gate. Windows 10 has no such gate, so the whole `<RunSynchronous>` block that sets `BypassTPMCheck`, `BypassSecureBootCheck`, `BypassCPUCheck`, and `BypassRAMCheck` is unnecessary — remove it.
- **Use a Windows 10 product key and image name.** Set the `<Key>` to a generic Windows 10 install key and the `InstallFrom` `/IMAGE/NAME` `<Value>` to e.g. `Windows 10 Pro` to match the edition on your media.

The disk-layout (`windowsPE`), OOBE-bypass/local-account (`oobeSystem`), and regional (`specialize`) passes are otherwise identical. As on the Windows 11 page, the answer file contains a **plaintext password** — keep a real one out of git and change it after first boot.

### 6. After install: remove media, get RDP working

RDP is built into **Windows 10 Pro** (Home has no RDP host). Detaching the install media, installing spice-guest-tools, enabling RDP, and exposing 3389 through a proxy device gated by UFW are **identical to the [Windows 11 page](windows-vm.md#after-install-remove-install-media-get-rdp-working)** — follow it rather than re-deriving. The essentials, from inside the guest:

```powershell
# Enable Remote Desktop (Windows 10 Pro)
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 1
```

```bash
# Detach install media so the VM boots from disk
incus stop win10
incus config device remove win10 install
incus config device remove win10 drivers
incus start win10

# Expose RDP: proxy 3389 on the host, then gate it with UFW (LAN / Tailscale only)
incus config device add win10 rdp proxy \
  listen=tcp:0.0.0.0:3389 connect=tcp:127.0.0.1:3389 bind=host
sudo ufw allow from 192.168.0.0/24 to any port 3389 proto tcp
```

The build's [Windows RDP Setup](../remote-desktop/rdp/windows-setup.md) convention — NLA, user permissions, restricting RDP to the Tailscale range (`100.64.0.0/10`) — applies unchanged. **Never expose RDP to the internet**; keep it on the LAN and over Tailscale only.

## Windows 7

Windows 7 predates the TPM / Secure Boot model entirely. It **must** run with Secure Boot **off**, gets **no `vtpm`**, and loads its virtio storage driver from the `amd64\w7` folder. RDP is available in **7 Professional and Ultimate** (Home Premium has no RDP host).

!!! warning "Windows 7 is out of support — treat this as a lab exercise"
    Windows 7 reached end of extended support in January 2020 and receives **no security updates**. Do not put it on an untrusted network, do not expose any of its services beyond the LAN/Tailscale gate, and prefer a snapshot you can roll back. This page documents *how* to run it, not a recommendation to run it for anything exposed.

### 1. Initialize the VM and turn Secure Boot off

```bash
incus init win7 --vm --empty \
  -c limits.cpu=4 \
  -c limits.memory=4GiB \
  -d root,size=60GiB

# Windows 7 predates Secure Boot — it must be disabled, and there is no vtpm
incus config set win7 security.secureboot false
```

Windows 7 x64 *is* UEFI-capable through the VM's OVMF firmware, but its UEFI support is partial (GPT/UEFI-mode install only, no Secure Boot), and it is happiest booting in a plain, non-Secure-Boot configuration. Setting `security.secureboot false` is the essential and usually sufficient knob.

!!! note "If Windows 7 still won't boot the installer, try CSM / legacy-BIOS firmware"
    Incus exposes `security.csm` — a VM-only bool (**default `false`**) documented as enabling "a firmware that supports UEFI-incompatible operating systems," i.e. a legacy-BIOS-capable (CSM) firmware. If a Windows 7 ISO refuses to boot even with Secure Boot off, enabling CSM is the documented next step; the [instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/) note that `security.secureboot` should be `false` when `security.csm` is on (as it already is here):
    ```bash
    # Only if the UEFI/OVMF path won't boot the Win7 media — verify against the Incus docs first
    incus config set win7 security.csm true
    ```
    Reach for the low-level `raw.qemu` machine-type overrides described on the [legacy Windows page](windows-legacy-vm.md) **only** if `security.csm` doesn't get you there — and verify any such argument against the current Incus and QEMU docs rather than copying it blind.

### 2. Attach media, install, load the w7 driver

Import and attach the ISOs exactly as for Windows 10 above (managed volumes, `--type=iso`, `pool=lab`), then:

```bash
incus start win7
incus console win7 --type=vga
```

During Setup, at the drive-selection step click **Load driver** and load **viostor** from `amd64\w7`.

!!! warning "SHA-2 driver-signature failures on Windows 7"
    If *Load driver* shows the driver but Windows 7 rejects it with a signature error, the guest is missing the **SHA-2 code-signing update (KB4474419)** that newer virtio drivers require. Two fixes: slipstream KB4474419 into the install image, or download an **older virtio-win release** whose drivers were still SHA-1 signed and load `viostor` from that instead. This is the single most common Windows 7 virtio snag.

After install, run the virtio-win guest tools installer for NetKVM (network) and the rest. spice-guest-tools also has a Windows 7-compatible build for the QXL display driver and clipboard.

### 3. RDP on Windows 7 Pro/Ultimate

Enabling RDP and exposing 3389 is the same PowerShell + proxy + UFW pattern as Windows 10 (above) and [Windows 11](windows-vm.md#enable-rdp-inside-windows). Note Windows 7's RDP stack is old — insist on NLA where the client supports it, and keep the port gated to LAN/Tailscale. Given Windows 7 is unsupported, the Tailscale-only restriction matters more here than anywhere.

## Snapshots and backup

Snapshot before Windows Update, driver changes, or any experiment — doubly so on unsupported Windows 7:

```bash
incus stop win10                          # stop for a clean, consistent zvol snapshot
incus snapshot create win10 pre-update
incus start win10
```

A stopped snapshot is consistent; a running one is only crash-consistent. See [Snapshots & backup](snapshots-backup.md) and the [backup schedule](../operations/backup.md).

## Verify

```bash
incus list                                  # win10 / win7, VIRTUAL-MACHINE, RUNNING
incus config device show win10              # root disk, rdp proxy — and NO vtpm
incus config get win10 security.secureboot  # true (Win10 default) — or false if you disabled it
incus config get win7 security.secureboot   # false (required for Windows 7)
# From a client: RDP to the host on 3389 over LAN/Tailscale (Pro/Ultimate editions)
```

## Next steps

- [Windows 11 VM](windows-vm.md) — the parent page; TPM, Secure Boot, virtio drivers, autounattend, RDP in full.
- [Windows legacy VM](windows-legacy-vm.md) — Windows 9x / 2000 / XP, and the `raw.qemu` legacy-BIOS/IDE/legacy-NIC overrides referenced above.
- [Windows RDP Setup](../remote-desktop/rdp/windows-setup.md) — the full RDP-enablement convention.
- [VMs](vms.md) — the general VM model this builds on.
- [Graphical access](graphical-access.md) — the SPICE/VGA console used to drive Setup.
