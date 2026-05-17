# VBoxManage CLI

`VBoxManage` is the single CLI for everything VirtualBox can do. The GUI is a thin wrapper over it. This page is the field guide to the subset this build actually uses, with worked examples and the gotchas we hit.

For exhaustive reference: [Oracle's VirtualBox 7.2 manual](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/index.html). For "what does this specific subcommand take", `VBoxManage <subcommand> --help`.

## Command shape

```
VBoxManage [global-options] <subcommand> [subcommand-options]
```

Examples:

```bash
VBoxManage --version
VBoxManage list vms
VBoxManage createvm --name test --ostype Ubuntu_64 --register
VBoxManage modifyvm test --memory 4096 --cpus 4
```

There are about 30 top-level subcommands. The ones you'll use most: `list`, `showvminfo`, `createvm`, `modifyvm`, `startvm`, `controlvm`, `storagectl`, `storageattach`, `createmedium`, `snapshot`, `unregistervm`.

## Listing things

```bash
VBoxManage list vms              # all registered VMs (name + UUID)
VBoxManage list runningvms       # only those currently running
VBoxManage list ostypes          # OS-type identifiers you can pass to createvm
VBoxManage list systemproperties # global config (machine folder, default frontend, etc.)
VBoxManage list bridgedifs       # network interfaces usable for bridged networking
VBoxManage list hostonlyifs      # configured host-only networks
VBoxManage list dvds             # registered DVD/ISO images
VBoxManage list hdds             # registered hard disk images
```

Useful filters:

```bash
VBoxManage list --long vms                       # full details, not just name/UUID
VBoxManage list --platform-arch=arm ostypes      # only ARM ostypes (on Apple Silicon)
VBoxManage list --platform-arch=arm ostypes | grep -A1 -i ubuntu
```

## Inspecting a VM

```bash
VBoxManage showvminfo test                       # human-readable dump
VBoxManage showvminfo test --machinereadable     # parseable key=value lines
```

Parse:

```bash
# Get the firmware type
VBoxManage showvminfo test --machinereadable | awk -F= '/^firmware=/{print $2}'

# Find all SSH port-forward rules
VBoxManage showvminfo test --machinereadable | grep '^Forwarding'

# Get the path to the primary disk
VBoxManage showvminfo test --machinereadable | awk -F= '/^"SATA-0-0"=/{print $2}'
```

## Creating + configuring a VM

### createvm

```bash
VBoxManage createvm \
    --name test \
    --ostype Ubuntu_64 \             # or Ubuntu24_LTS_arm64 on ARM
    --platform-architecture x86 \    # required on ARM hosts: 'arm'
    --register                       # add to the registered-VM list
```

`--platform-architecture` is **set at createvm time only**; `modifyvm` can't change it later. On Apple Silicon you must pass `arm` or the VM tries to be x86 and never boots.

The VM is registered but has no hardware config. You need at least `modifyvm` + a disk before it'll start.

### modifyvm

Apply hardware/firmware/networking settings. Most-used flags:

```bash
VBoxManage modifyvm test \
    --memory 8192 \                   # MiB
    --cpus 4 \
    --vram 32 \                       # MiB of video RAM
    --firmware efi64 \                # bios | efi | efi32 | efi64 (x86 only)
    --nic1 nat \                      # nic1..nic8: nat|bridged|hostonly|intnet|none
    --rtcuseutc on \                  # store guest RTC as UTC (Linux convention)
    --audio-driver none \             # 'none' is usually right for headless
    --usbohci off --usbehci off --usbxhci off    # x86 only: turn off USB controllers
    --boot1 disk --boot2 dvd \        # boot order
    --graphicscontroller vmsvga       # x86 default; on ARM use qemuramfb
```

`modifyvm` is **re-runnable** — re-applying the same args is a no-op. Use this for "make sure the VM has these settings" idempotency in scripts.

NAT port-forwarding (SSH from host port 2222 to guest 22):

```bash
VBoxManage modifyvm test \
    --natpf1 "ssh,tcp,127.0.0.1,2222,,22"
#            ^name ^proto ^host-ip ^host-port ^guest-ip(empty)  ^guest-port
```

The guest IP can be empty (forwards to whatever the VM grabs via DHCP) or set explicitly. The name (`ssh`) is just a label so you can `--natpf1delete ssh` later.

Delete a port-forward:

```bash
VBoxManage modifyvm test --natpf1 delete ssh
```

### Architecture-specific gotchas

On **ARM** (Apple Silicon), several flags don't apply:

```bash
# These x86-only flags will error on ARM:
--firmware efi64                # ARM uses ARM EFI, set by createvm's --platform-architecture
--usbohci/--usbehci/--usbxhci   # x86 USB controllers
--x86-hpet, --x86-x2apic        # x86-specific

# Use these instead:
--graphicscontroller qemuramfb  # ARM-compatible (vboxvga crashes on ARM)
```

The lab's `_vbox.configure_vm` branches on platform and only sends the right flags.

## Creating disks

```bash
VBoxManage createmedium disk \
    --filename /path/to/disk.vdi \
    --size 20000 \                    # MiB
    --format VDI                      # VDI (default), VMDK, VHD, RAW
```

VDI dynamic-allocation by default (file grows as written). Add `--variant Fixed` to pre-allocate the full size.

```bash
# Show all registered disks
VBoxManage list hdds

# Show one
VBoxManage showmediuminfo disk /path/to/disk.vdi

# Resize (grow only)
VBoxManage modifymedium disk /path/to/disk.vdi --resize 40000

# Compact (shrink the .vdi file to match actual content; requires zeroed free space inside guest first)
VBoxManage modifymedium disk /path/to/disk.vdi --compact

# Close (un-register from VirtualBox's media registry)
VBoxManage closemedium disk /path/to/disk.vdi

# Close AND delete the file
VBoxManage closemedium disk /path/to/disk.vdi --delete
```

## Storage controllers + attachment

VirtualBox's storage model: a VM has zero or more **storage controllers**; each controller has **ports**; each port has **devices** (disks or DVD drives).

### Add a controller

```bash
# SATA controller, 30 ports, bootable
VBoxManage storagectl test \
    --name SATA --add sata \
    --controller IntelAhci --portcount 30 --bootable on

# IDE controller (2 channels, 2 devices each)
VBoxManage storagectl test \
    --name IDE --add ide

# NVMe controller
VBoxManage storagectl test \
    --name NVMe --add pcie --controller NVMe
```

`--name` is just a label; you'll reference it when attaching media.

### Attach a disk

```bash
VBoxManage storageattach test \
    --storagectl SATA --port 0 --device 0 \
    --type hdd \                       # hdd | dvddrive | fdd
    --medium /path/to/disk.vdi \
    --nonrotational on \               # marks as SSD-like to the guest
    --discard on                       # allow guest TRIM to free space in the .vdi
```

### Attach an ISO

```bash
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --type dvddrive \
    --medium /path/to/ubuntu.iso
```

### Detach (without removing the controller)

```bash
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --medium none
```

### Lab convention

The `msai create` flow attaches:

```
SATA port 0      primary disk (OS)
SATA port 1..6   lab disks (for ZFS)
SATA port 7      Ubuntu install ISO (autoinstall-patched)
SATA port 8      CIDATA cloud-init ISO
```

On ARM, everything goes on SATA because the IDE controller crashes VBox's firmware enumeration (see [Apple Silicon](apple-silicon.md)).

## Power + control

```bash
VBoxManage startvm test                          # opens a window (GUI default)
VBoxManage startvm test --type headless          # no window; for servers/scripts
VBoxManage startvm test --type separate          # window + detached process
VBoxManage startvm test --type sdl               # SDL frontend (rarely used)

VBoxManage controlvm test pause                  # freeze the VM
VBoxManage controlvm test resume
VBoxManage controlvm test reset                  # hard reset, no clean shutdown
VBoxManage controlvm test acpipowerbutton        # send power button (graceful shutdown)
VBoxManage controlvm test acpisleepbutton        # send sleep button
VBoxManage controlvm test poweroff               # pull the plug, no graceful
VBoxManage controlvm test savestate              # suspend to disk; restart with startvm
```

`acpipowerbutton` is the "polite" stop: guest runs its shutdown sequence. `poweroff` is "hardware power-off", which can corrupt running filesystems — only use when the VM is truly hung.

## Snapshots

```bash
VBoxManage snapshot test list                              # all snapshots, tree view
VBoxManage snapshot test list --machinereadable            # parseable

# Take (pause the VM during snapshot for consistency)
VBoxManage snapshot test take "fresh-install" --pause

# Restore the most recent
VBoxManage snapshot test restorecurrent

# Restore a named snapshot
VBoxManage snapshot test restore "fresh-install"

# Delete a snapshot (merges its delta back into the parent — can take a while)
VBoxManage snapshot test delete "fresh-install"

# Edit metadata
VBoxManage snapshot test edit "fresh-install" --description "after first lab run"
```

Snapshots branch — restore S1, take S2, you've created a new branch in the tree. Old branches stick around until deleted.

## Networking — port forwarding (NAT)

```bash
# Add a forward
VBoxManage modifyvm test --natpf1 "name,proto,host-ip,host-port,guest-ip,guest-port"

# Examples
VBoxManage modifyvm test --natpf1 "ssh,tcp,127.0.0.1,2222,,22"      # local-only
VBoxManage modifyvm test --natpf1 "http,tcp,,8080,,80"              # all host interfaces
VBoxManage modifyvm test --natpf1 "rdp,tcp,127.0.0.1,3389,,3389"

# Delete
VBoxManage modifyvm test --natpf1 delete ssh

# View existing
VBoxManage showvminfo test --machinereadable | grep '^Forwarding'
```

NAT forwarding works while the VM is running (you don't need to stop it to add/remove rules).

## Headless server operations

```bash
VBoxManage startvm test --type headless

# Headless VMs have no window. Use these to interact:
VBoxManage controlvm test screenshotpng /tmp/test.png      # capture framebuffer
VBoxManage controlvm test keyboardputstring "ls -la\n"     # type into guest
VBoxManage controlvm test keyboardputscancode 1c           # send raw scancode (Enter)
VBoxManage controlvm test mouse moveabs 100 100 0 0 0      # move mouse

# Enable VRDE (RDP server) for graphical remote access
VBoxManage modifyvm test \
    --vrde on --vrdeport 3389 --vrdeaddress 127.0.0.1 --vrdeauthtype null

# Then from your Mac: open Microsoft Remote Desktop -> 127.0.0.1:3389
```

VRDE requires the Extension Pack ([Installation](installation.md)).

## Guest control (run commands in the guest)

If the guest has Guest Additions installed:

```bash
VBoxManage guestcontrol test run --exe /bin/ls \
    --username morten --password 'changeme' \
    -- -la /home/morten

VBoxManage guestcontrol test copyto \
    --username morten --password 'changeme' \
    /local/file.txt /home/morten/file.txt
```

For lab work, SSH is simpler. Guest control is useful when SSH isn't available.

## Tear-down

```bash
# Stop if running
VBoxManage controlvm test poweroff 2>/dev/null
sleep 1

# Unregister + delete all VM files (disks too)
VBoxManage unregistervm test --delete

# Or unregister and keep the files (useful for moving VMs between hosts)
VBoxManage unregistervm test
```

`--delete` removes:
- The `.vbox` config file and its backups
- Per-VM `Logs/` directory
- Snapshots directory
- Any disks attached to the VM that VirtualBox considers "owned" by it

Disks created with `VBoxManage createmedium disk --filename /path/...` and then attached via `storageattach --medium /path/...` are usually considered owned and get deleted. If you want to keep specific disks, detach them with `storageattach ... --medium none` first.

## Subcommand reference (the ones this build uses)

```
list           list things VirtualBox knows about
showvminfo     full info about one VM
createvm       create a new (empty) VM
modifyvm       change settings on a registered VM
startvm        boot a VM
controlvm      send control commands to a running VM (pause/resume/poweroff/...)
unregistervm   remove from VBox; optionally delete files
createmedium   create a new disk/ISO/floppy image
modifymedium   resize/compact/etc. an existing image
closemedium    de-register a medium (optionally delete its file)
storagectl     add/remove a storage controller on a VM
storageattach  attach/detach a medium to a controller port
snapshot       take/restore/delete/list snapshots
unattended     templates for unattended installs (we don't use this anymore)
extpack        manage installed extension packs
sharedfolder   share a host directory into the guest
guestcontrol   run commands in the guest (requires Guest Additions)
```

For deeper detail on any: `VBoxManage <subcommand> --help`.

## Where to go next

- [VMs](vms.md) — the VM lifecycle commands in context
- [Storage](storage.md) — disk + controller details
- [Networking](networking.md) — NAT vs bridge vs the others
- [Snapshots](snapshots.md) — branching, merging, what each operation costs
- [Apple Silicon](apple-silicon.md) — the arm-specific quirks
