#!/usr/bin/env python3
"""Fresh root-on-ZFS install driver — ``msai lab install-zfs-root``.

Rehearses the documented root-on-ZFS ALTERNATIVE — not the canonical MS-S1 MAX
install, which is Subiquity + ext4 (see
docs/ubuntu/installation/zfs-root-alternative.md): boot the Ubuntu Server
live ISO, get a root shell in the LIVE environment, then partition + create both
pools, ``debootstrap`` a fresh Ubuntu into ``rpool/ROOT/ubuntu``, chroot to
configure it, install ZFSBootMenu, and register the EFI boot entry — never an
ext4 stage.

How the live environment is reached: the VM boots the same remastered live-server
ISO the ext4 flow uses (``autoinstall`` on the kernel cmdline), but with a
different autoinstall config (see
:func:`msai_setup.lab.cloudinit.render_live_install_user_data`) whose
``early-commands`` only authorise the lab SSH key for ``root`` and start sshd,
while ``interactive-sections: [storage]`` pauses Subiquity so it never runs a
real install or reboots. We then drive the whole install over SSH via the
``zfs-root-install`` Ansible playbook — far more observable and retryable than
cramming it into one opaque ``early-commands`` blob.

Verification (the aarch64 lab reality): VirtualBox's ARM firmware cannot execute
the ZFSBootMenu EFI binary, so the installed system cannot actually boot ZBM in
the lab (the pools, initramfs and ZBM artifacts are still fully real and
correct). So instead of "reboot into ZFSBootMenu and re-verify", we verify
OFFLINE from the live environment — where ``rpool/ROOT/ubuntu`` is a plain
(non-root) dataset that can be mounted, snapshotted and rolled back freely — and
we prove boot-environment rollback ACROSS A REAL REBOOT:

  1. Phase A (live env): import the pools the playbook created, assert every
     install artifact (pools healthy, boot environment complete with a ZFS-aware
     initramfs, EFI-only fstab, admin user, ZFSBootMenu on the ESP), snapshot the
     boot environment, write a marker into it, ``sync``, export.
  2. Reboot the VM host-side (DVD-first boot order re-enters the live ISO).
  3. Phase B (live env again): re-import the pools, confirm the marker SURVIVED
     the real reboot (the boot environment is genuinely on-disk and durable),
     then ``zfs rollback`` and confirm the marker is GONE — the exact operation
     ZFSBootMenu drives from its boot menu to undo a bad upgrade.

On real x86_64 hardware, run the playbook directly with ``do_reboot=true`` and
the firmware boots straight into ZFSBootMenu.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from msai_setup.lab import apply as apply_mod
from msai_setup.lab import cloudinit, iso, ssh, state, vbox
from msai_setup.lab.config import LabConfig, load_config

log = logging.getLogger(__name__)

PLAYBOOK = "zfs-root-install"
LIVE_SSH_USER = "root"
INSTALL_INVENTORY = apply_mod.ANSIBLE_DIR / "inventory.install.generated.yml"

# Phase A: import the freshly-created pools, assert every install artifact, then
# snapshot the boot environment and drop a marker that must survive a reboot.
_VERIFY_PHASE_A = r"""
set -uo pipefail
export PATH="$PATH:/usr/sbin:/sbin"
ADMIN_USER="__ADMIN_USER__"
fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

echo "== importing rpool + tank (BE is not the live root here) =="
import_pool() {
  local pool="$1"
  zpool list -H -o name "$pool" >/dev/null 2>&1 && { echo "  ($pool already imported)"; return; }
  zpool import -f -N -d /dev/disk/by-id -R /mnt "$pool" || fail "cannot import $pool"
}
import_pool rpool
import_pool tank

echo "== pool health =="
[ "$(zpool list -H -o health rpool)" = ONLINE ] || fail "rpool not ONLINE"
[ "$(zpool list -H -o health tank)"  = ONLINE ] || fail "tank not ONLINE"
pass "rpool + tank both ONLINE"

echo "== dataset layout =="
[ "$(zfs get -H -o value canmount rpool/ROOT/ubuntu)" = noauto ] || fail "BE canmount != noauto"
altroot=$(zpool get -H -o value altroot rpool); [ "$altroot" = "-" ] && altroot="/"
be_mp=$(zfs get -H -o value mountpoint rpool/ROOT/ubuntu)
[ "$be_mp" = "$altroot" ] || fail "BE mountpoint ($be_mp) != pool root ($altroot)"
pass "rpool/ROOT/ubuntu is canmount=noauto, mountpoint=/ (shown as $be_mp under altroot)"

echo "== boot environment contents (freshly debootstrapped) =="
zfs mount rpool/ROOT/ubuntu 2>/dev/null || true
mount | grep -q 'rpool/ROOT/ubuntu on /mnt ' || fail "BE did not mount at /mnt"
grep -q 'Ubuntu' /mnt/etc/os-release || fail "BE has no Ubuntu os-release"
ls /mnt/boot/vmlinuz-* >/dev/null 2>&1 || fail "BE has no kernel"
newest_initrd=$(ls -1 /mnt/boot/initrd.img-* 2>/dev/null | sort -V | tail -1)
[ -n "$newest_initrd" ] || fail "BE has no initramfs"
lsinitramfs "$newest_initrd" 2>/dev/null | grep -qE 'zfs' || fail "initramfs lacks ZFS support"
pass "BE holds a fresh Ubuntu system with a ZFS-aware initramfs"

echo "== admin user provisioned in the BE =="
# /home is a separate dataset (rpool/home), so the admin's authorized_keys lives
# there, not in the BE — mount it on top of the BE to inspect it.
zfs mount rpool/home 2>/dev/null || true
grep -q "^${ADMIN_USER}:" /mnt/etc/passwd || fail "admin user ${ADMIN_USER} missing from BE"
[ -s "/mnt/home/${ADMIN_USER}/.ssh/authorized_keys" ] || fail "admin authorized_keys missing/empty"
grep -qE 'ssh-ed25519 [A-Za-z0-9+/]{60,}' "/mnt/home/${ADMIN_USER}/.ssh/authorized_keys" \
  || fail "admin authorized_keys does not hold a complete ssh-ed25519 key (truncated?)"
grep -q "${ADMIN_USER}" /mnt/etc/sudoers.d/90-${ADMIN_USER} 2>/dev/null || fail "admin sudoers drop-in missing"
pass "admin user ${ADMIN_USER} present with a complete SSH key + passwordless sudo"

echo "== EFI-only fstab =="
grep -q '/boot/efi' /mnt/etc/fstab || fail "fstab missing /boot/efi"
grep -qE '^\s*[^#].*\s/\s+ext4' /mnt/etc/fstab && fail "fstab still has an ext4 / entry"
pass "target /etc/fstab is EFI-only (no ext4 root)"

echo "== ZFSBootMenu artifacts =="
[ "$(zfs get -H -o value org.zfsbootmenu:commandline rpool/ROOT/ubuntu)" != "-" ] \
  || fail "org.zfsbootmenu:commandline not set"
esp=$(blkid -L EFI 2>/dev/null) || fail "no EFI-labelled ESP found"
mkdir -p /mnt/esp && mount "$esp" /mnt/esp
ls /mnt/esp/EFI/ZBM/*.EFI >/dev/null 2>&1 || { umount /mnt/esp; fail "ZFSBootMenu EFI binary missing from ESP"; }
ls /mnt/esp/EFI/BOOT/BOOT*.EFI >/dev/null 2>&1 || { umount /mnt/esp; fail "ESP fallback EFI binary missing"; }
umount /mnt/esp
pass "ZFSBootMenu EFI binary present on the ESP (+ removable-media fallback)"

echo "== stage boot-environment rollback proof (survives a real reboot) =="
# Snapshot the CLEAN boot environment FIRST, then write the marker so the live
# dataset diverges from the snapshot. That way a later rollback to the snapshot
# genuinely REMOVES the marker (a snapshot taken after the write would keep it).
zfs destroy rpool/ROOT/ubuntu@msai-reboot-test 2>/dev/null || true
rm -f /mnt/etc/msai-reboot-marker
zfs snapshot rpool/ROOT/ubuntu@msai-reboot-test
echo "content-before-reboot-and-rollback" > /mnt/etc/msai-reboot-marker
sync
[ -e /mnt/etc/msai-reboot-marker ] || fail "marker not created"
pass "snapshot rpool/ROOT/ubuntu@msai-reboot-test taken (clean); marker written and synced"

echo "== export pools so the reboot gets a clean on-disk state =="
zfs unmount -a 2>/dev/null || true
for pool in tank rpool; do
  for attempt in 1 2 3 4 5; do
    zpool export "$pool" 2>/dev/null || zpool export -f "$pool" 2>/dev/null && break
    sleep 2
  done
done
echo "PHASE-A-OK"
"""

# Phase B (after a real reboot): re-import, confirm the marker survived, then
# roll the boot environment back and confirm the marker is gone.
_VERIFY_PHASE_B = r"""
set -uo pipefail
export PATH="$PATH:/usr/sbin:/sbin"
export DEBIAN_FRONTEND=noninteractive
fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

# The reboot dropped us into a pristine live ISO again (casper overlay resets),
# so the ZFS userland installed during the install is gone — reinstall it.
if ! command -v zpool >/dev/null 2>&1; then
  echo "== reinstalling zfsutils-linux in the fresh live env =="
  apt-get update -qq && apt-get install -y -qq zfsutils-linux >/dev/null || fail "cannot install zfsutils-linux"
fi
modprobe zfs 2>/dev/null || true

echo "== re-import pools after the real reboot =="
zpool import -f -N -d /dev/disk/by-id -R /mnt rpool || fail "cannot re-import rpool"
zfs mount rpool/ROOT/ubuntu 2>/dev/null || true
mount | grep -q 'rpool/ROOT/ubuntu on /mnt ' || fail "BE did not mount after reboot"

echo "== marker must have SURVIVED the real reboot =="
[ -e /mnt/etc/msai-reboot-marker ] || fail "marker did NOT survive the reboot (BE not durable)"
grep -q 'content-before-reboot-and-rollback' /mnt/etc/msai-reboot-marker \
  || fail "marker content changed unexpectedly across reboot"
pass "boot-environment change survived a genuine VM power cycle (BE is durable on-disk)"

echo "== snapshot must still exist =="
zfs list -H -t snapshot rpool/ROOT/ubuntu@msai-reboot-test >/dev/null 2>&1 \
  || fail "rollback snapshot missing after reboot"
pass "rollback snapshot rpool/ROOT/ubuntu@msai-reboot-test present after reboot"

echo "== roll the boot environment back; marker must be GONE =="
zfs rollback rpool/ROOT/ubuntu@msai-reboot-test
[ -e /mnt/etc/msai-reboot-marker ] && fail "marker survived rollback (rollback did not work)"
zfs destroy rpool/ROOT/ubuntu@msai-reboot-test
pass "boot-environment rollback works: reboot -> marker persisted -> rollback -> marker gone"

echo "== leave the pools exported =="
zfs unmount -a 2>/dev/null || true
zpool export rpool 2>/dev/null || zpool export -f rpool 2>/dev/null || true
echo "ALL-VERIFY-CHECKS-PASSED"
"""


def _provision_live_vm(cfg: LabConfig) -> None:
    """Create the VM, boot the live installer ISO, wait for root SSH in the live env.

    Reuses the same ISO download/remaster and VirtualBox machinery as the ext4
    flow, but attaches only the two dedicated ZFS-target disks (fast -> rpool,
    slow -> tank), sets a DVD-first boot order (so reboots re-enter the live ISO
    on the aarch64 lab), and boots an autoinstall whose ``early-commands`` open
    SSH into the live session.
    """
    if state.is_phase_done(cfg.state_path, "provision"):
        log.info("live VM already provisioned (state file says so); reusing it.")
        if not vbox.vm_running(cfg.vm_name):
            vbox.start_headless(cfg.vm_name)
        _wait_for_live_ssh(cfg)
        return

    vbox.require_vboxmanage()
    cloudinit.require_xorriso()

    priv_key = ssh.ensure_lab_keypair(cfg.ssh_public_key_path)
    ssh_pubkey = cfg.ssh_public_key_path.read_text().strip()

    iso.ensure_iso(cfg.iso_path, url=cfg.iso_url, sha_url=cfg.iso_sha256_url)
    iso.remaster_iso_for_autoinstall(cfg.iso_path, cfg.autoinstall_iso_path)

    user_data = cloudinit.render_live_install_user_data(ssh_public_key=ssh_pubkey)
    meta_data = cloudinit.render_meta_data(hostname=cfg.vm_hostname.split(".")[0])
    cloudinit.build_cidata_iso(
        user_data=user_data,
        meta_data=meta_data,
        output_path=cfg.cidata_iso_path,
    )

    vbox.create_vm(cfg.vm_name, ostype=cfg.vm_ostype, platform=cfg.platform)
    vbox.configure_vm(
        cfg.vm_name,
        memory_mb=cfg.memory_mb,
        cpus=cfg.cpus,
        vram_mb=cfg.vram_mb,
        platform=cfg.platform,
    )
    # DVD first: on aarch64 the installed disk's ZFSBootMenu EFI cannot execute,
    # so booting the DVD every time deterministically re-enters the live ISO for
    # offline verification (and re-runs early-commands to reopen SSH).
    vbox.set_boot_order(cfg.vm_name, ["dvd", "disk"])
    vbox.add_ssh_port_forward(cfg.vm_name, host_port=cfg.ssh_forward_port)

    # Exactly the two dedicated NVMe stand-ins — no primary/practice disks. This
    # mirrors the real MS-S1 MAX (two physical drives) and makes disk
    # identification unambiguous (two disks: larger -> rpool, smaller -> tank).
    for i in range(1, cfg.install_disk_count + 1):
        vbox.create_disk(cfg.install_disk_path(i), size_mb=cfg.install_disk_size_mb(i))

    vbox.ensure_storage_controller(
        cfg.vm_name,
        ctrl_name="SATA",
        kind="sata",
        controller="IntelAhci",
        portcount="30",
        bootable="on",
    )
    for i in range(1, cfg.install_disk_count + 1):
        vbox.attach_disk(
            cfg.vm_name, controller="SATA", port=i - 1, device=0,
            medium=cfg.install_disk_path(i),
        )

    # ISOs: IDE on x86, SATA (past the data disks) on ARM — same rationale as
    # provision.py (ARM's VBox firmware chokes on the IDE controller).
    iso_controller = "IDE" if cfg.platform == "x86" else "SATA"
    iso_primary_port = 0 if cfg.platform == "x86" else cfg.install_disk_count
    iso_cidata_port = 1 if cfg.platform == "x86" else cfg.install_disk_count + 1
    if cfg.platform == "x86":
        vbox.ensure_storage_controller(cfg.vm_name, ctrl_name="IDE", kind="ide")
    vbox.attach_iso(
        cfg.vm_name, controller=iso_controller,
        port=iso_primary_port, device=0, iso=cfg.autoinstall_iso_path,
    )
    vbox.attach_iso(
        cfg.vm_name, controller=iso_controller,
        port=iso_cidata_port, device=0, iso=cfg.cidata_iso_path,
    )

    vbox.start_headless(cfg.vm_name)
    log.info("live VM started; waiting for SSH into the LIVE environment as root ...")
    _wait_for_live_ssh(cfg, priv_key=priv_key)  # priv_key is a Path

    state.mark_phase_done(
        cfg.state_path,
        "provision",
        vm_name=cfg.vm_name,
        platform=cfg.platform,
        ostype=cfg.vm_ostype,
        mode="zfs-root-live",
        lab_disk_count=0,
        install_disk_count=cfg.install_disk_count,
    )


def _wait_for_live_ssh(cfg: LabConfig, *, priv_key: Path | None = None) -> None:
    """Block until root SSH into the live installer environment succeeds."""
    key = priv_key if priv_key is not None else cfg.ssh_public_key_path.with_suffix("")
    ssh.wait_for_ssh(
        cfg.ssh_host,
        cfg.ssh_forward_port,
        user=LIVE_SSH_USER,
        identity_file=key,
        timeout=1800,
    )
    log.info("live installer environment reachable as %s@%s:%d",
             LIVE_SSH_USER, cfg.ssh_host, cfg.ssh_forward_port)


def _run_install_playbook(cfg: LabConfig, *, do_reboot: bool, extra_args: list[str]) -> None:
    """Write the root/live-env inventory and run the install playbook."""
    apply_mod.require_ansible()
    apply_mod.write_inventory(cfg, user=LIVE_SSH_USER, become=False, path=INSTALL_INVENTORY)
    ssh_pubkey = cfg.ssh_public_key_path.read_text().strip()
    # Pass driver-controlled vars as a single JSON object. `-e key=value` splits
    # the value on whitespace, which would truncate an SSH public key (`ssh-ed25519
    # AAAA... comment`) at the first space; JSON extra-vars preserve it intact.
    extra_vars = {
        "do_reboot": do_reboot,
        "admin_user": cfg.vm_user,
        "admin_ssh_pubkey": ssh_pubkey,
        "target_hostname": cfg.vm_hostname.split(".")[0],
    }
    args = ["-e", json.dumps(extra_vars), *extra_args]
    apply_mod.run_playbook(PLAYBOOK, args, inventory=INSTALL_INVENTORY)


def _run_script(cfg: LabConfig, script: str, *, label: str) -> str:
    """Run a bash script in the live env as root over SSH; return stdout, raise on failure."""
    priv_key = cfg.ssh_public_key_path.with_suffix("")
    result = ssh.run_remote_script(
        LIVE_SSH_USER,
        cfg.ssh_host,
        cfg.ssh_forward_port,
        script,
        identity_file=priv_key,
        sudo=False,  # already root in the live env
    )
    for line in (result.stdout or "").splitlines():
        log.info("  %s: %s", label, line)
    if result.returncode != 0:
        raise RuntimeError(
            f"{label} failed (rc={result.returncode}):\n"
            + (result.stdout or "") + "\n" + (result.stderr or "")
        )
    return result.stdout or ""


def _verify_and_prove_rollback(cfg: LabConfig) -> None:
    """Verify install artifacts offline, then prove BE rollback across a real reboot."""
    log.info("verifying install artifacts + staging the rollback proof (phase A)")
    phase_a = _VERIFY_PHASE_A.replace("__ADMIN_USER__", cfg.vm_user)
    out_a = _run_script(cfg, phase_a, label="verify-A")
    if "PHASE-A-OK" not in out_a:
        raise RuntimeError("phase A did not complete:\n" + out_a)

    log.info("rebooting the VM host-side to prove boot-environment durability")
    vbox.power_off(cfg.vm_name)
    vbox.wait_until_stopped(cfg.vm_name)
    vbox.start_headless(cfg.vm_name)
    _wait_for_live_ssh(cfg)

    log.info("confirming the marker survived, then rolling back (phase B)")
    out_b = _run_script(cfg, _VERIFY_PHASE_B, label="verify-B")
    if "ALL-VERIFY-CHECKS-PASSED" not in out_b:
        raise RuntimeError("phase B did not complete:\n" + out_b)
    log.info("VERIFICATION PASSED: pools healthy, BE complete, rollback proven across a real reboot")


def run_install_zfs_root(
    *,
    do_reboot: bool = False,
    skip_verify: bool = False,
    extra_args: list[str] | None = None,
) -> None:
    """Provision a live-boot VM and perform a fresh root-on-ZFS + ZFSBootMenu install.

    Args:
        do_reboot: Pass ``do_reboot=true`` to the playbook so it reboots into
            ZFSBootMenu at the end (the real-hardware / x86_64 path). Left False
            in the lab, where the install is verified offline instead (see the
            module docstring for the VirtualBox aarch64 firmware limitation).
        skip_verify: Skip the offline verification + boot-environment rollback
            proof.
        extra_args: Extra arguments forwarded to ``ansible-playbook`` (e.g.
            ``-e fast_disk=...``).
    """
    extra_args = extra_args or []
    cfg = load_config()
    log.info("installing fresh root-on-ZFS + ZFSBootMenu on '%s'", cfg.vm_name)

    _provision_live_vm(cfg)
    _run_install_playbook(cfg, do_reboot=do_reboot, extra_args=extra_args)

    if do_reboot:
        log.info(
            "Playbook rebooted the guest into ZFSBootMenu (do_reboot=true). On real "
            "x86_64 hardware this lands on the new ZFS root once SSH returns."
        )
        return

    if skip_verify:
        log.info("skipping verification (skip_verify=True)")
    else:
        _verify_and_prove_rollback(cfg)

    state.mark_phase_done(
        cfg.state_path,
        "zfs_root_install",
        verified=not skip_verify,
        install_disk_count=cfg.install_disk_count,
    )
    log.info("root-on-ZFS install complete for '%s'", cfg.vm_name)
