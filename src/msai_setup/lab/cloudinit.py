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
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

log = logging.getLogger(__name__)


def require_xorriso() -> None:
    if shutil.which("xorriso") is None:
        raise SystemExit(
            "xorriso not found on PATH. Install:\n"
            "    brew install xorriso        # macOS\n"
            "    sudo apt install xorriso     # Linux"
        )


def _crypt_password(password: str) -> str:
    """Return a SHA-512 crypt of `password` for use in autoinstall identity:.

    Subiquity rejects plaintext passwords in `identity.password`; it wants a
    crypt-format hash. `openssl passwd -6` is universally available and
    produces a valid SHA-512 crypt with a random salt.
    """
    result = subprocess.run(
        ["openssl", "passwd", "-6", password],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


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
        "network": {
            "version": 2,
            "ethernets": {
                "enp0s3": {"dhcp4": True},
                "eth0": {"dhcp4": True},
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


def render_meta_data(*, hostname: str, instance_id: str | None = None) -> str:
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
