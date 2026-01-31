# Other Platforms

## macOS

### App Store

The easiest installation method:

1. Open the **Mac App Store**
2. Search for "Tailscale"
3. Click **Get** to install
4. Open Tailscale from Applications
5. Click the menu bar icon to connect

### Homebrew

```bash
brew install --cask tailscale
```

### Standalone Package

Download from [tailscale.com/download](https://tailscale.com/download):

1. Download the `.pkg` file
2. Double-click to install
3. Follow the installation wizard

### CLI Access on macOS

The macOS app includes CLI tools:

```bash
# Add to PATH (if needed)
export PATH="/Applications/Tailscale.app/Contents/MacOS:$PATH"

# Or use full path
/Applications/Tailscale.app/Contents/MacOS/Tailscale status
```

### macOS System Extension

Tailscale uses a system extension that requires approval:

1. Go to **System Preferences** → **Security & Privacy**
2. Click **Allow** for Tailscale extension
3. May require restart

## Windows

### GUI Installer

1. Download from [tailscale.com/download](https://tailscale.com/download)
2. Run the `.exe` installer
3. Click the system tray icon to connect
4. Authenticate in browser

### Winget

```powershell
winget install Tailscale.Tailscale
```

### Chocolatey

```powershell
choco install tailscale
```

### Windows CLI

```powershell
# Check status
tailscale status

# Connect
tailscale up

# Disconnect
tailscale down
```

### Windows Service

Tailscale runs as a Windows service:

```powershell
# Check service status
Get-Service Tailscale

# Restart service
Restart-Service Tailscale

# View logs
Get-EventLog -LogName Application -Source Tailscale -Newest 50
```

### Windows Server

Same installation as desktop. For headless/unattended:

```powershell
# Download and install silently
$installer = "tailscale-setup.exe"
Invoke-WebRequest -Uri "https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe" -OutFile $installer
Start-Process -FilePath $installer -Args "/quiet" -Wait

# Authenticate with auth key
tailscale up --auth-key=tskey-auth-xxxxx
```

## iOS

### App Store

1. Open the **App Store** on your iPhone/iPad
2. Search for "Tailscale"
3. Tap **Get** to install
4. Open the app and tap **Get Started**
5. Sign in with your identity provider

### Configuration

- Tap the Tailscale icon to toggle connection
- Use the app to manage exit nodes
- Enable/disable MagicDNS in settings

### MDM Deployment

For enterprise deployment, use an MDM configuration profile:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadType</key>
            <string>com.apple.vpn.managed</string>
            <!-- VPN configuration -->
        </dict>
    </array>
</dict>
</plist>
```

## Android

### Google Play Store

1. Open the **Play Store**
2. Search for "Tailscale"
3. Tap **Install**
4. Open the app and sign in

### Direct APK

Download APK from [tailscale.com/download](https://tailscale.com/download) for sideloading.

### Android TV

Install from Play Store on Android TV devices.

### Features

- VPN toggle in quick settings
- Exit node selection
- Taildrop file receiving
- Widget support

## FreeBSD

### Package

```bash
pkg install tailscale

# Enable and start
sysrc tailscaled_enable="YES"
service tailscaled start

# Authenticate
tailscale up
```

### Ports

```bash
cd /usr/ports/security/tailscale
make install clean
```

## OpenBSD

### Package

```bash
pkg_add tailscale

# Start daemon
rcctl enable tailscaled
rcctl start tailscaled

# Authenticate
tailscale up
```

## Synology NAS

### Package Center

1. Open **Package Center**
2. Search for "Tailscale"
3. Click **Install**
4. Open Tailscale from main menu
5. Click **Log in** and authenticate

### SSH Installation (Alternative)

```bash
# SSH into Synology
ssh admin@synology-ip

# Download and install
curl -fsSL https://pkgs.tailscale.com/stable/tailscale_latest_amd64.tgz | tar xzf -
sudo cp tailscale_*/tailscale tailscale_*/tailscaled /usr/local/bin/

# Start manually
sudo /usr/local/bin/tailscaled &
sudo /usr/local/bin/tailscale up
```

## QNAP NAS

### App Center

1. Open **App Center**
2. Search for "Tailscale"
3. Click **Install**
4. Configure through web UI

## TrueNAS

### TrueNAS SCALE (Linux-based)

```bash
# Via Apps
# Navigate to Apps → Available Applications → Tailscale

# Or via CLI
sudo tailscale up
```

### TrueNAS CORE (FreeBSD-based)

Use a jail:

```bash
# Create jail
iocage create -n tailscale -r 13.1-RELEASE

# Enter jail
iocage console tailscale

# Install
pkg install tailscale
```

## Raspberry Pi

### Raspberry Pi OS (Debian-based)

```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Start
sudo tailscale up
```

### Performance Notes

- Works well on Pi 3 and later
- Pi Zero may have limited performance
- Enable hardware crypto if available

### As Exit Node

```bash
# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Advertise as exit node
sudo tailscale up --advertise-exit-node
```

## routers

### OpenWrt

```bash
# Update packages
opkg update

# Install Tailscale
opkg install tailscale

# Start
/etc/init.d/tailscale start
/etc/init.d/tailscale enable

# Authenticate
tailscale up
```

### pfSense/OPNsense

Use the Tailscale package from the package manager:

1. Navigate to **System** → **Package Manager**
2. Search for "tailscale"
3. Install the package
4. Configure through web UI

### Ubiquiti EdgeRouter

```bash
# Add repository
curl -fsSL https://pkgs.tailscale.com/stable/debian/buster.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg] https://pkgs.tailscale.com/stable/debian buster main" | sudo tee /etc/apt/sources.list.d/tailscale.list

# Install
sudo apt update
sudo apt install tailscale

# Configure
sudo tailscale up --advertise-routes=192.168.1.0/24
```

## Virtual Machines

### VMware

Install Tailscale inside the guest OS normally. No special VMware configuration needed.

### VirtualBox

Same as VMware - install in guest OS.

### Hyper-V

Install in guest Windows/Linux normally.

### Proxmox VMs

Install in guest OS. For best performance:

```bash
# In VM
sudo tailscale up --accept-routes
```

## Cloud Instances

### AWS EC2

```bash
# User data script
#!/bin/bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key=tskey-auth-xxxxx --ssh
```

### Google Cloud

```bash
# Startup script
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key=tskey-auth-xxxxx --ssh
```

### Azure

```bash
# Custom script extension
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key=tskey-auth-xxxxx --ssh
```

### DigitalOcean

```bash
# Droplet user data
#!/bin/bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key=tskey-auth-xxxxx --ssh
```

## Embedded/IoT

### General Requirements

- ARM or x86 architecture
- Linux kernel 4.x or later
- ~50MB storage
- ~30MB RAM

### Static Binary

For minimal systems:

```bash
# Download appropriate architecture
# amd64, arm64, arm, 386
wget https://pkgs.tailscale.com/stable/tailscale_latest_arm64.tgz
tar xzf tailscale_latest_arm64.tgz
./tailscale_*/tailscaled &
./tailscale_*/tailscale up
```
