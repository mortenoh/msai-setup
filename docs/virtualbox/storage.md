# Storage

VirtualBox's storage model is straightforward once the vocabulary clicks: a VM has zero or more **storage controllers**; each controller has **ports**; each port has zero or more **devices** (disks, DVD drives, floppies). You attach **media** (disk image files or ISOs) to specific port/device positions on a specific controller.

## Storage controllers

A controller is the virtual chip the guest OS sees. Different controllers map to different guest drivers:

| Controller | Subtype | Guest sees | Ports | Use |
|---|---|---|---|---|
| **sata** | `IntelAhci` | AHCI disks (`/dev/sda`...) | 30 | Default for everything. Hot-pluggable. |
| **ide** | (PIIX3/PIIX4/ICH6) | PATA disks/CD | 4 (2 channels × 2) | Compatibility / legacy guests. **Crashes on Apple Silicon EFI.** |
| **scsi** | `LsiLogic`, `BusLogic`, `LsiLogicSas` | SCSI disks | 15 (LSI) | Enterprise OS compatibility. |
| **sas** | `LsiLogicSas` | SAS disks | 8 | Same as scsi LSI Logic SAS variant. |
| **nvme** | (just one) | NVMe namespaces (`/dev/nvme0n1`) | 255 | Realistic NVMe simulation. Hot-pluggable. |
| **usb** | (USB controller) | USB devices | many | USB pass-through. |
| **virtio-scsi** | (just one) | virtio devices | 255 | Best perf for KVM-like behaviour. Newer kernels only. |
| **floppy** | (just one) | `/dev/fd0` | 2 | If you really need it. |

### Add a controller

```bash
VBoxManage storagectl <vm> --name <label> --add <kind> [--controller <subtype>] [options]
```

```bash
# SATA controller, 30 ports, bootable
VBoxManage storagectl test \
    --name SATA --add sata \
    --controller IntelAhci \
    --portcount 30 \
    --bootable on \
    --hostiocache off                 # use the host's filesystem cache (off = direct I/O)

# IDE controller
VBoxManage storagectl test --name IDE --add ide --controller PIIX4

# NVMe controller
VBoxManage storagectl test --name NVMe --add pcie --controller NVMe

# SCSI (LSI Logic, common for enterprise compatibility)
VBoxManage storagectl test --name SCSI --add scsi --controller LsiLogic
```

`--name` is just a label you'll reference in `storageattach`. Convention: name it after the kind.

### `--hostiocache on/off`

Tells VirtualBox whether to use the host filesystem's cache for the controller's IO:

- `on` (default): VirtualBox lets the host kernel cache reads/writes. Higher throughput, but writes aren't immediately on disk — risk of corruption on host crash.
- `off`: direct/O_DIRECT-style IO. Slightly lower throughput, but writes hit disk when the guest thinks they do. Safer for storage-sensitive workloads.

For lab VMs: `off` is more honest behaviour, matching the real MS-S1 MAX's no-cache behaviour. Performance hit is modest on SSD-backed VDIs.

### Remove a controller

```bash
VBoxManage storagectl test --name IDE --remove
```

Detaches everything attached to it first.

## Disks

A VirtualBox disk is a file on the host filesystem. Multiple VMs can be attached to a single disk file (one at a time, in normal mode). The disk file is registered in VBox's media library when first used.

### Disk formats

| Format | Extension | Made by | Snapshots | Best for |
|---|---|---|---|---|
| **VDI** | `.vdi` | VirtualBox | Yes | New disks. Default. |
| **VMDK** | `.vmdk` | VMware | Yes | Cross-VMware/VBox use |
| **VHD** | `.vhd` | Microsoft | Yes | Hyper-V compatibility |
| **VHDX** | `.vhdx` | Microsoft | Yes | Newer Hyper-V |
| **RAW** | `.img`/`.raw` | (no metadata) | No (no metadata layer) | Bit-exact images, dd from physical disks |
| **Parallels HDD** | `.hdd` | Parallels | Yes | Cross-Parallels/VBox |

For lab work: stick with VDI unless you have a specific reason. It supports snapshots and dynamic sizing and is what VBoxManage defaults to.

### Allocation modes

| Mode | What | Pros | Cons |
|---|---|---|---|
| **Dynamic** (default) | File starts small, grows on write | Saves disk space; faster to create | First-time writes slightly slower; fragmentation possible |
| **Fixed** | File pre-allocated to full size | Fastest write perf, no fragmentation | Takes up full size on host immediately |
| **Differencing** | Stores only changes vs a parent disk | Useful for snapshots, clones | Chain of differencing files slows reads |

```bash
# Dynamic (default)
VBoxManage createmedium disk --filename disk.vdi --size 20000

# Fixed
VBoxManage createmedium disk --filename disk.vdi --size 20000 --variant Fixed

# Split into 2 GB chunks (VMDK only; for filesystems with 2 GB file size limits)
VBoxManage createmedium disk --filename disk.vmdk --size 20000 --format VMDK --variant Split2G
```

### Create a disk

```bash
VBoxManage createmedium disk \
    --filename /path/to/disk.vdi \
    --size 80000 \                       # MiB
    --format VDI                         # optional; inferred from extension
```

The disk is created and registered in VBox's media library. You can see it:

```bash
VBoxManage list hdds
# UUID: xxxxxxx
# Parent UUID: base
# State: created
# Location: /path/to/disk.vdi
# Storage format: VDI
# Format variant: dynamic default
# Capacity: 80000 MBytes
# Size on disk: 4 MBytes (the dynamic allocation hasn't grown yet)
```

### Modify a disk

```bash
# Grow (online if hot-plug, otherwise stop the VM first)
VBoxManage modifymedium disk /path/to/disk.vdi --resize 120000

# Compact — reclaim space inside the .vdi after the guest has zeroed it
# Step 1, inside the guest: dd if=/dev/zero of=/zerofile bs=1M; sync; rm /zerofile
# Step 2, on host (VM stopped):
VBoxManage modifymedium disk /path/to/disk.vdi --compact

# Mark non-rotational (the guest treats it like an SSD — no readahead games)
# Actually set on attachment, not creation; see storageattach below.

# Convert between formats
VBoxManage clonemedium disk old.vdi new.vmdk --format VMDK

# Clone (full copy)
VBoxManage clonemedium disk source.vdi clone.vdi
```

### Delete a disk

```bash
# Un-register from VBox's media library (keeps the file)
VBoxManage closemedium disk /path/to/disk.vdi

# Un-register AND delete the file
VBoxManage closemedium disk /path/to/disk.vdi --delete
```

Can't close a disk that's currently attached to a VM. Detach first:

```bash
VBoxManage storageattach test --storagectl SATA --port 0 --device 0 --medium none
VBoxManage closemedium disk /path/to/disk.vdi --delete
```

## Attach media to a VM

```bash
VBoxManage storageattach <vm> \
    --storagectl <controller-name> \
    --port <port> \
    --device <device-on-port> \
    --type <hdd|dvddrive|fdd> \
    --medium <path|"none"|"emptydrive"|"host:/dev/...">
    [extra flags]
```

```bash
# Attach a disk to SATA port 0
VBoxManage storageattach test \
    --storagectl SATA --port 0 --device 0 \
    --type hdd --medium /path/to/disk.vdi \
    --nonrotational on \                  # mark as SSD
    --discard on                          # propagate guest TRIM to .vdi

# Attach an ISO as a DVD drive
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --type dvddrive --medium /path/to/install.iso

# Empty DVD drive (no media inserted)
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --type dvddrive --medium emptydrive

# Pass through the host's actual DVD drive
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --type dvddrive --medium host:/dev/sr0

# Detach (no medium)
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --medium none
```

### Useful per-attachment flags

| Flag | What | Default |
|---|---|---|
| `--nonrotational on/off` | Marks the disk as SSD (no readahead, supports TRIM) | `off` |
| `--discard on/off` | Propagate guest TRIM to the host file (shrinks `.vdi` over time) | `off` |
| `--hotpluggable on/off` | Allow attach/detach while the VM runs | `off` |
| `--mtype normal/writethrough/immutable/shareable/readonly` | Disk semantics | `normal` |

### `mtype` (mount-type) modes

| Mode | Behaviour |
|---|---|
| `normal` | Default. Writes go to the .vdi, snapshots delta from base. |
| `writethrough` | Writes go straight to the .vdi, ignoring snapshots. Useful for "this disk's content is canonical regardless of snapshots". |
| `immutable` | All writes go to a per-VM delta that's discarded when the VM stops. Useful for templates / kiosks. |
| `shareable` | Multiple VMs can attach the same disk simultaneously (no snapshot). For shared cluster storage. |
| `readonly` | Self-explanatory. |

Lab use: stick with `normal`. The others are niche.

## TRIM / discard end-to-end

For TRIM to actually shrink the `.vdi` file when the guest deletes data:

1. **Guest filesystem mounted with `discard`** (or you run `fstrim -av` periodically). Ubuntu's default is `discard,errors=remount-ro`.
2. **Storage attached with `--discard on`** (you specify on `storageattach`).
3. **Disk marked nonrotational** (otherwise the guest doesn't issue TRIM): `--nonrotational on`.
4. **VDI format** supports TRIM. (VMDK, VHD also; RAW does not.)

```bash
# In the guest:
sudo fstrim -av

# On the host, see if the .vdi shrunk:
ls -lh disk.vdi
```

If `--discard off` (the default), TRIM in the guest is a no-op at the host file layer.

## Boot order

```bash
VBoxManage modifyvm test \
    --boot1 disk --boot2 dvd --boot3 net --boot4 none
```

VBox tries each device type in order. With `disk` first, the VM boots from the first bootable attached disk; if none is bootable, it tries DVD; etc.

`net` is PXE boot — needs the Extension Pack's PXE ROM.

## Hot-plug

Attach/detach disks while the VM is running:

```bash
# 1. Make sure the controller supports it. SATA and NVMe do; IDE doesn't.
# 2. Mark the attachment as hot-pluggable at attachment time:
VBoxManage storageattach test --storagectl SATA --port 7 --device 0 \
    --type hdd --medium new.vdi --hotpluggable on

# 3. Detach while running:
VBoxManage storageattach test --storagectl SATA --port 7 --device 0 \
    --medium none
```

Useful for simulating disk failure (detach), then bringing the disk back (re-attach) for ZFS resilver experiments.

## Lab disk layout (reference)

What `msai create` ends up with for one instance named `test`:

```
SATA controller (30 ports)
  port 0 device 0   test-primary.vdi             80 GB    OS disk
  port 1 device 0   test-lab-01.vdi               8 GB    ZFS lab disk 1
  port 2 device 0   test-lab-02.vdi               8 GB    ZFS lab disk 2
  port 3 device 0   test-lab-03.vdi               8 GB    ZFS lab disk 3
  port 4 device 0   test-lab-04.vdi               8 GB    ZFS lab disk 4
  port 5 device 0   test-lab-05.vdi               8 GB    ZFS lab disk 5
  port 6 device 0   test-lab-06.vdi               8 GB    ZFS lab disk 6
  port 7 device 0   ubuntu-26.04-server-arm64-autoinstall.iso     install
  port 8 device 0   test-cidata.iso              <1 MB    cloud-init
```

All on SATA because IDE crashes the ARM firmware. Lab disks 1-6 are blank — `zpool create` consumes them inside the guest. The two ISOs detach automatically after install completes (the boot order picks the OS disk after the first install reboot).

## See also

- [VBoxManage CLI](vboxmanage.md) — full command reference
- [Snapshots](snapshots.md) — how snapshots interact with disks (delta files)
- [Apple Silicon](apple-silicon.md) — IDE-crash details
