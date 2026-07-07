# Apple Silicon specifics

VirtualBox 7.2 on Apple Silicon is officially **Developer Preview**. ARM Linux guests work — the lab automation runs Ubuntu 26.04 ARM end-to-end — but there are three quirks that aren't documented anywhere obvious, and one of them is a hard "this exact combination crashes" issue. This page lists them all.

If you copy nothing else from this page: on Apple Silicon, **lab VMs must use `--platform-architecture arm` at createvm, `--graphicscontroller qemuramfb`, and only SATA storage** (no IDE).

## How to check what you have

```bash
uname -m              # 'arm64' on Apple Silicon, 'x86_64' on Intel
sw_vers               # macOS version
VBoxManage --version  # VirtualBox version
```

This page is verified against macOS 26.x ("Tahoe") on Apple Silicon with VirtualBox 7.2.8. Earlier macOS/VBox combos have additional bugs.

## Quirk 1: `--platform-architecture arm` is mandatory at create time

```bash
# Wrong — defaults to x86; VM has emulated x86 hardware, won't run
VBoxManage createvm --name test --ostype Ubuntu_64 --register

# Right — VM is an ARM machine matching your host
VBoxManage createvm \
    --name test \
    --ostype Ubuntu_arm64 \
    --platform-architecture arm \
    --register
```

The flag is **only valid on `createvm`**. `modifyvm --platform-architecture arm` doesn't exist; once created with the wrong architecture, you have to destroy the VM and recreate it.

The lab's `_vbox.create_vm` always passes `--platform-architecture` from `LabConfig.platform`, which auto-detects from `uname -m`.

## Quirk 2: graphics controller — `vboxvga` crashes ARM

Default `--graphicscontroller vboxvga` (legacy VGA emulation) is x86-specific. On ARM:

```bash
VBoxManage startvm test --type headless
# error: The configuration constructor in main failed due to a COM error.
# VBox.log: Failed to construct device 'vga' instance #0 (VERR_PGM_RAM_CONFLICT)
```

The fix is `qemuramfb` — a simple framebuffer device suitable for ARM virt machines:

```bash
VBoxManage modifyvm test --graphicscontroller qemuramfb
```

For x86 the modern default is `vmsvga`. The matrix:

| Host platform | Recommended `--graphicscontroller` | Why |
|---|---|---|
| x86 | `vmsvga` | Default, fully supported |
| ARM | `qemuramfb` | Only one that works |

The lab's `_vbox.configure_vm` sets `qemuramfb` automatically when `platform=arm`.

## Quirk 3: IDE controller crashes ARM EFI

On ARM, attaching the install ISO to an IDE controller crashes the VBox firmware before the guest even starts booting:

```bash
VBoxManage storagectl test --name IDE --add ide
VBoxManage startvm test --type headless
# VBox.log: Firmware type: failed - VERR_NOT_SUPPORTED
# VBox.log: Constructor failed with rc=VERR_MAIN_CONFIG_CONSTRUCTOR_COM_ERROR
```

The IDE virtual-device code path triggers something in the ARM EFI firmware that just doesn't work. There's no workaround other than "don't use IDE".

The fix: put everything on SATA. The lab attaches the install ISO + the CIDATA cloud-init ISO on SATA ports 7 and 8 (after the data disks):

```bash
VBoxManage storagectl test --name SATA --add sata --controller IntelAhci --portcount 30

# Disks 0-6
for i in 0 1 2 3 4 5 6; do
    VBoxManage storageattach test --storagectl SATA --port $i --device 0 \
        --type hdd --medium /path/to/disk$i.vdi
done

# ISOs on SATA, NOT IDE
VBoxManage storageattach test --storagectl SATA --port 7 --device 0 \
    --type dvddrive --medium /path/to/install.iso
VBoxManage storageattach test --storagectl SATA --port 8 --device 0 \
    --type dvddrive --medium /path/to/cidata.iso
```

Ubuntu's Subiquity is fine with the install ISO being on SATA; the boot sequence works the same.

On x86, IDE is fine — the lab uses IDE for ISOs there. The decision is `_provision_provision.py`:

```python
iso_controller = "IDE" if cfg.platform == "x86" else "SATA"
```

## Quirk 4: `unattended install` templates lag

VBoxManage 7.2.8 ships unattended-install templates that recognise up to Ubuntu 25.04. Ubuntu 26.04 ISOs return:

```bash
VBoxManage unattended detect --iso /path/to/ubuntu-26.04-live-server-arm64.iso
# OS TypeId    = (empty)
# Unattended installation supported = no
```

This isn't ARM-specific — VBoxManage's templates are version-bound and lag on every architecture. But on ARM it's more noticeable because (a) the bundled ARM templates are sparser, and (b) the lab is targeting 26.04 specifically for the real MS-S1 MAX.

The lab works around this by **not using VBoxManage's unattended install at all** — it drives Subiquity directly via a self-built cloud-init CIDATA ISO + a remastered install ISO with `autoinstall` in GRUB. Works for any Ubuntu release, present or future. See [Unattended install](unattended.md) for the details.

## Quirk 5: bridged Wi-Fi is fragile

On Apple Silicon with macOS 26.x, bridged networking over Wi-Fi (`en0`) is unreliable. Symptoms: VM gets a DHCP lease but packets don't flow, or the bridge interface periodically drops.

Workarounds:

- Use NAT instead (the lab's default).
- Use a USB-Ethernet adapter; bridged works fine over wired.
- Use a host-only network with `NAT` on a second NIC for internet.

Wired bridged networking on Apple Silicon is solid. Wi-Fi bridged is hit-or-miss.

## Quirk 6: extension pack quirks

The Extension Pack is required for VRDE (remote console). On Apple Silicon, after upgrading VirtualBox you usually need to re-install the matching Extension Pack version:

```bash
brew upgrade --cask virtualbox virtualbox-extension-pack

# Confirm
VBoxManage list extpacks
```

If the versions mismatch, VBoxManage prints "Extension pack 'Oracle VM VirtualBox Extension Pack' is incompatible with this VirtualBox version" and disables it. The fix is to reinstall the matching version.

## What works just fine

To balance the list of quirks: most things Just Work on Apple Silicon:

- **Headless operation**: `VBoxManage startvm --type headless` works the same as x86.
- **Snapshots**: take, restore, branch — all fine.
- **NAT networking + port forwarding**: works perfectly.
- **Multiple VMs concurrently**: each gets its own NAT instance; no conflicts.
- **VDI / VMDK / VHD disks**: all formats work.
- **TRIM / discard**: works when `--nonrotational on --discard on` is set on the attachment.
- **Hot-plug SATA**: works for simulating disk failures during ZFS exercises.

## Performance vs Intel Mac

On Apple Silicon, VirtualBox uses Apple's Hypervisor.framework (HVF) for ARM-on-ARM virtualization. Performance for ARM Linux guests is near-native — the lab's Ubuntu 26.04 install runs in ~3.5 minutes (compared to ~10 minutes for an x86 Linux guest via QEMU userspace emulation on the same M-series chip).

Running x86 Linux guests on Apple Silicon **is not supported** by VirtualBox 7.2 — you'd need full CPU emulation (QEMU TCG) which VBox doesn't ship. For cross-architecture, use UTM or Docker (which runs ARM Linux containers natively).

## A quick lab-VM template (ARM-aware)

For copy-paste reference, the minimal commands to bring up a clean ARM Linux VM on Apple Silicon:

```bash
NAME=demo

# Create with arm platform
VBoxManage createvm \
    --name "$NAME" \
    --ostype Ubuntu_arm64 \
    --platform-architecture arm \
    --register

# Configure (note: x86-only flags omitted, qemuramfb required)
VBoxManage modifyvm "$NAME" \
    --memory 4096 --cpus 4 --vram 32 \
    --graphicscontroller qemuramfb \
    --nic1 nat \
    --rtcuseutc on \
    --audio-driver none \
    --boot1 disk --boot2 dvd
VBoxManage modifyvm "$NAME" --natpf1 "ssh,tcp,127.0.0.1,2222,,22"

# Disk + SATA (NOT IDE)
VBoxManage createmedium disk --filename "${NAME}.vdi" --size 20000
VBoxManage storagectl "$NAME" --name SATA --add sata --controller IntelAhci
VBoxManage storageattach "$NAME" --storagectl SATA --port 0 --device 0 \
    --type hdd --medium "${NAME}.vdi" --nonrotational on --discard on

# ISO on SATA (NOT IDE)
VBoxManage storageattach "$NAME" --storagectl SATA --port 1 --device 0 \
    --type dvddrive --medium /path/to/ubuntu-26.04-live-server-arm64.iso

VBoxManage startvm "$NAME" --type headless
```

Skip those four ARM-specific items (`--platform-architecture arm`, `--graphicscontroller qemuramfb`, SATA-not-IDE, omit USB flags) and the VM either won't boot or will crash with `VERR_*` errors.

The lab automation (`msai lab create`) handles all of this for you. This page documents the underlying reasons so you can debug if something goes sideways or build similar workflows yourself.

## See also

- [Concepts](concepts.md) — virtualization model
- [VMs](vms.md) — full createvm/modifyvm reference
- [Storage](storage.md) — controller details
- [Troubleshooting](troubleshooting.md) — what to do when these quirks bite anyway
