# VM Storage on ZFS

How to back libvirt/QEMU VM disks with ZFS. Two storage models, two `volblocksize` debates, snapshot caveats for running guests, and TRIM/discard plumbing.

## File-on-dataset vs zvol — pick one

ZFS gives you two ways to back a VM disk:

| Approach | What it is | Pros | Cons |
|---|---|---|---|
| **File on dataset** | A `.qcow2` (or `.raw`) sitting on a normal ZFS dataset, like any other file | Simple. qcow2 has its own snapshot/clone semantics. Easy backups (`cp`). Works with libvirt's `dir` storage pool out of the box. | qcow2 layer adds overhead (~5-10% on write-heavy workloads). Two snapshot systems (qcow2 + ZFS) confuse things. |
| **Zvol** | A block device exposed by ZFS at `/dev/zvol/<pool>/<path>` | No qcow2 layer. Native ZFS snapshots are the only snapshot mechanism. Better for Windows / NTFS guests. | Less flexible (no thin provisioning of the qcow2 kind). libvirt needs to know about it (use a `zfs` storage pool or pass the device path directly). Resize requires guest-side steps. |

For this build, default to **file-on-dataset (`.raw` or `.qcow2`)** unless you have a specific reason to go zvol:

- It's simpler. One source of snapshots (ZFS), one tool (`zfs snapshot`).
- The overhead is negligible on NVMe.
- libvirt's `dir` storage pool just works.

Use **zvols** when:

- The guest is Windows and you want native NTFS performance (the qcow2 layer hurts NTFS more than ext4/xfs).
- You're running databases that issue heavy small synchronous IO and you want to skip the qcow2 layer overhead.

## File-on-dataset approach (default for this build)

The libvirt storage pool was already created in [KVM Setup](../virtualization/kvm-setup.md):

```bash
sudo virsh pool-define-as vm-pool dir - - - - /mnt/tank/vm
sudo virsh pool-start vm-pool
sudo virsh pool-autostart vm-pool
```

The dataset `tank/vm` holds `.qcow2`/`.raw` files for each VM:

```
/mnt/tank/vm/
+-- win11/win11.qcow2
+-- ubuntu-utility/ubuntu-utility.qcow2
+-- ...
```

Recommended dataset properties for `tank/vm`:

```bash
sudo zfs create -o recordsize=64K tank/vm
# (Already done if you followed datasets.md.)

# Consider:
sudo zfs set primarycache=metadata tank/vm   # if VM disks are very large; or all if small/hot
```

Per-VM child datasets are reasonable if you want per-VM snapshot independence:

```bash
sudo zfs create tank/vm/win11
sudo zfs create tank/vm/ubuntu-utility
```

Then store each VM's qcow2 under its own dataset:

```
/mnt/tank/vm/win11/win11.qcow2
/mnt/tank/vm/ubuntu-utility/ubuntu-utility.qcow2
```

### Snapshot pattern

```bash
# Before a Windows Update / VM-config change
sudo zfs snapshot tank/vm/win11@before-windows-update-2026-05-17

# Run the update; if it bricks the VM:
sudo virsh shutdown win11           # or sudo virsh destroy win11 if it's hung
sudo zfs rollback tank/vm/win11@before-windows-update-2026-05-17
sudo virsh start win11
```

### `cache='none'` on the libvirt disk

The qcow2 file already lives on ZFS; ZFS already has its own caching (ARC). Letting libvirt also cache it doubles up. In the VM XML:

```xml
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2' cache='none' io='native' discard='unmap'/>
  <source file='/mnt/tank/vm/win11/win11.qcow2'/>
  <target dev='vda' bus='virtio'/>
</disk>
```

`cache='none'` + `io='native'` is the right default on ZFS-backed storage. `discard='unmap'` propagates guest TRIM down to the host so ZFS can reclaim space when the guest deletes files (see "TRIM/discard" below).

## Zvol approach

A zvol is a block device backed by the pool. Created with `zfs create -V <size>`:

```bash
sudo zfs create -V 200G \
    -o volblocksize=64K \
    -o compression=lz4 \
    tank/vm/win11
```

The zvol appears at `/dev/zvol/tank/vm/win11` (symlinked to `/dev/zd0` or similar).

### `volblocksize` — immutable, picks workload

`volblocksize` is the **fixed** block size for the zvol. Set at creation; can never be changed.

| Guest workload | `volblocksize` | Reason |
|---|---|---|
| Windows / NTFS | 8K-16K | NTFS default cluster is 4K; matches better with smaller volblocksize. |
| Linux / ext4 / xfs | 64K (or 128K) | Bigger blocks reduce metadata overhead and benefit sequential IO. |
| Database VMs (Postgres, MySQL) | 16K | Match the DB page size to avoid read-modify-write. |
| Mixed / unknown | 64K | Reasonable default; balances most workloads. |

**Get it wrong** and you'll see one of:

- **Too small** -> metadata overhead grows; small reads become amplified.
- **Too big** -> write amplification on small guest IOs (a 4K guest write triggers a read-modify-write of a 64K block on the host).

### Use with virt-install

```bash
sudo virt-install \
    --name win11 \
    --memory 16384 \
    --vcpus 8 \
    --os-variant win11 \
    --disk path=/dev/zvol/tank/vm/win11,bus=virtio,cache=none,io=native,discard=unmap \
    --cdrom /path/to/win11.iso \
    --network network=default \
    --graphics spice \
    --boot uefi
```

Note `bus=virtio` for performance; the virtio-blk driver in Windows comes from the virtio-win ISO.

### Snapshot a zvol the same way as a dataset

```bash
sudo zfs snapshot tank/vm/win11@before-update
```

The snapshot captures the block-level state. Rolling back restores the entire virtual disk — equivalent to restoring a disk image.

### Resize a zvol

Grow only — shrinking zvols isn't supported.

```bash
sudo zfs set volsize=300G tank/vm/win11
```

Then in the guest, extend the partition + filesystem:

- Windows: Disk Management -> extend volume.
- Linux: `parted /dev/vda resizepart`, `resize2fs` / `xfs_growfs`.

## libvirt storage pool for zvols

Two options:

### Option A — `dir` pool with explicit device paths (simplest)

Use the existing `vm-pool` (which is `dir` type at `/mnt/tank/vm`) for qcow2 files. For zvols, **don't** use the dir pool — just reference `/dev/zvol/tank/vm/<name>` directly in the VM XML.

### Option B — native ZFS storage pool

libvirt has a `zfs` storage pool driver that knows how to create/destroy zvols via libvirt API. Requires the optional `libvirt-daemon-driver-storage-zfs` package (added in [KVM Setup](../virtualization/kvm-setup.md)).

```xml
<!-- zvol-pool.xml -->
<pool type='zfs'>
  <name>zvol-pool</name>
  <source>
    <name>tank/vm</name>
  </source>
</pool>
```

```bash
sudo virsh pool-define zvol-pool.xml
sudo virsh pool-start zvol-pool
sudo virsh pool-autostart zvol-pool
```

Now `virsh vol-create-as` works:

```bash
sudo virsh vol-create-as zvol-pool win11.zvol 200G --format raw
```

For one or two VMs the dir + explicit path approach is easier. For many VMs the native pool reduces friction.

## TRIM / discard end-to-end

When a guest filesystem deletes data, by default the host doesn't know — ZFS still holds those blocks. To reclaim them, TRIM must propagate from guest -> virtio-blk -> qemu -> host -> ZFS.

Required configuration:

1. **Guest**: filesystem with `discard` mount option, or scheduled `fstrim`. Windows uses NTFS Optimize Drives weekly by default.
2. **Libvirt disk XML**: `discard='unmap'` (already in the example above).
3. **Backing storage**:
   - File-on-dataset: ZFS sees the punch-hole and frees the blocks. Just works.
   - Zvol: `volblocksize`-aligned discards work; misaligned discards are noops.
4. **Pool**: `autotrim=on` (set at pool creation) makes the underlying NVMe see the TRIM eventually.

Verify the chain end-to-end:

```bash
# On the host: before/after `zfs list` to see space change
zfs list tank/vm
# Inside guest:
sudo fstrim -av           # Linux
# (Windows: built-in scheduled task; you can run "Optimize" manually)
# On host:
zfs list tank/vm           # should show freed space
```

## Snapshots of *running* VMs

Snapshotting a dataset while a VM is writing to a file/zvol on it captures a **crash-consistent** state — the same as if the VM had lost power at that instant. The VM filesystem will replay its journal on next boot, but you may lose recently-written application data.

For application-consistent snapshots:

1. **Quiesce the VM filesystem first** with the qemu-guest-agent. Install `qemu-guest-agent` inside the guest, configure libvirt to talk to it.
2. **Freeze**: `sudo virsh domfsfreeze win11`
3. **Snapshot**: `sudo zfs snapshot tank/vm/win11@app-consistent`
4. **Thaw**: `sudo virsh domfsthaw win11`

For most homelab uses, crash-consistent is fine — modern filesystems recover cleanly and you've usually got the snapshot for "before-update" purposes, not for "in-flight transactions".

The riskiest case is snapshotting a running **database** VM. For DBs:

- Either shut the DB down briefly (`docker compose stop postgres`) before snapshotting, or
- Use the DB's own backup mechanism (`pg_dump`, `mysqldump`) into a snapshotted dataset.

## Cloning VMs

ZFS clones are perfect for "give me a copy of this VM I can play with":

```bash
# Snapshot the source
sudo virsh shutdown ubuntu-base
sudo zfs snapshot tank/vm/ubuntu-base@golden

# Clone the dataset
sudo zfs clone tank/vm/ubuntu-base@golden tank/vm/ubuntu-test

# Copy the libvirt definition with a new name and disk path
sudo virsh dumpxml ubuntu-base | sed 's|ubuntu-base|ubuntu-test|g' > /tmp/ubuntu-test.xml
sudo virsh define /tmp/ubuntu-test.xml
sudo virsh start ubuntu-test
```

The new VM shares blocks with the original until it diverges. Cheap "I want 10 disposable VMs from the same base" pattern.

Inside the guest, change the hostname, machine-id, SSH host keys before letting it on the network:

```bash
sudo hostnamectl set-hostname ubuntu-test
sudo systemd-firstboot --setup-machine-id
sudo dpkg-reconfigure openssh-server   # regenerates host keys
```

## Performance considerations

For the MS-S1 MAX:

- **Keep VM disks on the primary 2 TB NVMe partition** (PCIe 4.0 x4). The secondary 4 TB NVMe is x1 — fine for media, slow for VM disks.
- **Use virtio drivers** end-to-end: `bus=virtio` for disks, `model=virtio` for network, virtio-balloon, virtio-rng.
- **Pin the VM to a single CCX** ([VM Resources](../virtualization/vm-resources.md)). Disk IO threads benefit from cache locality.
- **`cache=none`** for ZFS-backed VMs. ARC handles caching; double-caching wastes RAM.
- **`io=native`** with libaio is the right async-IO mode on Linux.
- Pre-allocate disks if guest perf matters: `qemu-img create -f raw -o preallocation=off` (sparse, normal) vs `falloc` (allocate-now). Trade space for predictability.

## When the VM corrupts its filesystem

The reason ZFS snapshots are so good for VMs: when the guest filesystem corrupts itself (botched update, kernel panic during a write, disk full at the wrong moment), you can:

1. Shut the VM down.
2. `zfs rollback tank/vm/<name>@<snapshot>`.
3. Start the VM.

The guest sees its disk as it was at snapshot time. No `fsck` adventure, no restoring from offline backup, no waiting on a slow rebuild.

That single workflow is the strongest reason to put VM disks on ZFS.

## Next steps

- [Docker Integration](docker-integration.md) — containers on ZFS-backed bind mounts.
- [Operations](operations.md) — scrub schedules, disk replace, expanding the pool.
- [Backup & Recovery](../operations/backup.md) — replicating snapshots off-host.
