# Audio Static Noise

Idle static, hiss, or popping from the analog output (or HDMI/DisplayPort audio) when nothing is actually playing. This is a hardware quirk of the MS-S1 MAX, not a software misconfiguration.

## Cause

The Intel HD-audio driver (`snd_hda_intel`, which also drives the AMD Radeon and Ryzen HD Audio controllers on this box) suspends the codec after a short idle timeout to save power. On this platform the codec powering down and back up produces an audible pop, hiss, or continuous static. Keeping the codec always powered on eliminates the noise, at the cost of a negligible amount of idle power.

Confirm the driver in use:

```bash
lspci -k | grep -iA3 audio
```

```
be:00.1 Audio device: Advanced Micro Devices, Inc. [AMD/ATI] Radeon High Definition Audio Controller
	Kernel driver in use: snd_hda_intel
be:00.6 Audio device: Advanced Micro Devices, Inc. [AMD] Ryzen HD Audio Controller
	Kernel driver in use: snd_hda_intel
```

## Fix

Disable codec power saving with a modprobe drop-in so it persists across reboots:

```bash
echo 'options snd_hda_intel power_save=0 power_save_controller=N' \
  | sudo tee /etc/modprobe.d/audio-disable-powersave.conf
```

Reload the module (or just reboot):

```bash
sudo modprobe -r snd_hda_intel && sudo modprobe snd_hda_intel
```

Verify it took effect — both must read as shown:

```bash
cat /sys/module/snd_hda_intel/parameters/power_save            # -> 0
cat /sys/module/snd_hda_intel/parameters/power_save_controller # -> N
```

!!! warning "A runtime-only change does not survive reboot"
    Setting the value directly, e.g. `echo 0 | sudo tee /sys/module/snd_hda_intel/parameters/power_save`, silences the noise immediately but is lost on the next boot and the static returns. The modprobe drop-in above is what makes it stick. Check that the file exists — if `power_save` reads `0` but there is no file under `/etc/modprobe.d/`, the fix is not persistent:

    ```bash
    grep -r power_save /etc/modprobe.d/
    ```

## If the driver is SOF instead

Some newer kernels bind the codec to the SOF (Sound Open Firmware) driver rather than `snd_hda_intel`. If `lspci -k` shows `snd_sof_pci` (or `sof-audio-pci`), target that module instead:

```bash
echo 'options snd_sof_pci power_save=0' \
  | sudo tee /etc/modprobe.d/sof-disable-powersave.conf
```

## Reference

- [Static noise when no audio playing (askubuntu.com/questions/1337064)](https://askubuntu.com/questions/1337064/static-noise-when-no-audio-playing)
