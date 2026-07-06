"""Tests for ISO helpers (msai_setup.lab.iso): SHA256SUMS parsing + GRUB patch."""

from __future__ import annotations

import pytest

from msai_setup.lab import iso

SAMPLE_SHA256SUMS = """\
1111111111111111111111111111111111111111111111111111111111111111 *ubuntu-26.04-live-server-amd64.iso
2222222222222222222222222222222222222222222222222222222222222222 *ubuntu-26.04-live-server-arm64.iso
3333333333333333333333333333333333333333333333333333333333333333 *ubuntu-26.04-desktop-amd64.iso
"""


def test_parse_sha256sums_amd64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(iso, "_fetch_text", lambda _url: SAMPLE_SHA256SUMS)
    got = iso._fetch_expected_sha256("http://example/SHA256SUMS", "ubuntu-26.04-live-server-amd64.iso")
    assert got == "1" * 64


def test_parse_sha256sums_arm64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(iso, "_fetch_text", lambda _url: SAMPLE_SHA256SUMS)
    got = iso._fetch_expected_sha256("http://example/SHA256SUMS", "ubuntu-26.04-live-server-arm64.iso")
    assert got == "2" * 64


def test_parse_sha256sums_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(iso, "_fetch_text", lambda _url: SAMPLE_SHA256SUMS)
    with pytest.raises(RuntimeError, match="not found"):
        iso._fetch_expected_sha256("http://example/SHA256SUMS", "does-not-exist.iso")


def test_parse_sha256sums_ignores_substring_collisions(monkeypatch: pytest.MonkeyPatch) -> None:
    # `server-amd64.iso` is a suffix of the full name; the parser must match the
    # exact `*<filename>` token, not a substring, so it returns the right hash.
    monkeypatch.setattr(iso, "_fetch_text", lambda _url: SAMPLE_SHA256SUMS)
    got = iso._fetch_expected_sha256("http://example/SHA256SUMS", "ubuntu-26.04-desktop-amd64.iso")
    assert got == "3" * 64


PLAIN_GRUB = """\
menuentry "Try or Install Ubuntu Server" {
	set gfxpayload=keep
	linux	/casper/vmlinuz  ---
	initrd	/casper/initrd
}
"""

HWE_GRUB = """\
menuentry "Ubuntu Server (HWE kernel)" {
	set gfxpayload=keep
	linux	/casper/hwe-vmlinuz  quiet ---
	initrd	/casper/hwe-initrd
}
"""


def test_inject_autoinstall_plain_vmlinuz() -> None:
    out, n = iso._inject_autoinstall(PLAIN_GRUB)
    assert n == 1
    assert "linux\t/casper/vmlinuz  autoinstall ---" in out
    # initrd line untouched.
    assert "/casper/initrd" in out
    assert out.count("autoinstall") == 1


def test_inject_autoinstall_hwe_vmlinuz() -> None:
    out, n = iso._inject_autoinstall(HWE_GRUB)
    assert n == 1
    # `autoinstall` is spliced in right after the kernel filename, ahead of
    # the pre-existing `quiet` arg, and before the `---` separator.
    assert "/casper/hwe-vmlinuz  autoinstall quiet ---" in out
    assert "/casper/hwe-initrd" in out


def test_inject_autoinstall_multiple_entries() -> None:
    out, n = iso._inject_autoinstall(PLAIN_GRUB + HWE_GRUB)
    assert n == 2
    assert out.count("autoinstall") == 2


def test_inject_autoinstall_no_match_returns_zero() -> None:
    out, n = iso._inject_autoinstall("menuentry {\n\tsomething unrelated\n}\n")
    assert n == 0
    assert "autoinstall" not in out
