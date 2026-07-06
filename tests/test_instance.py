"""Tests for lab instance discovery + name validation (msai_setup.lab.instance)."""

from __future__ import annotations

from pathlib import Path

import pytest

from msai_setup.lab import instance


@pytest.fixture
def target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point instance.py at an isolated target/ dir via $TARGET_DIR."""
    t = tmp_path / "target"
    t.mkdir()
    monkeypatch.setenv("TARGET_DIR", str(t))
    return t


@pytest.mark.parametrize("name", ["lab", "test", "ms-s1-max-lab", "a", "lab2", "a" * 31])
def test_validate_name_accepts_valid(name: str) -> None:
    instance.validate_name(name)  # should not raise


@pytest.mark.parametrize(
    "name",
    [
        "",  # empty
        "Lab",  # uppercase
        "-lab",  # leading hyphen
        "a" * 32,  # too long (max 31)
        "lab_2",  # underscore not allowed
        "lab/evil",  # path separator
        "lab name",  # space
        "../escape",  # traversal
    ],
)
def test_validate_name_rejects_invalid(name: str) -> None:
    with pytest.raises(ValueError):
        instance.validate_name(name)


def test_list_instances_empty(target: Path) -> None:
    assert instance.list_instances() == []


def test_list_instances_discovers_state_and_disks(target: Path) -> None:
    # Instance "alpha" has both a state file and a primary disk.
    (target / "alpha-state.json").write_text("{}")
    (target / "alpha-primary.vdi").write_text("stub")
    # Instance "beta" has only a disk (provisioned but no state yet).
    (target / "beta-primary.vdi").write_text("stub")
    # Instance "gamma" has only a state file.
    (target / "gamma-state.json").write_text("{}")

    by_name = {i.name: i for i in instance.list_instances()}
    assert set(by_name) == {"alpha", "beta", "gamma"}

    assert by_name["alpha"].has_state and by_name["alpha"].has_disks
    assert by_name["beta"].has_disks and not by_name["beta"].has_state
    assert by_name["gamma"].has_state and not by_name["gamma"].has_disks


def test_current_pointer_round_trip(target: Path) -> None:
    assert instance.get_current() is None
    instance.set_current("alpha")
    assert instance.get_current() == "alpha"
    instance.clear_current()
    assert instance.get_current() is None


def test_list_instances_marks_current(target: Path) -> None:
    (target / "alpha-state.json").write_text("{}")
    (target / "beta-state.json").write_text("{}")
    instance.set_current("beta")
    by_name = {i.name: i for i in instance.list_instances()}
    assert by_name["beta"].is_current
    assert not by_name["alpha"].is_current


def test_set_current_validates_name(target: Path) -> None:
    with pytest.raises(ValueError):
        instance.set_current("BAD/NAME")


def test_require_current_raises_when_unset(target: Path) -> None:
    with pytest.raises(SystemExit):
        instance.require_current()
