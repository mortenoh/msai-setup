#!/usr/bin/env python3
"""Phase 01 — provision the lab VM.

What this script does:

1. Verify VBoxManage is installed.
2. Download Ubuntu 26.04 LTS server ISO if missing, verify SHA256 against the
   official SHA256SUMS file.
3. Create a VirtualBox VM with:
   - EFI firmware (matches the real MS-S1 MAX install path)
   - Configurable CPU/RAM/VRAM
   - Host port 2222 -> guest 22 NAT forward for SSH
4. Create one primary disk + N "lab" disks for ZFS exercises.
5. Configure unattended Ubuntu install (user, password, hostname).
6. Start the VM headless; the installer will run, reboot, and end at a
   login prompt with SSH listening.

Run with:

    python3 scripts/lab/01_provision.py

Re-run safely: every step is idempotent.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow running this file directly: scripts/lab/01_provision.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab import _iso, _ssh, _state, _vbox  # noqa: E402
from lab._config import load_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lab.provision")


def main() -> None:
    cfg = load_config()
    log.info("provisioning VM '%s'", cfg.vm_name)

    if _state.is_phase_done(cfg.state_path, "provision"):
        log.info("provision phase is already complete (state file says so).")
        log.info("To re-run from scratch: destroy the VM (lab/destroy.py) or")
        log.info("delete the state file: %s", cfg.state_path)
        return

    _vbox.require_vboxmanage()

    # 1. ISO
    _iso.ensure_iso(
        cfg.iso_path,
        url=cfg.iso_url,
        sha_url=cfg.iso_sha256_url,
    )

    # 2. VM shell
    _vbox.create_vm(cfg.vm_name)
    _vbox.configure_vm(
        cfg.vm_name,
        memory_mb=cfg.memory_mb,
        cpus=cfg.cpus,
        vram_mb=cfg.vram_mb,
    )
    _vbox.add_ssh_port_forward(cfg.vm_name, host_port=cfg.ssh_forward_port)

    # 3. Disks
    _vbox.create_disk(cfg.primary_disk_path, size_mb=cfg.primary_disk_size_mb)
    for i in range(1, cfg.lab_disk_count + 1):
        _vbox.create_disk(cfg.lab_disk_path(i), size_mb=cfg.lab_disk_size_mb)

    # 4. Storage controllers
    _vbox.ensure_storage_controller(
        cfg.vm_name,
        ctrl_name="SATA",
        kind="sata",
        controller="IntelAhci",
        portcount="30",
        bootable="on",
    )
    _vbox.ensure_storage_controller(
        cfg.vm_name,
        ctrl_name="IDE",
        kind="ide",
    )

    # 5. Attach disks
    _vbox.attach_disk(
        cfg.vm_name,
        controller="SATA", port=0, device=0,
        medium=cfg.primary_disk_path,
    )
    for i in range(1, cfg.lab_disk_count + 1):
        _vbox.attach_disk(
            cfg.vm_name,
            controller="SATA", port=i, device=0,
            medium=cfg.lab_disk_path(i),
        )

    # 6. Attach ISO and start unattended install
    _vbox.attach_iso(
        cfg.vm_name,
        controller="IDE", port=0, device=0,
        iso=cfg.iso_path,
    )
    _vbox.unattended_install(
        cfg.vm_name,
        iso=cfg.iso_path,
        user=cfg.vm_user,
        password=cfg.vm_password,
        full_user_name=cfg.vm_fullname,
        hostname=cfg.vm_hostname,
    )

    # 7. Boot it
    _vbox.start_headless(cfg.vm_name)

    log.info("install is running. The VM will reboot a few times.")
    log.info("Waiting for SSH on %s:%d ...", cfg.ssh_host, cfg.ssh_forward_port)
    try:
        _ssh.wait_for_port(cfg.ssh_host, cfg.ssh_forward_port, timeout=1800)
    except TimeoutError as e:
        log.error("SSH never came up: %s", e)
        log.error("Check the VM's console via VirtualBox to see what's wrong:")
        log.error("  VBoxManage controlvm %s screenshotpng /tmp/screen.png", cfg.vm_name)
        raise

    log.info("SSH is up. Connect with:")
    log.info("  ssh -p %d %s@%s", cfg.ssh_forward_port, cfg.vm_user, cfg.ssh_host)
    log.info("Password is the one set via VM_PASSWORD (default '%s').", cfg.vm_password)
    log.info("")
    log.info("After confirming you can log in, detach the ISO so future")
    log.info("boots go straight to disk:")
    log.info("  VBoxManage storageattach %s --storagectl IDE --port 0 --device 0 --medium none",
             cfg.vm_name)

    _state.mark_phase_done(
        cfg.state_path,
        "provision",
        vm_name=cfg.vm_name,
        ubuntu_release=cfg.ubuntu_release,
        primary_disk=str(cfg.primary_disk_path),
        lab_disk_count=cfg.lab_disk_count,
    )


if __name__ == "__main__":
    main()
