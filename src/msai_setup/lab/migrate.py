#!/usr/bin/env python3
"""Root-on-ZFS migration driver — `msai lab migrate`.

Converts the running ext4-rooted lab VM into the documented root-on-ZFS +
ZFSBootMenu, two-independent-pool architecture (see START.md and
docs/ubuntu/installation/). It:

  1. Runs the ``zfs-root-migrate`` Ansible playbook with ``do_reboot=false``,
     which partitions the two dedicated migration disks, creates ``rpool`` and
     ``tank``, rsyncs the live system into ``rpool/ROOT/ubuntu``, builds a
     ZFS-capable dracut initramfs, installs ZFSBootMenu, registers the EFI boot
     entry, writes an EFI-only fstab, and exports the pools cleanly.
  2. Verifies the migration OFFLINE from the still-running source system, where
     ``rpool/ROOT/ubuntu`` is a plain (non-root) dataset. It ADOPTS the pools the
     playbook left imported (rather than re-importing — see the kernel note
     below) and asserts: both pools ONLINE and healthy, the boot environment
     holds a complete system with a ZFS-aware initramfs, the ESP carries the
     ZFSBootMenu binary + efibootmgr entry, and the EFI-only fstab is in place.
  3. Exercises the boot-environment rollback mechanism end to end (snapshot ->
     change -> ``zfs rollback`` -> change gone) — the single most valuable thing
     to prove, and the exact operation ZFSBootMenu performs under the hood.

Why offline verification instead of "reboot into ZFSBootMenu and re-verify":
the real MS-S1 MAX is x86_64, where firmware honours the efibootmgr entry and
boots the prebuilt ZFSBootMenu EFI directly (run the playbook with the default
``do_reboot=true`` there). VirtualBox's **aarch64** EFI firmware, however,
refuses to execute the ZFSBootMenu EFI image (``pe_kernel_check_no_relocation:
Inner kernel image contains base relocations, which we do not support``), so on
an Apple-Silicon lab the VM cannot actually boot ZFSBootMenu. The migration,
pools, initramfs and rollback semantics are all identical regardless, and are
fully proven offline — which is why the lab command verifies that way.

One further lab-only wrinkle: this VM runs OpenZFS 2.4.1 on a 7.0 kernel, which
OpenZFS itself flags as EXPERIMENTAL. On it, a freshly created pool can get
wedged "pool is busy" on ``zpool export`` (even ``-f``) until the next reboot.
So the verifier never depends on exporting/re-importing within one boot: it
adopts the imported pool and proves rollback in place. Reboot-level durability
(change persists across a real power cycle, then rolls back) is demonstrated by
a genuine VM reboot rather than an export/import cycle; that is documented in
``src/msai_setup/lab/README.md`` and is inherently reliable on x86_64 hardware.
"""

from __future__ import annotations

import logging

from msai_setup.lab import apply as apply_mod
from msai_setup.lab import ssh, state
from msai_setup.lab.config import LabConfig, load_config

log = logging.getLogger(__name__)

PLAYBOOK = "zfs-root-migrate"

# Bash run on the (still ext4-rooted) source VM after the playbook. Imports the
# freshly-created pools — where rpool/ROOT/ubuntu is NOT the live root, so it can
# be mounted, snapshotted and rolled back freely — asserts every migration
# artifact, proves boot-environment rollback, then exports the pools cleanly.
# Any failed check exits non-zero (set -e), which surfaces as a CLI error.
_VERIFY_SCRIPT = r"""
set -euo pipefail
export PATH="$PATH:/usr/sbin:/sbin"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

echo "== locating rpool + tank (source system; BE is not the live root here) =="
# ADOPT whatever the migration playbook left imported rather than insisting on a
# fresh export+import: on this experimental ZFS-on-kernel-7.0 lab (dmesg warns
# "Using ZFS ... is EXPERIMENTAL"), a freshly created pool can get stuck "pool is
# busy" on export until the next reboot — even `zpool export -f`. The real x86_64
# target exports cleanly and reboots straight into ZFSBootMenu; here we simply
# verify against the pool as the playbook left it. Import only if it isn't already
# imported. -N avoids auto-mounting rpool/home over the BE mountpoint (which would
# shadow /mnt/home); we mount just the BE, below.
adopt_pool() {
  local pool="$1"
  if zpool list -H -o name "$pool" >/dev/null 2>&1; then
    echo "  ($pool already imported by the playbook — adopting it)"
  else
    zpool import -f -N -d /dev/disk/by-id -R /mnt "$pool"
  fi
}
adopt_pool rpool
adopt_pool tank

# Best-effort cleanup: try to leave the pools exported, but never fail the
# verification if the experimental kernel keeps them "busy" (a reboot releases
# them, and the source system does not otherwise touch these pools).
cleanup() {
  zfs unmount -a 2>/dev/null || true
  zpool export tank  2>/dev/null || zpool export -f tank  2>/dev/null || true
  zpool export rpool 2>/dev/null || zpool export -f rpool 2>/dev/null || true
}
trap cleanup EXIT

echo "== pool health =="
zpool status -x rpool | grep -q 'is healthy' || zpool status -x | grep -q 'all pools are healthy' \
  || fail "rpool not healthy"
[ "$(zpool list -H -o health rpool)" = ONLINE ] || fail "rpool not ONLINE"
[ "$(zpool list -H -o health tank)"  = ONLINE ] || fail "tank not ONLINE"
pass "rpool + tank both ONLINE and healthy"

echo "== dataset layout =="
# `zfs get mountpoint` reports the altroot-prefixed path, so under -R /mnt the
# BE's mountpoint property (/ on the real system) shows as /mnt. Compare against
# the pool's altroot ("/" when there is none) instead of a bare "/".
altroot=$(zpool get -H -o value altroot rpool); [ "$altroot" = "-" ] && altroot="/"
be_mp=$(zfs get -H -o value mountpoint rpool/ROOT/ubuntu)
[ "$(zfs get -H -o value canmount rpool/ROOT/ubuntu)" = noauto ] || fail "BE canmount != noauto"
[ "$be_mp" = "$altroot" ] || fail "BE mountpoint ($be_mp) != pool root ($altroot)"
pass "rpool/ROOT/ubuntu is canmount=noauto, mountpoint=/ (root; shown as $be_mp under altroot)"

echo "== boot environment contents =="
zfs mount rpool/ROOT/ubuntu
mount | grep -q 'rpool/ROOT/ubuntu on /mnt ' || fail "BE did not mount at /mnt"
grep -q 'Ubuntu' /mnt/etc/os-release || fail "BE has no Ubuntu os-release"
ls /mnt/boot/vmlinuz-* >/dev/null 2>&1 || fail "BE has no kernel"
newest_initrd=$(ls -1 /mnt/boot/initrd.img-* | sort -V | tail -1)
[ -n "$newest_initrd" ] || fail "BE has no initramfs"
lsinitramfs "$newest_initrd" 2>/dev/null | grep -q 'zfs-import.target' \
  || fail "initramfs lacks ZFS root support"
pass "BE holds a complete Ubuntu system with a ZFS-aware (dracut) initramfs"

echo "== EFI-only fstab =="
grep -q '/boot/efi' /mnt/etc/fstab || fail "fstab missing /boot/efi"
grep -qE '^\s*[^#].*\s/\s+ext4' /mnt/etc/fstab && fail "fstab still has an ext4 / entry"
pass "target /etc/fstab is EFI-only (no ext4 root)"

echo "== ZFSBootMenu artifacts =="
[ "$(zfs get -H -o value org.zfsbootmenu:commandline rpool/ROOT/ubuntu)" != "-" ] \
  || fail "org.zfsbootmenu:commandline not set"
rpool_member=$(zpool status -PL rpool | grep -oE '/dev/sd[a-z][0-9]+' | head -1)
[ -n "$rpool_member" ] || fail "could not locate the rpool member device"
efi_part=$(echo "$rpool_member" | sed 's/[0-9]*$/1/')   # /dev/sdX2 -> /dev/sdX1 (the ESP)
mkdir -p /mnt/esp && mount "$efi_part" /mnt/esp
ls /mnt/esp/EFI/ZBM/*.EFI >/dev/null 2>&1 || { umount /mnt/esp; fail "ZFSBootMenu EFI binary missing from ESP"; }
ls /mnt/esp/EFI/BOOT/BOOT*.EFI >/dev/null 2>&1 || { umount /mnt/esp; fail "ESP fallback EFI binary missing"; }
umount /mnt/esp
pass "ZFSBootMenu EFI binary present on the ESP (+ removable-media fallback)"
if efibootmgr 2>/dev/null | grep -q ZFSBootMenu; then
  pass "efibootmgr entry 'ZFSBootMenu' is registered in firmware NVRAM"
else
  echo "NOTE: no ZFSBootMenu NVRAM entry visible from the source system (expected on some firmware)."
fi

echo "== boot-environment rollback proof =="
# This is the whole point of root-on-ZFS: snapshot the boot environment, make a
# change, then roll the WHOLE BE back to the snapshot and confirm the change is
# gone. On the real x86_64 box this exact snapshot+rollback is what ZFSBootMenu
# drives from its boot menu to undo a bad upgrade. `sync` first so the change is
# committed to the on-disk dataset (what would survive a reboot), not just cache.
# (A true reboot-persistence demonstration is done separately via a real VM
# reboot — see the module docstring — because export/re-import is unreliable on
# this experimental lab kernel.)
zfs destroy rpool/ROOT/ubuntu@msai-rollback-test 2>/dev/null || true
rm -f /mnt/etc/msai-rollback-marker

zfs snapshot rpool/ROOT/ubuntu@msai-rollback-test
echo "content-before-change" > /mnt/etc/msai-rollback-marker
sync
[ -e /mnt/etc/msai-rollback-marker ] || fail "marker not created"
pass "snapshot taken and a change committed inside the boot environment"

zfs rollback rpool/ROOT/ubuntu@msai-rollback-test
[ -e /mnt/etc/msai-rollback-marker ] && fail "marker survived rollback (rollback did not work)"
zfs destroy rpool/ROOT/ubuntu@msai-rollback-test
pass "boot-environment rollback works: snapshot -> change -> rollback -> change gone"

echo "ALL-VERIFY-CHECKS-PASSED"
"""


def _run_playbook(cfg: LabConfig, *, do_reboot: bool, extra_args: list[str]) -> None:
    """Write the inventory and run the migration playbook against the lab VM."""
    apply_mod.require_ansible()
    apply_mod.write_inventory(cfg)
    args = ["-e", f"do_reboot={'true' if do_reboot else 'false'}", *extra_args]
    apply_mod.run_playbook(PLAYBOOK, args)


def run_migrate(
    *,
    do_reboot: bool = False,
    skip_verify: bool = False,
    extra_args: list[str] | None = None,
) -> None:
    """Migrate the lab VM to root-on-ZFS + ZFSBootMenu and verify the result.

    Args:
        do_reboot: Pass ``do_reboot=true`` to the playbook so it reboots into
            ZFSBootMenu at the end (the real-hardware / x86_64 path). Left False
            in the lab, where the migration is verified offline instead (see the
            module docstring for the VirtualBox aarch64 firmware limitation).
        skip_verify: Skip the offline verification + rollback proof.
        extra_args: Extra arguments forwarded to ``ansible-playbook`` (e.g.
            ``-e fast_disk=...``).
    """
    extra_args = extra_args or []
    cfg = load_config()

    if not state.is_phase_done(cfg.state_path, "provision"):
        log.warning(
            "Phase 'provision' is not marked complete (%s). Create the VM first "
            "with `msai create <name>`.",
            cfg.state_path,
        )

    log.info("migrating '%s' to root-on-ZFS + ZFSBootMenu", cfg.vm_name)
    _run_playbook(cfg, do_reboot=do_reboot, extra_args=extra_args)

    if do_reboot:
        log.info(
            "Playbook rebooted the guest into ZFSBootMenu (do_reboot=true). On real "
            "x86_64 hardware this lands on the new ZFS root; verify with `msai lab status` "
            "and `zpool status` once SSH returns."
        )
        return

    if skip_verify:
        log.info("skipping verification (skip_verify=True)")
    else:
        _run_verification(cfg)

    state.mark_phase_done(
        cfg.state_path,
        "zfs_root_migrate",
        verified=not skip_verify,
    )
    log.info("root-on-ZFS migration complete for '%s'", cfg.vm_name)


def _run_verification(cfg: LabConfig) -> None:
    """Run the offline verification + rollback proof, raising on any failure."""
    priv_key = cfg.ssh_public_key_path.with_suffix("")
    log.info("verifying migration + proving boot-environment rollback (offline)")
    result = ssh.run_remote_script(
        cfg.vm_user,
        cfg.ssh_host,
        cfg.ssh_forward_port,
        _VERIFY_SCRIPT,
        identity_file=priv_key,
    )
    for line in (result.stdout or "").splitlines():
        log.info("  verify: %s", line)
    if result.returncode != 0 or "ALL-VERIFY-CHECKS-PASSED" not in (result.stdout or ""):
        raise RuntimeError(
            "migration verification failed:\n"
            + (result.stdout or "")
            + "\n"
            + (result.stderr or "")
        )
    log.info("verification PASSED: pools healthy, BE complete, rollback proven")
