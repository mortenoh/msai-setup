# Windows 11 VM

Windows 11 runs as an Incus VM instance. It needs three things Windows 11 specifically requires — an emulated **TPM 2.0**, **UEFI Secure Boot**, and **virtio drivers** — plus [RDP](../remote-desktop/rdp/windows-setup.md) for day-to-day access afterward. This page is the Windows-specific layer on top of [VMs](vms.md); read that first for the general VM model.

!!! note "The iGPU stays with the host — no passthrough to this VM"
    This is a deliberate, unchanged decision for the build: the Radeon 8060S iGPU stays with the **host** for ROCm, and is **not** passed to the Windows VM. Host ROCm and GPU passthrough are mutually exclusive, and this box exists for local LLM inference on the host, so the Windows VM runs on virtio graphics only (fine for RDP, Office, general desktop use). If you need GPU-accelerated Windows, that's a different machine — see `START.md`'s "intentionally avoids" list.

## Prerequisites

```bash
# QEMU must be installed for VM support (from the installation page)
dpkg -l | grep qemu-system

# The virtio-win driver ISO — Windows can't see virtio disks/NICs without it.
# Download the stable ISO from Fedora's virtio-win project onto the host.
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso \
  -O /tank/media/iso/virtio-win.iso

# A Windows 11 installation ISO (from Microsoft) placed somewhere on the host
ls /tank/media/iso/Win11.iso
```

## Create the VM with TPM and Secure Boot

Windows 11's installer refuses to proceed without a TPM 2.0 and (by default) Secure Boot. Incus provides both natively.

### 1. Initialize the VM

```bash
incus init images:windows/11 win11 --vm \
  -c limits.cpu=8 \
  -c limits.memory=16GiB \
  -d root,size=100GiB
```

!!! note "If there's no `images:windows/11` image, install from ISO"
    The community `images:` server may not always carry a ready Windows image (licensing). The reliable path is to create a **blank** VM and install from the Microsoft ISO:
    ```bash
    incus init win11 --vm --empty \
      -c limits.cpu=8 -c limits.memory=16GiB -d root,size=100GiB
    ```
    Then attach the install and driver ISOs as disk devices (below). Incus's `distrobuilder`/`incus-win11` tooling can also prep a Windows image, but the empty-VM-plus-ISO route is the most portable.

### 2. Add the emulated TPM 2.0

Verified against the [Incus TPM device reference](https://linuxcontainers.org/incus/docs/main/reference/devices_tpm/) — for a VM, no `path`/`pathrm` keys are needed (those are container-only):

```bash
incus config device add win11 vtpm tpm
```

This gives the guest a software TPM 2.0, which is what Windows 11 checks for. TPM devices **cannot be hotplugged into a running VM** — add it while the VM is stopped (it is, we haven't started it yet).

### 3. Confirm Secure Boot

`security.secureboot` is a VM-only bool that **defaults to `true`** — verified against the [Incus instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/) ("Whether UEFI secure boot is enforced with the default Microsoft keys"). For a stock Windows 11 install you *want* it on, so usually you do nothing:

```bash
incus config get win11 security.secureboot        # expect: true (default)
```

Only disable it if you're doing something that needs it off (an unsigned bootloader, certain custom images):

```bash
# Usually NOT needed for Windows 11 — leave Secure Boot on
incus config set win11 security.secureboot false
```

!!! warning "Secure Boot off + TPM present is a common misconfiguration"
    Windows 11 wants **both** TPM 2.0 and Secure Boot. Since Incus defaults Secure Boot to `true`, the trap is accidentally turning it *off* (copying a Linux-VM recipe that disabled it) and then wondering why the Win11 installer complains. For Windows 11: TPM device added, `security.secureboot` left at its `true` default. Verify both before installing.

### 4. Attach install media and virtio drivers

```bash
# The Windows installer ISO (boot from this first)
incus config device add win11 install disk \
  source=/tank/media/iso/Win11.iso boot.priority=10

# The virtio-win driver ISO (Windows needs it to see the virtio disk/NIC)
incus config device add win11 drivers disk \
  source=/tank/media/iso/virtio-win.iso
```

## Install Windows

```bash
incus start win11

# Open the graphical console to drive the installer
incus console win11 --type=vga
```

During setup:

1. **"Where do you want to install Windows?"** shows *no drives* — because the disk is a **virtio** block device Windows doesn't have a driver for yet.
2. Click **Load driver**, browse the virtio-win ISO, and load the **viostor** (virtio block) driver for your Windows version (e.g. `amd64\w11`). The disk appears.
3. Continue the install as normal.
4. After install, from inside Windows, run the virtio-win **guest tools installer** (on the same ISO) to get the network (NetKVM), balloon, and other virtio drivers — the NIC won't work until NetKVM is installed.

!!! note "No TPM/Secure Boot prompt if steps 2-3 were done right"
    If Windows 11 setup complains "This PC can't run Windows 11," the TPM or Secure Boot piece is wrong — go back and confirm the `vtpm` device is attached (`incus config device show win11`) and `security.secureboot` is `true`. Those two, plus 8 GB+ RAM and 64 GB+ disk (we gave 16 GB / 100 GB), satisfy the Win11 requirements.

## After install: remove install media, get RDP working

### Detach the ISOs

Once Windows is installed and virtio guest tools are in, remove the install media so the VM boots from disk:

```bash
incus config device remove win11 install
# Keep or remove the drivers ISO as you like
incus config device remove win11 drivers
incus restart win11
```

### Enable RDP inside Windows

This build's established RDP convention lives in [Windows RDP Setup](../remote-desktop/rdp/windows-setup.md) — follow it rather than inventing a parallel procedure. The essentials, from inside the Windows guest (via the VGA console first):

```powershell
# Enable Remote Desktop
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# Enable the firewall rule
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# Require Network Level Authentication (recommended)
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 1
```

See the [full RDP page](../remote-desktop/rdp/windows-setup.md) for NLA, user permissions, restricting RDP to the Tailscale range (`100.64.0.0/10`), and multi-monitor/audio options — all of which apply unchanged to an Incus-hosted Windows guest.

### Reach RDP from your client

The VM is on `incusbr0` (NAT) by default, so expose port 3389 with a proxy device bound on the host, then gate it with UFW (per [Networking](networking.md)):

```bash
# Forward host:3389 to the VM's RDP port
incus config device add win11 rdp proxy \
  listen=tcp:0.0.0.0:3389 \
  connect=tcp:127.0.0.1:3389 \
  bind=host

# Restrict to the LAN / Tailscale, never the public internet
sudo ufw allow from 192.168.0.0/24 to any port 3389 proto tcp
```

Then connect from a [macOS RDP client](../remote-desktop/rdp/macos-clients.md) to the host's address (or its MagicDNS name over Tailscale) on port 3389.

!!! warning "Never expose RDP to the internet"
    Same rule as the rest of this build: RDP is reachable on the LAN and over Tailscale only, gated by UFW and (inside Windows) restricted to the Tailscale CIDR. Do not port-forward 3389 from your router. The [RDP security checklist](../remote-desktop/rdp/windows-setup.md) applies verbatim.

## Snapshots and backup

Snapshot before Windows Update or driver changes:

```bash
incus stop win11                          # stop for a clean, consistent zvol snapshot
incus snapshot create win11 pre-update
incus start win11
```

The VM's zvol lives under `hot/incus/virtual-machines/win11.block`; this build treats VM disk images as *optional* off-site (they're large and re-creatable) — see the [backup schedule](../operations/backup.md) and [Snapshots & backup](snapshots-backup.md). A stopped snapshot is consistent; a running one is only crash-consistent.

## Verify

```bash
incus list                                  # win11, VIRTUAL-MACHINE, RUNNING
incus config device show win11              # vtpm (tpm), root disk, rdp proxy
incus config get win11 security.secureboot  # true
# From a client: RDP to the host on 3389 over LAN/Tailscale
```

## Next steps

- [Windows RDP Setup](../remote-desktop/rdp/windows-setup.md) — the full RDP-enablement convention.
- [macOS RDP clients](../remote-desktop/rdp/macos-clients.md) — connecting from a Mac.
- [VMs](vms.md) — the general VM model this builds on.
- [Networking](networking.md) — proxy devices and UFW for exposing 3389.
