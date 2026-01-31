"""Auto-fix suggestions and commands."""

from dataclasses import dataclass

from msai_setup.utils.shell import run_command


@dataclass
class FixResult:
    """Result of applying a fix."""

    success: bool
    message: str
    output: str | None = None


def apply_fix(command: str, *, dry_run: bool = False) -> FixResult:
    """Apply a fix command.

    Args:
        command: The command to run.
        dry_run: If True, just print what would be done.

    Returns:
        FixResult indicating success/failure.
    """
    if dry_run:
        return FixResult(
            success=True,
            message=f"Would run: {command}",
        )

    result = run_command(command)
    if result.success:
        return FixResult(
            success=True,
            message=f"Successfully ran: {command}",
            output=result.output,
        )

    return FixResult(
        success=False,
        message=f"Failed to run: {command}",
        output=result.stderr,
    )


# Common fixes that can be safely auto-applied
SAFE_FIXES: dict[str, str] = {
    "zfs_scrub": "sudo zpool scrub tank",
    "docker_start": "sudo systemctl start docker",
    "libvirtd_start": "sudo systemctl start libvirtd",
    "ollama_start": "sudo systemctl start ollama",
    "tailscale_start": "sudo systemctl start tailscaled",
}


def get_safe_fix(fix_key: str) -> str | None:
    """Get a safe fix command by key.

    Args:
        fix_key: Key identifying the fix.

    Returns:
        Command string or None if not found.
    """
    return SAFE_FIXES.get(fix_key)


def is_safe_fix(command: str) -> bool:
    """Check if a fix command is considered safe to auto-apply.

    Args:
        command: The fix command to check.

    Returns:
        True if the command is in the safe fixes list.
    """
    return command in SAFE_FIXES.values()
