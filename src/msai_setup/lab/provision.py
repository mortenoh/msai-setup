#!/usr/bin/env python3
"""Phase 01 - provision the lab VM via VirtualBox + a self-built cloud-init ISO.

Flow:

  1. Download the Ubuntu Server ISO and verify SHA256.
  2. Render an autoinstall user-data file with our SSH key, hostname, sudo,
     openssh-server, etc.
  3. Build a NoCloud CIDATA ISO containing user-data + meta-data.
  4. Create a VirtualBox VM (x86 or ARM, depending on host arch).
  5. Attach: primary disk + N lab disks + Ubuntu ISO + CIDATA ISO.
  6. Boot the VM headless. Subiquity reads CIDATA and installs Ubuntu
     unattended. On first reboot, SSH is up with our key authorised.
  7. Wait for SSH on the forwarded host port.

This is independent of VBoxManage's `unattended install` wrapper (which is
stale for newer Ubuntu releases) - we drive the install ourselves through
the standard Subiquity autoinstall mechanism.

Re-run safely: every step is idempotent. State recorded in target/.
"""

from __future__ import annotations

import logging

from msai_setup.lab import cloudinit, iso, ssh, state, vbox
from msai_setup.lab.config import load_config

log = logging.getLogger(__name__)


def main() -> None:
    """Provision a VirtualBox lab VM end-to-end."""
    cfg = load_config()
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

    # 2. ISO + remaster with autoinstall cmdline
    iso.ensure_iso(cfg.iso_path, url=cfg.iso_url, sha_url=cfg.iso_sha256_url)
    iso.remaster_iso_for_autoinstall(cfg.iso_path, cfg.autoinstall_iso_path)

    # 3. Build the CIDATA ISO
    user_data = cloudinit.render_user_data(
        hostname=cfg.vm_hostname.split(".")[0],
        user=cfg.vm_user,
        full_user_name=cfg.vm_fullname,
        password=cfg.vm_password,
        ssh_public_key=ssh_pubkey,
    )
    meta_data = cloudinit.render_meta_data(hostname=cfg.vm_hostname.split(".")[0])
    cloudinit.build_cidata_iso(
        user_data=user_data,
        meta_data=meta_data,
        output_path=cfg.cidata_iso_path,
    )

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

    # 5. Disks
    vbox.create_disk(cfg.primary_disk_path, size_mb=cfg.primary_disk_size_mb)
    for i in range(1, cfg.lab_disk_count + 1):
        vbox.create_disk(cfg.lab_disk_path(i), size_mb=cfg.lab_disk_size_mb)

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
    # so on ARM we attach the ISOs on SATA ports instead.
    iso_controller = "IDE" if cfg.platform == "x86" else "SATA"
    iso_primary_port = 0 if cfg.platform == "x86" else cfg.lab_disk_count + 1
    iso_cidata_port = 1 if cfg.platform == "x86" else cfg.lab_disk_count + 2

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
    for i in range(1, cfg.lab_disk_count + 1):
        vbox.attach_disk(
            cfg.vm_name, controller="SATA", port=i, device=0,
            medium=cfg.lab_disk_path(i),
        )
    # Ubuntu install ISO (the remastered one with `autoinstall` in GRUB)
    vbox.attach_iso(
        cfg.vm_name, controller=iso_controller,
        port=iso_primary_port, device=0,
        iso=cfg.autoinstall_iso_path,
    )
    # CIDATA ISO (Subiquity scans removable media for it)
    vbox.attach_iso(
        cfg.vm_name, controller=iso_controller,
        port=iso_cidata_port, device=0,
        iso=cfg.cidata_iso_path,
    )

    # 7. Boot headless
    vbox.start_headless(cfg.vm_name)

    log.info("VM started. Subiquity is installing Ubuntu using the CIDATA ISO.")
    log.info("Watch the install with:")
    log.info("    VBoxManage controlvm %s screenshotpng /tmp/lab.png && open /tmp/lab.png", cfg.vm_name)
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
    log.info("Your SSH key (%s) is already authorised via cloud-init.",
             cfg.ssh_public_key_path)

    state.mark_phase_done(
        cfg.state_path,
        "provision",
        vm_name=cfg.vm_name,
        platform=cfg.platform,
        ostype=cfg.vm_ostype,
        ubuntu_release=cfg.ubuntu_release,
        iso=str(cfg.iso_path),
        cidata=str(cfg.cidata_iso_path),
        primary_disk=str(cfg.primary_disk_path),
        lab_disk_count=cfg.lab_disk_count,
    )


