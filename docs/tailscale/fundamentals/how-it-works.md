# How Tailscale Works

## Overview

Tailscale creates a secure mesh network using WireGuard, allowing devices to communicate directly regardless of their network location.

## Core Components

### Coordination Server

The coordination server (control plane) handles:

- **Device registration**: Adding new devices to your network
- **Key distribution**: Sharing public keys between authorized devices
- **ACL enforcement**: Distributing access control policies
- **NAT traversal coordination**: Helping devices find each other

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Control Plane vs Data Plane                               │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     CONTROL PLANE                                    │   │
│   │                  (Tailscale servers)                                 │   │
│   │                                                                      │   │
│   │  • Device registration      • Public key exchange                   │   │
│   │  • ACL distribution         • NAT traversal help                    │   │
│   │  • DNS configuration        • DERP relay coordination               │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                          metadata only                                       │
│                          (no user data)                                      │
│                                   │                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      DATA PLANE                                      │   │
│   │                  (direct connections)                                │   │
│   │                                                                      │   │
│   │      Device A ◄────── WireGuard tunnel ──────► Device B            │   │
│   │                    encrypted, peer-to-peer                          │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

!!! info "Privacy"
    Tailscale's coordination servers never see your actual traffic. They only handle metadata for connection setup.

### Tailscale Client

The client runs on each device:

```bash
# Daemon (runs as root)
tailscaled

# CLI tool (user interface)
tailscale
```

Responsibilities:
- Generate and manage WireGuard keys
- Establish connections to peers
- Configure local network interface
- Enforce ACL policies locally

### DERP Relays

DERP (Designated Encrypted Relay for Packets) servers relay traffic when direct connections fail:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DERP Relay Usage                                      │
│                                                                              │
│   Scenario 1: Direct Connection (preferred)                                 │
│                                                                              │
│   ┌──────────┐                                    ┌──────────┐              │
│   │ Device A │◄───────── direct path ────────────►│ Device B │              │
│   └──────────┘            ~10ms                   └──────────┘              │
│                                                                              │
│   Scenario 2: DERP Relay (fallback)                                         │
│                                                                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐                         │
│   │ Device A │─────►│  DERP    │◄─────│ Device B │                         │
│   └──────────┘      │  Relay   │      └──────────┘                         │
│                     └──────────┘                                            │
│                        ~50ms                                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

DERP is used when:
- Both devices are behind symmetric NAT
- Firewalls block UDP
- Direct path discovery fails

## Connection Process

### 1. Device Registration

```
┌─────────────┐                    ┌─────────────────┐
│   Device    │                    │  Coordination   │
│             │                    │     Server      │
└──────┬──────┘                    └────────┬────────┘
       │                                    │
       │  1. tailscale up                   │
       │─────────────────────────────────►  │
       │                                    │
       │  2. Auth URL                       │
       │  ◄─────────────────────────────────│
       │                                    │
       │  3. User authenticates (browser)   │
       │─────────────────────────────────►  │
       │                                    │
       │  4. Device registered              │
       │  ◄─────────────────────────────────│
       │     - Assigned 100.x.x.x IP        │
       │     - Receives peer list           │
       │     - Gets ACL policies            │
       │                                    │
```

### 2. Key Exchange

Each device has a WireGuard key pair:

```bash
# View your node's public key
tailscale debug prefs | grep -i key
```

The coordination server distributes public keys to authorized peers:

```
Device A                 Coordination              Device B
   │                        │                         │
   │  Public Key A          │                         │
   │───────────────────────►│                         │
   │                        │   Public Key B          │
   │                        │◄────────────────────────│
   │                        │                         │
   │   Peer list + keys     │   Peer list + keys      │
   │◄───────────────────────│────────────────────────►│
   │                        │                         │
```

### 3. NAT Traversal

Tailscale uses multiple techniques to establish direct connections:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    NAT Traversal Techniques                                  │
│                                                                              │
│   1. STUN (Session Traversal Utilities for NAT)                            │
│      ┌────────┐                              ┌────────┐                     │
│      │Device A│──── What's my public IP? ───►│  STUN  │                     │
│      └────────┘◄─── 203.0.113.1:45678 ───────│ Server │                     │
│                                              └────────┘                     │
│                                                                              │
│   2. UDP Hole Punching                                                       │
│      Both devices send packets to each other's public IP:port               │
│      NAT creates mappings, allowing bidirectional traffic                   │
│                                                                              │
│   3. DERP Fallback                                                           │
│      If direct fails, relay through DERP servers                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4. WireGuard Tunnel

Once peers discover each other, they establish a WireGuard tunnel:

```bash
# View active connections
tailscale status

# See connection details
tailscale netcheck

# Ping through tunnel
tailscale ping my-server
```

## IP Addressing

Tailscale assigns each device an IP from the 100.64.0.0/10 CGNAT range:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Tailscale IP Addressing                                   │
│                                                                              │
│   100.64.0.0/10 (CGNAT range, ~4 million IPs)                               │
│                                                                              │
│   Device          Tailscale IP      Local IP         Location              │
│   ─────────────────────────────────────────────────────────────────        │
│   my-laptop       100.100.100.1     192.168.1.50     Home WiFi             │
│   my-server       100.100.100.2     10.0.0.5         Data center           │
│   my-phone        100.100.100.3     172.16.0.100     Mobile network        │
│                                                                              │
│   All devices reachable via 100.x.x.x regardless of physical location      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

!!! note "Stable IPs"
    Tailscale IPs are stable - they don't change when devices move between networks.

## Traffic Flow

### Direct Connection (99% of cases)

```
Your laptop                                          Your server
192.168.1.50                                        10.0.0.5
     │                                                   │
     │ tailscale0: 100.100.1.1                          │ tailscale0: 100.100.1.2
     │         │                                        │         │
     │         └────── WireGuard UDP ──────────────────►│         │
     │                 (encrypted)                      │         │
     │                                                  │         │
     └─── Physical: Home Router ─── Internet ─── DC Router ──────┘
```

### Relayed Connection (rare)

```
Your laptop              DERP Relay              Your server
     │                       │                        │
     │ ────── encrypted ────►│                        │
     │                       │ ────── encrypted ─────►│
     │                       │                        │
     │◄───── encrypted ──────│                        │
     │                       │◄───── encrypted ───────│
```

## Security Model

### End-to-End Encryption

- All traffic encrypted with WireGuard (ChaCha20-Poly1305)
- Keys never leave devices
- Coordination server never sees traffic content

### Authentication

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                                       │
│                                                                              │
│   User ───► Identity Provider ───► Tailscale ───► Device Access            │
│             (Google, Okta,         (verifies      (grants network           │
│              Microsoft, etc.)       identity)      membership)              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Authorization (ACLs)

Access Control Lists define who can access what:

```json
{
  "acls": [
    {"action": "accept", "src": ["group:dev"], "dst": ["tag:server:*"]},
    {"action": "accept", "src": ["autogroup:members"], "dst": ["*:22"]}
  ]
}
```

## Comparison with Traditional VPNs

| Aspect | Traditional VPN | Tailscale |
|--------|-----------------|-----------|
| Architecture | Hub-and-spoke | Mesh |
| Traffic path | Through VPN server | Direct peer-to-peer |
| Single point of failure | VPN server | None |
| Configuration | Complex | Zero-config |
| NAT traversal | Often problematic | Automatic |
| Scaling | Limited by server | Scales naturally |
| Latency | Higher (via server) | Lower (direct) |
