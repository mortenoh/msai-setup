# VM Storage on ZFS

On this build, **VMs are Incus VM instances**, and their disks are ZFS **zvols that Incus creates and manages automatically** under `hot/incus/virtual-machines/`. There is no hand-rolled `tank/vm` dataset, no `virsh`/`virt-install`, and no `.qcow2` files on a `dir` pool. Incus's ZFS storage driver does the block-device plumbing for you.

So this page is now mostly **background**: it explains *why* zvol-backed VM disks behave the way they do, so the properties you set through Incus make sense. For the mechanics of creating VMs and managing their storage, the source-of-truth pages are:

- [Incus storage — the ZFS driver in depth](../incus/storage.md) — how `hot/incus` becomes Incus's pool, per-instance zvols, sizing, snapshots, clones.
- [Incus VMs](../incus/vms.md) — launching and configuring VM instances.
- [Windows VM](../incus/windows-vm.md) — the Windows 11 instance (TPM, Secure Boot, virtio).

!!! note "What changed from the old design"
    The original design ran VMs under bare libvirt/QEMU with qcow2 files (or manual zvols) on a `tank/vm` dataset. That's gone. Incus is the single virtualization layer, KVM/QEMU runs under it, and every VM's disk is a ZFS zvol Incus manages on `hot/incus`. The ZFS *concepts* below still apply — Incus just owns the create/destroy/snapshot lifecycle now.

## Why a zvol (and not a file on a dataset)

ZFS can back a virtual disk two ways, and it's worth understanding the choice Incus makes for you:

| Approach | What it is | Trade-offs |
|---|---|---|
| **File on dataset** | A `.raw`/`.qcow2` file on a normal ZFS filesystem dataset | Simple to `cp`, but adds a qcow2/file layer on top of ZFS, and tempts you into two snapshot systems (qcow2 *and* ZFS). |
| **Zvol** | A ZFS block device (`/dev/zvol/...`) exposed straight to the guest | No file-format layer; native ZFS snapshots are the only snapshot mechanism; better for NTFS/Windows guests. **This is what Incus uses.** |

Incus gives each VM a small config filesystem dataset plus a `.block` zvol for the disk:

```bash
zfs list -t all -r hot/incus/virtual-machines
# hot/incus/virtual-machines/win11         (a small config filesystem)
# hot/incus/virtual-machines/win11.block   (the zvol — the VM's disk)
```

You never run `zfs create -V` for these by hand — `incus launch ... --vm` does it. (See [Incus storage → VMs](../incus/storage.md#vms).)

## `volblocksize` — why it matters even though Incus sets it

A zvol has a fixed **`volblocksize`** (the block size the guest's I/O is chopped into), set at creation and immutable afterward. Getting it wrong causes:

- **Too small** → more metadata overhead; small reads amplified.
- **Too big** → write amplification (a 4 K guest write triggers a read-modify-write of the whole block).

Rules of thumb by guest workload:

| Guest workload | Good block size | Reason |
|---|---|---|
| Windows / NTFS | 8K–16K | NTFS default cluster is 4K; smaller blocks align better. |
| Linux / ext4 / xfs | 64K | Bigger blocks cut metadata overhead, help sequential I/O. |
| Database VMs | 16K | Match the DB page size to avoid read-modify-write. |
| Mixed / unknown | 16K | Incus's own default for zvols; a safe middle ground. |

You don't set this with `zfs create` — you set it through Incus, which applies it when it creates the zvol:

```bash
# Pool-wide default block size for new volumes
incus storage set default volume.zfs.blocksize 16KiB

# Per-volume override (e.g. a Linux VM wanting larger blocks)
incus storage volume set default win11.block zfs.blocksize 16KiB
```

See [Incus storage → sizing and properties](../incus/storage.md#sizing-and-properties). The old `recordsize=64K` advice for `tank/vm` was the same instinct — balance guest small-I/O against bulk operations — just expressed through the file-on-dataset knob instead of the zvol one.

## Sizing a VM's disk

The disk size is a property of the instance's `root` disk device (Incus turns it into a ZFS quota/refquota), not something you `zfs set volsize` directly:

```bash
# At launch
incus launch images:ubuntu/24.04 builder --vm -d root,size=60GiB

# Later
incus config device set builder root size=80GiB
```

Growing works; shrinking a zvol does not (same ZFS limitation as before). After growing, extend the partition + filesystem inside the guest.

## Snapshots of running VMs — crash-consistent by default

Snapshotting a VM's zvol while the guest is running captures a **crash-consistent** state — as if the VM lost power at that instant. The guest journals replay on next boot; you may lose the last few seconds of in-flight application writes. Prefer Incus's own snapshot command so its database stays in sync:

```bash
# Incus-aware snapshot (recommended)
incus snapshot create win11 before-update

# Restore
incus snapshot restore win11 before-update
```

Under the hood this is a ZFS snapshot on `hot/incus/virtual-machines/win11.block` — see [Incus storage → snapshots](../incus/storage.md#snapshots-and-clones-incus-vs-raw-zfs).

For **application-consistent** snapshots (databases especially), quiesce inside the guest first — stop the DB, or use the guest agent to freeze the filesystem — before taking the snapshot. For most homelab uses, crash-consistent "before-update" snapshots are enough.

!!! warning "Never `zfs rollback`/`zfs receive` a running VM's zvol"
    Overwriting an instance's zvol while the VM runs corrupts the guest filesystem. Stop the instance first (`incus stop win11`), do the ZFS-level operation, then start it. This is the [stop-before-you-receive rule](../incus/storage.md#composing-with-sanoid-and-syncoid).

## Cloning VMs

ZFS clones make "give me a throwaway copy of this VM" cheap — but go through Incus so its database and the ZFS clone stay consistent:

```bash
# ZFS-clone-backed copy (fast, space-efficient — shares blocks until diverged)
incus copy win11 win11-experiment
incus start win11-experiment
```

The pool's `zfs.clone_copy` setting controls whether `incus copy` produces a lightweight clone (default, fast) or a full independent copy — see [Incus storage → clones](../incus/storage.md#clones). Inside a cloned Linux guest, change the hostname, machine-id, and SSH host keys before putting it on the network.

## TRIM / discard end-to-end

When a guest deletes files, the freed space isn't reclaimed on the host unless TRIM propagates guest → virtio-blk → QEMU → host → ZFS. For Incus VM instances:

1. **Guest**: filesystem mounted with `discard`, or scheduled `fstrim` (Windows runs NTFS Optimize weekly).
2. **Incus/QEMU**: Incus configures virtio-blk with discard support for VM instances by default.
3. **Pool**: `autotrim=on` (set at creation on both pools) lets the underlying NVMe see the TRIM.

Verify by watching zvol space before/after a guest `fstrim`:

```bash
zfs list -t all hot/incus/virtual-machines/win11.block
incus exec win11 -- fstrim -av        # Linux guest
zfs list -t all hot/incus/virtual-machines/win11.block   # should show freed space
```

## Why VM disks on ZFS is still the whole point { #when-the-vm-corrupts-its-filesystem }

The single strongest reason to back VM disks with ZFS is unchanged by the move to Incus: when a guest filesystem corrupts itself, recovery is a snapshot rollback, not an `fsck` adventure or a restore from offline backup.

```bash
incus stop win11
incus snapshot restore win11 <snapshot>   # or, instance stopped, a raw zfs rollback of the .block zvol
incus start win11
```

The guest sees its disk exactly as it was at snapshot time. That workflow — plus per-instance `zfs send`/`receive` for off-host replication — is why this build keeps every VM's storage on ZFS, now via Incus's driver.

## GPU note

VMs on this build get **no GPU passthrough by default** — the iGPU stays with the host for ROCm. This is a virtualization decision, not a storage one, but it's why there's no VRAM/zvol interaction to worry about here. See the repo-root `START.md` and [Incus VMs](../incus/vms.md).

## Next steps

- [Incus storage](../incus/storage.md) — the authoritative page for VM/container storage on `hot/incus`.
- [Incus VMs](../incus/vms.md) / [Windows VM](../incus/windows-vm.md) — creating and running VM instances.
- [Docker Integration](docker-integration.md) — the container-side bind-mount pattern.
- [Backup & Recovery](../operations/backup.md) — replicating instance datasets off-host.
