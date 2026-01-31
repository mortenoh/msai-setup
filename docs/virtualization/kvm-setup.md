# KVM Setup

## Install Virtualization Packages

```bash
sudo apt install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virtinst \
    ovmf
```

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

### virt-manager over SSH

From your workstation:

```bash
virt-manager -c qemu+ssh://user@ms-s1-max/system
```

### Enable SSH X11 Forwarding

On the server, edit `/etc/ssh/sshd_config`:

```
X11Forwarding yes
```

## VM Best Practices

| Setting | Value | Reason |
|---------|-------|--------|
| Chipset | Q35 | Modern, PCIe support |
| Firmware | UEFI (OVMF) | Required for GPU passthrough |
| CPU | host-passthrough | Full CPU features |
| Disk | virtio | Best performance |
| Network | virtio | Best performance |
