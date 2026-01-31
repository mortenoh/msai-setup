"""Rich console output formatting utilities."""

from enum import Enum

from rich.console import Console
from rich.theme import Theme

# Custom theme for consistent styling
custom_theme = Theme(
    {
        "ok": "green",
        "warn": "yellow",
        "fail": "red bold",
        "info": "blue",
        "header": "bold cyan",
        "dim": "dim",
    }
)

console = Console(theme=custom_theme)


class CheckStatus(Enum):
    """Status of a health check."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


STATUS_SYMBOLS = {
    CheckStatus.OK: ("[OK]", "ok"),
    CheckStatus.WARN: ("[WARN]", "warn"),
    CheckStatus.FAIL: ("[FAIL]", "fail"),
    CheckStatus.SKIP: ("[SKIP]", "dim"),
}


def print_header(title: str) -> None:
    """Print a section header."""
    console.print(f"\n[header]{title}[/header]")


def print_status(
    status: CheckStatus,
    message: str,
    *,
    detail: str | None = None,
    fix: str | None = None,
) -> None:
    """Print a status line with optional details and fix suggestion.

    Args:
        status: The check status (OK, WARN, FAIL, SKIP).
        message: The main status message.
        detail: Optional detail/explanation line.
        fix: Optional fix command suggestion.
    """
    symbol, style = STATUS_SYMBOLS[status]
    console.print(f"  [{style}]{symbol}[/{style}] {message}")

    if detail:
        console.print(f"         [dim]{detail}[/dim]")

    if fix:
        console.print(f"         Run: [info]{fix}[/info]")


def print_summary(passed: int, warnings: int, failed: int) -> None:
    """Print a summary of check results."""
    parts: list[str] = []
    if passed:
        parts.append(f"[ok]{passed} passed[/ok]")
    if warnings:
        parts.append(f"[warn]{warnings} warning{'s' if warnings != 1 else ''}[/warn]")
    if failed:
        parts.append(f"[fail]{failed} failed[/fail]")

    console.print(f"\nSummary: {', '.join(parts)}")
