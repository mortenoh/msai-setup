# VirtualBox Lab

A hands-on lab for practising ZFS before you commit to the real MS-S1 MAX install. Everything below runs in a VirtualBox VM with virtual disks — you can blow it away and start over as many times as you like.

The lab progresses from "first pool" through "topology comparisons", "snapshots + send/receive", "simulated disk failure + scrub", "encryption", and finishes with a mock-up of the production MS-S1 MAX layout.

## Why use a lab

- You can simulate failures (rip a disk out, see what `zpool status` says) without losing data.
- You can compare topologies (stripe vs mirror vs raidz) side by side without buying extra hardware.
- You can rehearse the actual production commands, then `zpool destroy && exit` and walk away.
- You learn the tools (`gdisk`, `parted`, `wipefs`, `sgdisk`, `zpool`, `zfs`) on disks where mistakes are free.

VirtualBox is the easiest path on macOS/Windows hosts. If you have a Linux box, KVM/libvirt works equally well — substitute `virt-install` for the VirtualBox UI steps.

## Setting up the lab VM

The repo ships a small Python CLI (`msai`) that wraps `VBoxManage` so you can create the lab VM with one command. The VM comes with a primary disk and 6 spare SATA "lab" disks — exactly what the exercises below assume.

```bash
# From the msai-setup repo root
uv sync                       # one-time install of the msai CLI
uv run msai create zfs-lab    # ~3-4 minutes: builds VM, installs Ubuntu 26.04, comes up with SSH key-auth
uv run msai list              # confirm it's running
uv run msai ssh               # opens a shell on the lab VM
```

That's enough to start Lab 1 below. You don't need the Ansible playbook for the exercises — they walk through `zpool create` by hand, on purpose.

### A few CLI cheats while you work

```bash
# Power
uv run msai stop zfs-lab
uv run msai start zfs-lab

# Snapshot the VirtualBox VM between experiments
VBoxManage snapshot zfs-lab take pre-experiment --pause

# Restore to the last snapshot when an exercise blew up
VBoxManage snapshot zfs-lab restorecurrent

# Throw it away entirely
uv run msai lab destroy
```

### Optional — run the ZFS playbook to see the "production" layout

If you want to see what a "real" pool + dataset layout looks like before doing the exercises by hand, run the Ansible playbook once:

```bash
uv run msai lab apply zfs    # creates `tank` pool across 6 disks + dataset hierarchy
```

Then `zpool destroy tank` and start over manually for the labs. The point is to *do* the commands, not just read them.

### What this build does for you

For reference, the equivalent `VBoxManage` calls (substitute your instance name for `<vm>`):

```bash
# Create the VM (UEFI on amd64; arm-firmware on Apple Silicon)
VBoxManage createvm --name <vm> --register
VBoxManage modifyvm <vm> \
    --memory 8192 --cpus 4 --vram 32 \
    --firmware efi64 \
    --nic1 nat \
    --natpf1 "ssh,tcp,127.0.0.1,2222,,22" \
    --rtcuseutc on \
    --audio-driver none

# Primary disk + 6 lab disks on the SATA controller
VBoxManage storagectl <vm> --name SATA --add sata --controller IntelAhci --portcount 30 --bootable on
VBoxManage createmedium disk --filename "target/<vm>-primary.vdi" --size 80000 --format VDI
VBoxManage storageattach <vm> --storagectl SATA --port 0 --device 0 \
    --type hdd --medium "target/<vm>-primary.vdi" --nonrotational on --discard on
for i in 1 2 3 4 5 6; do
    pad=$(printf "%02d" "$i")
    VBoxManage createmedium disk --filename "target/<vm>-lab-${pad}.vdi" --size 8000 --format VDI
    VBoxManage storageattach <vm> --storagectl SATA --port "$i" --device 0 \
        --type hdd --medium "target/<vm>-lab-${pad}.vdi" --nonrotational on --discard on
done

VBoxManage startvm <vm> --type headless
```

On Apple Silicon the wrapper adds `--platform-architecture arm` at createvm time, sets `--ostype Ubuntu_arm64`, and uses `qemuramfb` instead of `vboxvga` — see `docs/virtualbox/apple-silicon.md` for the full ARM-specific recipe.

### Other useful VBoxManage commands

```bash
# List VMs / show details
VBoxManage list vms
VBoxManage list runningvms
VBoxManage showvminfo <vm>
VBoxManage showvminfo <vm> --machinereadable    # parseable

# Live VM control
VBoxManage controlvm <vm> pause
VBoxManage controlvm <vm> resume
VBoxManage controlvm <vm> reset                  # hard reset (Ctrl+Alt+Del-style)
VBoxManage controlvm <vm> acpipowerbutton        # graceful shutdown
VBoxManage controlvm <vm> poweroff               # pull the plug

# Snapshots (lifecycle of the VM image itself, not ZFS snapshots)
VBoxManage snapshot <vm> take pre-experiment --pause
VBoxManage snapshot <vm> list
VBoxManage snapshot <vm> restorecurrent          # restore most recent
VBoxManage snapshot <vm> restore pre-experiment  # restore by name
VBoxManage snapshot <vm> delete pre-experiment

# Hotplug a disk (e.g. to simulate adding a replacement drive)
VBoxManage createmedium disk --filename target/extra.vdi --size 8000 --format VDI
VBoxManage storageattach <vm> --storagectl SATA --port 7 --device 0 \
    --type hdd --medium target/extra.vdi --hotpluggable on --nonrotational on

# Detach a disk (simulate failure)
VBoxManage storageattach <vm> --storagectl SATA --port 7 --device 0 --medium none

# Resize a disk
VBoxManage modifymedium disk target/extra.vdi --resize 16000

# Unregister + delete everything
VBoxManage unregistervm <vm> --delete
```

## Inside the VM — install ZFS and identify the lab disks

SSH in (`uv run msai ssh`) and prepare the toolchain:

```bash
sudo apt update
sudo apt install -y zfsutils-linux
sudo modprobe zfs                       # safe to re-run

# Verify
modinfo zfs | grep -E '^version'
sudo zpool status
sudo zfs version
```

You should see "no pools available" — that's expected; we'll create them in a minute.

```bash
lsblk -o NAME,SIZE,MODEL,SERIAL,TYPE
ls -la /dev/disk/by-id/ | grep ata-VBOX_HARDDISK | grep -v part
```

VirtualBox sets the disk serial automatically. The primary OS disk (the one you booted from) is `sda`; the six lab disks are `sdb`-`sdg`. By-id paths look like:

```
/dev/disk/by-id/ata-VBOX_HARDDISK_VB12345678-12345678 -> ../../sdb
/dev/disk/by-id/ata-VBOX_HARDDISK_VB23456789-23456789 -> ../../sdc
...
```

Set env vars so the rest of the commands stay readable:

```bash
DISK1=/dev/disk/by-id/ata-VBOX_HARDDISK_VB12345678-12345678
DISK2=/dev/disk/by-id/ata-VBOX_HARDDISK_VB23456789-23456789
DISK3=/dev/disk/by-id/ata-VBOX_HARDDISK_VB34567890-34567890
DISK4=/dev/disk/by-id/ata-VBOX_HARDDISK_VB45678901-45678901
# ...etc
```

## Lab 1 — Your first pool (single disk, stripe)

```bash
sudo zpool create -o ashift=12 \
    -O compression=lz4 \
    -O atime=off \
    -O xattr=sa \
    -O acltype=posixacl \
    -O mountpoint=/mnt/lab \
    lab "$DISK1"

zpool status lab
zfs list
df -h /mnt/lab
```

Read the output carefully — `zpool status` shows the topology and (right now) one healthy disk.

Write something, prove it works:

```bash
sudo dd if=/dev/urandom of=/mnt/lab/test.bin bs=1M count=500
ls -lh /mnt/lab/
zfs list lab
```

Tear it down:

```bash
sudo zpool destroy lab
```

The pool is gone. The data on `$DISK1` is gone (well, the metadata pointing to it — the blocks are still there until overwritten). The disk is "free" again. This is the cheap-disposability you don't get with physical drives.

## Lab 2 — Mirror

A two-disk mirror — survives losing one disk.

```bash
sudo zpool create -o ashift=12 \
    -O compression=lz4 -O mountpoint=/mnt/lab \
    lab mirror "$DISK1" "$DISK2"

zpool status lab
sudo zpool list lab
```

Note: `zpool list` shows the **raw** size (sum of both disks). `df -h /mnt/lab` shows the **usable** size (half of that). Mirrors trade space for redundancy.

### Simulate a disk failure

In VirtualBox:

1. With the VM running, go to Settings -> Storage and detach `lab-disk-02.vdi` (right-click on the controller line -> Remove Attachment, or use **VBoxManage storagectl --remove** from the host CLI).
2. Back in the VM: `sudo zpool status lab`

You'll see the missing disk listed as `UNAVAIL` or `REMOVED`. The pool is still online — reads and writes continue.

Re-attach the disk and let ZFS resilver:

```bash
sudo zpool online lab "$DISK2"
sudo zpool status lab        # should now show DEGRADED -> resilvering -> ONLINE
```

Watch the resilver run:

```bash
watch -n 1 zpool status lab
```

### Replace a disk

Pretend a disk died and you've installed a new one. The new disk shows up as `$DISK3`.

```bash
sudo zpool replace lab "$DISK2" "$DISK3"
sudo zpool status lab        # resilvering onto $DISK3
```

Once resilver completes, `$DISK2` is no longer a pool member. You could now physically remove it.

Destroy and reset:

```bash
sudo zpool destroy lab
```

## Lab 3 — RAIDZ1

Three or more disks; survives one failure; more space-efficient than mirrors.

```bash
sudo zpool create -o ashift=12 \
    -O compression=lz4 -O mountpoint=/mnt/lab \
    lab raidz1 "$DISK1" "$DISK2" "$DISK3"

zpool list lab
zfs list lab
```

For 3x8 GB disks in raidz1 you should see ~16 GB usable (2/3 efficiency).

Compare with `zpool status -v` and `zpool iostat -v lab 1` while you write data:

```bash
sudo dd if=/dev/zero of=/mnt/lab/big.bin bs=1M count=4096 status=progress
```

(With compression=lz4 and zeros input, compression will be ~∞:1 — try `/dev/urandom` for realistic throughput.)

Destroy when done.

## Lab 4 — Datasets, properties, inheritance

```bash
# Re-create a simple pool
sudo zpool create -o ashift=12 \
    -O compression=lz4 -O atime=off \
    -O mountpoint=/mnt/lab \
    lab "$DISK1"

# Top-level: defaults to the pool's settings
zfs get compression,recordsize,atime lab

# Create child datasets, override properties
sudo zfs create lab/media
sudo zfs set recordsize=1M lab/media

sudo zfs create lab/db
sudo zfs set recordsize=16K lab/db
sudo zfs set primarycache=metadata lab/db   # demonstrate; not usually a good idea

sudo zfs create lab/scratch
sudo zfs set sync=disabled lab/scratch       # demonstrate; data loss possible on crash

# See inheritance — each gets its own value or inherits
zfs get -r compression,recordsize,primarycache,sync lab
```

Try a quota and a reservation:

```bash
sudo zfs set quota=1G lab/db
sudo zfs set reservation=500M lab/db

# Try to exceed quota
sudo dd if=/dev/urandom of=/mnt/lab/db/blob bs=1M count=2000 || echo "blocked"

# Check
zfs list -o name,used,avail,quota,reservation lab/db
```

Destroy:

```bash
sudo zpool destroy lab
```

## Lab 5 — Snapshots, clones, rollback

```bash
sudo zpool create -O mountpoint=/mnt/lab lab "$DISK1"
sudo zfs create lab/data
echo "version 1" | sudo tee /mnt/lab/data/state.txt

# Snapshot
sudo zfs snapshot lab/data@v1

# Change live filesystem
echo "version 2" | sudo tee /mnt/lab/data/state.txt
echo "version 3" | sudo tee /mnt/lab/data/state.txt

# Inspect snapshot vs live
cat /mnt/lab/data/state.txt
cat /mnt/lab/data/.zfs/snapshot/v1/state.txt

# Rollback
sudo zfs rollback lab/data@v1
cat /mnt/lab/data/state.txt   # back to version 1

# Clone (writable fork of the snapshot)
sudo zfs clone lab/data@v1 lab/data-fork
echo "alternate timeline" | sudo tee /mnt/lab/data-fork/state.txt

# The original snapshot is still pristine
cat /mnt/lab/data/.zfs/snapshot/v1/state.txt

# Promote the clone (swap roles — now lab/data-fork is the parent, lab/data depends on it)
sudo zfs promote lab/data-fork
zfs list -r -t all lab
```

Snapshots take zero space initially:

```bash
zfs list -t snapshot
zfs list -o name,used,refer lab/data
```

The `USED` column on a snapshot is "blocks unique to this snapshot that the live filesystem no longer references". It grows as the live filesystem diverges.

## Lab 6 — `zfs send`/`zfs receive` for replication

Two pools on the same VM, simulating "main" and "backup":

```bash
sudo zpool create -O mountpoint=/mnt/lab main "$DISK1"
sudo zpool create -O mountpoint=/mnt/backup backup "$DISK2"

sudo zfs create main/data
echo "important" | sudo tee /mnt/lab/data/file.txt
ls /mnt/lab/data           # the `main` pool is mounted at /mnt/lab, so main/data is /mnt/lab/data
```

(Adjust paths to your `mountpoint=` choice; the example uses pool-level mountpoints — `main` at `/mnt/lab`, `backup` at `/mnt/backup`.)

Snapshot + full send:

```bash
sudo zfs snapshot main/data@snap1
sudo zfs send main/data@snap1 | sudo zfs receive backup/data

zfs list -r backup
```

Make changes, take a second snapshot, send incrementally:

```bash
echo "more important" | sudo tee /mnt/lab/data/file.txt
sudo zfs snapshot main/data@snap2

sudo zfs send -i main/data@snap1 main/data@snap2 | sudo zfs receive backup/data
```

You've now replicated only the delta. For real-world use, install `syncoid` (from the `sanoid` package) and let it do the bookkeeping:

```bash
sudo apt install -y sanoid

# Local replication (same machine, between pools)
syncoid main/data backup/data

# Or remote — practice the SSH form by SSH'ing to localhost
syncoid main/data root@127.0.0.1:backup/data
```

## Lab 7 — Native ZFS encryption

```bash
sudo zpool create -O mountpoint=/mnt/lab lab "$DISK1"

# Create an encrypted dataset with a passphrase
sudo zfs create -o encryption=aes-256-gcm \
                -o keyformat=passphrase \
                lab/secrets

# It prompts for the passphrase. Try writing:
echo "secret message" | sudo tee /mnt/lab/secrets/file.txt
```

Unmount and force a "lock" by unloading the key:

```bash
sudo zfs unmount lab/secrets
sudo zfs unload-key lab/secrets

# Now the dataset has no in-RAM key. Reading the disk would yield ciphertext.
ls /mnt/lab/secrets        # empty / unmounted

# To use it again:
sudo zfs load-key lab/secrets   # prompts for passphrase
sudo zfs mount lab/secrets
cat /mnt/lab/secrets/file.txt
```

Try a **raw send** — keeps ciphertext encrypted on the receiving side:

```bash
sudo zpool create -O mountpoint=/mnt/backup backup "$DISK2"

sudo zfs snapshot lab/secrets@e1
sudo zfs send -w lab/secrets@e1 | sudo zfs receive backup/secrets

# The receiving side has no key. Trying to mount fails:
sudo zfs mount backup/secrets    # error: encrypted dataset, no key loaded

# Load the same passphrase on the receiving side:
sudo zfs load-key backup/secrets
sudo zfs mount backup/secrets
cat /mnt/backup/secrets/file.txt
```

The point: you can replicate encrypted data to an untrusted backup host. The backup host stores ciphertext only and cannot read it without the key.

## Lab 8 — Scrubs and bit-rot simulation

Scrubs read everything and verify checksums. You can simulate corruption by writing garbage to a leaf disk and then scrubbing — ZFS will report errors and (on a redundant vdev) self-heal them.

```bash
# Two-disk mirror so we have redundancy to heal from
sudo zpool create -o ashift=12 \
    -O mountpoint=/mnt/lab \
    lab mirror "$DISK1" "$DISK2"

# Fill with random data
sudo dd if=/dev/urandom of=/mnt/lab/big.bin bs=1M count=1024 status=progress
sync

# Find the on-disk location of some blocks (advanced — just for demonstration)
# Or skip that and just corrupt random sectors on $DISK1 directly.
# DANGEROUS in real life; OK in the lab.
sudo dd if=/dev/urandom of="$DISK1" bs=4K count=10 seek=2000 conv=notrunc

# Now scrub
sudo zpool scrub lab
watch -n 1 zpool status lab
```

When the scrub finishes you'll see a checksum error count under `$DISK1` and (because the pool has a mirror) the data is repaired transparently. On a single-disk pool, those same errors would result in unreadable files.

Clear the error counters:

```bash
sudo zpool clear lab
```

## Lab 9 — Recreate the MS-S1 MAX layout (two pools)

Final lab: build a model of the actual production layout inside the VM, so you can rehearse the partitioning, pool-creation, and dataset-setup commands you'll run for real. The real build uses **two independent pools** — `hot` on the fast 4 TB drive (hot data + Incus instances) and `tank` on the slow 2 TB drive (bulk/cold data) — see [Datasets](datasets.md) and [Pool Creation](pool-creation.md).

!!! note "The lab mirrors the production pools exactly now"
    On real hardware root is ext4 and `hot`/`tank` are plain data pools at their default mountpoints `/hot` and `/tank` — so the lab reproduces them one-for-one, no root-on-ZFS boot to fake. Create `hot` and `tank` on two spare disks and you have the production storage shape. (To rehearse the root-on-ZFS *alternative* instead, use `msai lab install-zfs-root` — see [ZFS Root (Alternative)](../ubuntu/installation/zfs-root-alternative.md).)

### Set up the disks

Add two new virtual disks. The real hardware puts the **larger 4 TB drive in the fast slot as `hot`** and the **smaller 2 TB drive in the slow slot as `tank`**, so make the `hot` disk the bigger of the two. Ports 0-6 already hold the OS disk + six lab disks, so attach on ports 7 and 8. Run on the **host** (your Mac), substituting your VM name for `zfs-lab`:

```bash
# hot disk — the bigger one (mocks the fast 4 TB drive)
VBoxManage createmedium disk --filename "target/lab-hot-4tb.vdi" --size 200000 --format VDI
VBoxManage storageattach zfs-lab --storagectl SATA --port 7 --device 0 \
    --type hdd --medium "target/lab-hot-4tb.vdi" --hotpluggable on --nonrotational on --discard on

# tank disk — the smaller one (mocks the slow 2 TB drive)
VBoxManage createmedium disk --filename "target/lab-tank-2tb.vdi" --size 100000 --format VDI
VBoxManage storageattach zfs-lab --storagectl SATA --port 8 --device 0 \
    --type hdd --medium "target/lab-tank-2tb.vdi" --hotpluggable on --nonrotational on --discard on
```

`--size` is in MB, so 200000 ≈ 200 GB and 100000 ≈ 100 GB. Only the relative sizing matters — `hot` disk ~2x the `tank` disk, matching the 4 TB / 2 TB reality. Because the disks are `--hotpluggable`, they appear inside the running VM as two new `ata-VBOX_HARDDISK_*` entries under `/dev/disk/by-id/` (confirm with `lsblk` / `ls -la /dev/disk/by-id/ | grep -v part`).

### Partition the disks

On real hardware the primary also carries the ext4 EFI/`/boot`/root partitions (Subiquity's job) with `hot` as p4; in the lab there's no OS on these spare disks, so put each pool on a single whole-disk ZFS partition:

```bash
HOT_DISK=/dev/disk/by-id/ata-VBOX_HARDDISK_VB-hot-...
TANK_DISK=/dev/disk/by-id/ata-VBOX_HARDDISK_VB-tank-...

# Wipe the hot disk and lay down a single ZFS member
sudo wipefs -a "$HOT_DISK"
sudo sgdisk --zap-all "$HOT_DISK"
sudo sgdisk -n1:0:0 -t1:BF00 "$HOT_DISK"   # ZFS pool member (whole disk)
sudo partprobe "$HOT_DISK"

# Wipe the tank disk entirely; whole-disk pool
sudo wipefs -a "$TANK_DISK"
sudo sgdisk --zap-all "$TANK_DISK"
sudo sgdisk -n1:0:0 -t1:BF00 "$TANK_DISK"
sudo partprobe "$TANK_DISK"
```

### Create the two pools

```bash
# hot — the fast pool (default mountpoint /hot, exactly as in production)
sudo zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    hot "${HOT_DISK}-part1"

# tank — the bulk/cold pool
sudo zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    tank "${TANK_DISK}-part1"

sudo zpool status
sudo zpool list
```

Both pools take their default mountpoints (`/hot`, `/tank`) — the same as production, since root is ext4 and neither pool holds `/`.

### Recreate the production dataset layout

```bash
# hot — hot data (hot/incus is Incus's backend; on real hardware you hand it to Incus)
sudo zfs create -o mountpoint=none        hot/incus
sudo zfs create -o recordsize=16K         hot/db
sudo zfs create -o recordsize=1M -o compression=off hot/ai

# tank — bulk/cold data
sudo zfs create -o recordsize=1M          tank/media
sudo zfs create                           tank/nextcloud-data
sudo zfs create                           tank/nextcloud-app
sudo zfs create -o compression=zstd-3     tank/backups

zfs list
zfs get compression,recordsize -r hot
zfs get compression,recordsize -r tank
```

Note there is **no `tank/vm` or `tank/containers`** — on real hardware Incus creates per-instance datasets under `hot/incus` automatically. In the lab you can simulate that with a couple of throwaway child datasets if you want to see the shape:

```bash
sudo zfs create hot/incus/containers
sudo zfs create hot/incus/virtual-machines
```

(On the real box, never hand-create datasets under `hot/incus` — Incus owns it. See [Incus storage](../incus/storage.md).)

### Cap the ARC (matches the real install)

```bash
echo 'options zfs zfs_arc_max=2147483648' | sudo tee /etc/modprobe.d/zfs.conf
# Apply live without reboot for the lab:
echo 2147483648 | sudo tee /sys/module/zfs/parameters/zfs_arc_max
cat /sys/module/zfs/parameters/zfs_arc_max
```

(The lab caps at 2 GiB because the VM has limited RAM; the production cap is 16 GiB, shared across both pools.)

### Try sanoid (matches the real install plan)

```bash
sudo apt install -y sanoid

sudo tee /etc/sanoid/sanoid.conf > /dev/null <<'EOF'
[template_data]
    hourly = 24
    daily = 30
    weekly = 4
    monthly = 3
    autosnap = yes
    autoprune = yes

[hot/incus]
    use_template = data
    recursive = yes

[hot/db]
    use_template = data
    recursive = yes

[tank/nextcloud-data]
    use_template = data
EOF

sudo sanoid --cron
zfs list -t snapshot
```

You've now rehearsed the whole two-pool production storage setup on disposable virtual hardware.

## Tear-down

When you're done with an exercise but want to keep the VM (destroy whichever pools you created):

```bash
sudo zpool destroy tank
sudo zpool destroy hot     # if you did Lab 9's two-pool mock
sudo zpool list
```

When you're done with the VM entirely:

```bash
# From your Mac, not the VM
uv run msai lab destroy
```

Between exercises, the lighter pattern is to snapshot the VM:

```bash
VBoxManage snapshot zfs-lab take fresh-zfs --pause
# ... do an exercise that blows things up ...
VBoxManage snapshot zfs-lab restorecurrent       # back to "ZFS installed, no pool"
```

## What this lab doesn't cover

- **Disk-firmware-specific behaviour**: real NVMe drives have power-loss-protection differences, TRIM behaviour, and write-amplification that VirtualBox doesn't model.
- **Performance**: virtual disks share host I/O; numbers are not representative.
- **NUMA and large-RAM ARC behaviour**: only visible on real hardware with lots of RAM.

For everything else — operations, command syntax, recovery flows, mental model — the lab is a faithful enough environment that you'll arrive at the real install confident about which key to press.
