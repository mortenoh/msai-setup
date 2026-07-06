"""Tests for the JSON state store (msai_setup.lab.state)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from msai_setup.lab import state


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert state.load(tmp_path / "nope.json") == {}


def test_mark_and_is_phase_done_round_trip(tmp_path: Path) -> None:
    sp = tmp_path / "state.json"
    assert state.is_phase_done(sp, "provision") is False
    state.mark_phase_done(sp, "provision", lab_disk_count=6, vm_name="lab")
    assert state.is_phase_done(sp, "provision") is True

    loaded = state.load(sp)
    info = loaded["phases"]["provision"]
    assert info["lab_disk_count"] == 6
    assert info["vm_name"] == "lab"
    assert info["finished_at"].endswith("Z")  # UTC marker, not deprecated utcnow


def test_reset_phase(tmp_path: Path) -> None:
    sp = tmp_path / "state.json"
    state.mark_phase_done(sp, "apply", playbooks=["bootstrap"])
    assert state.is_phase_done(sp, "apply") is True
    state.reset_phase(sp, "apply")
    assert state.is_phase_done(sp, "apply") is False


def test_multiple_phases_coexist(tmp_path: Path) -> None:
    sp = tmp_path / "state.json"
    state.mark_phase_done(sp, "provision")
    state.mark_phase_done(sp, "apply")
    loaded = state.load(sp)
    assert set(loaded["phases"]) == {"provision", "apply"}


def test_save_is_atomic_no_partial_left_behind(tmp_path: Path) -> None:
    """Regression for L7: save writes via a .partial temp then renames."""
    sp = tmp_path / "state.json"
    state.save(sp, {"phases": {}})
    # After a successful save, no stray .partial file should remain.
    assert not (tmp_path / "state.json.partial").exists()
    assert sp.exists()


def test_save_interruption_leaves_previous_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the write crashes mid-way, the original state file is untouched."""
    sp = tmp_path / "state.json"
    state.save(sp, {"phases": {"provision": {"finished_at": "2026-01-01T00:00:00Z"}}})
    original = sp.read_text()

    # Simulate a crash during the temp-file write.
    real_write_text = Path.write_text

    def _boom(self: Path, *args: object, **kwargs: object) -> int:
        if self.name.endswith(".partial"):
            raise OSError("disk full")
        return real_write_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "write_text", _boom)
    with pytest.raises(OSError, match="disk full"):
        state.save(sp, {"phases": {"provision": {"finished_at": "changed"}}})

    # Original file intact and still valid JSON; no partial left behind.
    assert sp.read_text() == original
    assert json.loads(sp.read_text())["phases"]["provision"]["finished_at"] == "2026-01-01T00:00:00Z"
    assert not (tmp_path / "state.json.partial").exists()
