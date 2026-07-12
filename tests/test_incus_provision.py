"""Tests for the Incus provider dispatch (msai_setup.lab.incus_provision) and
the provider routing in provision.main — all without touching real tools.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from msai_setup.lab import incus_provision, provision
from msai_setup.lab.config import LabConfig


def _cfg(os_profile: str, tmp_path: Path, *, provider: str = "incus") -> LabConfig:
    return LabConfig(
        vm_name="lab",
        vm_hostname="lab.local",
        os_profile=os_profile,
        provider=provider,
        target_dir=tmp_path,
    )


def test_flow_ubuntu(tmp_path: Path) -> None:
    assert incus_provision._flow_for(_cfg("ubuntu-server", tmp_path)) == "ubuntu-launch"
    assert incus_provision._flow_for(_cfg("ubuntu-desktop", tmp_path)) == "ubuntu-launch"


def test_flow_fedora(tmp_path: Path) -> None:
    assert incus_provision._flow_for(_cfg("fedora", tmp_path)) == "fedora-iso"


def test_flow_windows(tmp_path: Path) -> None:
    assert incus_provision._flow_for(_cfg("windows-11", tmp_path)) == "windows-iso"
    assert incus_provision._flow_for(_cfg("windows-10", tmp_path)) == "windows-iso"


def test_ubuntu_image_default_and_override(tmp_path: Path) -> None:
    cfg = _cfg("ubuntu-server", tmp_path)
    assert incus_provision._ubuntu_image(cfg) == f"images:ubuntu/{cfg.ubuntu_release}"
    cfg2 = LabConfig(
        vm_name="lab", vm_hostname="lab.local", os_profile="ubuntu-server",
        provider="incus", target_dir=tmp_path, incus_image="images:ubuntu/noble",
    )
    assert incus_provision._ubuntu_image(cfg2) == "images:ubuntu/noble"


def test_provision_main_routes_to_incus(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    called: list[str] = []

    cfg = _cfg("ubuntu-server", tmp_path, provider="incus")
    monkeypatch.setattr(provision, "load_config", lambda: cfg)

    def fake_incus_provision(c: LabConfig) -> None:
        called.append("incus")

    monkeypatch.setattr(incus_provision, "provision", fake_incus_provision)
    provision.main()
    assert called == ["incus"]


def test_provision_main_vbox_does_not_route_to_incus(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A vbox cfg must NOT call the incus provider. We stop the VBox path early by
    # marking the provision phase already-done so main() returns without tools.
    from msai_setup.lab import state

    cfg = _cfg("ubuntu-server", tmp_path, provider="vbox")
    cfg.target_dir.mkdir(parents=True, exist_ok=True)
    state.mark_phase_done(cfg.state_path, "provision", vm_name=cfg.vm_name)
    monkeypatch.setattr(provision, "load_config", lambda: cfg)

    def boom(c: LabConfig) -> None:
        raise AssertionError("vbox provider must not call the incus provider")

    monkeypatch.setattr(incus_provision, "provision", boom)
    provision.main()  # returns via the already-done short-circuit, no incus call
