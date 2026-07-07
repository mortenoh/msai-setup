# Snapshots

A VBox snapshot freezes the entire VM state at one moment — disks, RAM (if running), settings — and lets you keep working from there. If something goes wrong, you restore the snapshot and you're back. Snapshots can branch (multiple children from the same parent), and they can be merged or pruned to keep the tree manageable.

For lab work this is the safety net. Snapshot a fresh-install state, experiment, roll back, experiment again — for free.

## How snapshots work, on disk

A snapshot doesn't copy your VM. It freezes the current disk as **read-only** and starts a new **delta file** for subsequent writes:

```
Before snapshot:
  test.vdi  <-- all reads + writes go here

After snapshot S1:
  test.vdi              (read-only base, never changes again)
  Snapshots/{S1-uuid}.vdi  (writes go here now)
```

Reads walk back: a block requested by the guest is looked up first in the delta, then in the base. Writes go to the delta. Restoring S1 just discards the delta — the base is untouched.

If you take a second snapshot S2:

```
test.vdi                       (read-only)
Snapshots/{S1-uuid}.vdi        (read-only now)
Snapshots/{S2-uuid}.vdi        (writes go here)
```

Each snapshot adds another link in the chain. Reads walk back through them all.

## Lifecycle commands

### Take

```bash
VBoxManage snapshot test take "fresh-install" --pause
VBoxManage snapshot test take "after-ansible" --description "post-apply"
```

`--pause` briefly pauses the VM during the snapshot for filesystem consistency. Without it, the snapshot is "live" — captures the running RAM state too. For most purposes pausing is the right call.

Take a snapshot while the VM is running: the snapshot includes both disk + RAM state. Restoring resumes from exactly that suspended moment.

Take while the VM is off: snapshot is just disk + config, no RAM. Restoring leaves the VM stopped.

### List

```bash
VBoxManage snapshot test list
# Name: fresh-install (UUID: ...)
#   Name: after-ansible (UUID: ...)

VBoxManage snapshot test list --machinereadable
# SnapshotName="fresh-install"
# SnapshotUUID="..."
# SnapshotName-1="after-ansible"
# ...
```

The tree is indented by level. The current state is "after the most recent snapshot in whatever branch you're on" — there's no marker in `list` output but `showvminfo` mentions it:

```bash
VBoxManage showvminfo test --machinereadable | grep 'CurrentSnapshot'
```

### Restore

```bash
# Restore the most recent
VBoxManage snapshot test restorecurrent

# Restore by name (or UUID)
VBoxManage snapshot test restore "fresh-install"
```

Restoring discards everything after the snapshot — both the delta files (data the guest wrote) and any newer snapshots on the same branch.

**The VM must be stopped to restore.** If running, `poweroff` first.

After restoring, the VM is in the state from that snapshot. Start it with `VBoxManage startvm`.

### Delete (merge)

Deleting a snapshot doesn't discard its data — it **merges** the snapshot's delta back into its parent:

```bash
VBoxManage snapshot test delete "fresh-install"
# Merging differencing image... (can be slow on large disks)
```

The data in the snapshot's delta becomes part of the parent. The snapshot itself is gone.

Useful for pruning long chains. Don't delete the snapshot you currently *are* — that's the active branch.

### Edit

```bash
VBoxManage snapshot test edit "fresh-install" \
    --name "fresh-install-v2" \
    --description "regenerated after bug fix"
```

Renaming a snapshot is purely metadata.

## Branching

Snapshots can branch: restore an old snapshot, take a new one, and you have two siblings:

```
fresh-install
├── after-ansible-v1   (older branch)
└── after-ansible-v2   (newer branch — current)
```

Useful for "try one thing, roll back, try another, compare". To switch branches, restore the snapshot at the branch point and proceed from there.

VBox preserves all branches until you delete them.

## Snapshot-and-RAM ("online snapshot")

If the VM is running when you snapshot, VirtualBox saves the RAM state too. Restoring resumes the VM at exactly the moment of the snapshot — like a hibernate-and-wake but to any past hibernation.

```bash
VBoxManage snapshot test take "pre-experiment" --pause     # the VM is briefly paused; RAM captured
# ...experiment...
VBoxManage controlvm test poweroff
VBoxManage snapshot test restorecurrent
VBoxManage startvm test --type headless                    # resumes from RAM state
```

The snapshot file is bigger (RAM is dumped to disk) — for an 8 GiB VM, expect ~6-8 GiB extra per online snapshot.

For most lab work, **VM-off snapshots are enough**: power-off, snapshot, restart, experiment.

## Snapshots and storage

Each snapshot creates one delta `.vdi` per disk attached to the VM. With 7 disks (the lab's primary + 6 lab disks):

```
test/Snapshots/{snap-uuid}/test-primary.vdi
test/Snapshots/{snap-uuid}/test-lab-01.vdi
test/Snapshots/{snap-uuid}/test-lab-02.vdi
...
```

The deltas start tiny (just metadata) and grow as the guest writes. Even with empty deltas, having many snapshots means many open files — VirtualBox handles this fine, but be aware if you accumulate dozens of snapshots.

## When the chain gets long

Each snapshot adds a read-walk layer. Reads to blocks in the base disk traverse the whole chain.

| Chain length | Read overhead |
|---|---|
| 1-3 snapshots | Imperceptible |
| 10+ | Noticeable on random I/O |
| 50+ | Painful |

For long-running VMs that accumulate snapshots: periodically `snapshot delete` the older ones to merge them back. Or take a fresh full-clone:

```bash
# Make a full standalone clone without snapshot ancestry
VBoxManage clonevm test --name test-clean --register \
    --options keepallmacs,keepnatmacs,keepdisknames \
    --mode all
```

(`clonevm` is a separate subcommand; see `VBoxManage clonevm --help`.)

## Patterns this build uses

### "Take a snapshot before any risky experiment"

```bash
VBoxManage snapshot test take "before-zfs-mirror" --pause
msai lab apply zfs -e topology=mirror
# experiments...

# If it goes wrong:
VBoxManage controlvm test poweroff
VBoxManage snapshot test restore "before-zfs-mirror"
VBoxManage startvm test --type headless
```

The `msai lab snapshot <name>` and `msai lab restore <name>` commands wrap exactly this.

### "Fresh-install snapshot as the baseline"

After `msai lab create test` completes:

```bash
msai lab snapshot fresh-install
```

Now every experiment can restore back to "fresh Ubuntu, lab key authorised, sudoers set, that's it". The expensive part (the Ubuntu install — ~3.5 min) is captured; subsequent resets are seconds.

### Branching by feature

```bash
msai lab snapshot fresh-install            # baseline

# Try the stripe topology
msai lab apply zfs                          # topology=stripe (default)
msai lab snapshot zfs-stripe

# Roll back, try mirror
msai lab restore fresh-install
msai lab apply zfs -e topology=mirror
msai lab snapshot zfs-mirror

# Now you can flip between zfs-stripe and zfs-mirror at will
```

## Snapshots aren't backups

A snapshot lives in the same `.vbox` directory as the VM. If the host disk dies, both go together. For real backups:

- Export the VM: `VBoxManage export test --output test.ova`
- Or rsync the entire VM directory to another host
- For data inside the VM, use whatever the guest's own backup mechanism is (ZFS send, restic, etc.)

Snapshots are operational rollback, not disaster recovery.

## See also

- [VMs](vms.md) — VM lifecycle commands
- [Storage](storage.md) — disk + delta-file semantics
- [VBoxManage CLI](vboxmanage.md) — full snapshot subcommand reference
