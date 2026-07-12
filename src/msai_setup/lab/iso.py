"""Ubuntu ISO download + SHA256 verification + autoinstall remastering."""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)


def _sha256_file(path: Path) -> str:
    """Compute the SHA256 of a file as a hex string."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_text(url: str) -> str:
    """Fetch `url` and return its body decoded as UTF-8 text."""
    with urllib.request.urlopen(url, timeout=30) as resp:
        body: bytes = resp.read()
    return body.decode("utf-8")


# Fedora/BSD-style checksum line: `SHA256 (<file>) = <hex>`. Ubuntu/coreutils
# uses the other form (`<hex> *<file>` / `<hex>  <file>`), parsed below.
_BSD_SHA256_RE = re.compile(r"^SHA256\s*\((?P<name>.+?)\)\s*=\s*(?P<hex>[0-9a-fA-F]{64})$")


def _parse_expected_sha256(body: str, filename: str) -> str:
    """Extract the SHA256 for `filename` from a checksum manifest body.

    Handles BOTH manifest formats by matching the exact target filename:
      - Ubuntu / coreutils:  ``<hex> *<file>``  or  ``<hex>  <file>``
      - Fedora / BSD-style:  ``SHA256 (<file>) = <hex>``
    """
    for raw in body.splitlines():
        line = raw.strip()
        bsd = _BSD_SHA256_RE.match(line)
        if bsd is not None and bsd.group("name") == filename:
            return bsd.group("hex")
        # coreutils form: hash then filename, the latter maybe `*`-prefixed
        # (binary mode). Compare the whole token, not a substring.
        parts = line.split()
        if len(parts) >= 2 and parts[1].lstrip("*") == filename:
            return parts[0]
    raise RuntimeError(f"SHA256 entry for {filename} not found")


def _fetch_expected_sha256(sha_url: str, filename: str) -> str:
    """Fetch a checksum manifest and extract the SHA256 for `filename`."""
    body = _fetch_text(sha_url)
    try:
        return _parse_expected_sha256(body, filename)
    except RuntimeError as e:
        raise RuntimeError(f"{e} in {sha_url}") from e


def _download(url: str, dest: Path) -> None:
    """Stream a URL to a file with progress reporting via logging."""
    log.info("downloading %s -> %s", url, dest)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with urllib.request.urlopen(url, timeout=60) as resp, tmp.open("wb") as out:
        total = int(resp.headers.get("Content-Length", "0"))
        bytes_read = 0
        last_report = 0
        chunk_size = 1024 * 1024
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            bytes_read += len(chunk)
            if total and bytes_read - last_report >= 50 * 1024 * 1024:
                pct = (bytes_read / total) * 100
                log.info("  %.1f%% (%d / %d MiB)", pct, bytes_read >> 20, total >> 20)
                last_report = bytes_read
    tmp.rename(dest)
    log.info("download complete: %s", dest)


# Match `linux<ws>/casper/<name>vmlinuz<args>---` (covers plain vmlinuz and the
# HWE `hwe-vmlinuz` variant) so we can splice `autoinstall` in before the `---`.
_AUTOINSTALL_PATTERN = re.compile(
    r"(linux\s+/casper/[\w.-]*vmlinuz)(\s+)(.*?---)",
    re.MULTILINE,
)


def _inject_autoinstall(grub_cfg: str) -> tuple[str, int]:
    """Return (modified grub.cfg, count) with `autoinstall` added to kernel lines.

    Appends the `autoinstall` kernel parameter after each `/casper/*vmlinuz`
    filename and before the `---` separator. The count is the number of GRUB
    menu entries patched; callers should treat a count of 0 as an error.
    """
    return _AUTOINSTALL_PATTERN.subn(r"\1\2autoinstall \3", grub_cfg)


def remaster_iso_for_autoinstall(src: Path, dst: Path) -> None:
    """Copy `src` ISO to `dst` with `autoinstall` injected into the GRUB cmdline.

    Ubuntu's Subiquity installer only runs unattended when its kernel sees the
    `autoinstall` argument. The stock install ISO doesn't have it. We extract
    `boot/grub/grub.cfg`, append `autoinstall` before the `---` separator on
    every `linux /casper/vmlinuz...` and `linux /casper/hwe-vmlinuz...` line,
    and write a new bootable ISO.

    Idempotent: skips work if `dst` already exists and is newer than `src`.
    """
    if shutil.which("xorriso") is None:
        raise SystemExit("xorriso not on PATH (brew install xorriso)")

    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        log.info("remastered ISO already current: %s", dst)
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        extracted = td_path / "grub.cfg"

        log.info("extracting grub.cfg from %s", src)
        subprocess.run(
            [
                "xorriso", "-osirrox", "on",
                "-indev", str(src),
                "-extract", "/boot/grub/grub.cfg", str(extracted),
            ],
            check=True, capture_output=True, text=True,
        )

        # ISO9660 preserves read-only perms; allow writing.
        extracted.chmod(0o644)
        original = extracted.read_text()
        # Inject `autoinstall` after each kernel filename, before the `---`.
        modified, n = _inject_autoinstall(original)
        if n == 0:
            raise RuntimeError(
                "couldn't find /casper/vmlinuz pattern in grub.cfg; "
                "ISO layout may have changed:\n" + original[:400]
            )
        log.info("patched %d GRUB menu entries with autoinstall", n)
        extracted.write_text(modified)

        log.info("writing remastered ISO to %s", dst)
        subprocess.run(
            [
                "xorriso",
                "-indev", str(src),
                "-outdev", str(dst),
                "-boot_image", "any", "keep",
                "-map", str(extracted), "/boot/grub/grub.cfg",
                "-commit",
            ],
            check=True, capture_output=True, text=True,
        )
    log.info("remastered ISO ready: %s (%.1f MiB)",
             dst, dst.stat().st_size / (1024 * 1024))


def ensure_iso(iso_path: Path, *, url: str, sha_url: str) -> None:
    """Download the ISO if missing, then verify its SHA256.

    Idempotent: on a second run, only re-checks the checksum.
    Raises RuntimeError on checksum mismatch.
    """
    iso_path.parent.mkdir(parents=True, exist_ok=True)

    expected = _fetch_expected_sha256(sha_url, iso_path.name)
    log.info("expected SHA256: %s", expected)

    if not iso_path.exists():
        _download(url, iso_path)

    log.info("verifying SHA256 of %s", iso_path)
    actual = _sha256_file(iso_path)
    if actual != expected:
        iso_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"ISO checksum mismatch — file deleted.\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}\n"
            f"  url:      {url}"
        )
    log.info("checksum OK")
