# Installing VirtualBox

For the lab automation in this repo you need VirtualBox 7.2 or newer. The Extension Pack is optional but recommended.

## macOS

### Apple Silicon (M-series)

```bash
brew install --cask virtualbox
```

That installs the latest release from Oracle. Confirm:

```bash
VBoxManage --version
# 7.2.8r173730 or similar
```

**Apple Silicon caveats** (full details in [Apple Silicon specifics](apple-silicon.md)):

- ARM Linux guests work but are tech-preview-quality
- `vboxvga` graphics controller crashes — must use `qemuramfb`
- IDE controller crashes ARM EFI firmware enumeration — use SATA only
- `--platform-architecture arm` must be set at `createvm` time

The lab automation in this repo handles all three for you. Vanilla VBoxManage commands need to know.

### Intel macOS

Same install:

```bash
brew install --cask virtualbox
```

Intel macOS uses VT-x for hardware virtualization; no quirks. x86 Linux guests Just Work.

### Extension Pack (optional)

Adds USB 2.0/3.0 pass-through, VRDE (RDP for headless), disk encryption:

```bash
brew install --cask virtualbox-extension-pack
```

Confirm it's loaded:

```bash
VBoxManage list extpacks
```

You should see "Oracle VM VirtualBox Extension Pack" listed. The lab uses VRDE specifically when falling back to interactive install (rare path, but handy).

### macOS system settings

VirtualBox installs a kernel extension (or a System Extension on newer macOS). After first install:

1. **System Settings → Privacy & Security**
2. Look for "System software from developer 'Oracle America, Inc.' was blocked" and click Allow
3. Restart if prompted

Without this, `VBoxManage startvm` will fail with cryptic kernel-module errors.

## Linux

### Ubuntu / Debian

The distro packages tend to lag; prefer Oracle's apt repo for the current version:

```bash
# Add Oracle's signing key
wget -O - https://www.virtualbox.org/download/oracle_vbox_2016.asc | \
    sudo gpg --dearmor -o /usr/share/keyrings/oracle-vbox.gpg

# Add the repo (replace 'noble' with your codename: noble/jammy/focal)
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-vbox.gpg] \
    https://download.virtualbox.org/virtualbox/debian noble contrib" | \
    sudo tee /etc/apt/sources.list.d/virtualbox.list

sudo apt update
sudo apt install -y virtualbox-7.2
```

Add your user to the `vboxusers` group (needed for USB pass-through and some operations):

```bash
sudo usermod -aG vboxusers $USER
# log out + back in for it to take effect
```

Verify:

```bash
VBoxManage --version
```

### Fedora / RHEL

Oracle's yum repo:

```bash
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager addrepo --from-repofile=https://download.virtualbox.org/virtualbox/rpm/el/virtualbox.repo
sudo dnf install -y VirtualBox-7.2
sudo usermod -aG vboxusers $USER
```

### Arch

```bash
sudo pacman -S virtualbox virtualbox-host-modules-arch
sudo modprobe vboxdrv
sudo usermod -aG vboxusers $USER
```

### Extension Pack on Linux

Download manually (Oracle doesn't ship a repo for it):

```bash
VER=$(VBoxManage --version | sed 's/r.*//')
curl -L -o /tmp/Oracle_VM_VirtualBox_Extension_Pack.vbox-extpack \
    "https://download.virtualbox.org/virtualbox/${VER}/Oracle_VM_VirtualBox_Extension_Pack-${VER}.vbox-extpack"
sudo VBoxManage extpack install --replace /tmp/Oracle_VM_VirtualBox_Extension_Pack.vbox-extpack
```

## Windows

```powershell
# winget
winget install Oracle.VirtualBox

# Or download MSI from virtualbox.org
```

Confirm in PowerShell:

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" --version
```

For convenience, add `C:\Program Files\Oracle\VirtualBox` to your PATH so `VBoxManage` works without the full path.

## Verifying the install

A trivial round-trip to confirm things work:

```bash
# Create + register
VBoxManage createvm --name selftest --ostype Linux_64 --register

# Should appear in the list
VBoxManage list vms
# "selftest" {uuid}

# Show details
VBoxManage showvminfo selftest --machinereadable | head

# Unregister + delete
VBoxManage unregistervm selftest --delete
```

If those four commands all succeed, VirtualBox is healthy and the lab automation will work.

## Where the data lives

By default VirtualBox stores VM data under a per-user "machine folder":

| OS | Default machine folder |
|---|---|
| macOS | `~/VirtualBox VMs/` |
| Linux | `~/VirtualBox VMs/` |
| Windows | `C:\Users\<you>\VirtualBox VMs\` |

Change it:

```bash
VBoxManage setproperty machinefolder /path/to/where/you/want/it
```

For this build's lab, the VM config lives in the default machine folder, but the disk images live in `target/` inside the repo (where we created them). VirtualBox is happy with disks anywhere.

## Upgrading

```bash
# macOS
brew upgrade --cask virtualbox virtualbox-extension-pack

# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y virtualbox-7.2

# After upgrading the host VBox, you typically need to reinstall the
# matching Extension Pack version since they're version-locked.
```

## Uninstalling

```bash
# macOS
brew uninstall --cask virtualbox-extension-pack virtualbox

# Ubuntu/Debian
sudo apt remove --purge virtualbox-7.2

# Then remove VM data (careful — destructive)
rm -rf ~/VirtualBox\ VMs/
rm -rf ~/.config/VirtualBox/
```

## Where to go next

- [VBoxManage CLI](vboxmanage.md) — the actual commands
- [Apple Silicon](apple-silicon.md) — read this if you're on an M-series Mac
- [VMs](vms.md) — create your first VM
