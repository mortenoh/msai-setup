#!/usr/bin/env python3
"""Phase 01 - provision the lab VM via VirtualBox + a self-built seed ISO.

Flow:

  1. Download the install ISO and verify its checksum.
  2/3. Prepare the boot ISO + seed ISO for the selected profile's install
     mechanism (`_prepare_install_media` dispatches on `profile.unattended`):
       - Ubuntu (subiquity): remaster the ISO with `autoinstall` in GRUB and
         build a NoCloud CIDATA seed (user-data + meta-data).
       - Fedora (kickstart): keep the netinst ISO unmodified and build an
         OEMDRV-labelled seed carrying ks.cfg (anaconda auto-detects it).
       - Windows (autounattend): keep the user-supplied ISO unmodified and
         build an UNATTEND-labelled seed carrying autounattend.xml. On VBox the
         primary disk is SATA/AHCI, seen natively — NO virtio drivers.
  4. Create a VirtualBox VM (x86 or ARM, depending on host arch).
  5. Attach: primary disk (+ lab/install disks for Linux) + boot ISO + seed ISO.
     For Windows, apply TPM/Secure Boot per profile and boot the DVD first.
  6. Boot the VM. The installer reads the seed and installs unattended.
  7. Linux: wait for SSH on the forwarded host port. Windows won't bring up our
     sshd, so instead hand off to the visible console + log the RDP follow-up.

This is independent of VBoxManage's `unattended install` wrapper (which is
stale for newer releases) - we drive the install ourselves through each OS's
native unattended mechanism.

Re-run safely: every step is idempotent. State recorded in target/.
"""

from __future__ import annotations

import logging
from pathlib import Path

from msai_setup.lab import cloudinit, iso, kickstart, ssh, state, vbox, windows
from msai_setup.lab.config import LabConfig, load_config

log = logging.getLogger(__name__)


def _prepare_ubuntu_media(cfg: LabConfig, ssh_pubkey: str) -> tuple[Path, Path]:
    """Ubuntu (subiquity): remaster the ISO + build the CIDATA seed.

    Returns ``(boot_iso, seed_iso)``: the autoinstall-remastered Ubuntu ISO the
    VM boots, and the CIDATA ISO Subiquity scans for user-data/meta-data.
    """
    iso.ensure_iso(cfg.iso_path, url=cfg.iso_url, sha_url=cfg.iso_sha256_url)
    iso.remaster_iso_for_autoinstall(cfg.iso_path, cfg.autoinstall_iso_path)
    user_data = cloudinit.render_user_data(
        hostname=cfg.vm_hostname.split(".")[0],
        user=cfg.vm_user,
        full_user_name=cfg.vm_fullname,
        password=cfg.vm_password,
        ssh_public_key=ssh_pubkey,
        extra_packages=list(cfg.extra_packages),
    )
    meta_data = cloudinit.render_meta_data(hostname=cfg.vm_hostname.split(".")[0])
    cloudinit.build_cidata_iso(
        user_data=user_data,
        meta_data=meta_data,
        output_path=cfg.cidata_iso_path,
    )
    return cfg.autoinstall_iso_path, cfg.cidata_iso_path


def _prepare_fedora_media(cfg: LabConfig, ssh_pubkey: str) -> tuple[Path, Path]:
    """Fedora (kickstart): download the netinst ISO + build the OEMDRV seed.

    Returns ``(boot_iso, seed_iso)``: the UNMODIFIED Fedora netinst ISO the VM
    boots (no GRUB remaster), and the OEMDRV-labelled ISO anaconda auto-detects
    to run ks.cfg — no boot argument needed.
    """
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
    return cfg.iso_path, cfg.oemdrv_iso_path


def _prepare_windows_media(cfg: LabConfig, ssh_pubkey: str) -> tuple[Path, Path]:
    """Windows (autounattend): verify the local ISO + build the UNATTEND seed.

    Returns ``(boot_iso, seed_iso)``: the UNMODIFIED user-supplied Windows ISO
    (no download, no remaster — VBox's SATA/AHCI disk needs no virtio drivers),
    and the UNATTEND-labelled ISO Windows Setup scans for autounattend.xml.

    `ssh_pubkey` is unused (Windows doesn't use our SSH key); the parameter is
    kept for a uniform dispatcher signature.
    """
    del ssh_pubkey  # not used by Windows
    win_iso = cfg.windows_iso
    if win_iso is None or not win_iso.is_file():
        raise SystemExit(
            f"Windows install ISO not found: {win_iso!r}. "
            "Set WINDOWS_ISO=/path/to/Win.iso (or `msai lab create --iso <path>`)."
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
    return win_iso, cfg.unattend_iso_path


def _prepare_install_media(cfg: LabConfig, ssh_pubkey: str) -> tuple[Path, Path]:
    """Dispatch on the profile's install mechanism; return ``(boot_iso, seed_iso)``.

    Kept free of VBox calls so it's unit-testable: it only downloads/builds the
    two ISOs the common boot path then attaches.
    """
    mechanism = cfg.profile.unattended
    if mechanism == "subiquity":
        return _prepare_ubuntu_media(cfg, ssh_pubkey)
    if mechanism == "kickstart":
        return _prepare_fedora_media(cfg, ssh_pubkey)
    if mechanism == "autounattend":
        return _prepare_windows_media(cfg, ssh_pubkey)
    raise SystemExit(
        f"unsupported install mechanism '{mechanism}' for profile '{cfg.os_profile}'"
    )


def _disk_counts(cfg: LabConfig) -> tuple[int, int]:
    """Return ``(lab_disk_count, install_disk_count)`` for this profile.

    Zero for profiles that don't want the Linux ZFS-practice + root-on-ZFS
    install disks (Windows) — those get only the primary disk.
    """
    if not cfg.profile.wants_lab_disks:
        return 0, 0
    return cfg.lab_disk_count, cfg.install_disk_count


def _await_install_and_report(cfg: LabConfig) -> None:
    """Post-boot hand-off: wait for SSH (Linux) or log Windows next steps.

    Split out so the SSH-gate skip for Windows is unit-testable: Windows never
    brings up our sshd, so waiting would always time out. Raises on SSH timeout
    for Linux (so the caller does NOT mark the phase done).
    """
    if cfg.profile.family == "windows":
        _report_windows_next_steps(cfg)
        return
    _wait_for_ssh_and_report(cfg)


def _wait_for_ssh_and_report(cfg: LabConfig) -> None:
    """Wait for the installed Linux guest's SSH, then log connection details."""
    log.info("Waiting for SSH-as-%s on %s:%d (up to 30 min) ...",
             cfg.vm_user, cfg.ssh_host, cfg.ssh_forward_port)
    priv_key = cfg.ssh_public_key_path.with_suffix("")  # strip .pub
    try:
        ssh.wait_for_ssh(
            cfg.ssh_host,
            cfg.ssh_forward_port,
            user=cfg.vm_user,
            identity_file=priv_key,
            timeout=1800,
        )
    except TimeoutError as e:
        log.error("SSH never came up: %s", e)
        log.error("Capture the console to see what happened:")
        log.error("    VBoxManage controlvm %s screenshotpng /tmp/lab.png", cfg.vm_name)
        raise

    log.info("SSH is up. Connect with:")
    log.info("    ssh -p %d %s@%s", cfg.ssh_forward_port, cfg.vm_user, cfg.ssh_host)
    log.info("Your SSH key (%s) is already authorised via the installer seed.",
             cfg.ssh_public_key_path)

    # For a graphical profile, point the user at RDP once the desktop is set up.
    if cfg.profile.is_graphical:
        log.info("Graphical profile '%s' detected. To enable the desktop over RDP:", cfg.os_profile)
        log.info("    msai lab apply rdp")
        log.info("then connect an RDP client to %s:%d and log in as '%s' (console password).",
                 cfg.ssh_host, cfg.rdp_forward_port, cfg.vm_user)


def _report_windows_next_steps(cfg: LabConfig) -> None:
    """Log the manual hand-off for a Windows install (no SSH gate)."""
    log.info("A VirtualBox window opened for '%s'. Windows install hand-off:", cfg.vm_name)
    log.info("  1. At 'Press any key to boot from CD or DVD...', press a key so")
    log.info("     Setup boots from the install ISO.")
    log.info("  2. autounattend.xml installs %s hands-off and creates local admin",
             cfg.profile.display_name)
    log.info("     '%s' (password: the console password saved to %s).",
             cfg.vm_user, cfg.console_password_path)
    log.info("  3. On the post-install reboot do NOT press a key, so it boots the")
    log.info("     installed Windows from disk (not back into Setup).")
    log.info("  4. Then enable Remote Desktop inside Windows per")
    log.info("     docs/remote-desktop/rdp/windows-setup.md and connect an RDP client.")


def main() -> None:
    """Provision a lab instance end-to-end, dispatching on the configured provider.

    Default provider is "vbox" (the VirtualBox flow below, unchanged). With
    LAB_PROVIDER=incus (`msai lab create --provider incus`) it hands off to the
    Incus provider for the real Linux box instead.
    """
    cfg = load_config()
    if cfg.provider == "incus":
        # Incus provider (the real Linux box). Lazy import avoids any import
        # cost/cycle on the default VBox path. UNVALIDATED on this macOS host.
        from msai_setup.lab import incus_provision

        incus_provision.provision(cfg)
        return

    log.info("provisioning VM '%s' (platform=%s)", cfg.vm_name, cfg.platform)

    if state.is_phase_done(cfg.state_path, "provision"):
        log.info("provision phase already complete (state file says so).")
        log.info("Re-run from scratch:")
        log.info("    VBoxManage controlvm %s poweroff 2>/dev/null", cfg.vm_name)
        log.info("    VBoxManage unregistervm %s --delete", cfg.vm_name)
        log.info("    rm %s", cfg.state_path)
        return

    vbox.require_vboxmanage()
    cloudinit.require_xorriso()

    # 1. Lab SSH keypair (auto-generated if missing). This is dedicated to
    # the lab so it doesn't touch the user's main SSH key infrastructure.
    ssh.ensure_lab_keypair(cfg.ssh_public_key_path)
    ssh_pubkey = cfg.ssh_public_key_path.read_text().strip()

    # Record the console password (random per-instance unless $VM_PASSWORD was
    # set) so the user can still log in on the VM console if they ever need to.
    # SSH uses key auth, so this is only for local console access.
    cfg.console_password_path.write_text(cfg.vm_password + "\n")
    log.info("console login: user '%s', password '%s'", cfg.vm_user, cfg.vm_password)
    log.info("  (also saved to %s)", cfg.console_password_path)

    # 2/3. Prepare the boot ISO + seed ISO for this profile's install mechanism
    # (Ubuntu: remastered ISO + CIDATA; Fedora: plain netinst + OEMDRV kickstart).
    log.info("preparing %s install media (%s) ...",
             cfg.profile.display_name, cfg.profile.unattended)
    boot_iso, seed_iso = _prepare_install_media(cfg, ssh_pubkey)

    # 4. Create the VM
    vbox.create_vm(cfg.vm_name, ostype=cfg.vm_ostype, platform=cfg.platform)
    vbox.configure_vm(
        cfg.vm_name,
        memory_mb=cfg.memory_mb,
        cpus=cfg.cpus,
        vram_mb=cfg.vram_mb,
        platform=cfg.platform,
    )
    vbox.add_ssh_port_forward(cfg.vm_name, host_port=cfg.ssh_forward_port)
    # Graphical profiles (e.g. ubuntu-desktop) get a second NAT forward so the
    # in-guest xrdp is reachable on the host once `msai lab apply rdp` runs.
    if cfg.profile.is_graphical:
        vbox.add_rdp_port_forward(cfg.vm_name, host_port=cfg.rdp_forward_port)

    # 5. Disks. Windows profiles (wants_lab_disks False) get ONLY the primary
    # disk — the 6 ZFS-practice + 2 root-on-ZFS install disks are Linux-only.
    lab_disk_count, install_disk_count = _disk_counts(cfg)

    vbox.create_disk(cfg.primary_disk_path, size_mb=cfg.primary_disk_size_mb)
    for i in range(1, lab_disk_count + 1):
        vbox.create_disk(cfg.lab_disk_path(i), size_mb=cfg.lab_disk_size_mb)
    # Dedicated root-on-ZFS install disks, appended after the practice disks
    # (see config.py). These are additional to the 6 practice disks, so the
    # README's ZFS walkthrough is untouched.
    for i in range(1, install_disk_count + 1):
        vbox.create_disk(cfg.install_disk_path(i), size_mb=cfg.install_disk_size_mb(i))

    # 6. Storage controllers and attachments
    vbox.ensure_storage_controller(
        cfg.vm_name,
        ctrl_name="SATA",
        kind="sata",
        controller="IntelAhci",
        portcount="30",
        bootable="on",
    )
    # On x86, IDE is the conventional place for install ISOs. On ARM, the IDE
    # controller crashes VBox 7.2's firmware enumeration (VERR_NOT_SUPPORTED) -
    # so on ARM we attach the ISOs on SATA ports instead, past both the practice
    # disks (ports 1..lab_disk_count) and the install disks (the next block).
    data_disk_total = lab_disk_count + install_disk_count
    iso_controller = "IDE" if cfg.platform == "x86" else "SATA"
    iso_primary_port = 0 if cfg.platform == "x86" else data_disk_total + 1
    iso_cidata_port = 1 if cfg.platform == "x86" else data_disk_total + 2

    if cfg.platform == "x86":
        vbox.ensure_storage_controller(
            cfg.vm_name,
            ctrl_name="IDE",
            kind="ide",
        )

    # Primary disk on SATA port 0
    vbox.attach_disk(
        cfg.vm_name, controller="SATA", port=0, device=0,
        medium=cfg.primary_disk_path,
    )
    # Lab disks on SATA ports 1..N
    for i in range(1, lab_disk_count + 1):
        vbox.attach_disk(
            cfg.vm_name, controller="SATA", port=i, device=0,
            medium=cfg.lab_disk_path(i),
        )
    # Install disks on the SATA ports immediately after the lab disks.
    for i in range(1, install_disk_count + 1):
        vbox.attach_disk(
            cfg.vm_name, controller="SATA", port=lab_disk_count + i, device=0,
            medium=cfg.install_disk_path(i),
        )
    # Boot ISO: Ubuntu autoinstall-remaster / Fedora netinst / Windows install.
    vbox.attach_iso(
        cfg.vm_name, controller=iso_controller,
        port=iso_primary_port, device=0,
        iso=boot_iso,
    )
    # Seed ISO: Ubuntu CIDATA / Fedora OEMDRV / Windows UNATTEND — each installer
    # auto-detects its own seed by volume label.
    vbox.attach_iso(
        cfg.vm_name, controller=iso_controller,
        port=iso_cidata_port, device=0,
        iso=seed_iso,
    )

    # Windows-only firmware: TPM 2.0 (Win11) + Secure Boot per profile. Done
    # while the VM is stopped (TPM can't be hot-added). Linux profiles set
    # manage_firmware False so their firmware is left at VBox's defaults.
    if cfg.profile.manage_firmware:
        if cfg.profile.needs_tpm:
            vbox.add_tpm(cfg.vm_name, version="2.0")
        vbox.set_secure_boot(cfg.vm_name, enabled=cfg.profile.needs_secureboot)
        # Boot the DVD first so Windows Setup runs. The visible "Press any key to
        # boot from CD" prompt is the intended hand-off: press to install; on the
        # post-install reboot DON'T press, so it boots the installed disk.
        vbox.set_boot_order(cfg.vm_name, ["dvd", "disk"])

    # 7. Boot the VM. Headless by default is off (cfg.headless): a visible GUI
    # console window lets the user take over a stuck installer by hand.
    vbox.start(cfg.vm_name, headless=cfg.headless)

    seed_desc = {
        "subiquity": "CIDATA autoinstall",
        "kickstart": "OEMDRV kickstart",
        "autounattend": "UNATTEND autounattend.xml",
    }.get(cfg.profile.unattended, cfg.profile.unattended)
    boot_mode = "headless" if cfg.headless else "with a visible console window"
    log.info("VM started %s. Installing %s via the %s seed.",
             boot_mode, cfg.profile.display_name, seed_desc)
    log.info("Watch the install with:")
    log.info("    VBoxManage controlvm %s screenshotpng /tmp/lab.png && open /tmp/lab.png", cfg.vm_name)

    # Post-boot: Linux waits for SSH; Windows hands off to the visible console.
    # (For Windows this returns without an SSH gate — see the function.)
    _await_install_and_report(cfg)

    state.mark_phase_done(
        cfg.state_path,
        "provision",
        vm_name=cfg.vm_name,
        os_profile=cfg.os_profile,
        headless=cfg.headless,
        platform=cfg.platform,
        ostype=cfg.vm_ostype,
        os_release=cfg.os_release,
        iso=str(cfg.iso_path),
        seed=str(seed_iso),
        primary_disk=str(cfg.primary_disk_path),
        lab_disk_count=lab_disk_count,
        install_disk_count=install_disk_count,
    )


