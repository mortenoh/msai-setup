"""MS-S1 MAX CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from msai_setup.doctor.checks import Category
from msai_setup.doctor.profile import Profile, resolve_profile, set_profile
from msai_setup.doctor.runner import run_category, run_doctor
from msai_setup.lab import instance as lab_instance
from msai_setup.lab import profiles as lab_profiles
from msai_setup.lab import state as lab_state
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


@app.command()
def bootstrap(
    components: Annotated[
        list[str] | None,
        typer.Argument(help="Components to install (default: all). E.g. docker rocm kvm."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Print the plan without running anything."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the per-component confirmation prompt."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Install even if already detected as present."),
    ] = False,
) -> None:
    """Install the MS-S1 MAX stack (Docker, ZFS tools, ROCm, KVM, Tailscale, Ollama).

    Packages and daemons only; disk partitioning and ZFS pool creation stay
    manual. Run this ON the MS-S1 MAX. Each component is idempotent.
    """
    from msai_setup.install.runner import bootstrap as run_bootstrap

    run_bootstrap(components, dry_run=dry_run, assume_yes=yes, force=force)


# ---------------------------------------------------------------------------
# Lab-instance lifecycle (grouped under `msai lab`)
# ---------------------------------------------------------------------------


@lab_app.command()
def create(
    name: Annotated[str, typer.Argument(help="Instance name (lowercase, hyphens).")],
    os_profile: Annotated[
        str,
        typer.Option(
            "--os",
            help="OS profile to install. Valid: " + ", ".join(sorted(lab_profiles.PROFILES)),
        ),
    ] = "ubuntu-server",
    gui: Annotated[
        bool,
        typer.Option(
            "--gui/--headless",
            help="Boot the installer with a visible console window (default) or headless.",
        ),
    ] = True,
    iso: Annotated[
        str | None,
        typer.Option(
            "--iso",
            help="Path to a local install ISO. REQUIRED for windows-* profiles "
            "(user-supplied, not downloaded); ignored for Ubuntu/Fedora.",
        ),
    ] = None,
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            help="Backend: 'vbox' (default, VirtualBox on this Mac) or 'incus' "
            "(the real Linux box / MS-S1 MAX).",
        ),
    ] = "vbox",
) -> None:
    """Create a new lab instance and make it the current one.

    Provisions an instance by the given name via the chosen --provider: prepares
    the install + seed media, boots the installer (visible console by default;
    --headless for none) and (for Linux) waits for readiness. Windows profiles
    need a local ISO via --iso. After this, `msai lab <cmd>` targets this
    instance.
    """
    lab_instance.validate_name(name)
    if os_profile not in lab_profiles.PROFILES:
        valid = ", ".join(sorted(lab_profiles.PROFILES))
        typer.echo(f"unknown OS profile '{os_profile}'. Valid: {valid}", err=True)
        raise typer.Exit(code=1)
    if provider not in ("vbox", "incus"):
        typer.echo(f"unknown provider '{provider}'. Valid: vbox, incus", err=True)
        raise typer.Exit(code=1)
    # Local-ISO profiles (Windows) need a user-supplied install ISO — the config
    # layer reads it from $WINDOWS_ISO. Resolve --iso (or a pre-set env) here and
    # fail early with a clean message rather than deep in provisioning.
    profile = lab_profiles.PROFILES[os_profile]
    iso_path = iso or os.environ.get("WINDOWS_ISO")
    if profile.requires_local_iso:
        if not iso_path:
            typer.echo(
                f"profile '{os_profile}' needs a local install ISO. "
                "Pass --iso /path/to/Win.iso (or set WINDOWS_ISO).",
                err=True,
            )
            raise typer.Exit(code=1)
        if not Path(iso_path).is_file():
            typer.echo(f"--iso file not found: {iso_path}", err=True)
            raise typer.Exit(code=1)
    elif iso is not None:
        typer.echo(f"--iso is only used by windows-* profiles; ignoring it for '{os_profile}'.")
    existing = {i.name for i in lab_instance.list_instances()}
    if name in existing:
        typer.echo(f"instance '{name}' already exists; switching to it instead.")
        lab_instance.set_current(name)
        return
    lab_instance.set_current(name)
    typer.echo(f"current instance is now '{name}'")
    # The provision phase reads its settings from the environment (see
    # config.py), so surface the chosen profile / boot mode that way.
    os.environ["LAB_OS"] = os_profile
    os.environ["LAB_HEADLESS"] = "0" if gui else "1"
    os.environ["LAB_PROVIDER"] = provider
    if profile.requires_local_iso and iso_path:
        os.environ["WINDOWS_ISO"] = iso_path
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
    gui: Annotated[
        bool | None,
        typer.Option(
            "--gui/--headless",
            help="Show a visible console window, or run headless. "
            "Default: match how the VM was provisioned, else GUI.",
        ),
    ] = None,
) -> None:
    """Power on a lab instance.

    Boots with a visible console by default (or matching how the VM was
    provisioned); pass --headless for a windowless boot.
    """
    target = name or lab_instance.require_current()
    if not lab_vbox.vm_exists(target):
        typer.echo(f"VM '{target}' not present. Create it: msai lab create {target}", err=True)
        raise typer.Exit(code=1)
    if lab_vbox.vm_running(target):
        typer.echo(f"VM '{target}' is already running.")
        return
    if gui is None:
        # Fall back to the boot mode recorded at provision time, else GUI.
        cfg = load_config(vm_name=target)
        provision_info = lab_state.load(cfg.state_path).get("phases", {}).get("provision", {})
        recorded = provision_info.get("headless")
        headless = bool(recorded) if recorded is not None else False
    else:
        headless = not gui
    lab_vbox.start(target, headless=headless)
    typer.echo(f"started '{target}' {'headless' if headless else 'with GUI console'}")


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
def incus(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run Incus checks (installed, daemon, initialized, incus-admin group)."""
    _passed, _warnings, failed = run_category(Category.INCUS, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def kvm(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run KVM checks (KVM enabled, QEMU, IOMMU, vfio-pci)."""
    _passed, _warnings, failed = run_category(Category.KVM, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def gpu(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run GPU checks (AMD driver, ROCm, Vulkan)."""
    _passed, _warnings, failed = run_category(Category.GPU, fix=fix, apply=apply, assume_yes=yes)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def inference(fix: FixOption = False, apply: ApplyOption = False, yes: YesOption = False) -> None:
    """Run inference checks (llama.cpp installed, HIP/ROCm backend)."""
    _passed, _warnings, failed = run_category(
        Category.INFERENCE, fix=fix, apply=apply, assume_yes=yes
    )
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
