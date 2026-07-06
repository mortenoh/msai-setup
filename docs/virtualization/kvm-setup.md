# KVM Setup

!!! note "Background — Incus manages VMs on this build, not bare libvirt"
    This build creates and runs VMs through **[Incus](../incus/index.md)**
    ([Incus VMs](../incus/vms.md)), which drives QEMU/KVM itself. You do
    **not** need to install `libvirt-daemon-system`/`virtinst` or run
    `virsh`/`virt-manager` to run the VMs documented for this box — Incus
    (installed per [Incus installation](../incus/installation.md)) provides
    the VM lifecycle, TPM, Secure Boot, and storage.

    This page is retained as **background on the KVM/QEMU stack Incus sits
    on** — what the pieces are, how to confirm KVM is available on the
    hardware. The libvirt-specific setup below (storage pools, `virsh`
    networks, `virt-manager` over SSH) describes the *old* direct-libvirt
    path and is superseded; read it to understand the stack, not to operate
    this build.

## Confirming KVM is available

The one genuinely still-relevant check: the hardware and kernel support KVM.
Incus needs this too.

```bash
# CPU virtualization (AMD-V / SVM on this Ryzen part) — expect a non-zero count
egrep -c '(vmx|svm)' /proc/cpuinfo

# KVM kernel modules loaded (kvm + kvm_amd on AMD)
lsmod | grep kvm
```

If those are healthy, Incus can run VMs. The remainder of this page is the
legacy direct-libvirt setup, kept for background only.

## Install Virtualization Packages (legacy direct-libvirt path)

```bash
sudo apt install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virtinst \
    ovmf \
    swtpm \
    swtpm-tools
```

`swtpm` provides the emulated TPM 2.0 that Windows 11 requires for installation. `ovmf` ships both the standard and Secure-Boot variants of the UEFI firmware (`OVMF_CODE.fd` and `OVMF_CODE.secboot.fd`).

## Verify KVM Support

```bash
# Check CPU virtualization
egrep -c '(vmx|svm)' /proc/cpuinfo

# Verify KVM modules
lsmod | grep kvm
```

## Configure libvirt

### Add User to Groups

```bash
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
```

Log out and back in for group changes.

### Enable libvirt

```bash
sudo systemctl enable --now libvirtd
```

### Verify

```bash
virsh list --all
```

## Storage Pool

Create a ZFS-backed storage pool:

```bash
virsh pool-define-as vm-pool dir - - - - /mnt/tank/vm
virsh pool-start vm-pool
virsh pool-autostart vm-pool
```

## Network Configuration

### Default NAT Network

libvirt creates a default NAT network. Verify:

```bash
virsh net-list --all
```

### Bridge Network (Optional)

For VMs on the same network as the host:

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [enp5s0]
      dhcp4: true
```

## Remote Management

### virt-manager over SSH (recommended)

Install `virt-manager` **on your workstation/Mac** and point it at the headless server:

```bash
virt-manager -c qemu+ssh://user@ms-s1-max/system
```

`virt-manager` runs locally as a Python/GTK app and talks to `libvirtd` on the server over SSH — no X11 forwarding required.

!!! note "X11 forwarding is not needed"
    Earlier drafts of this doc recommended enabling `X11Forwarding yes` in sshd. That's only relevant if you intended to run `virt-manager` *on* the server and tunnel its GUI back, which contradicts the headless model. Leave `X11Forwarding no` on the server.

## VM Best Practices

| Setting | Value | Reason |
|---------|-------|--------|
| Chipset | Q35 | Modern, PCIe support |
| Firmware | UEFI (OVMF) | Required for GPU passthrough |
| CPU | host-passthrough | Full CPU features |
| Disk | virtio | Best performance |
| Network | virtio | Best performance |
