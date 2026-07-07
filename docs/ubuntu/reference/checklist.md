# Complete Hardening Checklist

Comprehensive checklist for hardening Ubuntu Server 26.04 LTS. Use this as a verification guide after installation.

## Pre-Installation

- [ ] Hardware requirements verified
- [ ] ISO downloaded from official source
- [ ] ISO checksum verified
- [ ] ISO GPG signature verified
- [ ] Boot media created and tested
- [ ] Disk partitioning plan determined (ext4 root on the 4 TB primary NVMe, plus `hot` on its leftover space and `tank` on the 2 TB secondary — see [Disk Partitioning](../installation/disk-partitioning.md))
- [ ] Network configuration planned

## BIOS/UEFI Settings

- [ ] UEFI mode enabled (not Legacy)
- [ ] Secure Boot disabled (this build's default — DKMS amdgpu/ROCm/ZFS modules make MOK enrollment its own chore; see `START.md`)
- [ ] TPM enabled (if available)
- [ ] Boot password set
- [ ] Setup/BIOS password set
- [ ] USB boot enabled temporarily for install
- [ ] Virtualization (VT-x/AMD-V) enabled if needed

## Installation

This build uses **plain ext4 root + GRUB, no LUKS, no LVM** via Ubuntu's guided installer (Subiquity) — see the [installation walkthrough](../installation/installation-walkthrough.md). The data lives on two independent ZFS pools, created post-install, one per drive:

- [ ] Guided ext4 install followed (Custom storage layout, not entire-disk)
- [ ] Primary 4 TB NVMe (slot 1, fast x4): EFI + `/boot` + ext4 `/`, leftover reserved for the `hot` pool member
  - [ ] /boot/efi (512 MB, FAT32), /boot (1 GB, ext4), / (500 GB, ext4)
  - [ ] `hot` created post-install with `incus` (`mountpoint=none`), `db`, `ai`
- [ ] Secondary 2 TB NVMe (slot 2, slow x1): entire disk as the separate `tank` pool (`media`, `nextcloud-data`, `nextcloud-app`, `backups`)
- [ ] GRUB installed to the primary disk (`grub-install /dev/nvme0n1`) and boots to login
- [ ] SSH server installed
- [ ] SSH keys imported

## Post-Installation - Immediate

- [ ] System updated: `sudo apt update && sudo apt upgrade`
- [ ] Timezone configured: `timedatectl set-timezone`
- [ ] Hostname configured properly
- [ ] Time synchronization verified
- [ ] SSH access verified from remote

## User Management

- [ ] Root direct login disabled
- [ ] Admin user created with sudo access
- [ ] SSH keys deployed for admin user
- [ ] Unique user accounts for each admin
- [ ] No shared accounts
- [ ] Unused default accounts removed
- [ ] Home directory permissions set to 700
- [ ] Password aging configured:
  - [ ] PASS_MAX_DAYS set
  - [ ] PASS_MIN_DAYS set
  - [ ] PASS_WARN_AGE set

## sudo Configuration

- [ ] NOPASSWD avoided (or documented exception)
- [ ] sudo group membership reviewed
- [ ] Custom rules in /etc/sudoers.d/
- [ ] Timeout configured (timestamp_timeout)
- [ ] Logging enabled

## PAM Configuration

- [ ] pam_pwquality installed and configured:
  - [ ] Minimum length 14+ characters
  - [ ] Complexity requirements set
  - [ ] Dictionary check enabled
- [ ] pam_faillock configured:
  - [ ] deny = 5
  - [ ] unlock_time = 600
- [ ] Password history enforced (remember)

## SSH Hardening

- [ ] Root login disabled (PermitRootLogin no)
- [ ] Password authentication disabled
- [ ] Public key authentication enabled
- [ ] Strong key exchange algorithms only
- [ ] Strong ciphers only
- [ ] Strong MACs only
- [ ] MaxAuthTries set (3)
- [ ] LoginGraceTime set (60)
- [ ] ClientAliveInterval configured
- [ ] X11Forwarding disabled (unless needed)
- [ ] AllowTcpForwarding disabled (unless needed)
- [ ] Banner configured (optional)
- [ ] Fail2ban protecting SSH

For detailed SSH hardening, see [SSH Hardening](../security/ssh-hardening.md).

## Firewall

- [ ] UFW enabled
- [ ] Default deny incoming
- [ ] Default allow outgoing
- [ ] Only necessary ports allowed
- [ ] SSH allowed (before enabling UFW!)
- [ ] Source IP restrictions where possible
- [ ] Logging enabled

For detailed firewall configuration, see [Firewall Guide](../../networking/index.md).

## Kernel Hardening

sysctl settings in `/etc/sysctl.d/99-security.conf`:

- [ ] kernel.randomize_va_space = 2
- [ ] kernel.kptr_restrict = 2
- [ ] kernel.dmesg_restrict = 1
- [ ] fs.suid_dumpable = 0
- [ ] net.ipv4.conf.all.accept_source_route = 0
- [ ] net.ipv4.conf.all.accept_redirects = 0
- [ ] net.ipv4.conf.all.send_redirects = 0
- [ ] net.ipv4.conf.all.rp_filter = 1
- [ ] net.ipv4.conf.all.log_martians = 1
- [ ] net.ipv4.tcp_syncookies = 1
- [ ] net.ipv4.icmp_echo_ignore_broadcasts = 1

## Mount Options

Root, `/boot`, and `/boot/efi` are classic filesystems with `/etc/fstab` entries; the ZFS pools mount natively. Harden the fstab mounts, and use per-dataset ZFS properties for the pools:

- [ ] /boot/efi mounted with umask=0077,fmask=0077,dmask=0077
- [ ] /boot mounted with nodev,nosuid,noexec
- [ ] /dev/shm mounted with nodev,nosuid,noexec
- [ ] /tmp mounted as tmpfs with nodev,nosuid,noexec (optional — see [Disk Partitioning](../installation/disk-partitioning.md))
- [ ] ZFS datasets on `hot` and `tank` carry appropriate per-dataset properties (`atime=off`, `setuid`/`exec`/`devices` where a dataset warrants tightening)

## Automatic Updates

- [ ] unattended-upgrades installed
- [ ] Automatic security updates enabled
- [ ] Email notifications configured (optional)
- [ ] Automatic reboot configured or Livepatch enabled

## Logging

- [ ] journald configured for persistent storage
- [ ] rsyslog configured
- [ ] Log rotation configured
- [ ] Remote logging configured (optional)
- [ ] auditd installed and configured
- [ ] Audit rules for:
  - [ ] User/group changes
  - [ ] Authentication events
  - [ ] sudo usage
  - [ ] File changes in /etc
  - [ ] Time changes

## AppArmor

- [ ] AppArmor enabled
- [ ] Profiles in enforce mode
- [ ] Custom profiles for applications
- [ ] No unconfined processes (unless required)

## Fail2ban

- [ ] Fail2ban installed and enabled
- [ ] SSH jail configured
- [ ] Reasonable ban times
- [ ] Email notifications (optional)
- [ ] Jails for other services as needed

## Services

- [ ] Unnecessary services disabled:
  - [ ] cups (unless printing needed)
  - [ ] avahi-daemon (unless mDNS needed)
  - [ ] bluetooth (unless hardware present)
  - [ ] snapd (unless using snaps)
- [ ] Running services reviewed
- [ ] Service hardening applied (systemd options)
- [ ] Network services bound to specific interfaces

## File Integrity

- [ ] AIDE installed and initialized
- [ ] AIDE database baseline created
- [ ] Daily AIDE checks scheduled
- [ ] rkhunter installed
- [ ] rkhunter database updated
- [ ] Rootkit checks scheduled

## Disk Encryption

!!! note "Only applicable if you chose an encrypted alternative"
    This build's default layout is **unencrypted ext4 root** (the host lives on a private network behind UFW/Tailscale; encryption adds a remote-unlock problem on a headless box). Skip this section unless you followed an encrypted path in [Disk Partitioning](../installation/disk-partitioning.md#encrypted-alternative-zfs-native-encryption-or-luks-lvm). ZFS native encryption covers the `hot`/`tank` data pools; LUKS+LVM covers the ext4 root if you need root encrypted too.

- [ ] Encryption active (ZFS native encryption on the data pools, or LUKS on root if you chose that path)
- [ ] Strong passphrase used
- [ ] Recovery key / raw key stored securely
- [ ] ZFS `keylocation` / `keyformat` recorded (or LUKS header backed up)
- [ ] Unlock mechanism planned (`zfs load-key` at boot / dropbear-initramfs / walk-up)

## Backup

- [ ] Backup solution configured
- [ ] Critical data backed up:
  - [ ] /etc
  - [ ] /home
  - [ ] Application data
  - [ ] Databases
- [ ] Backup restoration tested
- [ ] Off-site backup configured

## ZFS Pools (`hot` + `tank`)

- [ ] Hot data pool `hot` `ONLINE`, no errors: `zpool status -v hot`
- [ ] Cold data pool `tank` `ONLINE`, no errors: `zpool status -v tank`
- [ ] `hot` datasets present per layout (`incus`, `db`, `ai`) and `tank` datasets present (`media`, `nextcloud-data`, `nextcloud-app`, `backups`): `zfs list`
- [ ] Scrub scheduled on **both** pools, last scrub clean: `zpool status | grep scrub`
- [ ] ARC capped (e.g. 16 GiB, shared across both pools) so Incus VMs and Ollama have predictable memory: `cat /sys/module/zfs/parameters/zfs_arc_max`
- [ ] sanoid snapshot schedule present and running: `systemctl status sanoid.timer`
- [ ] Snapshots being taken on both pools incl. `hot/incus`: `zfs list -t snapshot | head`
- [ ] syncoid / restic off-host replication configured and tested (see [Backup](../../operations/backup.md))

## Bootloader (GRUB, ext4 root)

- [ ] GRUB installed to the primary disk and boots to login: `sudo efibootmgr -v`
- [ ] At least one previous kernel kept for GRUB "Advanced options" recovery: `dpkg --list | grep linux-image`
- [ ] GRUB config and EFI boot entries backed up (see [Boot Issues](../troubleshooting/boot-issues.md#back-up-grub-and-the-esp))
- [ ] (Alternative build only) If you took the [ZFS Root alternative](../installation/zfs-root-alternative.md), ZFSBootMenu is first in the EFI boot order and a prior boot environment exists to roll back to

## GPU / AI Stack

- [ ] ROCm installed and iGPU visible: `rocminfo | grep gfx1151`
- [ ] `/dev/kfd` and `/dev/dri` present with correct group ownership (render/video)
- [ ] amd-ttm GTT allocation configured (kernel `ttm.pages_limit` / `ttm.page_pool_size`)
- [ ] Ollama / llama.cpp inference functional against the iGPU

## Containers & Virtualization (Incus)

Incus is the single virtualization/container layer — Docker nests inside an Incus container, VMs are Incus VM instances. See the [Incus deep-dive](../../incus/index.md).

- [ ] Incus healthy and its ZFS backend points at `hot/incus`: `incus storage show default` (`driver: zfs`, `source: hot/incus`)
- [ ] Instances present and running as expected: `incus list`
- [ ] Instance storage is native ZFS datasets under `hot/incus` (not opaque named volumes): `zfs list -r hot/incus`
- [ ] Docker workloads run **inside** an Incus system container (`security.nesting=true`), with important data on host datasets bind-mounted in — not Docker named volumes ([docker-in-incus](../../incus/docker-in-incus.md))
- [ ] Incus bridge (`incusbr0`) forwarding filtered by UFW — same treatment `ufw-docker` gave bare Docker ([networking](../../incus/networking.md))
- [ ] VMs are Incus VM instances (`incus list --type=virtual-machine`); no bare libvirt/`virsh` on the host
- [ ] Service ports bound to 127.0.0.1 / proxied through a reverse proxy, not published straight to the LAN

## Network

- [ ] Static IP configured (for servers)
- [ ] DNS servers configured
- [ ] Network interfaces reviewed (two RTL8127 10GbE NICs, r8169 driver)
- [ ] Tailscale up and reachable: `tailscale status`
- [ ] Host confirmed NOT directly exposed to the public internet (LAN + Tailscale only)

## Documentation

- [ ] System configuration documented
- [ ] Changes logged
- [ ] Recovery procedures documented
- [ ] Contact information recorded

## Verification Commands

Run these to verify hardening:

```bash
# Security scan
sudo lynis audit system

# Service security scores
systemd-analyze security

# Listening ports
sudo ss -tlnp

# Failed services
systemctl --failed

# Users with login shells
grep -v nologin /etc/passwd

# SUID files
sudo find / -type f -perm -4000 2>/dev/null

# World-writable files
sudo find / -type f -perm -0002 2>/dev/null

# Firewall status
sudo ufw status verbose

# SSH configuration test
sudo sshd -t

# AppArmor status
sudo aa-status

# Fail2ban status
sudo fail2ban-client status

# Update status
apt list --upgradable
```

## Regular Maintenance

### Daily

- [ ] Review failed login attempts
- [ ] Check fail2ban bans
- [ ] Verify backup completion
- [ ] Monitor disk space

### Weekly

- [ ] Apply security updates
- [ ] Review system logs
- [ ] Check AIDE reports
- [ ] Run rkhunter

### Monthly

- [ ] Full system update
- [ ] Review user accounts
- [ ] Review sudo access
- [ ] Test backup restoration
- [ ] Review firewall rules
- [ ] Update AIDE baseline after changes

### Quarterly

- [ ] Security audit (Lynis)
- [ ] Review and rotate credentials
- [ ] Test disaster recovery
- [ ] Review and update documentation

## CIS Benchmark Reference

For comprehensive CIS compliance, run:

```bash
# OpenSCAP assessment
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --report /var/log/cis-report.html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```

## Notes

Use this space to document exceptions and custom configurations:

```
Date: _______________
Reviewed by: _______________
Exceptions:


Custom configurations:


Follow-up items:


```
