"""Tests for OS profiles (msai_setup.lab.profiles).

Pin the Ubuntu media values each profile derives per-arch to the known
constants, so the default `ubuntu-server` profile keeps producing a
byte-for-byte identical VM to before profiles existed.
"""

from __future__ import annotations

import pytest

from msai_setup.lab.profiles import PROFILES, get_profile

# The Ubuntu 26.04 media constants config.py historically hardcoded per arch.
_ARM = {
    "iso_filename": "ubuntu-26.04-live-server-arm64.iso",
    "iso_base_url": "https://cdimage.ubuntu.com/releases/26.04/release",
    "ostype": "Ubuntu_arm64",
    "platform": "arm",
}
_AMD = {
    "iso_filename": "ubuntu-26.04-live-server-amd64.iso",
    "iso_base_url": "https://releases.ubuntu.com/26.04",
    "ostype": "Ubuntu_64",
    "platform": "x86",
}


@pytest.mark.parametrize("key", ["ubuntu-server", "ubuntu-desktop"])
def test_ubuntu_media_matches_known_constants(key: str) -> None:
    profile = get_profile(key)
    assert profile.iso_filename("arm64") == _ARM["iso_filename"]
    assert profile.iso_base_url("arm64") == _ARM["iso_base_url"]
    assert profile.ostype("arm64") == _ARM["ostype"]
    assert profile.platform("arm64") == _ARM["platform"]
    assert profile.iso_filename("amd64") == _AMD["iso_filename"]
    assert profile.iso_base_url("amd64") == _AMD["iso_base_url"]
    assert profile.ostype("amd64") == _AMD["ostype"]
    assert profile.platform("amd64") == _AMD["platform"]


def test_ubuntu_server_is_plain_headless() -> None:
    profile = get_profile("ubuntu-server")
    assert profile.family == "ubuntu"
    assert profile.unattended == "subiquity"
    assert profile.extra_packages == ()
    assert profile.default_playbooks == ()
    assert profile.is_graphical is False


def test_ubuntu_desktop_has_gui_packages_and_rdp_playbook() -> None:
    profile = get_profile("ubuntu-desktop")
    assert profile.is_graphical is True
    assert "ubuntu-desktop-minimal" in profile.extra_packages
    assert "xrdp" in profile.extra_packages
    assert profile.default_playbooks == ("rdp",)


def test_desktop_playbooks_are_registered_and_runnable() -> None:
    """Every playbook the desktop profile declares must be a known playbook."""
    from msai_setup.lab.apply import KNOWN_PLAYBOOKS

    assert "rdp" in KNOWN_PLAYBOOKS
    for playbook in get_profile("ubuntu-desktop").default_playbooks:
        assert playbook in KNOWN_PLAYBOOKS


def test_ubuntu_desktop_uses_same_iso_as_server() -> None:
    server = get_profile("ubuntu-server")
    desktop = get_profile("ubuntu-desktop")
    for arch in ("arm64", "amd64"):
        assert desktop.iso_filename(arch) == server.iso_filename(arch)
        assert desktop.iso_base_url(arch) == server.iso_base_url(arch)


def test_get_profile_raises_on_unknown() -> None:
    with pytest.raises(ValueError, match="unknown OS profile 'nope'"):
        get_profile("nope")
    # The error should list the valid keys to help the user recover.
    with pytest.raises(ValueError, match="ubuntu-server"):
        get_profile("nope")


def test_registry_registers_both_ubuntu_profiles() -> None:
    assert set(PROFILES) >= {"ubuntu-server", "ubuntu-desktop"}


# --- Fedora profile ---------------------------------------------------------

# Pinned Fedora 44 (build 1.7) Server netinst media, verified 2026-07 against
# the Fedora mirror directory index.
_FED_AMD = {
    "iso_filename": "Fedora-Server-netinst-x86_64-44-1.7.iso",
    "iso_base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/44/Server/x86_64/iso",
    "checksum_filename": "Fedora-Server-44-1.7-x86_64-CHECKSUM",
    "ostype": "Fedora_64",
    "platform": "x86",
}
_FED_ARM = {
    "iso_filename": "Fedora-Server-netinst-aarch64-44-1.7.iso",
    "iso_base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/44/Server/aarch64/iso",
    "checksum_filename": "Fedora-Server-44-1.7-aarch64-CHECKSUM",
    "ostype": "Fedora_arm64",
    "platform": "arm",
}


def test_fedora_profile_is_kickstart_server() -> None:
    profile = get_profile("fedora")
    assert profile.family == "fedora"
    assert profile.unattended == "kickstart"
    assert profile.is_graphical is False
    assert profile.extra_packages == ()
    assert profile.default_playbooks == ()


def test_fedora_media_amd64() -> None:
    p = get_profile("fedora")
    assert p.iso_filename("amd64") == _FED_AMD["iso_filename"]
    assert p.iso_base_url("amd64") == _FED_AMD["iso_base_url"]
    assert p.checksum_filename("amd64") == _FED_AMD["checksum_filename"]
    assert p.ostype("amd64") == _FED_AMD["ostype"]
    assert p.platform("amd64") == _FED_AMD["platform"]


def test_fedora_media_arm64() -> None:
    p = get_profile("fedora")
    assert p.iso_filename("arm64") == _FED_ARM["iso_filename"]
    assert p.iso_base_url("arm64") == _FED_ARM["iso_base_url"]
    assert p.checksum_filename("arm64") == _FED_ARM["checksum_filename"]
    assert p.ostype("arm64") == _FED_ARM["ostype"]
    assert p.platform("arm64") == _FED_ARM["platform"]


def test_fedora_checksum_url_combines_base_and_filename() -> None:
    p = get_profile("fedora")
    assert p.checksum_url("amd64") == f"{_FED_AMD['iso_base_url']}/{_FED_AMD['checksum_filename']}"
    assert p.checksum_url("arm64") == f"{_FED_ARM['iso_base_url']}/{_FED_ARM['checksum_filename']}"


def test_ubuntu_checksum_url_is_sha256sums() -> None:
    p = get_profile("ubuntu-server")
    assert p.checksum_filename("amd64") == "SHA256SUMS"
    assert p.checksum_url("amd64") == "https://releases.ubuntu.com/26.04/SHA256SUMS"
