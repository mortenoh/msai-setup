# ZFS — learning path

Don't have ZFS in your hands yet? This is the short ordered path to take
the lab from zero to "you understand the production layout". It's a
sequence of links to the rest of this section with one line per stop
telling you what to focus on.

The whole path takes ~half a day if you go through it once, less if you
skim. Every command runs against the local VirtualBox lab — nothing on
the real MS-S1 MAX yet.

## Prereqs

- A working lab VM. From the repo root:

  ```bash
  uv sync
  uv run msai lab create zfs-lab    # ~3-4 min
  uv run msai lab ssh               # opens a shell on it
  ```

  Comes up with 6 spare SATA disks on `/dev/sdb-g` — see
  [VirtualBox Lab](virtualbox-lab.md) for the setup details.

- A second terminal window for `watch -n 1 zpool status tank` etc.
  Always-visible state is half the value of working in a lab.

## Stop 1 — Mental model (15 minutes)

[`concepts.md`](concepts.md) — read it once. The vocabulary
(`vdev`, `pool`, `dataset`, `snapshot`, `ARC`, `recordsize`) is the
thing that makes every later command make sense. Don't try to memorise
property tables; you'll meet them in context.

What you should be able to answer after this: *"what's the difference
between a vdev, a pool, and a dataset?"*

## Stop 2 — First pool, by hand (30 minutes)

[`virtualbox-lab.md`](virtualbox-lab.md) sections "Lab 1 - Your first
pool" through "Lab 4 - Datasets, properties, inheritance".

You'll:

- Run `zpool create` on a single disk and look at the output.
- Add a second pool with two disks as a mirror; rip one out; watch
  `zpool status` change.
- Try `raidz1`; compute the usable capacity by hand and confirm it
  matches `zfs list`.
- Create child datasets and override properties (`compression`,
  `recordsize`, `quota`). Watch inheritance.

What you should be able to answer after this: *"what topology would I
pick on real hardware, and why?"*

## Stop 3 — Snapshots and replication (30 minutes)

`virtualbox-lab.md` sections "Lab 5 - Snapshots, clones, rollback" and
"Lab 6 - `zfs send`/`zfs receive` for replication".

You'll:

- Snapshot a dataset, change the live filesystem, diff them.
- Roll back. Clone. Promote a clone.
- `zfs send | zfs receive` between two pools on the same VM — this is
  the building block for off-site backups.

What you should be able to answer after this: *"if my main pool dies
tomorrow, what's the recovery procedure?"*

[`snapshots.md`](snapshots.md) is the deep-dive reference for the
properties and tools (bookmarks, holds, sanoid/syncoid). Skim it
after the lab.

## Stop 4 — Encryption (20 minutes)

`virtualbox-lab.md` section "Lab 7 - Native ZFS encryption".

ZFS encryption lives at the dataset level. You'll create an encrypted
dataset, write to it, unload the key, watch it become unreadable, then
load the key again. Then practice the encrypted `zfs send` form so you
can replicate to an off-site box without exposing plaintext.

[`encryption.md`](encryption.md) is the reference page; read it after
you've done the lab.

What you should be able to answer after this: *"is my off-site backup
target trusted with my data? if not, what changes?"*

## Stop 5 — Failure modes (30 minutes)

`virtualbox-lab.md` section "Lab 8 - Scrubs and bit-rot simulation".

This is the most valuable lab. You'll deliberately corrupt random
sectors on one disk of a mirror, then `zpool scrub` and watch ZFS heal
the bad block from the good copy. Then you'll do the same on a
single-disk pool and see the difference — bit rot you can't heal from
is just data loss.

What you should be able to answer after this: *"how does my pool's
topology determine which failures it survives?"*

[`troubleshooting.md`](troubleshooting.md) covers the procedures for
real failures (faulted vdev, pool import failures, etc.). Skim it now
so you know it exists — you'll come back to it the first time something
goes wrong.

## Stop 6 — Tuning (20 minutes)

[`tuning.md`](tuning.md) — focused read on the parameters that
matter (`recordsize` per workload, `compression` choice, `xattr=sa`,
`atime=off`, `dnodesize=auto`, ARC sizing).

Then run the lab exercise that recreates the production layout:
`virtualbox-lab.md` section "Lab 9 - Recreate the MS-S1 MAX layout".
Drop in [`datasets.md`](datasets.md) as the reference for which
dataset gets which property and why.

What you should be able to answer after this: *"why is my AI dataset
1M recordsize and my DB dataset 16K?"*

## Stop 7 — Operations (15 minutes)

[`operations.md`](operations.md) — day-2 stuff: scrub schedule,
trim, capacity monitoring, snapshot retention with sanoid, replication
with syncoid. You don't run these in the lab beyond a sanity test —
they make more sense once you're on real hardware with real data.

[`docker-integration.md`](docker-integration.md) covers the
bind-mount-into-ZFS pattern that the Docker pages assume. Read it once
so the Docker pages make sense.

## How to know you're done

By the end of this path you should be able to walk through the real
MS-S1 MAX storage setup without consulting the docs for the basic
shape — only for property values. A working test:

- Describe out loud the pool topology you'd run, and why.
- Describe what `recordsize` you'd pick for `ai/`, `db/`, `media/`,
  and why.
- Describe what happens when one drive in your topology dies.
- Describe how you'd back up to an off-site target.
- Describe how you'd snapshot before a risky upgrade and roll back.

If any of those answers feel vague, go back to that stop.

## When something goes sideways in the lab

The lab is throwaway. Reset patterns, in order of cheapness:

```bash
# Inside the VM — just destroy the pool(s) you broke
sudo zpool destroy tank
sudo zpool destroy hot     # if you built the two-pool mock in Lab 9

# From your Mac — revert the VM to a snapshot
VBoxManage snapshot zfs-lab restorecurrent

# Nuclear — start over
uv run msai lab destroy
uv run msai lab create zfs-lab
```

## See also

- [VirtualBox Lab](virtualbox-lab.md) - the lab exercises themselves
- [Concepts](concepts.md) - vocabulary
- [Datasets](datasets.md) - property reference
- [Snapshots](snapshots.md) - snapshots, clones, send/recv
- [Encryption](encryption.md) - native ZFS encryption
- [Tuning](tuning.md) - what to tune and why
- [Operations](operations.md) - day-2 procedures
- [Troubleshooting](troubleshooting.md) - when things go wrong
