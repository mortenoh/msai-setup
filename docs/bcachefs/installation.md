# Bcachefs Installation

Since bcachefs was removed from the mainline kernel in Linux 6.18, installation requires building the DKMS module from source.

## Prerequisites

### Kernel Headers

Install headers matching your running kernel:

```bash
sudo apt update
sudo apt install linux-headers-$(uname -r)
```

### Build Dependencies

```bash
sudo apt install build-essential git pkg-config liblz4-dev \
    libzstd-dev libuuid-dev libblkid-dev libkeyutils-dev \
    liburcu-dev libsodium-dev liburing-dev
```

## Installation Methods

### Method 1: bcachefs-tools PPA (Recommended)

The bcachefs project maintains a PPA with pre-built packages:

```bash
# Add the PPA
sudo add-apt-repository ppa:bcachefs/ppa
sudo apt update

# Install tools and DKMS module
sudo apt install bcachefs-tools bcachefs-dkms
```

### Method 2: Build from Source

Clone and build the kernel module and userspace tools:

```bash
# Clone the repository
git clone https://github.com/koverstreet/bcachefs-tools.git
cd bcachefs-tools

# Build userspace tools
make
sudo make install

# Build and install DKMS module
cd ../
git clone https://github.com/koverstreet/bcachefs.git
cd bcachefs
sudo dkms add .
sudo dkms build bcachefs/$(cat VERSION)
sudo dkms install bcachefs/$(cat VERSION)
```

## Loading the Module

### Manual Loading

```bash
sudo modprobe bcachefs
```

### Verify Module Loaded

```bash
lsmod | grep bcachefs
```

### Load at Boot

```bash
echo 'bcachefs' | sudo tee /etc/modules-load.d/bcachefs.conf
```

## Verify Installation

Check that bcachefs tools are available:

```bash
# Check version
bcachefs version

# List available commands
bcachefs help
```

## Updating Bcachefs

### PPA Updates

```bash
sudo apt update
sudo apt upgrade bcachefs-tools bcachefs-dkms
```

### Source Updates

```bash
cd bcachefs-tools
git pull
make clean
make
sudo make install
```

After kernel updates, rebuild the DKMS module:

```bash
sudo dkms autoinstall
```

## Troubleshooting

### Module Won't Load

Check for build errors in DKMS:

```bash
dkms status
cat /var/lib/dkms/bcachefs/*/build/make.log
```

### Missing Kernel Headers

Ensure headers match your kernel exactly:

```bash
uname -r
apt list --installed | grep linux-headers
```

### Secure Boot Issues

If Secure Boot is enabled, you may need to sign the module:

```bash
# Generate signing key (if not already done)
sudo mokutil --generate-key
sudo mokutil --import MOK.der

# Reboot and enroll the key in MOK manager
# Then sign the module
sudo /usr/src/kernels/$(uname -r)/scripts/sign-file sha256 \
    /path/to/MOK.priv /path/to/MOK.der \
    /lib/modules/$(uname -r)/updates/dkms/bcachefs.ko
```

## Next Steps

After installation, proceed to [Usage](usage.md) to create your first bcachefs filesystem.
