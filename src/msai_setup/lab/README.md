# Local Lab — learn it before you build it

This is a hands-on walkthrough for someone who hasn't run ZFS or done SSH hardening before. Each section is `do this -> see this -> here's why -> read more`. By the end you'll have a working lab VM with ZFS, hardened SSH, and Docker, and you'll know enough to make decisions about the real MS-S1 MAX setup.

The lab runs locally on your Mac (Apple Silicon or Intel) or any Linux box with VirtualBox. Everything is throwaway — break it, blow it away, start over.

---

## 0. One-time setup

### What you need on the host

| Tool | Why |
|---|---|
| [VirtualBox 7.2+](https://www.virtualbox.org/) | the VM itself; `brew install --cask virtualbox` |
| [xorriso](https://www.gnu.org/software/xorriso/) | build cloud-init ISO + remaster install ISO; `brew install xorriso` |
| [uv](https://docs.astral.sh/uv/) | run the Python tooling; `brew install uv` |
| [ansible](https://docs.ansible.com/) | configure the VM (Section 4+); `brew install ansible` |

### Get the repo

```bash
git clone https://github.com/mortenoh/msai-setup.git
cd msai-setup
uv sync                                                                # installs `msai` CLI
ansible-galaxy collection install -r src/msai_setup/lab/ansible/requirements.yml
```

Everything that follows assumes you're in the `msai-setup/` directory.

---

## 1. Create your first lab VM (3-4 min)

```bash
msai create test
```

That command:

- Downloads the Ubuntu 26.04 LTS ARM/x86 server ISO and verifies its SHA256 (cached after first run — re-runs are fast)
- Remasters the ISO to add `autoinstall` to GRUB's kernel cmdline (so Subiquity skips its language/keyboard/storage menus)
- Generates a dedicated SSH keypair at `target/lab_id_ed25519` (separate from your real keys; throwaway with the lab)
- Builds a small "CIDATA" cloud-init ISO with your hostname/user/sudo/SSH-key config
- Creates a VirtualBox VM with **6 extra blank disks** (for ZFS), boots it headless, and waits until you can SSH in as the lab user

When it's done:

```bash
msai list
#  Name | State | Disks | VBox VM
#  test |  ok   |  ok   | running

msai ssh                              # drop into the VM
morten@test:~$ uname -m && lsb_release -d
aarch64
Description:    Ubuntu 26.04 LTS
```

**You now have a fully-installed Ubuntu 26.04 with SSH key auth.** Everything from here happens inside the VM.

> **Tip — multiple instances**: `msai create lab2` creates a second one and switches the "current" pointer to it. `msai use test` switches back. `msai list` shows which is current (the `*`).

---

## 2. ZFS — the 15-minute introduction

You don't need a textbook. You need to understand four things and then run the commands.

### What ZFS is, in two sentences

ZFS is a filesystem **and** a volume manager combined. Instead of "this partition has ext4 and this other one has xfs", you give ZFS a bunch of disks (or partitions) and it gives you a single **pool** that you can carve into named **datasets** with per-dataset settings.

### The four things to know

1. **Copy-on-write.** ZFS never overwrites a block. Edits write new blocks and update pointers. That's what makes **snapshots instant and free**: a snapshot is just "remember where the pointers were at this moment".
2. **Checksums on everything.** Every block has a SHA-256-ish checksum stored in its parent. If a disk returns a flipped bit, ZFS detects it; if you have redundancy, it self-heals.
3. **Datasets are mountpoints with policies.** `tank/media` and `tank/db` can have different compression, different block sizes, different snapshot retention — even though they're in the same pool.
4. **ARC** is ZFS's in-RAM read cache. Defaults to ~50% of system RAM. On the real MS-S1 MAX with 128 GB, **you cap this** so it doesn't fight your VMs and Ollama. We'll set that in a minute.

For deeper background once you're curious: [docs/zfs/concepts.md](../../../docs/zfs/concepts.md).

### Try it — pool, dataset, snapshot

SSH in (`msai ssh`) and run:

```bash
# Confirm our lab disks are there. We should see sda (root) + sdb..sdg (six 8GB lab disks).
lsblk -o NAME,SIZE,TYPE | head -20

# Install ZFS userland
sudo apt update && sudo apt install -y zfsutils-linux

# Create a pool named `tank` from the first lab disk (single-disk, no redundancy)
sudo zpool create -o ashift=12 -O compression=lz4 -O atime=off \
    tank /dev/sdb

# Look at it
zpool status tank
zfs list
df -h /tank
```

What just happened:

- `ashift=12` tells ZFS the disk uses 4 KiB physical blocks (right answer for any modern disk).
- `compression=lz4` is on by default in new ZFS but explicit is good; lz4 is fast enough that it's usually a net **win** even on uncompressible data.
- `atime=off` tells ZFS not to update access timestamps on reads (turns reads into writes when on — saves a ton of I/O).

Now create some datasets with different settings:

```bash
# Big sequential reads (media): big record size, default compression
sudo zfs create -o recordsize=1M tank/media

# Database-ish workload: small record size matches typical DB page size
sudo zfs create -o recordsize=16K tank/db

# See them
zfs list -o name,used,available,recordsize,compression,mountpoint
```

Each dataset shows up as a mountpoint automatically (`/tank/media`, `/tank/db`).

### Try it — snapshot, change, rollback

```bash
echo "v1" | sudo tee /tank/media/important.txt

# Snapshot the whole pool, recursively, with today's date
sudo zfs snapshot -r tank@day1

# Change the file
echo "v2 (oops, broke something)" | sudo tee /tank/media/important.txt
cat /tank/media/important.txt

# Browse the snapshot — it's a hidden directory at the dataset root
ls /tank/media/.zfs/snapshot/day1/
cat /tank/media/.zfs/snapshot/day1/important.txt

# Roll back the entire dataset to that snapshot
sudo zfs rollback tank/media@day1
cat /tank/media/important.txt           # back to v1
```

Snapshots cost nothing initially — they just freeze the pointer set. As the live filesystem diverges, the snapshot "holds onto" the blocks the live filesystem no longer uses. You see this as the snapshot's `USED` column growing.

```bash
zfs list -t snapshot
```

### Try it — simulate disk failure, replace it

Single-disk pools have no redundancy. Try a mirror:

```bash
sudo zpool destroy tank
sudo zpool create -o ashift=12 -O compression=lz4 -O atime=off \
    tank mirror /dev/sdb /dev/sdc

zpool status tank
# config:
#   tank
#     mirror-0
#       sdb
#       sdc

# Write something
sudo dd if=/dev/urandom of=/tank/big.bin bs=1M count=100

# Now "lose" sdb. From the *host* (outside the VM), in another terminal:
#   VBoxManage storageattach test --storagectl SATA --port 1 --device 0 --medium none
# Back in the VM:
sudo zpool status tank
# state: DEGRADED, sdb is missing

# Reads still work — ZFS serves from sdc.
sudo md5sum /tank/big.bin

# Re-attach the disk (from the host):
#   VBoxManage storageattach test --storagectl SATA --port 1 --device 0 --medium target/test-lab-01.vdi
# Back in the VM:
sudo zpool online tank /dev/sdb
sudo zpool status tank
# 'resilvering' — ZFS is copying the changed blocks back. When done: ONLINE.
```

You've now seen the whole "snapshot, divergence, rollback, replace a disk" cycle. The real MS-S1 MAX setup is the same commands at larger scale.

### Cap ARC (production-relevant)

On a 128 GB MS-S1 MAX with VMs + Ollama, leaving ARC at the default 64 GB causes real fights. Cap it:

```bash
echo 'options zfs zfs_arc_max=17179869184' | sudo tee /etc/modprobe.d/zfs.conf   # 16 GiB
sudo update-initramfs -u
# Takes effect next boot. To apply live:
echo 17179869184 | sudo tee /sys/module/zfs/parameters/zfs_arc_max
```

### Deeper reading (when you want it)

- [docs/zfs/concepts.md](../../../docs/zfs/concepts.md) — full mental model: vdev types, COW in detail, ARC, ZIL, ashift
- [docs/zfs/pool-creation.md](../../../docs/zfs/pool-creation.md) — every `zpool create` flag explained
- [docs/zfs/datasets.md](../../../docs/zfs/datasets.md) — full property reference (compression, recordsize, quotas, sync modes)
- [docs/zfs/snapshots.md](../../../docs/zfs/snapshots.md) — bookmarks, clones, send/receive, sanoid/syncoid
- [docs/zfs/troubleshooting.md](../../../docs/zfs/troubleshooting.md) — when things go wrong

---

## 3. SSH hardening — what actually matters

The default Ubuntu sshd config is fine for a private network. For an internet-exposed box (which the MS-S1 MAX shouldn't be, but might be via Tailscale Funnel etc.), there are four real things to do:

1. **Disable password auth.** Force key-only. The lab VM already does this (cloud-init set `allow-pw: false`).
2. **Disable root login over SSH.** Force `PermitRootLogin no`.
3. **Use modern key/cipher/MAC algorithms.** Older ssh-rsa-with-SHA1 and CBC ciphers are deprecated.
4. **Limit attack surface.** Disable agent/X11/TCP forwarding unless you use them. Cap MaxAuthTries.

There are dozens of other knobs (port-knocking, fail2ban, geographic IP restrictions) — they're tertiary. Get the four above right and you're 95% of the way.

### Try it — apply the hardening playbook

The `ssh-hardening.yml` Ansible playbook in this repo does exactly this. Let me show you what it changes by running it in `--check` mode (no actual changes):

```bash
# From the msai-setup repo (host, not the VM)
msai lab apply ssh-hardening --check --diff
```

You'll see a diff showing what would be added to `/etc/ssh/sshd_config.d/00-hardening.conf`. The important lines:

```
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowAgentForwarding no
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,...
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,...
MACs hmac-sha2-512-etm@openssh.com,...
PubkeyAcceptedAlgorithms ssh-ed25519,...,rsa-sha2-512,rsa-sha2-256
```

Apply for real:

```bash
msai lab apply ssh-hardening
```

Now log in again — you'll still get in (key auth works) but root login over SSH is blocked, and anyone trying password auth gets refused immediately. Verify:

```bash
msai ssh
morten@test:~$ sudo sshd -T | grep -iE 'permitroot|password|pubkey'
```

> **Deeper reading**:
> - [docs/ssh/server/hardening.md](../../../docs/ssh/server/hardening.md) — every directive explained
> - [docs/ubuntu/security/ssh-hardening.md](../../../docs/ubuntu/security/ssh-hardening.md) — Ubuntu-flavoured, includes fail2ban and journald monitoring

### The other safety net — UFW (firewall)

The Ansible `ufw` playbook sets the default to "deny all incoming except SSH". One command:

```bash
msai lab apply ufw
```

After this, the VM accepts only port 22 (SSH) inbound. Verify:

```bash
msai ssh
morten@test:~$ sudo ufw status verbose
```

For the real MS-S1 MAX, you'd add rules for whatever else you expose (80/443 for the reverse proxy, etc.). See [docs/networking/ufw/](../../../docs/networking/ufw/) for details.

---

## 4. Docker vs LXC — the decision

This comes up because Linux has two distinct "container" worlds:

| | **Docker** | **LXC / LXD** |
|---|---|---|
| **Mental model** | "Run this app" | "Run this OS userspace" |
| **Per container** | One process tree, usually one main process | Full Ubuntu (or whatever) install with systemd |
| **Data** | Bind mounts or named volumes | LVM/ZFS-backed root filesystem |
| **Ecosystem** | Massive — Nextcloud, Jellyfin, Authentik, *arr stack, all distributed as Docker images on Docker Hub | Smaller — you mostly run your own apps |
| **Orchestration** | `docker compose` (or Kubernetes for big setups) | `lxc` CLI, individual containers feel like SSH'ing into a VM |
| **Resource overhead** | Tiny (shared kernel + minimal userspace per container) | Small (shared kernel + full userspace per container) |
| **Updates** | `docker compose pull && up -d` per service | `apt upgrade` inside each container |

### Honest recommendation for this build

**Docker is the right default.** Every service the MS-S1 MAX docs talk about (Nextcloud, Jellyfin, Plex, Pi-hole, Traefik, Authentik, the *arr stack, Ollama, Open WebUI) is distributed as a Docker image with a maintained Compose file. LXC would mean you install each of those by hand inside a "real Ubuntu" container — much more work, no benefit.

**LXC makes sense when you specifically want:**
- A long-lived "build machine" or "scratch playground" you can SSH into like a VM
- A service that doesn't fit the Docker single-process model (e.g. a multi-process appliance you want to manage with systemd inside)
- Something requiring privileged kernel access that Docker would refuse (custom storage drivers, certain VPN clients)

For services in this build: **Docker for the services + a couple of LXC containers if you find a specific need**.

### Try it — Docker in the lab VM

The `docker.yml` Ansible playbook installs Docker CE properly on Ubuntu 26.04:

```bash
msai lab apply docker
```

What it does:
- Adds Docker's GPG-signed apt repo (with auto-fallback to `noble` if the `resolute` repo isn't published yet)
- Installs `docker-ce`, `docker-cli`, `containerd`, `docker-compose-plugin`, `docker-buildx-plugin`
- Adds your lab user to the `docker` group (no `sudo docker` needed)
- Writes a sane `/etc/docker/daemon.json` (overlay2 storage driver, JSON log rotation)
- Runs `docker run hello-world` to confirm

Try it:

```bash
msai ssh
morten@test:~$ docker run --rm -p 8080:80 traefik/whoami
# (in another terminal)
$ curl http://127.0.0.1:8080  # nothing — port forward isn't set up

# What we'd do for real: bring up the whole stack via compose
# The lab's services.yml playbook deploys Traefik + whoami as a smoke test
exit
msai lab apply services
msai ssh
morten@test:~$ curl http://127.0.0.1/whoami
# Hostname: ...
# IP: ...
```

You've now seen the lab's full path: provision a VM → ZFS → SSH hardening → UFW → Docker → a real Compose stack with the bind-mount-into-ZFS pattern.

> **`msai lab apply` vs `msai lab all`**: bare `msai lab apply` (no playbook args) runs only the conservative subset — `bootstrap`, `ssh-hardening`, `ufw`. That's deliberate: those touch nothing destructive. The heavier `zfs`, `docker`, and `services` playbooks are run explicitly, one at a time, as shown above. The one exception is `msai lab all`: because "all" means all, it intentionally runs the **full** pipeline (`bootstrap`, `ssh-hardening`, `ufw`, `zfs`, `docker`, `services`) end-to-end after provisioning. Narrow it with `--playbooks` if you want a subset.

### Try LXC (just to know what it looks like)

LXD is in Ubuntu's snap. In the VM:

```bash
sudo snap install lxd
sudo lxd init --auto                         # picks defaults
sudo lxc launch ubuntu:26.04 my-lxc-container
sudo lxc list
sudo lxc exec my-lxc-container -- bash       # SSH-like shell into the container
```

Compare the vibes: that container feels like a real machine with its own apt/systemd. That's what LXC gives you. For most homelab services, you don't need that — but knowing what it looks like helps you recognise when you do.

---

## 5. Snapshot, reset, iterate

This is the whole point of the lab — make experimentation cheap.

```bash
# Take a snapshot after a known-good run
msai lab snapshot fresh-install

# Now go break things
msai ssh
morten@test:~$ sudo rm -rf /etc/ssh    # please don't do this
exit

# Roll back
msai lab restore fresh-install

# VM is back to the snapshot state, SSH works again
msai ssh
```

VM-level snapshots cover everything (OS + ZFS state + Docker state). For finer-grained "undo", use ZFS snapshots **inside** the VM (`zfs rollback tank/foo@before-change`).

---

## 6. When you're done

```bash
msai lab destroy             # asks confirmation, removes VM + disks
# Cached files kept (ISO, autoinstall ISO, SSH keypair) for the next msai create
```

Or wipe everything including caches:

```bash
msai lab destroy
rm -rf target/
```

---

## 7. From lab to real MS-S1 MAX

The Ansible playbooks here are **the same playbooks you'd run on the real MS-S1 MAX**. Only the inventory changes:

```yaml
# ~/msai-prod-inventory.yml
all:
  children:
    production:
      hosts:
        ms-s1-max:
          ansible_host: 192.168.1.10           # or ms-s1-max.<tailnet>.ts.net
          ansible_user: morten
          ansible_become: true
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

```bash
cd src/msai_setup/lab/ansible
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/bootstrap.yml -l production
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/ssh-hardening.yml -l production
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/zfs.yml -l production
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/docker.yml -l production
# etc
```

That's the whole point of the lab: rehearse those playbooks against a sacrificial VM before they touch your homelab.

---

## What's next once you're comfortable

- Read [docs/zfs/](../../../docs/zfs/) end to end (it's 4000+ lines, but you can pick by section)
- Read [docs/ansible/](../../../docs/ansible/) if you want to extend the playbooks (15 pages, conceptually thorough)
- Look at the real production hardware decisions in [docs/getting-started/](../../../docs/getting-started/)
- Plan the actual reinstall using [docs/operations/rebuild-checklist.md](../../../docs/operations/rebuild-checklist.md)

You don't need to read all of that. Use them as references when you hit a question.
