# ZFS Concepts

This page builds the mental model. If you only have time for one ZFS doc before the install, read this one. Everything else in the section assumes you have the vocabulary and architecture clear.

## The layered model

ZFS deliberately blurs the line between volume manager and filesystem. Think of it as four layers, top to bottom:

```
+-------------------------------------------------+
|  Datasets (filesystems) and zvols (block devs)  |  <- what users and apps see
+-------------------------------------------------+
|  Object layer (DMU, ZIL, DSL)                   |  <- transactional, COW, snapshots
+-------------------------------------------------+
|  Storage pool allocator (SPA, vdev tree)        |  <- redundancy, checksums, scrub
+-------------------------------------------------+
|  Physical devices (NVMe, SSDs, partitions)      |
+-------------------------------------------------+
```

Two things that fall out of this design:

- A pool is a **single logical storage pool**, not "many drives mounted in many places". You allocate datasets from the pool freely; there are no per-disk filesystems to balance.
- Redundancy lives at the **vdev** layer, not at the dataset or filesystem level. A pool's redundancy is determined entirely by which vdev types you used when you created it.

## Terminology

| Term | Description |
|---|---|
| **Pool** (zpool) | The top-level construct. A named container of vdevs that exposes a single namespace of datasets. Example: `tank`. |
| **vdev** | A virtual device built from one or more physical devices. Examples: a single disk, a mirror, a raidz, a special vdev, a cache vdev. |
| **Top-level vdev** | A vdev that contributes capacity to the pool. The pool stripes writes across all top-level vdevs. |
| **Leaf vdev** | A physical device or partition inside a top-level vdev. |
| **Dataset** | A filesystem within a pool. Has its own properties (compression, recordsize, mountpoint). Inherits from parents. |
| **Zvol** | A block device exposed by ZFS. Backed by the pool, accessed via `/dev/zvol/<pool>/<path>`. Used for VM disks. |
| **Snapshot** | A read-only, point-in-time reference to a dataset's state at a transaction group boundary. Created in O(1). |
| **Bookmark** | A minimal marker that records "where a snapshot was" so it can be used as an incremental-send anchor after the snapshot itself is deleted. |
| **Clone** | A writable filesystem forked from a snapshot. Shares blocks with the snapshot until diverged. |
| **txg** | Transaction group. ZFS batches writes into atomic groups (~5s default), each numbered. |
| **uberblock** | The root of the on-disk pool metadata. Updated every txg. Each device keeps a rotating array of 128 uberblocks. |
| **ARC** | Adaptive Replacement Cache. ZFS's in-RAM read cache. |
| **L2ARC** | A second-level read cache on an SSD/NVMe device, populated from the ARC. |
| **ZIL** | ZFS Intent Log. The record of synchronous writes that haven't been committed to disk yet. Lives in the main pool unless... |
| **SLOG** | A dedicated device for the ZIL, typically a small, fast NVMe with PLP. Speeds up sync-heavy workloads. |
| **Scrub** | A background read of every block, verifying checksums and repairing from redundancy if available. |
| **Resilver** | Reconstruct missing data onto a replacement device (or a new device added to a mirror). |

## Vdev types

The vdev type is **immutable** for a top-level vdev. You can't turn a single-disk vdev into a mirror later (you can attach a mirror partner, which is sometimes confused with this). Choose carefully at pool creation time.

### Single-disk (stripe)

```
tank
  +-- nvme0n1
```

- One device per top-level vdev.
- **No redundancy.** A single failed device means a dead pool.
- 100% of raw capacity is usable.
- Fine when redundancy lives elsewhere (snapshots + replication, or, for laptops/single-NVMe boxes, accepting the risk).
- Multiple stripe vdevs in one pool = RAID-0 across them.

This is what the MS-S1 MAX uses, with the two unequal NVMe devices each being a top-level stripe vdev.

### Mirror

```
tank
  +-- mirror-0
        +-- disk1
        +-- disk2
```

- Two or more leaves; ZFS writes the same blocks to all leaves.
- Survives losing any (N-1) of N leaves. A 3-way mirror survives two failures.
- 50% raw efficiency for a 2-way mirror, 33% for 3-way.
- Excellent random-read performance: reads are striped across leaves.
- **Fast resilver**: only changed blocks are copied, not the whole disk.

### RAIDZ1 / RAIDZ2 / RAIDZ3

```
tank
  +-- raidz1-0
        +-- disk1
        +-- disk2
        +-- disk3
```

- Parity-based redundancy. raidz1 survives 1 failure, raidz2 survives 2, raidz3 survives 3.
- More space-efficient than mirrors at scale: 5 disks in raidz2 = ~60% efficiency, 5 disks in mirrors = 50%.
- Slower random I/O than mirrors (each logical record may span multiple disks).
- **Slow resilver**: the whole disk is reconstructed.
- raidz vdevs **cannot be expanded** in older ZFS releases. RAIDZ expansion is in OpenZFS 2.3+ but new disks are added one at a time and existing data isn't re-striped.

Rules of thumb (loose; benchmark for your workload):

- Use mirrors for VM/database workloads (random I/O, fast resilver matters).
- Use raidz2/3 for media archives (sequential, capacity matters, big disks make resilver risk high).
- Avoid raidz1 with disks ≥4 TB — resilver windows are long and a second failure during resilver kills the pool.

### dRAID (declustered RAID)

Newer in OpenZFS 2.1+. Like raidz but with reserved spare capacity distributed across all leaves, so a failed disk's data resilvers in parallel to many destinations. Designed for large pools (12+ disks). Not relevant to this build.

### Special vdev (allocation class)

```
tank
  +-- mirror-0  (HDDs, main capacity)
  +-- special mirror-1  (NVMe, metadata + small blocks)
```

- A dedicated vdev for metadata and (optionally) small blocks under a threshold.
- Massively speeds up metadata-heavy workloads (`ls -laR`, snapshot listing, scrub-completion).
- **Mandatory**: must be redundant. If a special vdev dies, the pool dies.
- Useful in mixed-tier setups (NVMe + HDD); not needed when all disks are already NVMe.

### Cache vdev (L2ARC)

```
tank
  +-- nvme0n1   (main capacity)
  +-- cache nvme1n1p1  (L2ARC on a faster device)
```

- A read cache that extends the ARC onto persistent storage. Single-device, no redundancy needed (it's a cache).
- Useful when the working set doesn't fit in RAM and the cache device is dramatically faster than the main pool.
- **Costs RAM**: every L2ARC entry needs ~70 bytes of header in ARC, so an oversized L2ARC eats the cache it's supposed to extend.
- On this build, with all NVMe, L2ARC adds little. Skip it.

### Log vdev (SLOG)

```
tank
  +-- main vdevs
  +-- log nvme0n1p2   (or a mirror of two SLOGs)
```

- Holds the ZIL on a dedicated device. Only relevant for **synchronous** writes (NFS sync exports, databases with `O_SYNC`, fsync-heavy workloads).
- Should have power-loss protection (PLP) in production — without it, a crash during a sync write can lose acknowledged writes.
- For an async-heavy workload (most home/lab use), a SLOG does nothing.

## Pool topology in one diagram

```
Pool (top-level, striped across vdevs)
+-- vdev (single, mirror, raidz, or draid) <- main data
+-- vdev (more main data; striped with the others)
+-- vdev (special, must be redundant)      <- optional, metadata/small blocks
+-- vdev (cache, no redundancy)            <- optional, L2ARC
+-- vdev (log, ideally mirrored)           <- optional, SLOG
+-- spare disk1                            <- optional, hot spares
+-- spare disk2
```

The pool's capacity is the sum of capacities of the main data vdevs. ARC, L2ARC, special, log, and spare vdevs don't add to user-visible capacity.

## Copy-on-write, in detail

Every block in ZFS lives in a tree. The pointer to a block records its physical location, length, and **checksum**.

```
                  uberblock (current txg)
                       |
                       v
                 +-----------+
                 | meta-obj  |
                 +-----+-----+
                       |
              +--------+--------+
              |        |        |
              v        v        v
          object   object   object        <- dataset filesystems / zvols
              |
        +-----+-----+
        |     |     |
        v     v     v
      data  data  data                    <- actual file/zvol blocks
```

When a block is modified:

1. ZFS allocates **new** blocks for the modified data.
2. Their parent block's pointers (with checksums) are also written to a new location, because pointers changed.
3. This propagates up to the uberblock, which is updated atomically (the uberblock array on each device is rotated).

Consequences:

- **No half-written state.** Either the new uberblock is committed and the whole txg is visible, or it isn't and the previous txg remains live. There's no `fsck` because there's no intermediate state to recover.
- **Snapshots are free.** A snapshot is just a frozen pointer at a particular uberblock. As the live filesystem diverges, the snapshot still references the old blocks (which are not freed). The snapshot grows as the filesystem changes, not as the snapshot is created.
- **Fragmentation accumulates.** Because ZFS never overwrites in place, repeatedly modifying a file fragments it. With SSDs/NVMe this rarely matters; with HDDs it does over time.

## Transaction groups (txg)

ZFS doesn't write every change immediately. It batches writes into a transaction group:

- Default `zfs_txg_timeout` is 5 seconds. Every ~5s the current txg is closed, sealed, and written to disk; a new txg opens for incoming writes.
- A txg is **atomic on disk**. Either all of it is committed or none of it is.
- The ZIL (intent log) handles the gap for synchronous writes: those get a durability acknowledgement via the ZIL while waiting for the next txg to commit.

You can see the txg-sync activity:

```bash
sudo zpool iostat -v -y 5
sudo cat /proc/spl/kstat/zfs/<pool>/txgs
```

This batching is also why ZFS performance is often described in "write throttle" terms — under pressure, ZFS slows down writers to avoid filling memory faster than disks can drain.

## End-to-end checksums and self-healing

Every block has a checksum stored in its **parent** (not in itself — important, because storing it in itself is what disk firmware does, and you can't detect a wholesale block-substitute attack that way).

On every read:

1. Read the block.
2. Compute its checksum.
3. Compare against the checksum recorded in the parent.
4. If they match -> return data.
5. If they don't and the vdev has redundancy -> read the redundant copy, return that, **and rewrite the bad copy** so it's healed.
6. If they don't and there's no redundancy -> return an I/O error to the caller, log it to `zpool status`.

A `zpool scrub` is just a full background traversal of every block, exercising this check on data that hasn't been read recently.

Algorithms available (`checksum` property):

| Algorithm | Notes |
|---|---|
| `on` / `fletcher4` | Default. Fast, decent collision resistance. |
| `sha256` | Cryptographic. Slower. Required for dedup. |
| `sha512`, `skein`, `edonr` | Stronger; modest performance cost. |
| `blake3` | Newest; fast and cryptographic. |

You almost never need to change this from the default unless you're enabling dedup (don't — see [Datasets](datasets.md)).

## ARC: the in-RAM read cache

ARC = Adaptive Replacement Cache. It's smarter than a simple LRU — it tracks both recently-used (MRU) and frequently-used (MFU) blocks, and rebalances dynamically.

- Caches **decompressed** blocks by default (`primarycache=all`). For datasets where you only want metadata cached (e.g. media archives that don't benefit from data caching), set `primarycache=metadata`.
- Default size: up to ~50% of system RAM. On a 128 GB box that's 64 GB, which is too much for a system running VMs + Ollama. **Cap it.** See [Pool Creation -> ARC](pool-creation.md#cap-the-arc-size).
- Inspect:

  ```bash
  arcstat 1            # if /usr/sbin/arcstat is installed
  cat /proc/spl/kstat/zfs/arcstats
  ```

ARC hit ratios above ~95% are healthy for typical workloads. Below ~80% suggests either undersized ARC or workloads that bypass it (large sequential reads, or `primarycache=metadata` datasets).

## ZIL and SLOG

The ZIL exists to provide **synchronous write durability** without making every write wait for the next txg commit.

- An app issues a sync write (`fsync`, `O_SYNC`, NFS sync export, DB commit).
- ZFS writes the data to the ZIL on stable storage **and** stages it for the next txg.
- The sync write is acknowledged to the caller as soon as the ZIL write completes.
- On the next txg flush, the staged data is written to its final location and the ZIL entry is no longer needed.
- On crash recovery, ZFS replays any ZIL entries whose txg never committed.

Without a SLOG, the ZIL lives **in the main pool** — sync writes go to disk twice (once to the ZIL location, once to the final location). With a SLOG, the ZIL writes go to a separate fast device and the doubled-write penalty disappears from the main pool.

For an async-heavy home/lab workload (Docker bind mounts, media, model files), a SLOG does nothing — those writes aren't synchronous. Databases and NFS sync exports are where SLOGs earn their keep.

You can also set `sync=disabled` on a dataset, which makes ZFS **ignore** sync requests and ack them immediately. Fast, but you can lose the last few seconds of writes on a crash. Useful for explicitly-disposable data (scratch space, ephemeral container state) and dangerous otherwise.

## ashift — physical block size

ashift is **set at vdev creation** and **cannot be changed**. It specifies the log2 of the smallest IO unit ZFS will use to that vdev.

| Setting | Block size | Use case |
|---|---|---|
| `ashift=9` | 512 B | Legacy 512n disks. Avoid on anything modern. |
| `ashift=12` | 4 KiB | The right default for almost everything: SSDs, NVMe, modern HDDs, 512e disks lying about their block size. |
| `ashift=13` | 8 KiB | Some NVMe drives report a preferred 8 K block. Worth checking with `nvme id-ns`. Bigger ashift = slightly less efficient for small files but matches the device. |

The MS-S1 MAX's two NVMe drives report 4 KiB blocks; `ashift=12` is correct. The pool-creation command explicitly sets it:

```bash
sudo zpool create -o ashift=12 ...
```

A pool created with ashift=9 on top of 4 KiB disks will silently work but write-amplify badly. Always set it explicitly.

## Compression

`compression=lz4` is on by default in modern OpenZFS, and you generally want it on:

- It is **CPU-light**. On Zen 5 you'll never notice it.
- It is **smart**: blocks that wouldn't compress (already-compressed data, encrypted blobs) are stored as-is, with no penalty.
- It is **usually a net throughput win** because less data needs to cross the bus.

| Algorithm | Speed | Ratio | Notes |
|---|---|---|---|
| `off` | N/A | 1.0 | Use only when data is already incompressible *and* you want to skip the test. |
| `lz4` | Very fast | Modest | Default; safe everywhere. |
| `zstd-1` to `zstd-19` | Slower with higher numbers | Better than lz4 | `zstd-3` is a reasonable backup target. |
| `gzip-1` to `gzip-9` | Old; slow at high levels | Similar to zstd | Legacy. Prefer zstd. |

Per-dataset compression for this build:

| Dataset | Compression | Reason |
|---|---|---|
| `tank/media` | `lz4` | Already-compressed files store as-is; metadata still compressed. |
| `tank/nextcloud-*` | `lz4` | Mixed content; lz4 wins most cases. |
| `tank/db` | `lz4` | Database pages are surprisingly compressible. |
| `tank/vm` | `lz4` | OS filesystems inside guests have plenty of text and zero-padding. |
| `tank/ai` | `off` | GGUF / safetensors are already heavily compressed; skip the test entirely. |
| `tank/backups` | `zstd-3` | Cold data, CPU-for-space trade is worth it. |

## What ZFS is not

A few myths that cost people time:

- **"ZFS needs ECC RAM."** It doesn't *need* ECC; it *benefits from* ECC like every other filesystem. The "ZFS will eat your data without ECC" claim is folklore. Bit-flips in non-ZFS memory hurt every filesystem equally; ZFS just makes some of them visible via checksum errors instead of silent corruption.
- **"Dedup is great."** Inline block-level dedup in ZFS requires a deduplication table (DDT) that lives in RAM. For most workloads the DDT cost dwarfs the space savings. **Don't enable dedup** unless you've measured a real benefit on your specific data.
- **"ZFS is slow."** Modern OpenZFS on SSD/NVMe is fast. Most "ZFS is slow" reports come from misconfigured ARC (capped too low or unbounded), wrong recordsize, or sync writes without a SLOG.

## Where to next

- [VirtualBox Lab](virtualbox-lab.md) — exercise the concepts on virtual disks before touching the real install.
- [Partitioning](partitioning.md) — GPT, alignment, by-id paths.
- [Pool Creation](pool-creation.md) — turn the above into a working pool.
- [Tuning](tuning.md) — ARC sizing, prefetch, txg timeouts.
