"""Render Ubuntu autoinstall + cloud-init data; build a NoCloud CIDATA ISO.

Subiquity (Ubuntu's installer since 20.04) automatically detects a second ISO
labelled `CIDATA` and reads its `user-data` / `meta-data` files. With the
right autoinstall YAML in `user-data`, the whole Ubuntu install completes
unattended — no menus, no questions.

We build the ISO ourselves rather than relying on `VBoxManage unattended
install`. That wrapper only knows about Ubuntu releases that shipped before
the VBox release, so newer Ubuntu ISOs fall off. Doing it directly works for
any Ubuntu version, current or future.

Requires `xorriso` on the control node (`brew install xorriso`).
"""

from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from msai_setup.lab.passwords import sha512_crypt

log = logging.getLogger(__name__)


def require_xorriso() -> None:
    """Raise SystemExit with install hints if `xorriso` is not on PATH."""
    if shutil.which("xorriso") is None:
        raise SystemExit(
            "xorriso not found on PATH. Install:\n"
            "    brew install xorriso        # macOS\n"
            "    sudo apt install xorriso     # Linux"
        )


# Subiquity rejects plaintext passwords in `identity.password`; it wants a
# crypt-format hash. The implementation now lives in passwords.py (shared with
# the Fedora kickstart path); this alias keeps the existing call site + tests.
_crypt_password = sha512_crypt


def render_user_data(
    *,
    hostname: str,
    user: str,
    full_user_name: str,
    password: str,
    ssh_public_key: str,
    locale: str = "en_US.UTF-8",
    keyboard_layout: str = "us",
    timezone: str = "Europe/Oslo",
    extra_packages: list[str] | None = None,
) -> str:
    """Produce a #cloud-config user-data document for Subiquity autoinstall.

    The resulting file should be written to a CIDATA ISO alongside meta-data.
    Subiquity uses the `autoinstall:` block; the embedded `user-data:` is run
    by cloud-init on first boot of the installed system.
    """
    extra_packages = list(extra_packages or [])
    packages = sorted({"openssh-server", "python3", *extra_packages})
    crypted = _crypt_password(password)

    autoinstall = {
        "version": 1,
        "interactive-sections": [],
        "refresh-installer": {"update": False},
        "locale": locale,
        "keyboard": {"layout": keyboard_layout},
        # Match every ethernet interface by name pattern rather than
        # hardcoding one. VirtualBox guest NIC naming varies (enp0s3, enp0s8,
        # eth0, ...) so a single match-all entry with DHCP is the robust choice.
        # `optional: true` keeps boot from blocking if a NIC is slow to appear.
        "network": {
            "version": 2,
            "ethernets": {
                "primary": {
                    "match": {"name": "e*"},
                    "dhcp4": True,
                    "optional": True,
                },
            },
        },
        "identity": {
            "realname": full_user_name,
            "username": user,
            "hostname": hostname,
            "password": crypted,
        },
        "ssh": {
            "install-server": True,
            "allow-pw": False,
            "authorized-keys": [ssh_public_key.strip()],
        },
        "storage": {"layout": {"name": "direct"}},
        "packages": packages,
        "late-commands": [
            f"echo '{user} ALL=(ALL) NOPASSWD:ALL' > /target/etc/sudoers.d/90-{user}",
            f"chmod 0440 /target/etc/sudoers.d/90-{user}",
        ],
        "shutdown": "reboot",
    }

    body = yaml.safe_dump(
        {"autoinstall": autoinstall},
        default_flow_style=False,
        sort_keys=False,
        width=1000,
    )
    return "#cloud-config\n" + body


def render_live_install_user_data(*, ssh_public_key: str) -> str:
    """Produce autoinstall user-data that opens SSH into the LIVE installer env.

    This is a deliberately different autoinstall config from
    :func:`render_user_data`: it does NOT drive a normal guided install. Its
    only job is to hand control to us over SSH so the root-on-ZFS install can be
    driven from the Python side (`msai lab install-zfs-root`), exactly the way a
    human would from a rescue shell.

    Two mechanisms combine:

    * ``early-commands`` run as root, very early — before storage/network
      probing — and authorise ``ssh_public_key`` for ``root`` in the live
      session, then start sshd. This is the documented technique for reaching an
      in-progress install remotely.
    * ``interactive-sections: [storage]`` makes Subiquity pause at the storage
      screen instead of auto-installing, so the live environment stays up
      indefinitely and never wipes a disk or reboots on its own. We do all the
      real work (partition, ``zpool create``, ``debootstrap``, chroot,
      ZFSBootMenu) over SSH against that paused live session.

    Args:
        ssh_public_key: The public key to authorise for ``root`` in the live
            installer environment.

    Returns:
        A ``#cloud-config`` document to write to the CIDATA ISO's ``user-data``.
    """
    key = ssh_public_key.strip()
    autoinstall = {
        "version": 1,
        # Pause here so Subiquity never runs a real install or reboots; the
        # live session stays alive for us to drive over SSH.
        "interactive-sections": ["storage"],
        "early-commands": [
            "mkdir -p /root/.ssh",
            "chmod 700 /root/.ssh",
            f"printf '%s\\n' {shlex.quote(key)} > /root/.ssh/authorized_keys",
            "chmod 600 /root/.ssh/authorized_keys",
            "systemctl enable ssh || true",
            "systemctl start ssh || true",
        ],
    }
    body = yaml.safe_dump(
        {"autoinstall": autoinstall},
        default_flow_style=False,
        sort_keys=False,
        width=1000,
    )
    return "#cloud-config\n" + body


def render_meta_data(*, hostname: str, instance_id: str | None = None) -> str:
    """Produce a NoCloud meta-data document with instance-id and local-hostname.

    Args:
        hostname: The guest hostname, used as the default instance-id seed.
        instance_id: Explicit cloud-init instance-id; derived from hostname if omitted.

    Returns:
        A YAML string suitable for writing to the CIDATA ISO's `meta-data` file.
    """
    inst = instance_id or f"iid-local-{hostname}"
    return yaml.safe_dump(
        {"instance-id": inst, "local-hostname": hostname},
        default_flow_style=False,
        sort_keys=False,
    )


def build_cidata_iso(
    *,
    user_data: str,
    meta_data: str,
    output_path: Path,
) -> None:
    """Build a NoCloud CIDATA ISO at `output_path`.

    Uses xorriso so it works on macOS/Linux/Windows alike. Idempotent: an
    existing ISO is overwritten in place.
    """
    require_xorriso()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        staging = Path(td)
        (staging / "user-data").write_text(user_data)
        (staging / "meta-data").write_text(meta_data)
        # Empty vendor-data is conventional; cloud-init won't complain if absent
        # but some Subiquity variants prefer it present.
        (staging / "vendor-data").write_text("")

        cmd = [
            "xorriso", "-as", "mkisofs",
            "-output", str(output_path),
            "-volid", "CIDATA",
            "-joliet",
            "-rock",
            str(staging / "user-data"),
            str(staging / "meta-data"),
            str(staging / "vendor-data"),
        ]
        log.info("building CIDATA ISO at %s", output_path)
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    log.info("CIDATA ISO ready: %s (%d bytes)", output_path, output_path.stat().st_size)
