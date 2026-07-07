"""Execute the stack manifest for `msai bootstrap`.

Every component is idempotent (skipped when its ``detect`` probe passes) and
isolated (a failing component warns and the run continues, rather than aborting
everything after it). ``sudo apt-get update`` runs at most once per invocation.
"""

from __future__ import annotations

from dataclasses import dataclass

import typer

from msai_setup.install.manifest import Component, load_manifest
from msai_setup.utils.formatting import console
from msai_setup.utils.shell import run_interactive, shell_succeeds


@dataclass
class ComponentOutcome:
    """What happened to one component during a bootstrap run."""

    name: str
    status: str  # "skipped" | "planned" | "installed" | "failed"


def install_commands(component: Component) -> list[str]:
    """The shell commands that install a component (excluding apt-get update)."""
    commands: list[str] = []
    if component.method == "apt":
        commands.append("sudo apt-get install -y " + " ".join(component.packages))
    elif component.method == "curl_sh":
        base = f"curl -fsSL {component.url} | {component.shell}"
        if component.extra_args:
            base = (
                f"curl -fsSL {component.url} | {component.shell} -s -- "
                + " ".join(component.extra_args)
            )
        commands.append(base)
    commands.extend(component.post)
    return commands


def _select(
    manifest: dict[str, Component], names: list[str] | None
) -> list[tuple[str, Component]]:
    """Resolve requested names to (name, component) pairs in manifest order."""
    if not names:
        return list(manifest.items())
    unknown = [n for n in names if n not in manifest]
    if unknown:
        known = ", ".join(manifest)
        typer.echo(f"unknown component(s): {', '.join(unknown)}. Known: {known}", err=True)
        raise typer.Exit(code=1)
    return [(n, manifest[n]) for n in manifest if n in set(names)]


def bootstrap(
    names: list[str] | None = None,
    *,
    dry_run: bool = False,
    assume_yes: bool = False,
    force: bool = False,
) -> list[ComponentOutcome]:
    """Install the selected stack components (all of them when names is empty).

    Args:
        names: Component names to install, or None/empty for all.
        dry_run: Print the plan without running anything.
        assume_yes: Skip the per-component confirmation prompt.
        force: Install even if the detect probe says it is already present.

    Returns:
        One ComponentOutcome per selected component.
    """
    manifest = load_manifest()
    selected = _select(manifest, names)

    console.print("\n[header]MS-S1 MAX Bootstrap[/header]")
    console.print("[dim]" + "=" * 18 + "[/dim]")
    if dry_run:
        console.print("[dim]dry run - nothing will be executed[/dim]")

    outcomes: list[ComponentOutcome] = []
    apt_updated = False

    for name, component in selected:
        if not force and component.detect and shell_succeeds(component.detect):
            console.print(f"[ok][OK][/ok] {name}: already installed")
            outcomes.append(ComponentOutcome(name, "skipped"))
            continue

        steps = install_commands(component)
        needs_update = component.method == "apt" and not apt_updated
        plan = (["sudo apt-get update"] if needs_update else []) + steps

        console.print(f"\n[header]{name}[/header] [dim]- {component.description}[/dim]")
        for cmd in plan:
            console.print(f"  [info]$[/info] {cmd}")

        if dry_run:
            outcomes.append(ComponentOutcome(name, "planned"))
            continue

        if not assume_yes and not typer.confirm(f"Install {name}?", default=True):
            outcomes.append(ComponentOutcome(name, "skipped"))
            continue

        outcomes.append(_run_component(name, plan, needs_update=needs_update))
        if needs_update:
            apt_updated = True

    _print_summary(outcomes, dry_run=dry_run)
    return outcomes


def _run_component(name: str, plan: list[str], *, needs_update: bool) -> ComponentOutcome:
    """Run a component's commands in order, stopping at the first failure."""
    for cmd in plan:
        try:
            code = run_interactive(cmd)
        except Exception as exc:  # noqa: BLE001 - isolate one component's failure
            console.print(f"[fail]{name}: {cmd!r} raised {exc}; skipping rest[/fail]")
            return ComponentOutcome(name, "failed")
        if code != 0:
            console.print(f"[fail]{name}: '{cmd}' exited {code}; skipping rest[/fail]")
            return ComponentOutcome(name, "failed")
    console.print(f"[ok][OK][/ok] {name}: installed")
    return ComponentOutcome(name, "installed")


def _print_summary(outcomes: list[ComponentOutcome], *, dry_run: bool) -> None:
    """Print a one-line tally and a nudge to re-run doctor."""
    tally: dict[str, int] = {}
    for outcome in outcomes:
        tally[outcome.status] = tally.get(outcome.status, 0) + 1
    parts = [f"{count} {status}" for status, count in sorted(tally.items())]
    console.print(f"\nSummary: {', '.join(parts) or 'nothing to do'}")
    if not dry_run and tally.get("installed"):
        console.print(
            "[dim]Group changes (docker/render/libvirt) take effect on next login. "
            "Verify with [cyan]msai doctor[/cyan].[/dim]"
        )
