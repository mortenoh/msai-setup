"""Tests for the doctor fix-application layer."""

from msai_setup.doctor.checks import CheckResult, registry
from msai_setup.doctor.fixes import (
    SAFE_FIXES,
    apply_fix,
    get_safe_fix,
    is_safe_fix,
)
from msai_setup.utils.shell import run_interactive


def test_every_registered_check_returns_a_checkresult() -> None:
    """Guard against a decorator landing on a helper instead of a check."""
    for _category, check in registry.get_checks():
        result = check.run()
        assert isinstance(result, CheckResult), f"{check.name} returned {type(result)}"


def test_run_interactive_success() -> None:
    """A shell command that exits 0 returns 0."""
    assert run_interactive("true") == 0


def test_run_interactive_failure() -> None:
    """A shell command that exits non-zero propagates its code."""
    assert run_interactive("false") == 1


def test_run_interactive_supports_pipes() -> None:
    """Pipes work (run_command's shlex.split would have broken this)."""
    assert run_interactive("echo hi | grep -q hi") == 0


def test_apply_fix_dry_run_does_not_execute() -> None:
    """Dry run reports intent without running anything."""
    result = apply_fix("false", dry_run=True)
    assert result.success is True
    assert "Would run" in result.message


def test_apply_fix_runs_command() -> None:
    """A real (harmless) fix is executed and reported as applied."""
    assert apply_fix("true").success is True


def test_apply_fix_reports_failure() -> None:
    """A failing fix is reported as not applied, with the exit code."""
    result = apply_fix("false")
    assert result.success is False
    assert "exit 1" in result.message


def test_is_safe_fix_recognizes_registered_fixes() -> None:
    """Every registered safe fix is classified as safe."""
    for command in SAFE_FIXES.values():
        assert is_safe_fix(command) is True


def test_is_safe_fix_rejects_unknown_command() -> None:
    """An install-type command is not auto-safe."""
    assert is_safe_fix("sudo apt install rocm-libs") is False


def test_get_safe_fix_lookup() -> None:
    """Known keys resolve; unknown keys return None."""
    assert get_safe_fix("docker_start") == "sudo systemctl start docker"
    assert get_safe_fix("nonexistent") is None
