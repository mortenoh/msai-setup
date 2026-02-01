# Fundamentals

Understanding how remote desktop protocols work helps you choose the right one and troubleshoot issues effectively.

## What is a Remote Desktop Protocol?

A remote desktop protocol transmits:

1. **Display data** - Screen contents from server to client
2. **Input events** - Keyboard and mouse from client to server
3. **Clipboard** - Copy/paste between systems
4. **Audio** - Sound from server to client (some protocols)
5. **Devices** - USB redirection (some protocols)

## The Three Protocols

### VNC (Virtual Network Computing)

Originally developed at AT&T Cambridge Laboratory in 1998. VNC uses the RFB (Remote Framebuffer) protocol.

**How it works:**

- Captures raw framebuffer data
- Sends pixel differences to client
- Simple protocol, works everywhere
- No audio or USB by design

### RDP (Remote Desktop Protocol)

Microsoft's proprietary protocol, released with Windows NT 4.0 Terminal Server in 1998.

**How it works:**

- Sends high-level drawing commands (not raw pixels)
- Client reconstructs display locally
- Much more efficient for typical desktop work
- Full multimedia and device redirection

### SPICE (Simple Protocol for Independent Computing Environments)

Developed by Red Hat, initially for virtualization environments.

**How it works:**

- Designed specifically for VMs
- Agent runs inside guest OS
- Can leverage VM host for optimization
- Excellent USB and display features

## Learn More

- [Protocol Details](protocols.md) - Technical deep-dive into each protocol
