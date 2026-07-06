# ZFS Native Encryption

OpenZFS has native, dataset-level encryption — independent of LUKS or any other layer. This page covers when to use it, how it works, and the practical gotchas (raw send/receive, key loss, performance).

## When to use ZFS native encryption

This build defaults to **no disk encryption**: the host lives behind UFW/Tailscale, the threat model is online attack, not physical theft. ZFS native encryption becomes interesting if:

- You want **off-host backups** (syncoid over Tailscale to a friend's box or a VPS) where the receiving side should hold only ciphertext.
- You hold **regulated data** (health, financial, customer PII) that needs encryption at rest as a compliance requirement.
- Specific datasets need extra protection (e.g. `tank/secrets`) while the rest of the pool stays unencrypted.

If you want **encryption of root itself**: since root is `rpool` (see [Disk Partitioning](../ubuntu/installation/disk-partitioning.md#creating-the-layout)), ZFS native encryption on the pool is now the natural default — set it at `zpool create` time and ZFSBootMenu can prompt for the passphrase at boot. LUKS+LVM is only relevant if you went with the [ext4-root alternative](../ubuntu/installation/disk-partitioning.md#canonical-layout-ext4-root-two-independent-zfs-pools) instead. Either way, native encryption doesn't cover `/boot/efi` — the EFI partition is always unencrypted, same as any LUKS+GRUB setup.

## How it works

- Encryption is **per dataset**, not per pool. You can have encrypted and unencrypted datasets in the same pool.
- Each dataset has a **wrapping key** (loaded into the kernel from a passphrase, raw key, or file) which encrypts the dataset's **data encryption keys (DEKs)** stored in the pool metadata.
- Once the key is loaded, the dataset behaves like any other — applications see plaintext.
- When the key is unloaded (`zfs unload-key`), the dataset is locked: it can't be mounted, and reads of the underlying blocks see ciphertext.
- Snapshots and clones inherit the encryption (and DEK) of the source dataset.
- Algorithms: `aes-256-gcm` (default, recommended), `aes-128-gcm`, `aes-256-ccm`, `aes-128-ccm`.

What's encrypted: all user data, file/directory names, and most metadata (timestamps, sizes, permissions are encrypted).

What's **not** encrypted: the dataset hierarchy (you can see the dataset names exist), pool topology, and some bookkeeping data. The fact that an encrypted dataset *exists* is visible; its contents are not.

## Creating encrypted datasets

You set encryption properties **at dataset create time**. They cannot be added to an existing dataset (you'd need to create a new encrypted dataset and migrate data).

### Passphrase-protected (easiest)

```bash
sudo zfs create \
    -o encryption=aes-256-gcm \
    -o keyformat=passphrase \
    -o keylocation=prompt \
    tank/secrets
```

`keylocation=prompt` (the default for passphrase) means ZFS asks for the passphrase on `zfs load-key` or `zfs mount` for that dataset. There's no caching — every mount needs the passphrase typed.

For a headless server, that's painful at boot. See "Auto-unlock at boot" below.

### Raw key file (better for automation)

Generate a 32-byte raw key:

```bash
sudo install -d -m 700 /etc/zfs/keys
sudo dd if=/dev/urandom of=/etc/zfs/keys/tank-secrets.key bs=32 count=1
sudo chmod 0400 /etc/zfs/keys/tank-secrets.key
```

Create the dataset with `keyformat=raw` and a file location:

```bash
sudo zfs create \
    -o encryption=aes-256-gcm \
    -o keyformat=raw \
    -o keylocation=file:///etc/zfs/keys/tank-secrets.key \
    tank/secrets
```

Now the dataset can be loaded non-interactively because the key is on disk. The catch: **the key file lives on the host**, so anyone who gets the host filesystem gets the key. That's still meaningful — it protects against off-host backup theft, lost/stolen drives, replaced storage — but it doesn't protect against a host compromise.

### Hex-encoded key

Same as raw but with a hex-encoded key, useful when you want to copy/paste it:

```bash
sudo zfs create \
    -o encryption=aes-256-gcm \
    -o keyformat=hex \
    -o keylocation=file:///etc/zfs/keys/tank-secrets.hex \
    tank/secrets
```

## Encrypted child datasets

You can make a parent dataset encrypted; children inherit:

```bash
# Create encrypted parent
sudo zfs create -o encryption=aes-256-gcm -o keyformat=passphrase tank/private

# Children inherit
sudo zfs create tank/private/a
sudo zfs create tank/private/b

# All three are encrypted with the same wrapping key
zfs get encryption,keyformat,encryptionroot tank/private tank/private/a tank/private/b
```

`encryptionroot` is the dataset that owns the wrapping key. Children show their parent's name there.

You can also have an unencrypted pool root and only some children encrypted — but in that case those encrypted children can't be moved/renamed across the encryption boundary trivially.

## Loading and unloading keys

```bash
# Load (mount-friendly)
sudo zfs load-key tank/secrets         # prompts (passphrase) or reads file (raw/hex)
sudo zfs mount tank/secrets

# Or in one go:
sudo zfs mount -l tank/secrets         # -l: load key first

# Unload (locks the dataset)
sudo zfs unmount tank/secrets
sudo zfs unload-key tank/secrets

# Load ALL keys at once (loads parents before children automatically)
sudo zfs load-key -a
```

`zfs unload-key` requires the dataset to be unmounted first. The unload itself purges the in-RAM key.

## Auto-unlock at boot

Three common patterns:

### Pattern 1 — key file on the boot disk (simplest)

If you accept that "the host is the security boundary, anyone with root on the host can read everything anyway", just store the key file and let systemd auto-mount:

```bash
# /etc/zfs/keys/tank-secrets.key exists with mode 0400, owned by root

# systemd unit /etc/systemd/system/zfs-load-key@.service
sudo tee /etc/systemd/system/zfs-load-key@.service > /dev/null <<'EOF'
[Unit]
Description=Load ZFS encryption key for %i
DefaultDependencies=no
Before=zfs-mount.service
After=zfs-import.target
Wants=zfs-import.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/zfs load-key %i

[Install]
WantedBy=zfs-mount.service
EOF

sudo systemctl daemon-reload
sudo systemctl enable zfs-load-key@tank-secrets.service
```

(Adjust `%i` substitution if your dataset name contains slashes — systemd escapes them as `-`.)

### Pattern 2 — Tang / Clevis (network-bound)

Bind the key to a Tang server elsewhere on your network. The host can boot and unlock the dataset *only* if the Tang server is reachable. Loses the dataset access if either the host **or** the Tang server is stolen.

Not covered in detail here; it's the same setup you'd use for LUKS Clevis bindings, applied to a key file consumed by ZFS instead of `cryptsetup`. See the Clevis docs.

### Pattern 3 — 1Password CLI or other secret manager

Pull the key from `op` at boot:

```bash
# Service file pulls the key just-in-time
ExecStart=/bin/bash -c 'op read "op://Private/tank-secrets/key" > /run/zfs-key && zfs load-key -L file:///run/zfs-key tank/secrets && shred -u /run/zfs-key'
```

Requires `op` to be authenticated non-interactively (account session token or service account). Workable but fragile.

## Raw send/receive (`-w`) — the killer feature

The thing that makes ZFS native encryption uniquely useful: **you can replicate encrypted datasets without the receiving side ever knowing the key**.

```bash
# On the source
sudo zfs snapshot tank/secrets@2026-05-17
sudo zfs send -w tank/secrets@2026-05-17 | ssh backup-host 'zfs receive backup/secrets'

# On the backup host
zfs list -r backup
sudo zfs get encryption,keyformat,encryptionroot backup/secrets
# encryption=aes-256-gcm, keyformat=passphrase, encryptionroot=backup/secrets
# but no key loaded:
sudo zfs mount backup/secrets    # error: encryption key not loaded
```

The backup host stores ciphertext only. It cannot read the data. If you later need to read it on the backup host, load the same passphrase/key there. The wrapping key travels independently of the data stream.

Incremental raw sends work the same way:

```bash
sudo zfs send -w -i tank/secrets@2026-05-17 tank/secrets@2026-05-18 | ssh backup-host 'zfs receive backup/secrets'
```

Combine with syncoid for scheduling — `syncoid --sendoptions=w …`.

## Key rotation

You can change the **wrapping key** at any time without re-encrypting data:

```bash
sudo zfs change-key tank/secrets
# Prompts for new passphrase (if keyformat=passphrase)
# Or:
sudo zfs change-key -o keyformat=raw -o keylocation=file:///etc/zfs/keys/new.key tank/secrets
```

What this does: re-encrypts the DEKs with a new wrapping key. The data itself isn't touched. This is fast — milliseconds, not "rewrite the dataset".

**Caveat**: the old wrapping key is rendered useless for live data, but **does** still decrypt any earlier raw-send snapshots that were sent before the change. So a leaked old wrapping key still compromises old backups.

To do a true cryptoshred of an old key's effect on backups, you need to also delete the old raw-send snapshots from the backup host.

## Performance

AES-256-GCM with AES-NI (Zen 5 has it) costs ~1-3% of CPU on typical workloads. Not noticeable.

On encrypted datasets, **compression happens first** (so it can actually compress) and then encryption. Compression ratios are unaffected by enabling encryption.

`zfs scrub` reads ciphertext from disk and verifies the per-block authentication tag — it doesn't need the key loaded to scrub.

## Things that go wrong

### Lost passphrase

There's no recovery. The data is unreadable. Always:

- Store passphrases in a password manager.
- For raw-key datasets, **back up the key file** (off-host, encrypted with another key you also have backed up). Losing the key file = losing the data.
- For mission-critical setups, keep an offline copy of the key on paper, in a sealed envelope, in a safe.

### You forgot you had encryption enabled

Check before assuming:

```bash
zfs get encryption,keyformat,keylocation,encryptionroot -r tank
```

A dataset with `encryption=off` was created without encryption and **cannot be retroactively encrypted** — you'd create a new encrypted dataset, `zfs send | zfs receive` data in, then destroy the original.

### `keylocation` points to a missing file

Boot stalls at "loading keys" if a systemd unit depends on a key file that isn't there. Make sure key files are local-only (`/etc/zfs/keys/...`) and exist before the import service runs.

### Receiving a raw send on a host without `encryption` feature enabled

The pool on the receiving side must have the `encryption` pool feature enabled (it is, by default, in any pool created on a recent OpenZFS). If not:

```bash
sudo zpool set feature@encryption=enabled backup
```

## Recommendation for this build

If you decide to encrypt:

1. **Encrypt only datasets that need it**, not the entire pool root. Typical: `tank/secrets`, `tank/nextcloud-data` if compliance requires it.
2. Use **`keyformat=raw` with a key file on `/etc/zfs/keys/`**, backed up in 1Password. The threat model (host stolen -> drives readable) is what this protects against.
3. Set up `zfs-load-key@…` systemd units so boot is unattended.
4. Use `zfs send -w` (or `syncoid --sendoptions=w`) for off-host replication.
5. Test the recovery path: take a raw send, send it to a different machine, load the key, mount, read. Do this once and document it in your password manager record.

If you decide *not* to encrypt:

- Make sure the threat model justifies that choice (private network, no shared physical access, no compliance pressure).
- Take care during disk disposal — `blkdiscard` and `nvme format` for SSDs, physical destruction for HDDs.
