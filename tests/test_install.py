"""Tests for the bootstrap manifest and runner."""

import pytest

from msai_setup.install.manifest import (
    Component,
    ManifestError,
    load_manifest,
)
from msai_setup.install.runner import bootstrap, install_commands


def test_manifest_loads_and_is_ordered() -> None:
    """The shipped manifest parses and docker comes first (install order)."""
    manifest = load_manifest()
    assert "docker" in manifest
    assert "rocm" in manifest
    assert list(manifest)[0] == "docker"


def test_manifest_methods_valid() -> None:
    """Every component uses a supported method with its required fields."""
    for name, component in load_manifest().items():
        assert component.method in {"apt", "curl_sh", "script"}, name
        if component.method == "apt":
            assert component.packages, name
        elif component.method == "curl_sh":
            assert component.url, name
        else:
            assert component.commands, name


def test_install_commands_apt() -> None:
    comp = Component(method="apt", packages=["a", "b"], post=["echo done"])
    assert install_commands(comp) == ["sudo apt-get install -y a b", "echo done"]


def test_install_commands_curl_sh() -> None:
    comp = Component(method="curl_sh", url="https://x/i.sh")
    assert install_commands(comp) == ["curl -fsSL https://x/i.sh | sh"]


def test_install_commands_script() -> None:
    comp = Component(method="script", commands=["a", "b"], post=["c"])
    assert install_commands(comp) == ["a", "b", "c"]


def test_install_commands_curl_sh_with_args() -> None:
    comp = Component(method="curl_sh", url="https://x/i.sh", shell="bash", extra_args=["-y"])
    assert install_commands(comp) == ["curl -fsSL https://x/i.sh | bash -s -- -y"]


def test_rejects_unknown_method(tmp_path) -> None:
    bad = tmp_path / "m.toml"
    bad.write_text('[thing]\nmethod = "wat"\n')
    with pytest.raises(ManifestError):
        load_manifest(bad)


def test_rejects_apt_without_packages(tmp_path) -> None:
    bad = tmp_path / "m.toml"
    bad.write_text('[thing]\nmethod = "apt"\n')
    with pytest.raises(ManifestError):
        load_manifest(bad)


def test_rejects_unknown_key(tmp_path) -> None:
    bad = tmp_path / "m.toml"
    bad.write_text('[thing]\nmethod = "apt"\npackages = ["x"]\nbogus = 1\n')
    with pytest.raises(ManifestError):
        load_manifest(bad)


def test_dry_run_never_executes() -> None:
    """A dry run only ever plans or skips; it never installs or fails."""
    outcomes = bootstrap(dry_run=True)
    assert outcomes
    assert all(o.status in {"planned", "skipped"} for o in outcomes)


def test_unknown_component_exits() -> None:
    """Requesting an unknown component is a clean error, not a crash."""
    import typer

    with pytest.raises(typer.Exit):
        bootstrap(["does-not-exist"], dry_run=True)
