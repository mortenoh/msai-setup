"""Tests for the provision install-media dispatch (msai_setup.lab.provision).

The dispatch (`_prepare_install_media`) is deliberately free of VBox calls so it
can be unit-tested: we stub the per-family media builders and assert the right
one is chosen for the profile's `unattended` mechanism.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from msai_setup.lab import profiles, provision
from msai_setup.lab.config import LabConfig
from msai_setup.lab.profiles import OSProfile


def _cfg(os_profile: str, tmp_path: Path) -> LabConfig:
    return LabConfig(
        vm_name="lab",
        vm_hostname="lab.local",
        os_profile=os_profile,
        target_dir=tmp_path,
    )


def _install_recorders(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    """Stub both per-family media builders; return the list they record into."""
    called: list[str] = []

    def fake_ubuntu(c: LabConfig, k: str) -> tuple[Path, Path]:
        called.append("ubuntu")
        return Path("boot"), Path("seed")

    def fake_fedora(c: LabConfig, k: str) -> tuple[Path, Path]:
        called.append("fedora")
        return Path("boot"), Path("seed")

    monkeypatch.setattr(provision, "_prepare_ubuntu_media", fake_ubuntu)
    monkeypatch.setattr(provision, "_prepare_fedora_media", fake_fedora)
    return called


def test_dispatch_selects_subiquity_for_ubuntu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    called = _install_recorders(monkeypatch)
    boot, seed = provision._prepare_install_media(_cfg("ubuntu-server", tmp_path), "ssh-key")
    assert called == ["ubuntu"]
    assert (boot, seed) == (Path("boot"), Path("seed"))


def test_dispatch_selects_kickstart_for_fedora(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    called = _install_recorders(monkeypatch)
    provision._prepare_install_media(_cfg("fedora", tmp_path), "ssh-key")
    assert called == ["fedora"]


def test_dispatch_rejects_unknown_mechanism(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Register a throwaway profile with an unimplemented install mechanism.
    bogus = OSProfile(
        key="bogus",
        display_name="Bogus",
        family="bogus",
        unattended="autounattend",
        extra_packages=(),
        default_playbooks=(),
        is_graphical=False,
    )
    monkeypatch.setitem(profiles.PROFILES, "bogus", bogus)
    with pytest.raises(SystemExit, match="unsupported install mechanism"):
        provision._prepare_install_media(_cfg("bogus", tmp_path), "ssh-key")
