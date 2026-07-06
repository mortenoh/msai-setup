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

import hashlib
import logging
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

# Alphabet used by crypt(3) for its custom base64 encoding (note: not the
# standard base64 alphabet — `.` and `/` lead, and there is no padding).
_CRYPT_B64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Byte-permutation order the SHA-512 crypt scheme applies to the final digest
# before base64-encoding it, per the reference implementation (Ulrich Drepper's
# sha512-crypt spec / glibc). Each triple is encoded into 4 output characters.
_SHA512_CRYPT_ORDER = (
    (0, 21, 42), (22, 43, 1), (44, 2, 23), (3, 24, 45),
    (25, 46, 4), (47, 5, 26), (6, 27, 48), (28, 49, 7),
    (50, 8, 29), (9, 30, 51), (31, 52, 10), (53, 11, 32),
    (12, 33, 54), (34, 55, 13), (56, 14, 35), (15, 36, 57),
    (37, 58, 16), (59, 17, 38), (18, 39, 60), (40, 61, 19),
    (62, 20, 41),
)


def require_xorriso() -> None:
    """Raise SystemExit with install hints if `xorriso` is not on PATH."""
    if shutil.which("xorriso") is None:
        raise SystemExit(
            "xorriso not found on PATH. Install:\n"
            "    brew install xorriso        # macOS\n"
            "    sudo apt install xorriso     # Linux"
        )


def _b64_from_24bit(b2: int, b1: int, b0: int, n: int) -> str:
    """Encode up to three bytes into `n` crypt-base64 characters (low bits first)."""
    w = (b2 << 16) | (b1 << 8) | b0
    out: list[str] = []
    for _ in range(n):
        out.append(_CRYPT_B64[w & 0x3F])
        w >>= 6
    return "".join(out)


def _crypt_password(password: str, *, salt: str | None = None, rounds: int = 5000) -> str:
    """Return a SHA-512 crypt (`$6$...`) hash of `password` for autoinstall identity:.

    Subiquity rejects plaintext passwords in `identity.password`; it wants a
    crypt-format hash. This is a pure-Python implementation of the SHA-512
    crypt scheme (built on `hashlib`) so it never shells out to `openssl` —
    Apple's bundled LibreSSL `openssl passwd` does not support `-6`, and the
    stdlib `crypt` module was removed in Python 3.13.

    Args:
        password: The plaintext password to hash.
        salt: Up to 16 chars from the crypt base64 alphabet. Random if omitted.
        rounds: SHA-512 crypt round count (5000 is the crypt(3) default).

    Returns:
        A `$6$<salt>$<hash>` string compatible with crypt(3)/`openssl passwd -6`.
    """
    if salt is None:
        salt = "".join(secrets.choice(_CRYPT_B64) for _ in range(16))
    pw = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")[:16]
    pw_len = len(pw)

    # Digest "A": password + salt + digest "B"-derived bytes.
    ctx = hashlib.sha512()
    ctx.update(pw)
    ctx.update(salt_bytes)

    alt = hashlib.sha512()
    alt.update(pw)
    alt.update(salt_bytes)
    alt.update(pw)
    alt_result = alt.digest()

    cnt = pw_len
    while cnt > 64:
        ctx.update(alt_result)
        cnt -= 64
    ctx.update(alt_result[:cnt])

    cnt = pw_len
    while cnt > 0:
        ctx.update(alt_result if cnt & 1 else pw)
        cnt >>= 1

    digest_a = ctx.digest()

    # Sequence "P": password repeated, sized to the password length.
    dp_ctx = hashlib.sha512()
    for _ in range(pw_len):
        dp_ctx.update(pw)
    dp = dp_ctx.digest()
    p_bytes = b""
    cnt = pw_len
    while cnt > 64:
        p_bytes += dp
        cnt -= 64
    p_bytes += dp[:cnt]

    # Sequence "S": salt repeated (16 + first digest byte) times, sized to salt.
    ds_ctx = hashlib.sha512()
    for _ in range(16 + digest_a[0]):
        ds_ctx.update(salt_bytes)
    ds = ds_ctx.digest()
    s_bytes = b""
    cnt = len(salt_bytes)
    while cnt > 64:
        s_bytes += ds
        cnt -= 64
    s_bytes += ds[:cnt]

    # The stretching loop that makes the hash expensive to brute-force.
    c = digest_a
    for i in range(rounds):
        loop = hashlib.sha512()
        loop.update(p_bytes if i & 1 else c)
        if i % 3:
            loop.update(s_bytes)
        if i % 7:
            loop.update(p_bytes)
        loop.update(c if i & 1 else p_bytes)
        c = loop.digest()

    encoded = "".join(_b64_from_24bit(c[b2], c[b1], c[b0], 4) for b2, b1, b0 in _SHA512_CRYPT_ORDER)
    encoded += _b64_from_24bit(0, 0, c[63], 2)
    return f"$6${salt}${encoded}"


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
