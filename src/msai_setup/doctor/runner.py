"""Check orchestration and reporting."""

import typer

from msai_setup.doctor.checks import Category, CheckResult, registry
from msai_setup.doctor.fixes import apply_fix, is_safe_fix
from msai_setup.utils.formatting import (
    CheckStatus,
    console,
    print_header,
    print_status,
    print_summary,
)

_FIXABLE = (CheckStatus.WARN, CheckStatus.FAIL)


def _maybe_apply(result: CheckResult, *, assume_yes: bool) -> None:
    """Offer to apply a check's fix, honoring safe-vs-prompt policy."""
    if not result.fix or result.status not in _FIXABLE:
        return

    safe = is_safe_fix(result.fix)
    if assume_yes and safe:
        console.print(f"         [info]applying:[/info] {result.fix}")
        outcome = apply_fix(result.fix)
        style = "ok" if outcome.success else "fail"
        console.print(f"         [{style}]{outcome.message}[/{style}]")
        return

    label = "Apply this fix?" if safe else "Apply this fix? (installs/changes state)"
    if typer.confirm(f"         {label}", default=safe):
        outcome = apply_fix(result.fix)
        style = "ok" if outcome.success else "fail"
        console.print(f"         [{style}]{outcome.message}[/{style}]")


def run_doctor(
    categories: list[Category] | None = None,
    *,
    fix: bool = False,
    apply: bool = False,
    assume_yes: bool = False,
) -> tuple[int, int, int]:
    """Run health checks and display results.

    Args:
        categories: Categories to check, or None for all.
        fix: If True, display fix commands for issues.
        apply: If True, offer to run each fix (safe fixes auto-apply with
            assume_yes; install/state-changing fixes always prompt).
        assume_yes: If True, auto-apply safe fixes without prompting.

    Returns:
        Tuple of (passed, warnings, failed) counts.
    """
    console.print("\n[header]MS-S1 MAX Health Check[/header]")
    console.print("[dim]" + "=" * 22 + "[/dim]")

    # Applying implies showing the fix line.
    if apply:
        fix = True

    checks = registry.get_checks(categories)

    # Group checks by category
    checks_by_category: dict[Category, list[CheckResult]] = {}
    for cat, check in checks:
        if cat not in checks_by_category:
            checks_by_category[cat] = []

        try:
            result = check.run()
            checks_by_category[cat].append(result)
        except Exception as e:
            # Handle unexpected errors in checks
            checks_by_category[cat].append(
                CheckResult(
                    name=check.name,
                    status=CheckStatus.FAIL,
                    message=f"Check failed: {e}",
                    category=cat,
                )
            )

    # Display results by category
    passed = 0
    warnings = 0
    failed = 0

    for category in Category:
        if category not in checks_by_category:
            continue

        results = checks_by_category[category]
        print_header(category.value.title())

        for result in results:
            show_fix = (
                fix
                and result.fix
                and result.status
                in (
                    CheckStatus.WARN,
                    CheckStatus.FAIL,
                )
            )
            print_status(
                result.status,
                result.message,
                detail=result.detail,
                fix=result.fix if show_fix else None,
            )

            if apply:
                _maybe_apply(result, assume_yes=assume_yes)

            if result.status == CheckStatus.OK:
                passed += 1
            elif result.status == CheckStatus.WARN:
                warnings += 1
            elif result.status == CheckStatus.FAIL:
                failed += 1
            # SKIP doesn't count toward totals

    print_summary(passed, warnings, failed)

    return passed, warnings, failed


def run_category(
    category: Category,
    *,
    fix: bool = False,
    apply: bool = False,
    assume_yes: bool = False,
) -> tuple[int, int, int]:
    """Run checks for a single category.

    Args:
        category: The category to check.
        fix: If True, display fix commands.
        apply: If True, offer to run each fix.
        assume_yes: If True, auto-apply safe fixes without prompting.

    Returns:
        Tuple of (passed, warnings, failed) counts.
    """
    return run_doctor([category], fix=fix, apply=apply, assume_yes=assume_yes)
