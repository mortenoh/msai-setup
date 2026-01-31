"""Check orchestration and reporting."""

from msai_setup.doctor.checks import Category, CheckResult, registry
from msai_setup.utils.formatting import (
    CheckStatus,
    console,
    print_header,
    print_status,
    print_summary,
)


def run_doctor(
    categories: list[Category] | None = None,
    *,
    fix: bool = False,
) -> tuple[int, int, int]:
    """Run health checks and display results.

    Args:
        categories: Categories to check, or None for all.
        fix: If True, display fix commands for issues.

    Returns:
        Tuple of (passed, warnings, failed) counts.
    """
    console.print("\n[header]MS-S1 MAX Health Check[/header]")
    console.print("[dim]" + "=" * 22 + "[/dim]")

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

            if result.status == CheckStatus.OK:
                passed += 1
            elif result.status == CheckStatus.WARN:
                warnings += 1
            elif result.status == CheckStatus.FAIL:
                failed += 1
            # SKIP doesn't count toward totals

    print_summary(passed, warnings, failed)

    return passed, warnings, failed


def run_category(category: Category, *, fix: bool = False) -> tuple[int, int, int]:
    """Run checks for a single category.

    Args:
        category: The category to check.
        fix: If True, display fix commands.

    Returns:
        Tuple of (passed, warnings, failed) counts.
    """
    return run_doctor([category], fix=fix)
