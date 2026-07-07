# Headless operation

A headless VM runs in the background without opening a window. This is how `msai lab create` runs the lab VM, and how anything serious uses VirtualBox.

## Starting headless

```bash
VBoxManage startvm test --type headless
```

The command returns as soon as the VM begins booting (a few seconds). The VM is now running in the background.

You can confirm:

```bash
VBoxManage list runningvms
# "test" {uuid}
```

## Interacting with a headless VM

You have no window. Three ways to interact:

### 1. SSH into the guest (the usual)

Once the guest is up and sshd is listening:

```bash
ssh -p 2222 -i target/lab_id_ed25519 morten@127.0.0.1
```

This is the lab's normal path. The NAT port-forward (`127.0.0.1:2222 -> guest:22`) makes it work.

### 2. VRDE — VirtualBox Remote Desktop

For when you need a graphical console (interactive installer, recovery, etc.). VRDE is VirtualBox's RDP server.

```bash
# Enable VRDE (requires Extension Pack)
VBoxManage modifyvm test \
    --vrde on \
    --vrdeport 3389 \
    --vrdeaddress 127.0.0.1 \         # bind localhost only
    --vrdeauthtype null               # no auth (lab use only!)
```

Then from your Mac, connect with any RDP client:

```bash
# Microsoft Remote Desktop (App Store)
# Connect to: 127.0.0.1:3389
```

Or from the command line with an RDP client like FreeRDP:

```bash
brew install freerdp
xfreerdp /v:127.0.0.1:3389 /size:1280x800
```

VRDE shows you the VM's framebuffer (boot messages, login prompt, GUI if any) and lets you send keyboard/mouse. It's the closest thing to "the GUI but remote".

Disable VRDE when done:

```bash
VBoxManage modifyvm test --vrde off
```

Without the Extension Pack, `--vrde on` is rejected with "VRDE not supported". The Extension Pack is free for personal use; install it once.

### 3. Direct framebuffer / keyboard

Crude but functional. Useful for one-off operations without setting up RDP.

```bash
# Capture the current framebuffer as PNG
VBoxManage controlvm test screenshotpng /tmp/test.png
open /tmp/test.png

# Type into the guest
VBoxManage controlvm test keyboardputstring "hostname\n"
VBoxManage controlvm test keyboardputstring "uname -a\n"

# Send raw scancodes (e.g., the keycode for Enter is 1c)
VBoxManage controlvm test keyboardputscancode 1c

# Move/click the mouse
VBoxManage controlvm test mouse moveabs 100 100 0 0 0
VBoxManage controlvm test mouse buttonclick 100 100 left
```

I use this mostly for verifying boot progress during VM creation — `screenshotpng` every minute to see what GRUB / installer / system is doing.

## Watching boot progress

The lab uses this pattern during `msai lab create`:

```bash
# Start the VM
VBoxManage startvm test --type headless

# While waiting for SSH, optionally check the screen
VBoxManage controlvm test screenshotpng /tmp/test.png
open /tmp/test.png
```

The framebuffer keeps updating during boot; subsequent `screenshotpng` calls show current state. Each capture is ~10-50 KB PNG.

## Sending keys to the guest

`keyboardputstring` is convenient for typing ASCII text. For special keys you need `keyboardputscancode`:

```bash
# Common scancodes
# Enter:    1c
# Esc:      01
# Backspace: 0e
# Tab:      0f
# Up:       e0 48 (extended)
# Down:     e0 50

VBoxManage controlvm test keyboardputscancode 01           # Esc
VBoxManage controlvm test keyboardputscancode e0 48        # Up arrow
```

Most use cases are better served by SSH or VRDE. Keyboard injection is for "I need to press a key at the GRUB menu before SSH is up".

## Reading guest console output (Linux)

If the guest configures its kernel to log to a virtual serial port, VBox can capture that:

```bash
# Add a serial port to the VM (before booting)
VBoxManage modifyvm test \
    --uart1 0x3F8 4 \                                   # standard COM1
    --uartmode1 file /tmp/test-console.log

# In the guest, configure GRUB to log to console:
# /etc/default/grub:
#   GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200"
# sudo update-grub
```

After reboot, `/tmp/test-console.log` captures all kernel/init output. Useful for debugging boots that hang before SSH is available.

`--uartmode1 server /tmp/test.sock` would create a Unix socket that you `socat` into for an interactive console. More setup; rarely needed for lab work.

## Stopping headless VMs

```bash
# Polite (ACPI signal — the guest's systemd does a clean shutdown)
VBoxManage controlvm test acpipowerbutton

# Wait for the guest to actually finish shutting down
until ! VBoxManage list runningvms | grep -q "\"test\""; do sleep 1; done

# Or "yank the cord" (use only if hung)
VBoxManage controlvm test poweroff
```

`acpipowerbutton` is what `msai lab stop` does. `poweroff` is what `msai lab stop --force` does. The first is always safer; the second is for when the VM is unresponsive.

## Running multiple VMs

Headless VMs are cheap (just background processes). You can have several lab instances up at once:

```bash
msai lab create lab1     # creates + boots
msai lab create lab2     # creates + boots; lab1 stays running
msai lab list            # both shown, both running
VBoxManage list runningvms
# "lab1" {...}
# "lab2" {...}
```

Each has its own port-forward; the lab uses 2222 for the **current** instance. If you want lab2 reachable too, override `SSH_FORWARD_PORT` before `msai lab create`:

```bash
msai lab use lab1
SSH_FORWARD_PORT=2223 msai lab create lab2    # would conflict with lab1 on 2222 otherwise
```

(In practice, the lab automation always uses 2222 because most workflows only need to talk to one instance at a time. Multi-instance is the user-driven case.)

## VRDE security (when actually exposed)

Defaults are no auth (`--vrdeauthtype null`) so it's localhost-only by virtue of `--vrdeaddress 127.0.0.1`. If you ever bind to a public address:

```bash
VBoxManage modifyvm test --vrdeauthtype external
# Or:
VBoxManage modifyvm test --vrdeauthtype guest    # guest authenticates the connection
```

Setting up VRDE password auth is well-documented in the VirtualBox manual. For lab use, stay on localhost + null auth.

## See also

- [VBoxManage CLI](vboxmanage.md) — full subcommand reference
- [Unattended install](unattended.md) — the headless install flow `msai lab create` uses
- [Networking](networking.md) — NAT port-forwarding for SSH access
