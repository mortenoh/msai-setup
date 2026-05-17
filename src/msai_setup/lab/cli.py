"""Lab CLI - `msai lab <command>`."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from msai_setup.lab import apply as apply_mod
from msai_setup.lab import pipeline as pipeline_mod
from msai_setup.lab import state as state_mod
from msai_setup.lab import vbox as vbox_mod
from msai_setup.lab.apply import KNOWN_PLAYBOOKS
from msai_setup.lab.config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

lab_app = typer.Typer(
    name="lab",
    help="VirtualBox lab — provision an Ubuntu VM, configure it with Ansible.",
    no_args_is_help=True,
)


_VerboseOption = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Show debug logging."),
]


def _configure_logging(verbose: bool) -> None:
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@lab_app.command()
def apply(
    playbooks: Annotated[
        list[str] | None,
        typer.Argument(
            help=f"Playbooks to run, in order. Known: {', '.join(KNOWN_PLAYBOOKS)}.",
            show_default=False,
        ),
    ] = None,
    check: Annotated[
        bool,
        typer.Option("--check/--no-check", help="Pass --check to ansible-playbook"),
    ] = False,
    diff: Annotated[
        bool,
        typer.Option("--diff/--no-diff", help="Pass --diff to ansible-playbook"),
    ] = False,
    extra_var: Annotated[
        list[str] | None,
        typer.Option(
            "--extra-var", "-e",
            help="Forwarded as -e to ansible-playbook (repeatable).",
        ),
    ] = None,
    verbose: _VerboseOption = False,
) -> None:
    """Run one or more Ansible playbooks against the lab VM."""
    _configure_logging(verbose)
    chosen = list(playbooks) if playbooks else list(apply_mod.DEFAULT_PLAYBOOKS)
    extras: list[str] = []
    if check:
        extras.append("--check")
    if diff:
        extras.append("--diff")
    for v in extra_var or []:
        extras.extend(["-e", v])
    apply_mod.run_apply(chosen, extras)


@lab_app.command()
def all(
    force: Annotated[
        bool,
        typer.Option("--force", help="Re-run phases even if state.json says they're done."),
    ] = False,
    stop_after: Annotated[
        str | None,
        typer.Option(
            "--stop-after",
            help="Stop after the named phase ('provision' or 'apply').",
        ),
    ] = None,
    playbooks: Annotated[
        str,
        typer.Option(
            "--playbooks",
            help="Comma-separated playbooks for the apply phase.",
        ),
    ] = ",".join(pipeline_mod.DEFAULT_PLAYBOOKS),
    verbose: _VerboseOption = False,
) -> None:
    """Run the whole pipeline end-to-end: provision then apply."""
    _configure_logging(verbose)
    pb_list = [p.strip() for p in playbooks.split(",") if p.strip()]
    if stop_after not in (None, "provision", "apply"):
        raise typer.BadParameter("--stop-after must be 'provision' or 'apply'")
    pipeline_mod.run_pipeline(
        playbooks=pb_list,
        force=force,
        stop_after=stop_after,  # type: ignore[arg-type]
    )


@lab_app.command()
def status() -> None:
    """Show the current state of the lab (VM, phase markers, snapshots)."""
    cfg = load_config()
    typer.echo(f"VM name:     {cfg.vm_name}")
    typer.echo(f"Platform:    {cfg.platform}")
    typer.echo(f"OS type:     {cfg.vm_ostype}")
    typer.echo(f"State file:  {cfg.state_path}")
    typer.echo("")

    typer.echo("VirtualBox:")
    if vbox_mod.vm_exists(cfg.vm_name):
        running = vbox_mod.vm_running(cfg.vm_name)
        typer.echo(f"  vm:        present, {'running' if running else 'stopped'}")
        try:
            snaps = vbox_mod.snapshot_list(cfg.vm_name)
            if snaps:
                typer.echo(f"  snapshots: {', '.join(snaps)}")
        except Exception:  # noqa: BLE001
            pass
    else:
        typer.echo("  vm:        not present")

    typer.echo("")
    typer.echo("Phases:")
    s = state_mod.load(cfg.state_path)
    phases = s.get("phases", {})
    if not phases:
        typer.echo("  (none recorded yet)")
    for name, info in phases.items():
        typer.echo(f"  {name}: finished_at={info.get('finished_at')}")


@lab_app.command()
def destroy(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Don't prompt for confirmation."),
    ] = False,
) -> None:
    """Power off, unregister, and delete the VM + its disks + state."""
    cfg = load_config()

    if not yes:
        typer.confirm(
            f"This will permanently delete VM '{cfg.vm_name}' and all its disks. Continue?",
            abort=True,
        )

    vbox_mod.unregister_and_delete(cfg.vm_name)

    # Remove disks and ISOs that the VM was using
    for p in [
        cfg.primary_disk_path,
        cfg.cidata_iso_path,
        cfg.state_path,
    ]:
        if p.exists():
            p.unlink()
            typer.echo(f"removed {p}")
    for i in range(1, cfg.lab_disk_count + 1):
        path = cfg.lab_disk_path(i)
        if path.exists():
            path.unlink()
            typer.echo(f"removed {path}")
    typer.echo("done.")


@lab_app.command()
def snapshot(
    name: Annotated[
        str,
        typer.Argument(help="Snapshot name."),
    ],
    pause: Annotated[
        bool,
        typer.Option("--pause/--no-pause", help="Pause the VM during snapshot."),
    ] = True,
) -> None:
    """Take a VirtualBox snapshot of the lab VM."""
    cfg = load_config()
    vbox_mod.snapshot_take(cfg.vm_name, name, pause=pause)
    typer.echo(f"snapshot '{name}' taken")


@lab_app.command()
def restore(
    name: Annotated[
        str | None,
        typer.Argument(help="Snapshot name (default: most recent)."),
    ] = None,
) -> None:
    """Restore the VM to a snapshot."""
    cfg = load_config()
    if vbox_mod.vm_running(cfg.vm_name):
        vbox_mod.power_off(cfg.vm_name)
    if name:
        # `snapshot restore <name>` form; fall back to current if it errors
        try:
            subprocess.run(
                ["VBoxManage", "snapshot", cfg.vm_name, "restore", name],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise typer.Exit(code=e.returncode)
    else:
        vbox_mod.snapshot_restore_current(cfg.vm_name)
    typer.echo(f"restored to snapshot {name or '(most recent)'}")


@lab_app.command()
def ssh() -> None:
    """SSH into the lab VM using the lab keypair."""
    cfg = load_config()
    priv_key = cfg.ssh_public_key_path.with_suffix("")
    if not priv_key.exists():
        typer.echo(f"lab key missing at {priv_key}; run `msai create <name>` first.", err=True)
        raise typer.Exit(code=1)
    cmd = [
        "ssh", "-p", str(cfg.ssh_forward_port),
        "-i", str(priv_key),
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "UserKnownHostsFile=/dev/null",
        f"{cfg.vm_user}@{cfg.ssh_host}",
    ]
    import os
    os.execvp(cmd[0], cmd)  # replace this process with ssh
