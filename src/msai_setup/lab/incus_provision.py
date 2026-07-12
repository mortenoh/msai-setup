#!/usr/bin/env python3
"""Provision a lab instance on Incus (the real Linux box / MS-S1 MAX).

The Incus counterpart to provision.py. Same OSProfile abstraction, same seed
renderers (cloudinit / kickstart / windows) — but the delivery differs per OS
family because each has a different "cleanest" Incus path:

  * Ubuntu  -> `incus launch images:ubuntu/... --vm` with cloud-init passed as
    `config: user.user-data`. A ready VM image + first-boot cloud-config is far
    lighter than an ISO install, and the incus-agent gives us readiness.
  * Fedora  -> blank VM + the Fedora netinst ISO and an OEMDRV kickstart seed,
    both imported as managed ISO volumes (there's no reliable in-project Fedora
    cloud image path, and anaconda auto-detects the OEMDRV label).
  * Windows -> blank VM + the user-supplied Windows ISO and an UNATTEND
    autounattend seed as managed volumes, plus a vTPM + Secure Boot per profile,
    then a visible-console hand-off (no SSH gate) — mirrors the VBox flow and
    docs/incus/windows-vm.md.

Managed-volume ISO import (not raw host paths) is mandatory in the restricted
user-1000 project — see docs/incus/vms.md.

HONESTY: UNVALIDATED on this macOS dev host (no Incus). Written to the documented
`incus` CLI and unit-tested against a mocked subprocess; real validation is on
the MS-S1 MAX. The provider dispatch + argv are the tested contract.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from msai_setup.lab import cloudinit, incus, iso, kickstart, ssh, state, windows
from msai_setup.lab.config import LabConfig, load_config

log = logging.getLogger(__name__)


def _flow_for(cfg: LabConfig) -> str:
    """Return the Incus install flow for the profile's family (unit-testable)."""
    family = cfg.profile.family
    if family == "ubuntu":
        return "ubuntu-launch"
    if family == "fedora":
        return "fedora-iso"
    if family == "windows":
        return "windows-iso"
    raise SystemExit(f"no Incus flow for family '{family}' (profile '{cfg.os_profile}')")


def _ubuntu_image(cfg: LabConfig) -> str:
    """Image ref for the Ubuntu launch path ($INCUS_IMAGE overrides the default).

    Default is `images:ubuntu/<release>`. NOTE (unverified): the `images:` remote
    may not carry a VM variant for every release (e.g. a not-yet-published
    26.04); set INCUS_IMAGE to a known-good ref on the host if the default
    doesn't resolve. `incus image list images: type=virtual-machine` lists them.
    """
    return cfg.incus_image or f"images:ubuntu/{cfg.ubuntu_release}"


def _provision_ubuntu_launch(cfg: LabConfig, ssh_pubkey: str) -> None:
    """Ubuntu: launch a ready images: VM with first-boot cloud-init."""
    user_data = cloudinit.render_incus_user_data(
        hostname=cfg.vm_hostname.split(".")[0],
        user=cfg.vm_user,
        full_user_name=cfg.vm_fullname,
        password=cfg.vm_password,
        ssh_public_key=ssh_pubkey,
        extra_packages=list(cfg.extra_packages),
    )
    image = _ubuntu_image(cfg)
    log.info("launching Incus VM '%s' from %s (cloud-init first boot) ...", cfg.vm_name, image)
    incus.launch_vm(
        cfg.vm_name,
        image=image,
        project=cfg.incus_project,
        config={"user.user-data": user_data},
        cpu=cfg.cpus,
        memory_mb=cfg.memory_mb,
        disk_size_mb=cfg.primary_disk_size_mb,
    )
    _report_linux_access(cfg)


def _provision_fedora_iso(cfg: LabConfig, ssh_pubkey: str) -> None:
    """Fedora: blank VM + netinst ISO + OEMDRV kickstart seed (managed volumes)."""
    iso.ensure_iso(cfg.iso_path, url=cfg.iso_url, sha_url=cfg.iso_sha256_url)
    ks = kickstart.render_kickstart(
        hostname=cfg.vm_hostname.split(".")[0],
        user=cfg.vm_user,
        full_user_name=cfg.vm_fullname,
        password=cfg.vm_password,
        ssh_public_key=ssh_pubkey,
        extra_packages=list(cfg.extra_packages),
    )
    kickstart.build_oemdrv_iso(kickstart=ks, output_path=cfg.oemdrv_iso_path)

    incus.init_vm(
        cfg.vm_name, empty=True, project=cfg.incus_project,
        cpu=cfg.cpus, memory_mb=cfg.memory_mb, disk_size_mb=cfg.primary_disk_size_mb,
    )
    _import_and_attach_iso(cfg, cfg.iso_path, "iso", "install", boot_priority=10)
    _import_and_attach_iso(cfg, cfg.oemdrv_iso_path, "oemdrv", "oemdrv", boot_priority=None)
    incus.start(cfg.vm_name, project=cfg.incus_project)
    log.info("Fedora install started. anaconda auto-detects the OEMDRV kickstart seed.")
    log.info("Watch it: incus console %s --type=vga", cfg.vm_name)
    _report_linux_access(cfg)


def _provision_windows_iso(cfg: LabConfig) -> None:
    """Windows: blank VM + Windows ISO + UNATTEND seed + vTPM + Secure Boot."""
    win_iso = cfg.windows_iso
    if win_iso is None or not win_iso.is_file():
        raise SystemExit(
            f"Windows install ISO not found: {win_iso!r}. Set WINDOWS_ISO / --iso."
        )
    edition = "Windows 11 Pro" if cfg.os_profile == "windows-11" else "Windows 10 Pro"
    autounattend = windows.render_autounattend(
        hostname=cfg.vm_hostname.split(".")[0],
        user=cfg.vm_user,
        full_user_name=cfg.vm_fullname,
        password=cfg.vm_password,
        edition=edition,
        bypass_hw_checks=(cfg.os_profile == "windows-11"),
    )
    windows.build_unattend_iso(autounattend=autounattend, output_path=cfg.unattend_iso_path)

    incus.init_vm(
        cfg.vm_name, empty=True, project=cfg.incus_project,
        cpu=cfg.cpus, memory_mb=cfg.memory_mb, disk_size_mb=cfg.primary_disk_size_mb,
    )
    _import_and_attach_iso(cfg, win_iso, "iso", "install", boot_priority=10)
    _import_and_attach_iso(cfg, cfg.unattend_iso_path, "unattend", "unattend", boot_priority=None)
    # Firmware while stopped (TPM can't be hot-added).
    if cfg.profile.needs_tpm:
        incus.add_vtpm(cfg.vm_name, project=cfg.incus_project)
    incus.set_secure_boot(cfg.vm_name, enabled=cfg.profile.needs_secureboot, project=cfg.incus_project)
    incus.start(cfg.vm_name, project=cfg.incus_project)
    _report_windows_next_steps(cfg)


def _import_and_attach_iso(
    cfg: LabConfig,
    iso_path: Path,
    suffix: str,
    dev_name: str,
    *,
    boot_priority: int | None,
) -> None:
    """Import an ISO as a managed volume and attach it as a boot disk device."""
    vol_name = f"{cfg.vm_name}-{suffix}"
    incus.storage_volume_import(cfg.incus_pool, iso_path, vol_name, project=cfg.incus_project)
    incus.attach_iso_volume(
        cfg.vm_name, dev_name,
        pool=cfg.incus_pool, vol_name=vol_name,
        boot_priority=boot_priority, project=cfg.incus_project,
    )


def _report_linux_access(cfg: LabConfig) -> None:
    """Best-effort: wait briefly for an IPv4 and log the SSH command."""
    ipv4 = _wait_for_ipv4(cfg, timeout=180)
    if ipv4:
        log.info("Instance '%s' is up at %s.", cfg.vm_name, ipv4)
        priv_key = cfg.ssh_public_key_path.with_suffix("")
        log.info("    ssh -i %s %s@%s", priv_key, cfg.vm_user, ipv4)
        log.info("Your SSH key is authorised via cloud-init.")
    else:
        log.info("Instance '%s' has no IPv4 yet; check `incus list`.", cfg.vm_name)


def _wait_for_ipv4(cfg: LabConfig, *, timeout: int, interval: int = 5) -> str | None:
    """Poll `incus list` until the instance has a global IPv4, or time out."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ipv4 = incus.get_ipv4(cfg.vm_name, project=cfg.incus_project)
        if ipv4:
            return ipv4
        time.sleep(interval)
    return None


def _report_windows_next_steps(cfg: LabConfig) -> None:
    """Log the manual hand-off for a Windows install on Incus (no SSH gate)."""
    log.info("Windows install started on Incus for '%s'. Hand-off:", cfg.vm_name)
    log.info("  1. Open the console: incus console %s --type=vga", cfg.vm_name)
    log.info("  2. autounattend.xml installs %s and creates local admin '%s'.",
             cfg.profile.display_name, cfg.vm_user)
    log.info("  3. After install, detach the install ISO so it boots from disk:")
    log.info("       incus stop %s && incus config device remove %s install && incus start %s",
             cfg.vm_name, cfg.vm_name, cfg.vm_name)
    log.info("  4. Enable RDP in Windows (docs/remote-desktop/rdp/windows-setup.md) and expose")
    log.info("     it with a proxy device, gated to LAN/Tailscale (docs/incus/networking.md).")


def provision(cfg: LabConfig) -> None:
    """Provision `cfg`'s instance on Incus (dispatch on OS family)."""
    log.info("provisioning Incus instance '%s' (profile=%s, project=%s)",
             cfg.vm_name, cfg.os_profile, cfg.incus_project or "(current)")

    if state.is_phase_done(cfg.state_path, "provision"):
        log.info("provision phase already complete (state file says so).")
        log.info("Re-run from scratch: incus delete %s --force && rm %s",
                 cfg.vm_name, cfg.state_path)
        return

    incus.require_incus()

    # Lab SSH keypair (auto-generated if missing) — same as the VBox path.
    ssh.ensure_lab_keypair(cfg.ssh_public_key_path)
    ssh_pubkey = cfg.ssh_public_key_path.read_text().strip()

    # Record the console password for local console access (SSH is key-based).
    cfg.console_password_path.write_text(cfg.vm_password + "\n")
    log.info("console login: user '%s', password '%s'", cfg.vm_user, cfg.vm_password)

    flow = _flow_for(cfg)
    if flow == "ubuntu-launch":
        _provision_ubuntu_launch(cfg, ssh_pubkey)
    elif flow == "fedora-iso":
        _provision_fedora_iso(cfg, ssh_pubkey)
    else:  # windows-iso
        _provision_windows_iso(cfg)

    state.mark_phase_done(
        cfg.state_path,
        "provision",
        provider="incus",
        vm_name=cfg.vm_name,
        os_profile=cfg.os_profile,
        os_release=cfg.os_release,
        incus_pool=cfg.incus_pool,
        incus_project=cfg.incus_project,
        flow=flow,
    )


def main() -> None:
    """Provision the current instance on Incus (entrypoint mirroring provision.main)."""
    provision(load_config())
