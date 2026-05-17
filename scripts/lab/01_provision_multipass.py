#!/usr/bin/env python3
"""Phase 01 — provision the lab VM using Multipass.

Use this script on Apple Silicon Macs where VirtualBox 7.2's ARM Linux guest
support is still in tech preview and unreliable.

Multipass is Canonical's native Ubuntu-VM-on-your-laptop tool — it handles
the ISO + cloud-init + first boot in one shot and gives you SSH to an Ubuntu
VM in a couple of minutes.

Trade-offs vs. the VirtualBox path:
  + Native Apple Silicon support
  + Much simpler — Multipass handles ISO + install + cloud-init
  - Multipass VMs use a single primary disk by default (no multi-disk for
    ZFS exercises). The ZFS playbook here works against loopback files we
    create inside the VM, so the ZFS lab is still real — just on loopbacks,
    not on separate virtual disks.
  - Snapshots are per-Multipass-VM, not per-VBox-VM.

Install Multipass first:
    brew install --cask multipass        # macOS
    sudo snap install multipass          # Linux

Run:
    python3 scripts/lab/01_provision_multipass.py
"""

from __future__ import annotations

import logging
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab import _multipass, _state  # noqa: E402
from lab._config import load_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lab.provision.multipass")


CLOUD_INIT_TEMPLATE = """\
#cloud-config
hostname: {hostname}
locale: en_US.UTF-8
timezone: Europe/Oslo
users:
  - name: {user}
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    groups: [sudo]
    lock_passwd: false
    plain_text_passwd: '{password}'
    ssh_authorized_keys:
      - {ssh_pubkey}
package_update: true
package_upgrade: true
packages:
  - htop
  - tmux
  - jq
  - rsync
ssh_pwauth: true
"""


def main() -> None:
    cfg = load_config()
    log.info("provisioning Multipass VM '%s'", cfg.vm_name)

    if _state.is_phase_done(cfg.state_path, "provision"):
        log.info("provision phase already complete (state file says so).")
        return

    _multipass.require_multipass()

    # Read the user's SSH public key for cloud-init
    if not cfg.ssh_public_key_path.exists():
        raise SystemExit(
            f"SSH public key not found at {cfg.ssh_public_key_path}.\n"
            f"Generate one: ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519"
        )
    ssh_pubkey = cfg.ssh_public_key_path.read_text().strip()

    # Build cloud-init
    cloud_init = CLOUD_INIT_TEMPLATE.format(
        hostname=cfg.vm_hostname.split(".")[0],
        user=cfg.vm_user,
        password=cfg.vm_password,
        ssh_pubkey=ssh_pubkey,
    )

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(cloud_init)
        cloud_init_path = Path(f.name)

    log.info("cloud-init written to %s", cloud_init_path)

    # Launch
    _multipass.launch(
        cfg.vm_name,
        release=cfg.ubuntu_release,
        cpus=cfg.cpus,
        memory_gb=cfg.memory_mb // 1024,
        primary_disk_gb=cfg.primary_disk_size_mb // 1000,
        cloud_init=cloud_init_path,
    )

    info = _multipass.info(cfg.vm_name)
    log.info("VM state: %s", info.get("state"))

    try:
        ip = _multipass.get_ipv4(cfg.vm_name)
        log.info("VM IPv4: %s", ip)
        log.info("")
        log.info("SSH in with:")
        log.info("  ssh %s@%s", cfg.vm_user, ip)
        log.info("(your key has been authorised via cloud-init)")
    except _multipass.MultipassError as e:
        log.warning("could not get IPv4 yet: %s", e)
        log.warning("Retry: multipass info %s", cfg.vm_name)

    _state.mark_phase_done(
        cfg.state_path,
        "provision",
        provisioner="multipass",
        vm_name=cfg.vm_name,
        ubuntu_release=cfg.ubuntu_release,
        ip=ip if 'ip' in locals() else None,
    )

    log.info("")
    log.info("Next step: configure with Ansible:")
    log.info("  python3 scripts/lab/02_apply.py")
    log.info("(02_apply.py uses the state file to find the VM)")


if __name__ == "__main__":
    main()
