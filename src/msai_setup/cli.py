"""MS-S1 MAX CLI."""

from typing import Annotated

import typer

from msai_setup.doctor.checks import Category
from msai_setup.doctor.runner import run_category, run_doctor

app = typer.Typer(
    name="msai",
    help="MS-S1 MAX Home Server Setup CLI",
    no_args_is_help=True,
)

doctor_app = typer.Typer(
    name="doctor",
    help="System health checks",
    invoke_without_command=True,
)
app.add_typer(doctor_app, name="doctor")


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
def status() -> None:
    """Show quick status overview of all services."""
    from msai_setup.utils.formatting import console

    console.print("\n[header]MS-S1 MAX Status[/header]")
    console.print("[dim]" + "=" * 16 + "[/dim]")
    console.print("[dim]Run 'msai doctor' for detailed health checks[/dim]\n")

    # Run abbreviated checks for status overview
    run_doctor(fix=False)


# Doctor subcommands

FixOption = Annotated[
    bool,
    typer.Option("--fix", "-f", help="Show fix commands for issues"),
]


@doctor_app.callback(invoke_without_command=True)
def doctor_main(
    ctx: typer.Context,
    fix: FixOption = False,
) -> None:
    """Run all health checks."""
    if ctx.invoked_subcommand is None:
        _passed, _warnings, failed = run_doctor(fix=fix)
        raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def system(fix: FixOption = False) -> None:
    """Run system checks (Ubuntu, kernel, memory, CPU, SSH)."""
    _passed, _warnings, failed = run_category(Category.SYSTEM, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def zfs(fix: FixOption = False) -> None:
    """Run ZFS checks (pool, health, scrub, snapshots)."""
    _passed, _warnings, failed = run_category(Category.ZFS, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def docker(fix: FixOption = False) -> None:
    """Run Docker checks (daemon, group, compose)."""
    _passed, _warnings, failed = run_category(Category.DOCKER, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def kvm(fix: FixOption = False) -> None:
    """Run KVM checks (libvirtd, IOMMU, vfio-pci)."""
    _passed, _warnings, failed = run_category(Category.KVM, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def gpu(fix: FixOption = False) -> None:
    """Run GPU checks (AMD driver, ROCm, Vulkan)."""
    _passed, _warnings, failed = run_category(Category.GPU, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def ollama(fix: FixOption = False) -> None:
    """Run Ollama checks (service, API, models)."""
    _passed, _warnings, failed = run_category(Category.OLLAMA, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


@doctor_app.command()
def tailscale(fix: FixOption = False) -> None:
    """Run Tailscale checks (daemon, connection, MagicDNS)."""
    _passed, _warnings, failed = run_category(Category.TAILSCALE, fix=fix)
    raise typer.Exit(code=1 if failed > 0 else 0)


if __name__ == "__main__":
    app()
