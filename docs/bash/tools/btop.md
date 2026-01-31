# btop

Modern, feature-rich resource monitor for the terminal.

## Overview

btop (btop++) provides:

- **Beautiful UI** - Color themes, graphs, braille characters
- **Comprehensive metrics** - CPU, memory, disk, network, processes
- **Mouse support** - Click to select, scroll, navigate
- **Process management** - Kill, nice, filter processes
- **Low resource usage** - Efficient C++ implementation

## Installation

### macOS

```bash
brew install btop
```

### Linux

```bash
# Ubuntu/Debian
sudo apt install btop

# Arch
sudo pacman -S btop

# Fedora
sudo dnf install btop

# From source
git clone https://github.com/aristocratos/btop.git
cd btop
make
sudo make install
```

### Verify

```bash
btop --version
```

## Basic Usage

```bash
# Start btop
btop

# With specific theme
btop --theme adapta

# Low color mode (for limited terminals)
btop --low-color
```

## Navigation

### Keyboard Controls

| Key | Action |
|-----|--------|
| `Up/Down/j/k` | Navigate processes |
| `Left/Right/h/l` | Change sorting column |
| `Enter` | Show process details |
| `Space` | Mark process |
| `f` | Filter processes |
| `t` | Tree view toggle |
| `r` | Reverse sort order |
| `c` | Per-core CPU view |
| `m` | Toggle mini mode |
| `q/Esc` | Quit |

### Process Actions

| Key | Action |
|-----|--------|
| `k` | Kill process (SIGTERM) |
| `K` | Kill process (SIGKILL) |
| `n` | Nice (change priority) |
| `i` | Toggle idle processes |
| `s` | Select signal to send |

### View Controls

| Key | Action |
|-----|--------|
| `1` | Toggle CPU box |
| `2` | Toggle memory box |
| `3` | Toggle network box |
| `4` | Toggle process box |
| `d` | Toggle disk IO |
| `g` | Toggle GPU (if available) |

## Configuration

### Config Location

| Platform | Path |
|----------|------|
| Linux | `~/.config/btop/btop.conf` |
| macOS | `~/.config/btop/btop.conf` |

### Configuration Options

```bash
# ~/.config/btop/btop.conf

# Color theme
color_theme = "adapta"

# UI options
theme_background = True
truecolor = True
force_tty = False
vim_keys = True

# Update interval (ms)
update_ms = 1000

# Graph symbol style
graph_symbol = "braille"  # braille, block, tty

# Process sorting
proc_sorting = "cpu lazy"
proc_reversed = False
proc_tree = False

# Show per-core CPU
cpu_single_graph = False
cpu_bottom = False

# Disk options
show_disks = True
disk_free_prec = 0

# Network options
net_download = 100
net_upload = 100
net_auto = True

# Memory options
mem_graphs = True
show_swap = True
swap_disk = True

# Process options
show_detailed = False
proc_per_core = False
proc_mem_bytes = True
proc_info_smaps = False
```

## Themes

### Built-in Themes

btop includes several themes:

- `Default` - Dark theme
- `adapta` - Material design inspired
- `dracula` - Dracula color scheme
- `gruvbox_dark` - Gruvbox dark
- `nord` - Nord color scheme
- `onedark` - Atom One Dark
- `solarized_dark` - Solarized dark

### Change Theme

```bash
# Via command line
btop --theme nord

# Or press 'm' in btop to access menu
# Navigate to Options -> Theme
```

### Theme Location

Custom themes: `~/.config/btop/themes/`

### Create Custom Theme

```bash
# ~/.config/btop/themes/custom.theme

# Main colors
theme[main_bg]="#1e1e2e"
theme[main_fg]="#cdd6f4"

# Box colors
theme[title]="#89b4fa"
theme[hi_fg]="#f5c2e7"

# CPU
theme[cpu_box]="#89b4fa"
theme[cpu_graph]="#a6e3a1"

# Memory
theme[mem_box]="#f5c2e7"
theme[mem_graph]="#f38ba8"

# Network
theme[net_box]="#fab387"
theme[net_graph]="#f9e2af"

# Process
theme[proc_box]="#94e2d5"
theme[proc_highlight]="#45475a"
```

## Display Sections

### CPU Section

Shows:
- Overall CPU usage graph
- Per-core usage bars
- CPU temperature (if sensors available)
- Load averages
- Frequency

Toggle per-core: Press `c`

### Memory Section

Shows:
- RAM usage graph and percentage
- Swap usage (if enabled)
- Memory breakdown (used, cached, available)

### Disk Section

Shows:
- Read/write activity
- Usage percentage per disk
- IO stats

Toggle: Press `d`

### Network Section

Shows:
- Upload/download graphs
- Current bandwidth
- Total data transferred

Auto-scale: Configure `net_auto`

### Process Section

Shows:
- Process list with PID, user, CPU%, MEM%
- Command line
- Tree view option

## Comparison

### btop vs htop

| Feature | btop | htop |
|---------|------|------|
| UI | Modern, graphs | Classic |
| Mouse support | Full | Yes |
| Themes | Many built-in | Limited |
| GPU monitoring | Yes | No |
| Resource usage | Low | Very low |
| Configuration | File-based | Interactive |
| Graphs | Yes | Yes |

### btop vs top

| Feature | btop | top |
|---------|------|-----|
| Visual appeal | High | Basic |
| Ease of use | High | Moderate |
| Customization | Extensive | Limited |
| Resource usage | Low | Very low |
| Availability | Install required | Pre-installed |

### btop vs glances

| Feature | btop | glances |
|---------|------|---------|
| UI | Terminal native | Terminal/Web |
| Resource usage | Low | Higher |
| Remote monitoring | No | Yes |
| Export formats | No | Yes |
| Docker integration | No | Yes |

## Tips and Tricks

### Quick Filtering

Press `f` and type to filter processes:

```
# Filter by name
f → nginx

# Filter by user
f → user:www-data

# Filter by PID
f → pid:1234
```

### Kill Multiple Processes

1. Press `Space` to mark processes
2. Navigate and mark more
3. Press `k` or `K` to kill all marked

### Mini Mode

Press `m` for compact view - useful for small terminals or tmux panes.

### Preset Views

| Key | View |
|-----|------|
| `p` → `1` | Default |
| `p` → `2` | Minimal |
| `p` → `3` | Detailed |

### Mouse Usage

- **Click process**: Select
- **Double-click**: Show details
- **Scroll**: Navigate list
- **Right-click**: Context menu

## Troubleshooting

### No Colors

```bash
# Check terminal color support
echo $TERM

# Force truecolor
btop --truecolor

# Or low-color mode
btop --low-color
```

### No GPU Information

GPU monitoring requires:
- NVIDIA: nvidia-smi
- AMD: rocm-smi or radeontop
- Intel: intel_gpu_top

### High CPU Usage

```bash
# Increase update interval
# Edit ~/.config/btop/btop.conf
update_ms = 2000  # Update every 2 seconds
```

### No Temperature Sensors

```bash
# Linux - install lm-sensors
sudo apt install lm-sensors
sudo sensors-detect

# macOS - requires root for some sensors
sudo btop
```

## Shell Integration

### Aliases

```bash
# ~/.bashrc or ~/.zshrc

# Quick system check
alias sys='btop'

# Minimal view
alias sysm='btop --preset 2'

# Specific theme
alias sysd='btop --theme dracula'
```

### tmux Integration

```bash
# Start btop in new tmux pane
tmux split-window -h btop

# Or in new window
tmux new-window btop
```

## See Also

- [Process Management](process-management.md) - Process control
- [Modern Replacements](modern-replacements.md) - CLI alternatives
- [tmux](tmux.md) - Terminal multiplexer
