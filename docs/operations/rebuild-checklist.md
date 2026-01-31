# Rebuild Checklist

## When to Use

Use this checklist when:

- Host OS is corrupted
- Major OS upgrade (fresh install preferred)
- Hardware replacement

## Prerequisites

- [ ] ZFS pool is healthy (`zpool status tank`)
- [ ] Recent backups verified
- [ ] Ubuntu Server ISO ready
- [ ] SSH keys backed up

## Phase 1: Prepare

```bash
# Export pool cleanly (if possible)
sudo zpool export tank

# Document current state
zfs list > ~/zfs-datasets.txt
zpool status > ~/zpool-status.txt
docker ps -a > ~/docker-containers.txt
virsh list --all > ~/vm-list.txt
```

## Phase 2: Install Ubuntu

1. Boot from USB
2. Install Ubuntu Server 24.04 LTS
3. Use same partition layout:
    - 512 MB EFI
    - 1 GB /boot (ext4)
    - ~1 TB / (ext4)
    - Leave remaining space for ZFS
4. Create same user account
5. Enable SSH

## Phase 3: Base Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Set timezone
sudo timedatectl set-timezone Europe/Oslo

# Install essentials
sudo apt install -y vim htop tmux git curl wget

# Restore SSH keys
# Copy from backup to ~/.ssh/
```

## Phase 4: Import ZFS Pool

```bash
# Install ZFS
sudo apt install -y zfsutils-linux

# Import pool
sudo zpool import tank

# Verify
zpool status tank
zfs list
```

## Phase 5: Install Virtualization

```bash
# Install KVM stack
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients \
    bridge-utils virtinst ovmf

# Add user to groups
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER

# Enable libvirt
sudo systemctl enable --now libvirtd

# Recreate storage pool
virsh pool-define-as vm-pool dir - - - - /mnt/tank/vm
virsh pool-start vm-pool
virsh pool-autostart vm-pool
```

## Phase 6: Restore GPU Passthrough

```bash
# Edit GRUB
sudo vim /etc/default/grub
# Add: amd_iommu=on iommu=pt

# Create VFIO config
sudo vim /etc/modprobe.d/vfio.conf
# Add: options vfio-pci ids=1002:xxxx,1002:yyyy

# Create modules config
sudo vim /etc/modules-load.d/vfio.conf
# Add: vfio-pci, vfio, vfio_iommu_type1

# Blacklist AMD drivers
sudo vim /etc/modprobe.d/blacklist-amd.conf
# Add: blacklist amdgpu, blacklist radeon

# Update and reboot
sudo update-grub
sudo update-initramfs -u
sudo reboot
```

## Phase 7: Install Docker

```bash
# Add Docker repository
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
```

## Phase 8: Restore Services

```bash
# Clone or restore compose files
cd ~
git clone <your-docker-configs-repo> docker

# Start services
cd ~/docker/nextcloud && docker compose up -d
cd ~/docker/plex && docker compose up -d
```

## Phase 9: Restore VMs

```bash
# VMs should still be defined if pool was imported
virsh list --all

# If not, redefine from XML backups
virsh define /path/to/win11.xml

# Start VMs
virsh start win11
```

## Phase 10: Configure Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw enable
```

## Verification Checklist

- [ ] ZFS pool mounted at /mnt/tank
- [ ] All datasets accessible
- [ ] Docker services running
- [ ] VMs starting correctly
- [ ] GPU passthrough working
- [ ] SSH access confirmed
- [ ] Firewall enabled
