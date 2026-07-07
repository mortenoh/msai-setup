"""Auto-fix suggestions and commands."""

from dataclasses import dataclass

from msai_setup.utils.shell import run_interactive


@dataclass
class FixResult:
    """Result of applying a fix."""

    success: bool
    message: str
    output: str | None = None


def apply_fix(command: str, *, dry_run: bool = False) -> FixResult:
    """Apply a fix command.

    Runs through a shell with inherited stdio so pipes, redirects and sudo
    password prompts work and the user sees output live.

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

    code = run_interactive(command)
    if code == 0:
        return FixResult(
            success=True,
            message=f"Applied: {command}",
        )

    return FixResult(
        success=False,
        message=f"Failed (exit {code}): {command}",
    )


# Fixes that are safe to auto-apply with --yes: idempotent, non-destructive,
# no package installation and no data changes. Install-type or state-changing
# fixes are deliberately excluded so they always require an explicit prompt.
SAFE_FIXES: dict[str, str] = {
    "docker_start": "sudo systemctl start docker",
    "libvirtd_start": "sudo systemctl start libvirtd",
    "ollama_start": "sudo systemctl start ollama",
    "tailscaled_start": "sudo systemctl start tailscaled",
    "audio_powersave": (
        "echo 'options snd_hda_intel power_save=0 power_save_controller=N' "
        "| sudo tee /etc/modprobe.d/audio-disable-powersave.conf"
    ),
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
