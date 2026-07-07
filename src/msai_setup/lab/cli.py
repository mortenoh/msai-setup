"""Lab CLI - `msai lab <command>`."""

from __future__ import annotations

import logging
from typing import Annotated

import typer

from msai_setup.lab import apply as apply_mod
from msai_setup.lab import pipeline as pipeline_mod
from msai_setup.lab import state as state_mod
from msai_setup.lab import vbox as vbox_mod
from msai_setup.lab import zfsroot as zfsroot_mod
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
    chosen: list[str] = list(playbooks) if playbooks else list(apply_mod.DEFAULT_PLAYBOOKS)
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
    """Run the whole pipeline end-to-end: provision then apply.

    Unlike bare `msai lab apply` (which runs only the conservative subset:
    bootstrap, ssh-hardening, ufw), `msai lab all` intentionally runs the FULL
    playbook set including zfs, docker, and services — "all" means all. Narrow
    it with --playbooks, or run individual playbooks via `msai lab apply <name>`.
    """
    _configure_logging(verbose)
    pb_list = [p.strip() for p in playbooks.split(",") if p.strip()]
    if stop_after not in (None, "provision", "apply"):
        raise typer.BadParameter("--stop-after must be 'provision' or 'apply'")
    pipeline_mod.run_pipeline(
        playbooks=pb_list,
        force=force,
        stop_after=stop_after,  # type: ignore[arg-type]
    )


@lab_app.command(name="install-zfs-root")
def install_zfs_root(
    do_reboot: Annotated[
        bool,
        typer.Option(
            "--do-reboot/--no-reboot",
            help="Reboot into ZFSBootMenu at the end (real x86_64 hardware path). "
            "Off in the lab, where the install is verified offline.",
        ),
    ] = False,
    skip_verify: Annotated[
        bool,
        typer.Option("--skip-verify", help="Skip offline verification + rollback proof."),
    ] = False,
    extra_var: Annotated[
        list[str] | None,
        typer.Option(
            "--extra-var", "-e",
            help="Forwarded as -e to the install playbook (repeatable), e.g. fast_disk=...",
        ),
    ] = None,
    verbose: _VerboseOption = False,
) -> None:
    """Fresh-install root-on-ZFS + ZFSBootMenu, rehearsing the documented ZFS-root ALTERNATIVE.

    This rehearses the documented root-on-ZFS *alternative* — NOT the canonical
    MS-S1 MAX install, which is Subiquity + ext4 (see
    docs/ubuntu/installation/zfs-root-alternative.md). Boots the current instance's
    VM into the live-server ISO, opens SSH into the LIVE environment via autoinstall
    early-commands, then debootstraps a fresh Ubuntu into rpool/ROOT/ubuntu, installs
    ZFSBootMenu, and (in the lab) proves boot-environment rollback across a real
    reboot. Create the instance first with `msai create <name>` is NOT required —
    this provisions its own live VM; just pick the current instance name with
    `msai use <name>` or let it use the default. Use a fresh instance name to avoid
    clashing with an ext4 VM.
    """
    _configure_logging(verbose)
    extras: list[str] = []
    for v in extra_var or []:
        extras.extend(["-e", v])
    zfsroot_mod.run_install_zfs_root(
        do_reboot=do_reboot,
        skip_verify=skip_verify,
        extra_args=extras,
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

    # Read the disk count actually used at creation time from the saved state,
    # so a VM created with a non-default LAB_DISK_COUNT still gets all its disks
    # removed even if the current env/default differs. Fall back to the config
    # default for state files that predate this recording.
    saved = state_mod.load(cfg.state_path)
    provision_info = saved.get("phases", {}).get("provision", {})
    zfs_info = saved.get("phases", {}).get("zfs_root_install", {})
    disk_count = provision_info.get("lab_disk_count", cfg.lab_disk_count)
    # Install disks are recorded by both the ext4 provision phase and the
    # root-on-ZFS install flow; fall back to the legacy "migration" key for VMs
    # created before the rename, then to the config default.
    install_count = (
        provision_info.get("install_disk_count")
        or zfs_info.get("install_disk_count")
        or provision_info.get("migration_disk_count")
        or cfg.install_disk_count
    )

    vbox_mod.unregister_and_delete(cfg.vm_name)

    # Remove disks and ISOs that the VM was using
    for p in [
        cfg.primary_disk_path,
        cfg.cidata_iso_path,
        cfg.console_password_path,
        cfg.state_path,
    ]:
        if p.exists():
            p.unlink()
            typer.echo(f"removed {p}")
    for i in range(1, disk_count + 1):
        path = cfg.lab_disk_path(i)
        if path.exists():
            path.unlink()
            typer.echo(f"removed {path}")
    for i in range(1, install_count + 1):
        path = cfg.install_disk_path(i)
        if path.exists():
            path.unlink()
            typer.echo(f"removed {path}")
        # Also clean up any legacy "-migration-" disks from before the rename.
        legacy = cfg.target_dir / f"{cfg.vm_name}-migration-{i:02d}.vdi"
        if legacy.exists():
            legacy.unlink()
            typer.echo(f"removed {legacy}")
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
    try:
        if name:
            vbox_mod.snapshot_restore(cfg.vm_name, name)
        else:
            vbox_mod.snapshot_restore_current(cfg.vm_name)
    except vbox_mod.VBoxError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e
    typer.echo(f"restored to snapshot {name or '(most recent)'}")


