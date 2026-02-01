# SPICE Server Setup

Configure SPICE display and agents in KVM/QEMU virtual machines.

## QEMU Command Line

### Basic SPICE Configuration

```bash
qemu-system-x86_64 \
  -spice port=5900,disable-ticketing=on \
  -device virtio-serial-pci \
  -chardev spicevmc,id=vdagent,debug=0,name=vdagent \
  -device virtserialport,chardev=vdagent,name=com.redhat.spice.0 \
  ...
```

### With TLS

```bash
qemu-system-x86_64 \
  -spice port=5900,tls-port=5901,x509-dir=/etc/pki/qemu \
  ...
```

## libvirt/virsh Configuration

### Enable SPICE Display

Edit VM with `virsh edit vm-name`:

```xml
<graphics type='spice' autoport='yes' listen='127.0.0.1'>
  <listen type='address' address='127.0.0.1'/>
  <image compression='auto_glz'/>
  <streaming mode='filter'/>
  <zlib compression='auto'/>
</graphics>
```

### SPICE with VNC Fallback

You can have both:

```xml
<graphics type='spice' autoport='yes'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
<graphics type='vnc' port='-1' autoport='yes'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

### QXL Video Device

For best SPICE performance, use QXL video:

```xml
<video>
  <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1' primary='yes'/>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x0'/>
</video>
```

Multiple monitors:

```xml
<video>
  <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='4' primary='yes'/>
</video>
```

### SPICE Agent Channel

Required for clipboard, resolution changes:

```xml
<channel type='spicevmc'>
  <target type='virtio' name='com.redhat.spice.0'/>
  <address type='virtio-serial' controller='0' bus='0' port='1'/>
</channel>
```

### USB Redirection

Enable USB passthrough via SPICE:

```xml
<controller type='usb' index='0' model='qemu-xhci'>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
</controller>

<redirdev bus='usb' type='spicevmc'>
</redirdev>
<redirdev bus='usb' type='spicevmc'>
</redirdev>
<redirdev bus='usb' type='spicevmc'>
</redirdev>
<redirdev bus='usb' type='spicevmc'>
</redirdev>
```

## Guest Agent Installation

### Linux Guest

=== "Ubuntu/Debian"
    ```bash
    sudo apt install spice-vdagent
    sudo systemctl enable spice-vdagent
    sudo systemctl start spice-vdagent
    ```

=== "Fedora/RHEL"
    ```bash
    sudo dnf install spice-vdagent
    sudo systemctl enable spice-vdagent
    sudo systemctl start spice-vdagent
    ```

=== "Arch"
    ```bash
    sudo pacman -S spice-vdagent
    sudo systemctl enable spice-vdagentd
    sudo systemctl start spice-vdagentd
    ```

### Windows Guest

1. Download [spice-guest-tools](https://www.spice-space.org/download.html)
2. Run installer in Windows VM
3. Reboot

Includes:
- QXL display driver
- SPICE agent
- VirtIO serial driver

### Verify Agent Running

Linux:
```bash
systemctl status spice-vdagent
# or
ps aux | grep spice
```

Windows:
- Services > "SPICE Agent"

## Complete libvirt Example

Full VM configuration with SPICE:

```xml
<domain type='kvm'>
  <name>linux-spice-vm</name>
  <memory unit='GiB'>4</memory>
  <vcpu>4</vcpu>

  <os>
    <type arch='x86_64' machine='q35'>hvm</type>
    <boot dev='hd'/>
  </os>

  <features>
    <acpi/>
    <apic/>
  </features>

  <devices>
    <!-- SPICE display -->
    <graphics type='spice' autoport='yes'>
      <listen type='address' address='0.0.0.0'/>
      <image compression='auto_glz'/>
      <streaming mode='filter'/>
    </graphics>

    <!-- QXL video -->
    <video>
      <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1'/>
    </video>

    <!-- Virtio serial for agent -->
    <controller type='virtio-serial' index='0'/>

    <!-- SPICE agent channel -->
    <channel type='spicevmc'>
      <target type='virtio' name='com.redhat.spice.0'/>
    </channel>

    <!-- USB controller for redirection -->
    <controller type='usb' model='qemu-xhci'/>

    <!-- USB redirection channels -->
    <redirdev bus='usb' type='spicevmc'/>
    <redirdev bus='usb' type='spicevmc'/>

    <!-- Audio -->
    <sound model='ich9'>
      <codec type='micro'/>
    </sound>
    <audio id='1' type='spice'/>

    <!-- Other devices... -->
  </devices>
</domain>
```

## Network Binding

### Localhost Only (Secure)

```xml
<graphics type='spice' autoport='yes' listen='127.0.0.1'>
  <listen type='address' address='127.0.0.1'/>
</graphics>
```

Access via SSH tunnel or Tailscale with port forward.

### All Interfaces

```xml
<graphics type='spice' port='5900' autoport='no' listen='0.0.0.0'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

!!! warning "Security"
    When binding to all interfaces, ensure firewall is configured.

### With Password

```xml
<graphics type='spice' autoport='yes' passwd='your-password'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

## Performance Tuning

### Compression Settings

```xml
<graphics type='spice' autoport='yes'>
  <!-- Image compression -->
  <image compression='auto_glz'/>  <!-- auto_glz, auto_lz, quic, glz, lz, off -->

  <!-- Video streaming detection -->
  <streaming mode='filter'/>  <!-- filter, all, off -->

  <!-- Zlib compression for data -->
  <zlib compression='auto'/>  <!-- auto, never, always -->

  <!-- JPEG for lossy compression -->
  <jpeg compression='auto'/>  <!-- auto, never, always -->

  <!-- Playback compression -->
  <playback compression='on'/>  <!-- on, off -->
</graphics>
```

### For LAN (High Bandwidth)

```xml
<image compression='off'/>
<streaming mode='all'/>
```

### For WAN (Low Bandwidth)

```xml
<image compression='auto_glz'/>
<streaming mode='filter'/>
<jpeg compression='always'/>
```

## Audio Configuration

### Enable SPICE Audio

```xml
<sound model='ich9'>
  <codec type='micro'/>
</sound>
<audio id='1' type='spice'/>
```

### PulseAudio Backend

```xml
<audio id='1' type='pulseaudio'>
  <input mixingEngine='yes'/>
  <output mixingEngine='yes'/>
</audio>
```

## USB Redirection

### Enable in VM

```xml
<!-- USB 3.0 controller -->
<controller type='usb' index='0' model='qemu-xhci'>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
</controller>

<!-- Redirection channels (one per device) -->
<redirdev bus='usb' type='spicevmc'/>
<redirdev bus='usb' type='spicevmc'/>
<redirdev bus='usb' type='spicevmc'/>
<redirdev bus='usb' type='spicevmc'/>
```

### Client-side Usage

In virt-viewer/remote-viewer:
1. File > USB device selection
2. Check devices to redirect
3. Devices appear in guest

## Finding SPICE Port

```bash
# Get SPICE port for a VM
virsh domdisplay vm-name
# Output: spice://localhost:5900

# Or via dumpxml
virsh dumpxml vm-name | grep -A5 "graphics type='spice'"
```

## Troubleshooting

### No Display

1. Check SPICE is configured: `virsh dumpxml vm | grep spice`
2. Verify port: `ss -tlnp | grep qemu`
3. Check QXL driver in guest

### Agent Not Working

1. Verify channel in VM config
2. Check agent running in guest
3. Restart agent: `systemctl restart spice-vdagent`

### Poor Performance

1. Enable QXL driver in guest
2. Adjust compression settings
3. Check network bandwidth
4. Verify video RAM settings

### USB Redirection Fails

1. Check `usbredir` package installed on host
2. Verify USB controller in VM
3. Check device permissions on host

## virt-manager Setup

### Using GUI

1. Open VM settings
2. Add Hardware > Graphics
3. Type: SPICE server
4. Address: All interfaces (or localhost)
5. Apply

### Enable USB Redirection

1. Add Hardware > USB Redirector
2. Add multiple for more devices
3. Apply

### Add QXL Video

1. Remove existing video device
2. Add Hardware > Video
3. Model: QXL
4. Configure RAM amounts
5. Apply
