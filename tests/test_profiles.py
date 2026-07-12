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
