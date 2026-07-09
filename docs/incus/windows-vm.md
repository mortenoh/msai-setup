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
  -O /data/iso/virtio-win.iso

# A Windows 11 installation ISO (from Microsoft) placed somewhere on the host
ls /data/iso/Win11.iso
```

## The virtio-driver problem (and `distrobuilder repack-windows`)

Windows Setup ships **no virtio drivers**. Because Incus VMs present their disk and NIC as virtio devices, a stock Windows ISO boots and then shows **no disk to install to** — the installer can't see the virtio block device. There are two ways to solve it:

1. **Load the driver manually during Setup** (the simple path, below) — click *Load driver*, point at the virtio-win ISO, load `viostor`.
2. **Repack the ISO with the drivers baked in** using Incus's **`distrobuilder repack-windows`** — the cleaner path for repeatable/unattended installs, because Setup then sees the disk immediately with no manual driver load:

```bash
# distrobuilder injects virtio-win drivers (and can inject an answer file) into a Windows ISO
sudo distrobuilder repack-windows /data/iso/Win11.iso /data/iso/Win11-virtio.iso \
  --drivers=/data/iso/virtio-win.iso
```

The repacked `Win11-virtio.iso` boots straight to a disk-visible installer. This matters most for the **fully unattended** install below: an `autounattend.xml` that references the disk won't work if Setup can't see the disk in the first place, so repack-windows (or a driver path in the answer file) is effectively required for hands-off installs.

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

### 4. Attach install media and virtio drivers (managed volumes)

This build runs Windows in the restricted **`user-1000` project**, which **forbids raw host-path disk devices**. You cannot attach `source=/data/iso/Win11.iso` directly — the project policy rejects a host path as a disk source. Import each ISO as a managed **iso-type storage volume** on the `lab` pool first, then attach the volumes:

```bash
# Import the Windows installer ISO (repacked with virtio drivers if you did that above)
incus storage volume import lab /data/iso/Win11-virtio.iso win11-iso --type=iso

# Import the virtio-win driver ISO (needed if you did NOT repack the installer)
incus storage volume import lab /data/iso/virtio-win.iso virtio-iso --type=iso

# Attach the installer ISO, boot.priority high so firmware boots it first
incus config device add win11 install disk \
  pool=lab source=win11-iso boot.priority=10

# Attach the driver ISO as a second optical device (skip if you repacked)
incus config device add win11 drivers disk \
  pool=lab source=virtio-iso
```

!!! warning "Managed-volume ISO import is mandatory in this project"
    `--type=iso` and `pool=lab` both matter, and the raw-host-path form (`source=/path/to.iso`) you'll see in generic Windows-on-Incus guides will **not** attach in the `user-1000` project. List imported ISOs with `incus storage volume list lab type=iso`. This is the same restricted-project gotcha documented on the [VMs page](vms.md).

## Install Windows

```bash
incus start win11

# Open the graphical console to drive the installer
incus console win11 --type=vga
```

The SPICE VGA console is your only way to see Windows Setup — Windows has no network or RDP yet. See [Graphical access](graphical-access.md) for the SPICE stack, reaching this console remotely, and the harmless `GSpice-CRITICAL usbredir` warning you'll see when it opens.

During setup:

1. **"Where do you want to install Windows?"** shows *no drives* — because the disk is a **virtio** block device Windows doesn't have a driver for yet.
2. Click **Load driver**, browse the virtio-win ISO, and load the **viostor** (virtio block) driver for your Windows version (e.g. `amd64\w11`). The disk appears.
3. Continue the install as normal.
4. After install, from inside Windows, run the virtio-win **guest tools installer** (on the same ISO) to get the network (NetKVM), balloon, and other virtio drivers — the NIC won't work until NetKVM is installed.

!!! note "No TPM/Secure Boot prompt if steps 2-3 were done right"
    If Windows 11 setup complains "This PC can't run Windows 11," the TPM or Secure Boot piece is wrong — go back and confirm the `vtpm` device is attached (`incus config device show win11`) and `security.secureboot` is `true`. Those two, plus 8 GB+ RAM and 64 GB+ disk (we gave 16 GB / 100 GB), satisfy the Win11 requirements.

## Fully unattended install (autounattend.xml)

To install Windows with **zero clicks**, Windows Setup reads an answer file named **`autounattend.xml`** from the root of any attached volume (a floppy, a second ISO, or the installer media itself) during the WindowsPE phase. Combined with the virtio-driver-injected ISO from `repack-windows` (so Setup sees the disk), this makes Windows install hands-off.

`distrobuilder repack-windows` can inject the answer file for you, or you attach it as a small extra ISO/FAT image imported as a managed volume.

### A complete `autounattend.xml`

This example does a whole-disk install to the first virtio disk, bypasses the Windows 11 hardware checks (belt-and-suspenders even though we provide TPM+Secure Boot), skips the OOBE/Microsoft-account nonsense, and creates a local administrator:

```xml
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">

  <!-- 1. WindowsPE: disk layout + skip the Win11 hardware gate -->
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64"
               language="neutral" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <UserData>
        <ProductKey>
          <!-- Generic Win11 Pro key for install (not activation) -->
          <Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>
        </ProductKey>
        <AcceptEula>true</AcceptEula>
      </UserData>
      <DiskConfiguration>
        <Disk wcm:action="add">
          <DiskID>0</DiskID>
          <WillWipeDisk>true</WillWipeDisk>
          <CreatePartitions>
            <!-- EFI system partition -->
            <CreatePartition wcm:action="add">
              <Order>1</Order><Type>EFI</Type><Size>260</Size>
            </CreatePartition>
            <!-- MSR -->
            <CreatePartition wcm:action="add">
              <Order>2</Order><Type>MSR</Type><Size>128</Size>
            </CreatePartition>
            <!-- Windows -->
            <CreatePartition wcm:action="add">
              <Order>3</Order><Type>Primary</Type><Extend>true</Extend>
            </CreatePartition>
          </CreatePartitions>
          <ModifyPartitions>
            <ModifyPartition wcm:action="add">
              <Order>1</Order><PartitionID>1</PartitionID>
              <Format>FAT32</Format><Label>System</Label>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>2</Order><PartitionID>2</PartitionID>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>3</Order><PartitionID>3</PartitionID>
              <Format>NTFS</Format><Label>Windows</Label><Letter>C</Letter>
            </ModifyPartition>
          </ModifyPartitions>
        </Disk>
      </DiskConfiguration>
      <ImageInstall>
        <OSImage>
          <InstallTo><DiskID>0</DiskID><PartitionID>3</PartitionID></InstallTo>
          <!-- Pick the edition you have; "Windows 11 Pro" is typical -->
          <InstallFrom>
            <MetaData wcm:action="add">
              <Key>/IMAGE/NAME</Key><Value>Windows 11 Pro</Value>
            </MetaData>
          </InstallFrom>
        </OSImage>
      </ImageInstall>
      <RunSynchronous>
        <!-- LabConfig: bypass TPM/SecureBoot/RAM/CPU checks as a safety net -->
        <RunSynchronousCommand wcm:action="add">
          <Order>1</Order>
          <Path>reg add HKLM\SYSTEM\Setup\LabConfig /v BypassTPMCheck /t REG_DWORD /d 1 /f</Path>
        </RunSynchronousCommand>
        <RunSynchronousCommand wcm:action="add">
          <Order>2</Order>
          <Path>reg add HKLM\SYSTEM\Setup\LabConfig /v BypassSecureBootCheck /t REG_DWORD /d 1 /f</Path>
        </RunSynchronousCommand>
        <RunSynchronousCommand wcm:action="add">
          <Order>3</Order>
          <Path>reg add HKLM\SYSTEM\Setup\LabConfig /v BypassCPUCheck /t REG_DWORD /d 1 /f</Path>
        </RunSynchronousCommand>
        <RunSynchronousCommand wcm:action="add">
          <Order>4</Order>
          <Path>reg add HKLM\SYSTEM\Setup\LabConfig /v BypassRAMCheck /t REG_DWORD /d 1 /f</Path>
        </RunSynchronousCommand>
      </RunSynchronous>
    </component>
  </settings>

  <!-- 2. OOBE bypass + local account -->
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64"
               language="neutral" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
        <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
        <ProtectYourPC>3</ProtectYourPC>
      </OOBE>
      <UserAccounts>
        <LocalAccounts>
          <LocalAccount wcm:action="add">
            <Name>morten</Name>
            <Group>Administrators</Group>
            <Password><Value>ChangeMe123!</Value><PlainText>true</PlainText></Password>
          </LocalAccount>
        </LocalAccounts>
      </UserAccounts>
      <AutoLogon>
        <Enabled>true</Enabled>
        <Username>morten</Username>
        <Password><Value>ChangeMe123!</Value><PlainText>true</PlainText></Password>
        <LogonCount>1</LogonCount>
      </AutoLogon>
    </component>
  </settings>

  <!-- 3. Regional/keyboard defaults so OOBE has nothing to ask -->
  <settings pass="specialize">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64"
               language="neutral" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <InputLocale>en-US</InputLocale>
      <SystemLocale>en-US</SystemLocale>
      <UILanguage>en-US</UILanguage>
      <UserLocale>en-US</UserLocale>
    </component>
  </settings>

</unattend>
```

!!! warning "This file contains a plaintext password — do not commit real secrets"
    The `<PlainText>true</PlainText>` password and any product key are literal. Keep a real `autounattend.xml` out of git (or use a placeholder and inject the secret at build time). Change the password immediately after first boot. The generic install key is for *installation only*, not activation.

!!! note "Why the LabConfig bypass keys even though we provide TPM + Secure Boot"
    We *do* give this VM a real `vtpm` and Secure Boot, so the checks should pass — the `LabConfig` `Bypass*` registry keys are a **safety net** so an unattended install can never stall on a hardware-requirement dialog (e.g. if a future image, edition, or a momentarily-detached vtpm trips the gate). They cost nothing and keep the install truly hands-off. For a *manual* install you don't need them at all — TPM + Secure Boot alone satisfy Setup.

## After install: remove install media, get RDP working

### Detach the managed ISO volumes

Once Windows is installed and the virtio guest tools are in, remove the install media so the VM boots from disk (leaving the installer attached with a high `boot.priority` can re-enter Setup):

```bash
incus stop win11
incus config device remove win11 install
incus config device remove win11 drivers        # keep if you still need the driver ISO
incus start win11

# Reclaim the imported ISO volumes once no VM needs them
incus storage volume delete lab win11-iso
incus storage volume delete lab virtio-iso
```

Remember these are **managed volumes** in the `lab` pool, not host files — detaching the device leaves the volume in the pool until you delete it explicitly.

### Install spice-guest-tools and the Windows incus-agent

Before you leave the SPICE console, install the guest tooling from inside Windows — this is what makes both the console *and* later management pleasant:

- **spice-guest-tools** (from the virtio-win / SPICE tools ISO) installs the QXL/virtio display driver, **`spice-vdagent`** (clipboard sharing and dynamic resolution in the SPICE console), and the **Windows incus-agent** (so `incus exec win11 -- ...` and `incus file` work against the Windows guest).
- The virtio-win **guest tools installer** (same ISO) finishes the NetKVM network driver, balloon, and the rest — the NIC won't come up until NetKVM is installed, so do this while the driver ISO is still attached.

```powershell
# From inside Windows (run the installers off the mounted virtio-win / spice-guest-tools ISO)
# e.g. D:\virtio-win-guest-tools.exe   and   the spice-guest-tools installer
```

With the Windows incus-agent running, you can drive the guest headlessly the same way you do a Linux VM:

```bash
incus exec win11 -- powershell -Command "Get-ComputerInfo | Select CsName,OsName"
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
