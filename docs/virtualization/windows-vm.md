# Windows 11 VM (superseded — see the Incus page)

!!! warning "This walkthrough is superseded — use the Incus Windows 11 VM page"
    The Windows 11 VM on this build is an **[Incus VM instance](../incus/windows-vm.md)**,
    created with `incus` — not with `virt-install`/`virsh`/`virt-manager`.
    The `virt-install` command and libvirt XML that used to live here have
    been **replaced** by the `incus` equivalents. Do not follow a bare
    `virt-install` recipe to build the real Windows VM on this box.

    **Go to [Incus Windows 11 VM](../incus/windows-vm.md)** for the current,
    canonical walkthrough: TPM 2.0 via Incus's `tpm` device, Secure Boot via
    the `security.secureboot` config key, virtio driver loading, RDP, and the
    "iGPU stays with the host" decision.

This page is kept only as a short pointer plus the small amount of
Windows-guest background that is independent of which tool drives QEMU.

## What carried over unchanged

The Windows-specific *requirements* did not change with the pivot to Incus —
only the tool that satisfies them did:

| Windows 11 needs | Old (libvirt) | Now (Incus) |
|---|---|---|
| TPM 2.0 | `swtpm` + `--tpm` in `virt-install` | `incus config device add win11 vtpm tpm` |
| Secure Boot | `OVMF_CODE.secboot.fd` loader | `security.secureboot` (defaults to `true`) |
| virtio disk/NIC drivers | virtio-win ISO, load `viostor`/NetKVM | virtio-win ISO, same drivers — attached as an Incus `disk` device |
| Day-to-day access | RDP over the NAT network | RDP via an Incus `proxy` device, gated by UFW |
| GPU | virtio-gpu, host keeps the iGPU for ROCm | unchanged — virtio graphics, no passthrough |

## The GPU decision (unchanged)

!!! note "The iGPU stays with the host — no passthrough to the Windows VM"
    This is a deliberate, unchanged decision: the Strix Halo iGPU stays with
    the **host** for ROCm-based local LLM inference (this box's primary
    purpose), so the Windows VM runs on virtio graphics and is reached over
    RDP. Host ROCm and GPU passthrough are mutually exclusive. If you ever
    want to flip that trade-off, see [GPU Passthrough](gpu-passthrough.md) —
    but understand it takes host AI workloads offline whenever the VM runs.

## Windows-guest notes worth keeping

These apply regardless of the hypervisor front-end and are still useful when
you follow the Incus walkthrough:

- **Load the virtio block driver during install.** Windows setup shows *no
  disk* until you "Load driver" from the virtio-win ISO and pick `viostor`
  for your Windows version (`amd64\w11`). The disk then appears.
- **Install the rest of the virtio drivers after first boot** (NetKVM for
  networking, balloon, etc.) from the same ISO's guest-tools installer — the
  NIC won't work until NetKVM is in.
- **Pin the VM's vCPUs to a single CCX.** The Ryzen AI Max+ 395 is 2 x CCX of
  8 cores; keeping an interactive Windows guest on one CCX avoids the
  cross-CCX L3 penalty. Under Incus this is `limits.cpu.pin` rather than
  libvirt `<vcpupin>` — see [VM Resources](vm-resources.md) for the mapping
  and [Incus VMs](../incus/vms.md#resource-allocation) for the commands.
- **RDP is LAN/Tailscale only, never the public internet.** Same rule as the
  rest of the build; the [RDP setup convention](../remote-desktop/rdp/windows-setup.md)
  applies verbatim to an Incus-hosted guest.

## Next steps

- [Incus Windows 11 VM](../incus/windows-vm.md) - the canonical current
  walkthrough.
- [Incus VMs](../incus/vms.md) - the general VM model it builds on.
- [Windows RDP Setup](../remote-desktop/rdp/windows-setup.md) - enabling RDP
  inside the guest.
