# Wireless Configuration

## Overview

Netplan supports WiFi configuration for both client connections and access points. For servers, WiFi is typically used as:

- Backup connectivity
- Out-of-band management
- Edge/IoT deployments

!!! note "Server Use Case"
    While this documentation focuses on server setups, WiFi is occasionally needed for portable servers, edge computing, or emergency access.

## Basic WiFi Connection

### WPA2 Personal (Most Common)

```yaml
network:
  version: 2
  renderer: NetworkManager  # Required for WiFi

  wifis:
    wlan0:
      access-points:
        "MyNetworkSSID":
          password: "secretpassword"
      dhcp4: true
```

### WPA3 Personal

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "SecureNetwork":
          password: "secretpassword"
          # WPA3 is auto-negotiated when available
      dhcp4: true
```

### Static IP

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "MyNetwork":
          password: "secretpassword"
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
```

## Hidden Networks

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "HiddenNetwork":
          password: "secretpassword"
          hidden: true
      dhcp4: true
```

## Open Networks

!!! warning "Security Risk"
    Open networks have no encryption. Use VPN if connecting to open networks.

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "OpenCafe": {}
      dhcp4: true
```

## Enterprise WiFi (WPA2/WPA3 Enterprise)

### PEAP/MSCHAPv2

Common in corporate environments:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "CorpNetwork":
          auth:
            key-management: eap
            method: peap
            identity: "username@corp.com"
            password: "userpassword"
      dhcp4: true
```

### EAP-TLS (Certificate-Based)

Most secure enterprise option:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "SecureCorpNetwork":
          auth:
            key-management: eap
            method: tls
            identity: "user@corp.com"
            ca-certificate: /etc/ssl/certs/corp-ca.pem
            client-certificate: /etc/ssl/certs/user-cert.pem
            client-key: /etc/ssl/private/user-key.pem
            client-key-password: "keypassword"
      dhcp4: true
```

### EAP-TTLS

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "CorpWiFi":
          auth:
            key-management: eap
            method: ttls
            anonymous-identity: "anonymous@corp.com"
            identity: "user@corp.com"
            password: "password"
            ca-certificate: /etc/ssl/certs/corp-ca.pem
      dhcp4: true
```

## Multiple Networks

Priority-based connection:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        # Highest priority - office
        "OfficeWiFi":
          password: "officepass"

        # Home network
        "HomeNetwork":
          password: "homepass"

        # Backup - mobile hotspot
        "MyPhone":
          password: "phonepass"

      dhcp4: true
```

## Band Selection

### Prefer 5GHz

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "DualBandNetwork":
          password: "password"
          band: 5GHz  # Prefer 5GHz band
      dhcp4: true
```

### 2.4GHz Only

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "LegacyNetwork":
          password: "password"
          band: 2.4GHz
      dhcp4: true
```

## BSSID Lock

Connect to specific access point:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "MultiAPNetwork":
          password: "password"
          bssid: "aa:bb:cc:dd:ee:ff"  # Specific AP MAC
      dhcp4: true
```

## WiFi Power Management

### Disable Power Saving

For stable connections:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "MyNetwork":
          password: "password"
      dhcp4: true
      # Power management via NetworkManager
      networkmanager:
        passthrough:
          wifi.powersave: "2"  # Disable power save
```

## MAC Address Handling

### Random MAC (Privacy)

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "PublicWiFi":
          password: "password"
      macaddress: random
      dhcp4: true
```

### Stable Random MAC

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "MyNetwork":
          password: "password"
      macaddress: stable
      dhcp4: true
```

### Permanent MAC

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "MACFilteredNetwork":
          password: "password"
      macaddress: permanent  # Use hardware MAC
      dhcp4: true
```

### Custom MAC

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      macaddress: "aa:bb:cc:dd:ee:ff"
      access-points:
        "MyNetwork":
          password: "password"
      dhcp4: true
```

## WiFi as Backup Link

### Primary Ethernet, Backup WiFi

```yaml
network:
  version: 2
  renderer: NetworkManager

  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        route-metric: 100  # Preferred

  wifis:
    wlan0:
      access-points:
        "BackupNetwork":
          password: "password"
      dhcp4: true
      dhcp4-overrides:
        route-metric: 600  # Fallback
```

## WiFi with Match

### Match by Driver

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    any-wifi:
      match:
        driver: "iwlwifi"
      access-points:
        "MyNetwork":
          password: "password"
      dhcp4: true
```

## Regulatory Domain

Set WiFi regulatory country:

```bash
# Set regulatory domain (run before WiFi config)
sudo iw reg set US
```

Or via configuration:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      regulatory-domain: US
      access-points:
        "MyNetwork":
          password: "password"
      dhcp4: true
```

## WiFi Access Point Mode

Create a hotspot:

```yaml
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      access-points:
        "MyHotspot":
          password: "hotspotpass"
          mode: ap
          band: 5GHz
      addresses:
        - 10.42.0.1/24
```

!!! note "Additional Setup"
    AP mode requires dnsmasq or similar for DHCP, and hostapd is typically used for more robust AP functionality.

## WiFi + Ethernet Bridge

Bridge WiFi to wired network (not commonly supported):

```yaml
# Most WiFi drivers don't support bridging directly
# Use routing instead

network:
  version: 2
  renderer: NetworkManager

  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.1/24

  wifis:
    wlan0:
      access-points:
        "InternetAccess":
          password: "password"
      dhcp4: true
```

Then enable routing:

```bash
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Add NAT
iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
```

## Verifying WiFi Configuration

### Check Connection Status

```bash
# NetworkManager status
nmcli device wifi list

# Current connection
nmcli connection show --active

# Detailed WiFi info
iwconfig wlan0

# Signal quality
iw dev wlan0 link
```

### Check IP Configuration

```bash
ip addr show wlan0
ip route show dev wlan0
```

### Scan for Networks

```bash
# Using NetworkManager
nmcli device wifi rescan
nmcli device wifi list

# Using iw
sudo iw dev wlan0 scan | grep -E "SSID|signal|freq"
```

## Troubleshooting WiFi

### WiFi Interface Not Found

```bash
# Check hardware
lspci | grep -i wireless
lsusb | grep -i wireless

# Check drivers
lsmod | grep -E "iwl|ath|rtl|brcm"

# Check interface exists
ip link show

# Check rfkill
rfkill list
```

### Cannot Connect

```bash
# Check NetworkManager status
systemctl status NetworkManager

# View connection attempts
journalctl -u NetworkManager -f

# Check wpa_supplicant (if using networkd)
journalctl -u wpa_supplicant -f
```

### Weak Signal

```bash
# Check signal strength
iw dev wlan0 link

# Try different band
# Edit netplan to specify band: 5GHz or band: 2.4GHz
```

### Authentication Failures

```bash
# Check password
# Passwords are stored in /etc/netplan/*.yaml

# For enterprise, verify certificates
openssl verify -CAfile /etc/ssl/certs/corp-ca.pem /etc/ssl/certs/user-cert.pem

# Check system time (important for certificates)
date
```

### Disconnecting Frequently

```bash
# Disable power management
sudo iw dev wlan0 set power_save off

# Or via NetworkManager
nmcli connection modify "MyNetwork" wifi.powersave 2
```

## Security Best Practices

1. **Use WPA3 when available** - Strongest encryption
2. **Prefer EAP-TLS for enterprise** - Certificate-based is more secure than passwords
3. **Avoid open networks** - Use VPN if you must connect
4. **Randomize MAC** - On untrusted networks for privacy
5. **Keep firmware updated** - WiFi vulnerabilities are common
6. **Use 5GHz when possible** - Shorter range = harder to intercept

## Server WiFi Checklist

For servers using WiFi:

- [ ] Is WiFi the only option? Wired is more reliable
- [ ] Is the access point enterprise-grade?
- [ ] Is the signal strong and stable?
- [ ] Is there a wired fallback?
- [ ] Are proper security protocols in use?
- [ ] Is the server's WiFi adapter reliable?
- [ ] Is power management disabled?
- [ ] Are there alerts for disconnection?
