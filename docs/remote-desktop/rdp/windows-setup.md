# Windows RDP Setup

Configure Remote Desktop on Windows 10/11 VMs and servers.

## Enable Remote Desktop

### Via Settings (Windows 10/11)

1. Open **Settings** > **System** > **Remote Desktop**
2. Toggle **Enable Remote Desktop** to On
3. Confirm the prompt
4. Note your **PC name** for connections

### Via System Properties

1. Press ++win+pause++ or right-click Start > System
2. Click **Remote Desktop** in the left panel
3. Enable Remote Desktop
4. Click **Select users** to add non-admin users

### Via Command Line (Admin)

```powershell
# Enable RDP
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# Enable firewall rule
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# Set NLA requirement (recommended)
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 1
```

## Verify RDP is Working

```powershell
# Check RDP service status
Get-Service TermService

# Check listening port
netstat -an | findstr 3389

# Check firewall rules
Get-NetFirewallRule -DisplayGroup "Remote Desktop" | Select DisplayName, Enabled
```

## User Permissions

### Add Users to Remote Desktop Users

```powershell
# Add user to Remote Desktop Users group
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "username"

# View current members
Get-LocalGroupMember -Group "Remote Desktop Users"
```

### Via GUI

1. Right-click Start > Computer Management
2. Local Users and Groups > Groups
3. Double-click "Remote Desktop Users"
4. Add users

## Network Level Authentication (NLA)

NLA provides pre-authentication security.

### Why NLA Matters

| Without NLA | With NLA |
|-------------|----------|
| Login screen shown to anyone | Auth required before session |
| Vulnerable to pre-auth attacks | Prevents unauthorized access |
| Uses more server resources | More efficient |

### Enable NLA (Recommended)

```powershell
# Require NLA
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 1
```

### Disable NLA (If Needed)

Some older clients don't support NLA:

```powershell
# Allow connections without NLA (less secure)
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 0
```

## Firewall Configuration

### Windows Firewall

RDP firewall rules are created automatically but verify:

```powershell
# View RDP firewall rules
Get-NetFirewallRule -DisplayGroup "Remote Desktop"

# Enable if disabled
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```

### Restrict to Specific Networks

```powershell
# Restrict RDP to Tailscale network only
Set-NetFirewallRule -DisplayName "Remote Desktop - User Mode (TCP-In)" -RemoteAddress 100.64.0.0/10
```

## Multi-Monitor Support

### Enable Full Multi-Monitor

In client connection settings:
1. Display tab
2. Check "Use all monitors for the remote session"

Or via RDP file:

```
use multimon:i:1
```

## Audio Redirection

### Enable Remote Audio

1. In RDP client, go to Local Resources tab
2. Under Remote audio, click Settings
3. Select "Play on this computer"

### Audio Recording

To enable microphone:
1. Local Resources > Remote audio settings
2. Check "Record from this computer"

## Drive and Clipboard Redirection

### Map Local Drives

1. Local Resources tab
2. Click "More" under Local devices
3. Select drives to share

### Clipboard Settings

Clipboard is enabled by default. To verify:

```powershell
# Check clipboard redirection
Get-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' -Name fDisableClip -ErrorAction SilentlyContinue
```

## Performance Optimization

### For LAN/Tailscale (High Bandwidth)

RDP connection settings:
- Experience: LAN
- Enable: Desktop composition, Font smoothing, Visual styles

### For Slow Connections

- Experience: Low-speed broadband
- Disable: Desktop background, Visual styles
- Reduce color depth to 16-bit

### Group Policy Optimizations

```powershell
# Set optimal video compression
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' -Name 'AVCHardwareEncodePreferred' -Value 1 -Type DWord
```

## Session Settings

### Timeout Configuration

Via Group Policy (`gpedit.msc`):
- Computer Configuration > Administrative Templates > Windows Components > Remote Desktop Services > Session Time Limits

Or via PowerShell:

```powershell
# Set idle timeout (milliseconds)
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' -Name 'MaxIdleTime' -Value 3600000 -Type DWord
```

### Limit Sessions Per User

```powershell
# One session per user
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' -Name 'fSingleSessionPerUser' -Value 1 -Type DWord
```

## RDP Port Change (Optional)

Changing from default 3389 provides minor security through obscurity.

```powershell
# Change RDP port to 3390
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "PortNumber" -Value 3390

# Update firewall
New-NetFirewallRule -DisplayName "RDP Custom Port" -Direction Inbound -LocalPort 3390 -Protocol TCP -Action Allow

# Restart RDP service
Restart-Service TermService -Force
```

## Troubleshooting

### Cannot Connect

```powershell
# Verify RDP is enabled
(Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server').fDenyTSConnections

# Check service is running
Get-Service TermService | Select Status

# Test port accessibility (from client)
Test-NetConnection -ComputerName vm-ip -Port 3389
```

### NLA Authentication Errors

1. Verify clocks are synchronized
2. Check client supports NLA
3. Try disabling NLA temporarily to test

### Slow Performance

1. Reduce color depth
2. Disable visual effects
3. Check network latency
4. Verify hardware acceleration

### Black Screen After Connect

1. Wait 30 seconds (GPU initialization)
2. Press ++ctrl+alt+end++ then sign out
3. Check GPU drivers
4. Disable UDP in client (for testing)

## Security Checklist

- [ ] Remote Desktop enabled only when needed
- [ ] NLA enabled
- [ ] Strong passwords for RDP users
- [ ] Firewall restricts source IPs
- [ ] Not exposed to internet
- [ ] Using Tailscale or VPN for remote access
- [ ] Account lockout policy configured
- [ ] Security updates current
