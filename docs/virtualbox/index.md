# VirtualBox

VirtualBox is the hypervisor this build's lab automation uses. These docs cover everything from "what is a hypervisor" through the practical bits we hit in the lab — VBoxManage CLI, headless operation, unattended installs, snapshots — to the Apple-Silicon-specific quirks that bit us during the `msai create` integration.

If you only want to **use** the lab, `src/msai_setup/lab/README.md` in the repo is the right starting point. If you want to **understand** what's happening under the hood (or you want to script VirtualBox yourself), this is where to look.

## Why VirtualBox here

- **Free + cross-platform.** Same VBoxManage CLI on macOS, Linux, Windows.
- **Apple Silicon support** (tech-preview in 7.2.x, usable for ARM Linux guests with a few quirks documented here).
- **Full automation surface.** Everything VirtualBox can do is in VBoxManage; nothing requires the GUI.
- **Snapshots are first-class.** Take, branch, restore, prune — the lab uses these heavily as a safety net.

When VirtualBox is **not** the right choice:

- **Native performance for a single VM**: use [QEMU/KVM](https://www.qemu.org/) directly on Linux (no VBox layer).
- **Multiple VMs on the LAN with their own IPs**: [Multipass](https://multipass.run/) on macOS or libvirt on Linux are friendlier (we tried Multipass and decided against it for unrelated reasons — see [docs/zfs/virtualbox-lab.md](../zfs/virtualbox-lab.md)).
- **Production virtualization**: KVM/QEMU + libvirt is what the real MS-S1 MAX uses for VMs. VirtualBox is a developer tool, not a server hypervisor.

For this project's lab on a Mac, VBox + the wrapper code in `src/msai_setup/lab/` is the right combination.

## What this section covers

| Page | Topic |
|---|---|
| [Concepts](concepts.md) | hypervisors (type 1 vs 2), VM = config + disks, NAT vs bridge, snapshots |
| [Installation](installation.md) | macOS / Linux / Windows install; Apple Silicon notes |
| [VBoxManage CLI](vboxmanage.md) | Every command this build uses, with worked examples |
| [VMs](vms.md) | Lifecycle: createvm, modifyvm, startvm, controlvm, unregistervm |
| [Storage](storage.md) | Storage controllers (SATA/IDE/NVMe), disk creation, ISO attachment, formats (VDI/VMDK/VHD), TRIM/discard |
| [Networking](networking.md) | NAT, bridged, host-only, internal networks, port forwarding |
| [Snapshots](snapshots.md) | Take, list, restore, delete, branching, immutable vs writable |
| [Headless operation](headless.md) | startvm --type headless, VRDE for remote console, screenshotpng |
| [Unattended install](unattended.md) | VBoxManage's built-in templates, why they fall behind, our cloud-init approach |
| [Apple Silicon specifics](apple-silicon.md) | ARM platform, qemuramfb, SATA-only — the bugs we actually hit |
| [Automation](automation.md) | Scripting patterns: bash, Python subprocess, the lab's structure |
| [Troubleshooting](troubleshooting.md) | Common errors and what to do about them |

## Quick start (if you just want to launch a VM)

```bash
# Install VirtualBox (macOS)
brew install --cask virtualbox

# Verify
VBoxManage --version

# Create a VM
VBoxManage createvm --name demo --ostype Ubuntu_64 --register
VBoxManage modifyvm demo --memory 2048 --cpus 2 --firmware efi64 --nic1 nat
VBoxManage createmedium disk --filename demo.vdi --size 20000
VBoxManage storagectl demo --name SATA --add sata --controller IntelAhci
VBoxManage storageattach demo --storagectl SATA --port 0 --device 0 \
    --type hdd --medium demo.vdi
VBoxManage storageattach demo --storagectl SATA --port 1 --device 0 \
    --type dvddrive --medium /path/to/ubuntu.iso
VBoxManage startvm demo --type headless

# Tear down
VBoxManage controlvm demo poweroff
VBoxManage unregistervm demo --delete
```

Read the rest of this section to know **why** each of those flags is what it is, and how the lab automation wraps them.

## A note on versions

These docs are written against **VirtualBox 7.2.x** (released 2025-2026). Earlier versions:

- **7.0** dropped some old CPU virtualization features but added much better Apple Silicon support
- **7.1** added the modern unattended install machinery
- **6.x** is feature-frozen; avoid for new setups

When something in the docs refers to a behaviour that depends on the version, it's called out explicitly.
