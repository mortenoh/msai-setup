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
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _fetch_expected_sha256(sha_url: str, filename: str) -> str:
    """Extract the SHA256 for the given ISO filename from a SHA256SUMS body."""
    body = _fetch_text(sha_url)
    needle = f"*{filename}"
    for line in body.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == needle:
            return parts[0]
    raise RuntimeError(f"SHA256 entry for {filename} not found in {sha_url}")


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
        # Match the pattern: `linux<whitespace>/casper/<name>vmlinuz<args>---`
        pattern = re.compile(
            r"(linux\s+/casper/[\w.-]*vmlinuz)(\s+)(.*?---)",
            re.MULTILINE,
        )
        modified, n = pattern.subn(r"\1\2autoinstall \3", original)
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
