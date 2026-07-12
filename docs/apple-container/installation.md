# Installation

Apple Container installs on the Mac dev machine and registers a background service that hosts the per-container microVMs. This page covers getting it on disk, starting and checking the service, the **version-mismatch gotcha** that bites after every CLI upgrade, and how to reset or remove it. It assumes the model from the [section overview](index.md): each container is its own Linux VM, orchestrated by a local `container` API server.

!!! note "Apple Silicon, macOS 15+"
    Apple Container requires **macOS 15 or newer on Apple Silicon**. There is no Intel-Mac build and no Linux/Windows client — it is macOS-native. This build runs it on an M2 Max (macOS 26). If you are on an Intel Mac, use Docker Desktop or a Linux VM instead.

## Install

Apple Container is distributed as a **signed installer package** via the project's GitHub releases (`apple/container`). The standard path is to download the latest `.pkg` from the [releases page](https://github.com/apple/container/releases) and install it:

```bash
# Download the signed installer .pkg from the apple/container releases page
# (grab the latest release asset in a browser, or with curl/gh), then:
sudo installer -pkg ~/Downloads/container-installer-signed.pkg -target /

# Confirm the CLI is on PATH and see the version
container --version        # e.g. container CLI version 1.1.0
```

!!! tip "Verify the install method for your version"
    Exact asset names and any Homebrew tap change over time. Check the [apple/container releases](https://github.com/apple/container/releases) and the project README for the current recommended install for your macOS version rather than assuming an asset filename. The `container` version verified for this section is **1.1.0**.

## Start, check, stop the service

Apple Container runs a background **API server** (a launchd service) that the CLI talks to. Starting it the first time registers the service; you manage it through `container system`:

```bash
container system start     # register + start the apiserver (launchd service)
container system status    # is the service up? which version is it running?
container system stop      # stop the apiserver
```

`container system start` is what stands up the service after install (and after a reboot if it isn't set to auto-start). Confirm both the CLI and the running service agree on version — this matters for the gotcha below:

```bash
container system status | grep version
```

!!! note "Logs"
    The service and containers emit logs viewable through the CLI (standard usage: `container system logs`, and `container logs <name>` for a specific container). Exact subcommand syntax varies by version — run `container system --help` and `container --help` to see what your build exposes rather than relying on a fixed incantation.

## The version-mismatch gotcha (read this)

This one actually happened during testing, upgrading the CLI from **0.7.1 to 1.1.0**, and it is the single most confusing failure mode:

**After you upgrade the `container` CLI, the already-running apiserver stays on the OLD version.** The new CLI and the old service disagree, and then **every** command fails with:

```text
Error: failed to decode apiServerBuild in health check
```

It looks catastrophic — nothing works, no container command runs — but the fix is trivial: **reload the apiserver** so it comes up on the new version.

```bash
# EVERY command failing with "failed to decode apiServerBuild in health check"?
# The apiserver is still on the pre-upgrade version. Reload it:
container system stop
container system start

# Now the running service matches the CLI:
container system status | grep version     # should match `container --version`
```

!!! warning "Always restart the service after upgrading the CLI"
    Make `container system stop && container system start` a reflex immediately after every CLI upgrade. The `failed to decode apiServerBuild in health check` error means exactly one thing here — a stale apiserver — and the stop/start cycle is the whole fix. Don't go hunting for a deeper problem.

## Uninstall and reset

To stop everything and clean up, stop the service first, then remove the tool. Because each container is a small VM with its own state, a **reset** (blow away containers/images and start fresh) is the usual first move when something is wedged, short of a full uninstall:

```bash
# Stop the service
container system stop

# Remove running/stopped containers and unused images (standard cleanup)
container ls -a                 # see what exists first
container rm --all             # remove containers  (verify flag via `container rm --help`)
container images ls            # see cached images
# then remove images you no longer want with `container images rm <ref>`
```

For a **full uninstall**, remove the installed tool per the project's documented uninstall step (the installer package ships with, or the README documents, the removal procedure — check [apple/container](https://github.com/apple/container) for the exact command for your version). After uninstalling, the apiserver launchd service is deregistered by the same step.

!!! tip "When in doubt, restart the service before you reset"
    A lot of "it's broken" moments are the stale-apiserver gotcha above, not corrupted state. Try `container system stop && container system start` first; only reach for removing containers/images or a full uninstall if a clean service restart doesn't clear it.

## Verify

```bash
container --version                        # CLI version (1.1.0 here)
container system status                    # service up
container system status | grep version     # service version matches the CLI
container run --rm docker.io/library/ubuntu:24.04 echo ok   # end-to-end: pull + run
```

If that last line prints `ok`, the service is healthy, the registry is reachable, and a microVM booted, ran, and tore down cleanly.

## Next steps

- [Running containers](running-containers.md) — pull and run images, ports, volumes, `exec`, per-container IPs, `--rosetta`, and building.
- [Limitations](limitations.md) — GPU/Metal and Linux-only-guest boundaries, plus the Docker/Incus comparison.
- [Section overview](index.md) — the microVM-per-container model and where this fits the build.
