"""Tests for LabConfig env resolution (msai_setup.lab.config).

Config field defaults are evaluated at import time (the established pattern in
config.py), so env-honouring tests reload the module with the env set. The
`reset_config` fixture restores a clean import afterwards so other tests aren't
affected.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from msai_setup.lab import config as config_mod


@pytest.fixture
def reset_config() -> Iterator[None]:
    """Reload config with a pristine env after the test, undoing any reload.

    Scrub the env vars these tests set before reloading, so the restored module
    has clean defaults regardless of fixture-teardown ordering vs monkeypatch.
    """
    yield
    for key in ("LAB_OS", "LAB_HEADLESS", "TARGET_DIR"):
        os.environ.pop(key, None)
    importlib.reload(config_mod)


def _reload_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **env: str) -> None:
    """Reload config with TARGET_DIR pointed at tmp_path plus the given env."""
    monkeypatch.setenv("TARGET_DIR", str(tmp_path))
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    importlib.reload(config_mod)


def test_defaults_are_server_and_visible(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reset_config: None
) -> None:
    monkeypatch.delenv("LAB_OS", raising=False)
    monkeypatch.delenv("LAB_HEADLESS", raising=False)
    _reload_config(monkeypatch, tmp_path)
    cfg = config_mod.load_config(vm_name="lab")
    assert cfg.os_profile == "ubuntu-server"
    # Visible GUI by default so a stuck installer can be taken over by hand.
    assert cfg.headless is False


def test_default_profile_media_unchanged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reset_config: None
) -> None:
    monkeypatch.delenv("LAB_OS", raising=False)
    _reload_config(monkeypatch, tmp_path)
    cfg = config_mod.load_config(vm_name="lab")
    # The default profile exposes server (empty) extras/playbooks.
    assert cfg.extra_packages == ()
    assert cfg.default_playbooks == ()


def test_lab_os_env_honoured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reset_config: None
) -> None:
    _reload_config(monkeypatch, tmp_path, LAB_OS="ubuntu-desktop")
    cfg = config_mod.load_config(vm_name="lab")
    assert cfg.os_profile == "ubuntu-desktop"
    assert "xrdp" in cfg.extra_packages
    assert cfg.default_playbooks == ("rdp",)


def test_lab_headless_env_honoured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reset_config: None
) -> None:
    _reload_config(monkeypatch, tmp_path, LAB_HEADLESS="1")
    cfg = config_mod.load_config(vm_name="lab")
    assert cfg.headless is True


def test_unknown_lab_os_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reset_config: None
) -> None:
    _reload_config(monkeypatch, tmp_path, LAB_OS="fedora-server")
    with pytest.raises(ValueError, match="unknown OS profile 'fedora-server'"):
        config_mod.load_config(vm_name="lab")


def test_env_bool_parsing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reset_config: None
) -> None:
    _reload_config(monkeypatch, tmp_path)
    assert config_mod._env_bool("MISSING_KEY", True) is True
    for truthy in ("true", "1", "yes", "on", "ON", "Yes"):
        monkeypatch.setenv("SOME_BOOL", truthy)
        assert config_mod._env_bool("SOME_BOOL", False) is True
    for falsy in ("false", "0", "no", "off", ""):
        monkeypatch.setenv("SOME_BOOL", falsy)
        assert config_mod._env_bool("SOME_BOOL", True) is False
