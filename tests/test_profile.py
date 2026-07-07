"""Tests for host profile resolution and category expectations."""

from msai_setup.doctor import profile as profile_mod
from msai_setup.doctor.checks import Category
from msai_setup.doctor.profile import (
    Profile,
    category_expected,
    resolve_profile,
    set_profile,
)


def test_server_expects_everything() -> None:
    """On the server profile, every category is expected."""
    for category in Category:
        assert category_expected(Profile.SERVER, category) is True


def test_desktop_softens_infrastructure_categories() -> None:
    """ZFS and KVM are not expected on desktop; GPU/AI still are."""
    assert category_expected(Profile.DESKTOP, Category.ZFS) is False
    assert category_expected(Profile.DESKTOP, Category.KVM) is False
    assert category_expected(Profile.DESKTOP, Category.GPU) is True
    assert category_expected(Profile.DESKTOP, Category.SYSTEM) is True


def test_env_var_takes_precedence(monkeypatch) -> None:
    """MSAI_PROFILE overrides all other sources."""
    monkeypatch.setenv("MSAI_PROFILE", "desktop")
    profile, source = resolve_profile()
    assert profile is Profile.DESKTOP
    assert source == "MSAI_PROFILE"


def test_bad_env_var_falls_through(monkeypatch, tmp_path) -> None:
    """An invalid MSAI_PROFILE is ignored in favor of the config file."""
    monkeypatch.setenv("MSAI_PROFILE", "nonsense")
    monkeypatch.setattr(profile_mod, "CONFIG_PATH", tmp_path / "profile")
    set_profile(Profile.SERVER)
    profile, source = resolve_profile()
    assert profile is Profile.SERVER
    assert source == str(tmp_path / "profile")


def test_set_and_read_config(monkeypatch, tmp_path) -> None:
    """set_profile persists a value that resolve_profile reads back."""
    monkeypatch.delenv("MSAI_PROFILE", raising=False)
    monkeypatch.setattr(profile_mod, "CONFIG_PATH", tmp_path / "msai" / "profile")
    path = set_profile(Profile.DESKTOP)
    assert path.exists()
    profile, _ = resolve_profile()
    assert profile is Profile.DESKTOP
