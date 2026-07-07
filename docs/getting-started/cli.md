# The `msai` CLI

`msai` is the project's command-line tool. Top-level commands cover the real
hardware; the VirtualBox rehearsal lab lives under `msai lab`.

```
msai doctor      # health checks (run ON the MS-S1 MAX)
msai bootstrap   # install the stack (packages + daemons)
msai profile     # server/desktop profile used by doctor
msai lab ...      # VirtualBox rehearsal lab (create/apply/snapshot/...)
msai docs        # serve these docs locally
```

## `msai doctor` — health checks

Runs categorized checks (system, ZFS, Docker, KVM, GPU, inference, Tailscale) and
reports OK / WARN / FAIL / SKIP per item. Run it on the machine itself.

```bash
msai doctor              # all categories
msai doctor gpu          # one category
msai doctor --fix        # also print the remediation command for each issue
msai doctor --apply      # actually run the fixes (prompts before each)
msai doctor --apply -y   # auto-apply the safe fixes, prompt only for the rest
```

`--apply` classifies each fix: idempotent, non-destructive ones (starting a
service, disabling the audio codec power-save, ...) are "safe" and auto-run
with `-y`; anything that installs packages or changes state always prompts.
Fixes run through a shell, so `sudo` password prompts and pipes work.

## `msai profile` — server vs desktop

The same check can mean different things depending on the box. On the
provisioned server, a missing ZFS pool or KVM is a real failure; on an
experimental Ubuntu **desktop** install of the same hardware it is simply not
set up yet. The active profile decides which categories are expected — findings
in unexpected categories are softened to SKIP instead of showing red.

```bash
msai profile              # show the active profile and how it was resolved
msai profile set desktop  # persist a choice (server | desktop)
```

Resolution order: the `MSAI_PROFILE` environment variable, then the saved
config (`~/.config/msai/profile`), then autodetection from the systemd default
target (a graphical target autodetects as `desktop`, headless as `server`).

## `msai bootstrap` — install the stack

Brings a fresh Ubuntu install up to the target software state, driven by a
declarative manifest (`src/msai_setup/install/components.toml`). It installs
**packages and daemons only** — Docker, ZFS userland tools, Incus, ROCm
(gfx1151), KVM/libvirt, Tailscale, and llama.cpp. Disk partitioning and ZFS
**pool creation stay manual** (see [Disk Partitioning](../ubuntu/installation/disk-partitioning.md)),
because that is destructive and the [NVMe enumeration is reversed](hardware.md)
from the slot numbering. `incus admin init` (storage/network setup) is also left
to you, as it is interactive.

For llama.cpp there are two backend components (plain GGUF, OpenAI-compatible
`llama-server`):

- **`llamacpp-vulkan`** — the default, installed on `PATH`. On this Strix Halo,
  Vulkan (RADV) benchmarks faster than ROCm/HIP for inference (prompt processing
  ~2.4× faster; token generation slightly faster).
- **`llamacpp-hip`** — the ROCm/HIP build, kept under `/opt/llama.cpp-hip/build/bin`
  for A/B benchmarking. ROCm itself stays installed (the `rocm` component) for
  PyTorch/vLLM/fine-tuning, which Vulkan cannot do.

```bash
msai bootstrap --dry-run       # print the plan, run nothing (start here)
msai bootstrap                 # install everything, prompting per component
msai bootstrap docker rocm     # only the named components
msai bootstrap -y              # skip the per-component prompt
msai bootstrap --force         # install even if already detected
```

Every component is idempotent: a component whose `detect` probe passes (e.g.
`command -v docker`) is skipped. A failing component warns and the run
continues rather than aborting the rest. Group changes (docker, render, libvirt)
take effect on next login; verify afterwards with `msai doctor`.

!!! note "Tailscale and llama.cpp"
    `bootstrap` installs Tailscale but does not run `sudo tailscale up` (that is
    interactive browser auth); connect afterwards. Both `llamacpp-*` components
    are real source builds (several minutes each); the HIP one needs the `rocm`
    component first. `msai doctor inference` confirms the default `llama-server`
    lists a GPU device (Vulkan or ROCm).

## `msai lab` — the rehearsal lab

Everything for the VirtualBox practice environment is grouped here:
`msai lab create`, `msai lab apply`, `msai lab ssh`, `msai lab snapshot`,
`msai lab status`, `msai lab destroy`, and more. See the
[VirtualBox lab](../zfs/virtualbox-lab.md) walkthrough.
