# Troubleshooting

Common failures on this build, grouped by area. For happy-path setup see the topic pages; this is the "it's broken" page.

## First moves for any problem

```bash
# Is the daemon up?
systemctl status incus.service incus.socket
sudo journalctl -u incus --since '10 min ago'

# What does Incus think is going on?
incus list
incus info <instance>
incus config show <instance>          # effective config, incl. inherited profiles
incus monitor --type=logging          # live daemon event stream (Ctrl-c to stop)
```

`incus info <instance>` and the daemon journal catch most things — a device that failed to attach, an OOM kill, a storage error all surface here.

## Nesting / Docker-in-Incus

### Docker won't start inside a container

```bash
incus config get <c> security.nesting           # must be "true"
incus config set <c> security.nesting true       # if not
incus restart <c>
incus exec <c> -- systemctl status docker
incus exec <c> -- dockerd --debug                # foreground, read the error
```

If nesting is on and Docker still won't start, it's usually the **storage driver**.

### Docker storage-driver errors on ZFS

Symptom: Docker starts but images/containers fail with overlay or ZFS errors inside the container.

```bash
incus exec <c> -- docker info | grep -i 'storage driver'
```

Fixes, in order of preference:

```bash
# 1. Give /var/lib/docker its own dataset/volume so Docker isn't on the idmapped root
incus storage volume create default <c>-docker
incus config device add <c> docker-data disk pool=default source=<c>-docker path=/var/lib/docker
incus restart <c>

# 2. Or force a driver that behaves nested — inside the container:
#    /etc/docker/daemon.json -> {"storage-driver": "fuse-overlayfs"}   (needs fuse-overlayfs pkg)
#    or "vfs" (slow, always works) as a last resort
```

The full compose-migration guidance (including the recommended driver for this build) is in [Docker in Incus](docker-in-incus.md). See also [Containers](containers.md#nesting-running-docker-inside-a-container).

### Do NOT reach for `security.privileged`

If Docker-in-container only works with `security.privileged=true`, that's a signal something else is misconfigured (usually storage or a missing device), not a reason to run privileged. Privileged containers drop the UID/GID isolation that protects the host. Fix the underlying issue; keep the container unprivileged.

## GPU / ROCm devices

### `/dev/dri` present but `/dev/kfd` missing

The single most common GPU failure — you added the `gpu` device but not the `unix-char` device for `/dev/kfd`.

```bash
incus exec <c> -- ls -l /dev/kfd /dev/dri/       # kfd missing?
incus config device show <c> | grep -E 'kfd|unix-char'
# Fix:
incus config device add <c> dev_kfd unix-char source=/dev/kfd path=/dev/kfd gid=<render-gid>
incus restart <c>
incus exec <c> -- rocminfo | grep gfx1151
```

### Devices present but "permission denied" from ROCm

GID mismatch — the device's group inside the container isn't a group the process is in.

```bash
incus exec <c> -- stat -c '%g %n' /dev/kfd /dev/dri/renderD128   # GID on the nodes
incus exec <c> -- id <user>                                       # user's groups
getent group render                                              # host render GID

# Fix: recreate render/video at the host's GIDs inside the container, add the user
incus exec <c> -- groupadd -g <render-gid> render 2>/dev/null || true
incus exec <c> -- usermod -aG render,video <user>
incus restart <c>
```

### `rocminfo`: "ROCk module is NOT loaded"

Container can't reach the kernel driver. Check `/dev/kfd` is present (above) and that the **host** actually has amdgpu loaded:

```bash
lsmod | grep amdgpu                              # on the HOST
rocminfo | grep gfx1151                          # on the HOST — must work first
```

A container can only use a GPU the host already drives. If the host is broken, fix [ROCm installation](../ai/gpu/rocm-installation.md) first.

### Works privileged, fails unprivileged

Confirms a GID-mapping problem. Use privileged **only as a diagnostic**, then revert and fix the GID matching (above):

```bash
incus config set <c> security.privileged true && incus restart <c>   # test
incus exec <c> -- rocminfo | grep gfx1151
incus config set <c> security.privileged false && incus restart <c>  # revert — do not leave it on
```

Full GPU walkthrough: [GPU passthrough](gpu-passthrough.md).

## Storage / ZFS pool

### Instance won't start: storage error

```bash
incus info <instance> --show-log
sudo journalctl -u incus --since '5 min ago' | grep -i zfs

# Does the pool still resolve to rpool/incus?
incus storage show default
zfs list -r rpool/incus
zpool status rpool                               # pool healthy / imported?
```

If `rpool` isn't imported, nothing under `rpool/incus` works — import it (`sudo zpool import rpool`) before touching Incus.

### Incus database desynced from ZFS

Symptom: `incus list` shows an instance but its dataset is gone (or vice versa) — usually after someone ran raw `zfs destroy`/`rename` under `rpool/incus`.

```bash
zfs list -r rpool/incus                          # what's actually there
incus list                                       # what Incus believes
```

Prevention is the rule from [Storage](storage.md): **never** manually restructure datasets under `rpool/incus`. Recovery depends on the specifics — restore the dataset from a sanoid snapshot or syncoid replica if it was deleted, or `incus delete --force` the orphaned instance record if the data is truly gone. Don't hand-edit Incus's database.

### Out of space

```bash
incus storage info default
zfs list -o name,used,avail,refer rpool/incus
zpool list rpool
# Prune old snapshots (sanoid autoprune handles scheduled ones; check manual/Incus ones)
zfs list -t snapshot -r rpool/incus -s used | tail
```

Remember `rpool` also holds root, `rpool/ai` models, and `rpool/db` — Incus shares the pool. See [capacity planning](../operations/capacity-planning.md).

## Networking / UFW

### Instance has no internet

```bash
sysctl net.ipv4.conf.all.forwarding              # must be 1
incus network get incusbr0 ipv4.nat              # must be true
incus exec <c> -- ping -c2 1.1.1.1
incus exec <c> -- getent hosts example.com       # DNS working?
```

Most often it's IP forwarding off or UFW dropping forwarded traffic:

```bash
# Enable forwarding
echo "net.ipv4.conf.all.forwarding=1" | sudo tee /etc/sysctl.d/99-incus-forwarding.conf
sudo systemctl restart systemd-sysctl

# Allow the bridge through UFW's FORWARD chain
sudo ufw route allow in on incusbr0
sudo ufw route allow out on incusbr0
sudo ufw allow in on incusbr0
sudo ufw reload
```

### Traffic blocked despite Incus "working"

UFW's `DEFAULT_FORWARD_POLICY="DROP"` blocks bridge forwarding. The `ufw route allow` rules above are the fix. Confirm the two firewalls aren't both managing the bridge:

```bash
grep DEFAULT_FORWARD_POLICY /etc/default/ufw
incus network get incusbr0 ipv4.firewall         # should be "false" on this build
sudo nft list ruleset | grep -i incus            # Incus shouldn't be adding filter rules for incusbr0
```

### Published port unreachable

```bash
incus config device show <c> | grep -A5 proxy    # is bind=host set?
sudo ss -tlnp | grep <port>                       # is the host listening?
sudo ufw status | grep <port>                     # is UFW allowing it?
```

Proxy devices must be `bind=host` for UFW to govern them (see [Networking](networking.md)).

### `incusbr0` gone after reboot

It's Incus-managed, not Netplan — don't declare it in Netplan.

```bash
incus network list                               # is it there?
sudo systemctl restart incus
incus network show incusbr0
```

## VMs

### VM won't start / "QEMU not found"

```bash
dpkg -l | grep qemu-system                        # install qemu-system-x86 if missing
sudo apt install qemu-system-x86 qemu-utils
incus info <vm> --show-log
```

### Windows 11 installer: "This PC can't run Windows 11"

TPM or Secure Boot missing.

```bash
incus config device show <vm> | grep -A2 tpm      # vtpm device present?
incus config get <vm> security.secureboot          # should be true
# VM must be stopped to add a TPM (not hotpluggable for VMs)
incus stop <vm>
incus config device add <vm> vtpm tpm
incus start <vm>
```

### Windows install shows no disk

The virtio disk driver isn't loaded during setup. Attach the virtio-win ISO and **Load driver → viostor** at the disk-selection screen. Full flow: [Windows VM](windows-vm.md).

### Can't reach a VM (no `incus exec`)

VMs have no `incus exec` unless the guest runs incus-agent. Use `incus console <vm>` (serial) or `incus console <vm> --type=vga` (graphical), then SSH/RDP once networking is up.

## Daemon / permissions

### "Permission denied" running `incus`

Not in `incus-admin`:

```bash
groups                                            # incus-admin listed?
sudo usermod -aG incus-admin "$USER"
newgrp incus-admin                                # or log out/in
```

### Daemon won't start

```bash
sudo journalctl -u incus -n 100 --no-pager
sudo systemctl restart incus
incus admin sql global 'SELECT 1'                 # DB reachable? (advanced)
```

## When to escalate

If an instance is stuck and normal commands hang:

```bash
incus stop <instance> --force
incus monitor --type=logging                       # watch what the daemon is doing
sudo systemctl restart incus                        # last resort — restarts the daemon, not instances
```

Restarting the `incus` daemon does **not** stop running instances (they keep running), so it's safe as a management-plane reset.

## Cross-references

- [Containers](containers.md) — nesting setup.
- [GPU passthrough](gpu-passthrough.md) — the full device story.
- [Storage](storage.md) — dataset rules (what not to do to `rpool/incus`).
- [Networking](networking.md) — the UFW/bridge integration.
- [ROCm installation](../ai/gpu/rocm-installation.md) — host-side GPU stack.
- [ZFS troubleshooting](../zfs/troubleshooting.md) — pool-level problems.
