"""Subprocess helpers for running shell commands."""

import shlex
import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a shell command execution."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """Return True if command succeeded."""
        return self.returncode == 0

    @property
    def output(self) -> str:
        """Return stdout, stripped of whitespace."""
        return self.stdout.strip()


def run_command(
    cmd: str | list[str],
    *,
    check: bool = False,
    timeout: float | None = 30.0,
    capture: bool = True,
) -> CommandResult:
    """Run a shell command and return the result.

    Args:
        cmd: Command to run, either as string or list of arguments.
        check: If True, raise CalledProcessError on non-zero exit.
        timeout: Timeout in seconds, or None for no timeout.
        capture: If True, capture stdout/stderr. If False, let them pass through.

    Returns:
        CommandResult with returncode, stdout, and stderr.

    Raises:
        subprocess.CalledProcessError: If check=True and command fails.
        subprocess.TimeoutExpired: If command exceeds timeout.
    """
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = list(cmd)

    try:
        result = subprocess.run(
            args,
            capture_output=capture,
            text=True,
            timeout=timeout,
            check=check,
        )
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout if capture else "",
            stderr=result.stderr if capture else "",
        )
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return CommandResult(
            returncode=e.returncode,
            stdout=e.stdout or "",
            stderr=e.stderr or "",
        )
    except FileNotFoundError:
        return CommandResult(
            returncode=127,
            stdout="",
            stderr=f"Command not found: {args[0]}",
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
        )


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    result = run_command(f"which {cmd}")
    return result.success


def get_systemd_status(unit: str) -> str:
    """Get the status of a systemd unit.

    Returns:
        Status string: 'active', 'inactive', 'failed', or 'not-found'.
    """
    result = run_command(f"systemctl is-active {unit}")
    if result.success:
        return result.output
    if "could not be found" in result.stderr.lower():
        return "not-found"
    return result.output or "unknown"


def is_service_running(unit: str) -> bool:
    """Check if a systemd service is running."""
    return get_systemd_status(unit) == "active"
