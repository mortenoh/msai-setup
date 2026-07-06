"""SSH helpers for talking to the lab VM.

We shell out to the system `ssh`/`scp` rather than using paramiko — keeps
dependencies to stdlib only and lets users reuse their existing
~/.ssh/config / known_hosts setup.
"""

from __future__ import annotations

import logging
import socket
import subprocess
import time
from pathlib import Path

log = logging.getLogger(__name__)


def ensure_lab_keypair(public_key_path: Path) -> Path:
    """Generate an Ed25519 keypair at `public_key_path` (.pub) if missing.

    Returns the path to the private key (drops the .pub suffix). Idempotent:
    leaves an existing keypair alone.
    """
    if public_key_path.suffix != ".pub":
        raise ValueError(f"expected a .pub path, got {public_key_path}")
    priv = public_key_path.with_suffix("")  # strip .pub
    if public_key_path.exists() and priv.exists():
        log.info("lab keypair already present: %s", priv)
        return priv
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("generating dedicated lab keypair at %s", priv)
    subprocess.run(
        [
            "ssh-keygen",
            "-t", "ed25519",
            "-N", "",                       # no passphrase
            "-f", str(priv),
            "-C", "msai-lab",
        ],
        check=True,
        capture_output=True,
    )
    log.info("lab keypair generated")
    return priv


def wait_for_port(host: str, port: int, *, timeout: int = 1800, interval: int = 5) -> None:
    """Poll a TCP port until it accepts connections or `timeout` seconds pass.

    NOTE: VirtualBox NAT port-forwards accept the host-side TCP handshake even
    before guest sshd is listening, so this only confirms the forward exists -
    NOT that ssh is up. Use wait_for_ssh for the latter.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                log.info("port %s:%d is reachable", host, port)
                return
        except OSError:
            time.sleep(interval)
    raise TimeoutError(f"timed out waiting for {host}:{port}")


def wait_for_ssh(
    host: str,
    port: int,
    *,
    user: str,
    identity_file: Path,
    timeout: int = 1800,
    interval: int = 20,
) -> None:
    """Poll until we can SSH in as `user` with `identity_file` and run a command.

    Stricter than a banner-only probe: the Ubuntu live installer also runs
    sshd on the target during install (identical banner!), so the only
    reliable signal that the install has finished and our lab user is real
    is a successful key-based authentication.
    """
    deadline = time.monotonic() + timeout
    last_err: str = "(never tried)"
    while time.monotonic() < deadline:
        try:
            result = subprocess.run(
                ssh_args(user, host, port, identity_file=identity_file) + ["true"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                log.info("SSH authenticated as %s@%s:%d", user, host, port)
                return
            err = (result.stderr or result.stdout or "").strip()
            last_err = err.splitlines()[-1] if err else f"rc={result.returncode}"
        except subprocess.TimeoutExpired:
            last_err = "ssh exec timeout"
        except OSError as e:
            last_err = f"ssh spawn: {e}"
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for SSH on {host}:{port} (last error: {last_err})")


def ssh_args(
    user: str,
    host: str,
    port: int,
    *,
    extra_options: list[str] | None = None,
    identity_file: Path | None = None,
) -> list[str]:
    """Build a baseline `ssh` argument list with sane defaults for lab use."""
    args = [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
    ]
    if identity_file is not None:
        args.extend(["-i", str(identity_file), "-o", "IdentitiesOnly=yes"])
    if extra_options:
        args.extend(extra_options)
    args.append(f"{user}@{host}")
    return args


def run_remote(
    user: str,
    host: str,
    port: int,
    command: str,
    *,
    identity_file: Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command on the remote host via ssh."""
    cmd = ssh_args(user, host, port, identity_file=identity_file) + [command]
    log.debug("running remote: %s", command)
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=check,
    )


def run_remote_script(
    user: str,
    host: str,
    port: int,
    script: str,
    *,
    identity_file: Path | None = None,
    sudo: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a multi-line bash `script` on the remote host, fed over stdin.

    Piping the script to `bash -s` (rather than passing it as an argument)
    sidesteps shell-quoting problems for large scripts. `sudo=True` runs it as
    root via the lab user's passwordless sudo. Never raises on a non-zero exit;
    the caller inspects `returncode`/`stdout`.
    """
    remote = "sudo bash -s" if sudo else "bash -s"
    cmd = ssh_args(user, host, port, identity_file=identity_file) + [remote]
    log.debug("running remote script (%d chars, sudo=%s)", len(script), sudo)
    return subprocess.run(
        cmd,
        input=script,
        capture_output=True,
        text=True,
        check=False,
    )


def push_authorized_key(
    user: str,
    host: str,
    port: int,
    *,
    password: str,
    public_key_path: Path,
) -> None:
    """Copy a public key into the remote user's authorized_keys.

    Uses sshpass + ssh-copy-id when available (cleanest), falls back to a manual
    expect-style flow when sshpass isn't installed. Idempotent: ssh-copy-id
    appends rather than duplicates.
    """
    if not public_key_path.exists():
        raise FileNotFoundError(f"public key not found: {public_key_path}")

    if _have("sshpass"):
        cmd = [
            "sshpass", "-p", password,
            "ssh-copy-id",
            "-i", str(public_key_path),
            "-p", str(port),
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{user}@{host}",
        ]
        subprocess.run(cmd, check=True)
        log.info("pushed %s via ssh-copy-id+sshpass", public_key_path.name)
        return

    raise RuntimeError(
        "sshpass not available. Install it (e.g. `brew install hudochenkov/sshpass/sshpass`) "
        "or push the key manually:\n"
        f"  ssh-copy-id -i {public_key_path} -p {port} {user}@{host}"
    )


def _have(cmd: str) -> bool:
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0
