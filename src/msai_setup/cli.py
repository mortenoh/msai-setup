"""MS-S1 MAX CLI."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.table import Table

from msai_setup.doctor.checks import Category
from msai_setup.doctor.profile import Profile, resolve_profile, set_profile
from msai_setup.doctor.runner import run_category, run_doctor
from msai_setup.lab import instance as lab_instance
from msai_setup.lab import vbox as lab_vbox
from msai_setup.lab.cli import lab_app
from msai_setup.lab.config import load_config
from msai_setup.lab.provision import main as lab_provision
from msai_setup.utils.formatting import console

app = typer.Typer(
    name="msai",
    help="MS-S1 MAX Home Server Setup CLI",
    no_args_is_help=True,
)

doctor_app = typer.Typer(
    name="doctor",
    help="System health checks (run these ON the MS-S1 MAX, not your laptop).",
    invoke_without_command=True,
)
profile_app = typer.Typer(
    name="profile",
    help="Show or set the host profile (server vs desktop) used by doctor.",
    invoke_without_command=True,
    no_args_is_help=False,
)

app.add_typer(doctor_app, name="doctor")
app.add_typer(profile_app, name="profile")
app.add_typer(lab_app, name="lab")


@profile_app.callback(invoke_without_command=True)
def profile_main(ctx: typer.Context) -> None:
    """Show the active profile when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        profile, source = resolve_profile()
        typer.echo(f"profile: {profile.value} (resolved from {source})")


@profile_app.command("set")
def profile_set(
    name: Annotated[str, typer.Argument(help="Profile to persist: server or desktop.")],
) -> None:
    """Persist the host profile for future doctor runs."""
    try:
        profile = Profile(name.strip().lower())
    except ValueError:
        valid = ", ".join(p.value for p in Profile)
        typer.echo(f"unknown profile '{name}'. Valid: {valid}", err=True)
        raise typer.Exit(code=1) from None
    path = set_profile(profile)
    typer.echo(f"profile set to '{profile.value}' ({path})")


@app.command()
def version() -> None:
    """Show version information."""
    from msai_setup import __version__

    typer.echo(f"msai-setup {__version__}")


@app.command()
def docs() -> None:
    """Serve documentation locally."""
    import subprocess

    subprocess.run(["mkdocs", "serve"], check=True)


# ---------------------------------------------------------------------------
# Lab-instance lifecycle (grouped under `msai lab`)
# ---------------------------------------------------------------------------


@lab_app.command()
def create(
    name: Annotated[str, typer.Argument(help="Instance name (lowercase, hyphens).")],
) -> None:
    """Create a new lab instance and make it the current one.

    Provisions a VirtualBox VM by the given name: downloads Ubuntu, builds
    install + cloud-init ISOs, creates disks, boots headless and waits for
    SSH. After this, `msai lab <cmd>` commands target this instance.
    """
    lab_instance.validate_name(name)
    existing = {i.name for i in lab_instance.list_instances()}
    if name in existing:
        typer.echo(f"instance '{name}' already exists; switching to it instead.")
        lab_instance.set_current(name)
        return
    lab_instance.set_current(name)
    typer.echo(f"current instance is now '{name}'")
    lab_provision()


@lab_app.command(name="list")
@lab_app.command(name="ls", hidden=True)
def list_instances() -> None:
    """List lab instances visible in target/."""
    items = lab_instance.list_instances()
    if not items:
        typer.echo("no instances yet. Create one: msai lab create <name>")
        return

    table = Table(title="Lab instances", show_lines=False)
    table.add_column("", style="dim", justify="center")
    table.add_column("Name")
    table.add_column("State")
    table.add_column("Disks")
    table.add_column("VBox VM")

    for info in items:
        marker = "*" if info.is_current else " "
        vm_present = lab_vbox.vm_exists(info.name)
        vm_running = lab_vbox.vm_running(info.name) if vm_present else False
        vbox_status = (
            "running" if vm_running
            else "stopped" if vm_present
            else "absent"
        )
        table.add_row(
            marker,
            info.name,
            "ok" if info.has_state else "(not provisioned)",
            "ok" if info.has_disks else "-",
            vbox_status,
        )
    console.print(table)
    console.print("[dim]* = current instance (msai lab use <name> to switch)[/dim]")


@lab_app.command()
def use(
    name: Annotated[str, typer.Argument(help="Instance name to switch to.")],
) -> None:
    """Switch the current instance pointer to an existing instance."""
    existing = {i.name for i in lab_instance.list_instances()}
    if name not in existing:
        typer.echo(
            f"instance '{name}' not found. Known: {', '.join(sorted(existing)) or '(none)'}",
            err=True,
        )
        raise typer.Exit(code=1)
    lab_instance.set_current(name)
    typer.echo(f"current instance is now '{name}'")


@lab_app.command()
def start(
    name: Annotated[
        str | None,
        typer.Argument(help="Instance name (default: current)."),
    ] = None,
) -> None:
    """Power on a lab instance (headless)."""
    target = name or lab_instance.require_current()
    if not lab_vbox.vm_exists(target):
        typer.echo(f"VM '{target}' not present. Create it: msai lab create {target}", err=True)
        raise typer.Exit(code=1)
    if lab_vbox.vm_running(target):
        typer.echo(f"VM '{target}' is already running.")
        return
    lab_vbox.start_headless(target)
    typer.echo(f"started '{target}' headless")


@lab_app.command()
def stop(
    name: Annotated[
        str | None,
        typer.Argument(help="Instance name (default: current)."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force/--no-force",
            help="Hard power-off (default: graceful ACPI shutdown).",
        ),
    ] = False,
) -> None:
    """Power off a lab instance."""
    target = name or lab_instance.require_current()
    if not lab_vbox.vm_running(target):
        typer.echo(f"VM '{target}' is not running.")
        return
    if force:
        lab_vbox.power_off(target)
        typer.echo(f"hard-powered-off '{target}'")
    else:
        lab_vbox.acpi_power_button(target)
        typer.echo(
            f"sent ACPI power button to '{target}'; the guest will shut down cleanly. "
            "Use --force to skip the wait."
        )


@lab_app.command(
    name="ssh",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@lab_app.command(
    name="login",
    hidden=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def ssh_login(
    ctx: typer.Context,
    name: Annotated[
        str | None,
        typer.Argument(
            help="Instance name (default: current). Required if passing a remote COMMAND."
        ),
    ] = None,
) -> None:
    """SSH into a lab instance using the lab keypair.

    Pass a remote command after `--` to run it non-interactively instead of
    opening a shell, e.g. `msai lab ssh myvm -- uname -a`. NAME must be given
    explicitly when passing a command (it can't be inferred from "current"
    in that case, since the parser can't tell a command apart from a name).
    """
    import os

    target = name or lab_instance.require_current()
    cfg = load_config(vm_name=target)
    priv_key = cfg.ssh_public_key_path.with_suffix("")
    if not priv_key.exists():
        typer.echo(f"lab key missing at {priv_key}; run `msai lab create <name>` first.", err=True)
        raise typer.Exit(code=1)
    cmd = [
        "ssh",
        "-p", str(cfg.ssh_forward_port),
        "-i", str(priv_key),
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "UserKnownHostsFile=/dev/null",
        f"{cfg.vm_user}@{cfg.ssh_host}",
    ]
    if ctx.args:
        cmd.extend(ctx.args)
    os.execvp(cmd[0], cmd)


# ---------------------------------------------------------------------------
# Doctor subcommands (run ON the MS-S1 MAX, not the laptop)
# ---------------------------------------------------------------------------

FixOption = Annotated[
    bool,
    typer.Option("--fix", "-f", help="Show fix commands for issues"),
]
ApplyOption = Annotated[
    bool,
    typer.Option("--apply", "-a", help="Apply fixes (prompts before each; implies --fix)"),
]
YesOption = Annotated[
    bool,
    typer.Option("--yes", "-y", help="With --apply, auto-apply safe fixes without prompting"),
]


@doctor_app.callback(invoke_without_command=True)
def doctor_main(
    ctx: typer.Context,
    fix: FixOption = False,
    apply: ApplyOption = False,
    yes: YesOption = False,
) -> None:
    """Run all health checks."""
    if ctx.invoked_subcommand is None:
        _passed, _warnings, failed = run_doctor(fix=fix, apply=apply, assume_yes=yes)
        raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def system(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run system checks (Ubuntu, kernel, memory, CPU, SSH)."""
    _passed, _warnings, failed = run_category(
        Category.SYSTEM, fix=fix, apply=apply, assume_yes=yes
    )
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def zfs(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run ZFS checks (pool, health, scrub, snapshots)."""
    _passed, _warnings, failed = run_category(Category.ZFS, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def docker(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run Docker checks (daemon, group, compose)."""
    _passed, _warnings, failed = run_category(Category.DOCKER, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def kvm(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run KVM checks (libvirtd, IOMMU, vfio-pci)."""
    _passed, _warnings, failed = run_category(Category.KVM, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def gpu(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run GPU checks (AMD driver, ROCm, Vulkan)."""
    _passed, _warnings, failed = run_category(Category.GPU, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def ollama(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run Ollama checks (service, API, models)."""
    _passed, _warnings, failed = run_category(Category.OLLAMA, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def tailscale(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run Tailscale checks (daemon, connection, MagicDNS)."""
    _passed, _warnings, failed = run_category(
        Category.TAILSCALE, fix=fix, apply=apply, assume_yes=yes
    )
    raise typer.Exit(code=1 if failed > 0 else 0)


if __name__ == "__main__":
    app()
