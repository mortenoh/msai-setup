# Ghostty

Ghostty is a fast, feature-rich, and cross-platform terminal emulator that uses platform-native UI and GPU acceleration. Built by Mitchell Hashimoto (HashiCorp co-founder), it focuses on performance and correctness.

## Installation

### macOS

Download from the official website or use Homebrew:

```bash
brew install --cask ghostty
```

### Linux

```bash
# Build from source (requires Zig)
git clone https://github.com/ghostty-org/ghostty
cd ghostty
zig build -Doptimize=ReleaseFast
```

## Configuration

Ghostty uses a simple key-value configuration file.

**Location:**
- macOS: `~/.config/ghostty/config`
- Linux: `~/.config/ghostty/config`

### Complete Annotated Configuration

```ini
# ~/.config/ghostty/config
# Ghostty Terminal Configuration

# ============================================
# Terminal Settings
# ============================================

# Terminal type for applications to detect capabilities
# Options: xterm-256color, xterm-ghostty, ghostty
term = xterm-256color

# ============================================
# Font Settings
# ============================================

# Font family - use a Nerd Font for icons in prompts and TUIs
# Popular choices:
#   - JetBrainsMono Nerd Font
#   - FiraCode Nerd Font
#   - Hack Nerd Font
#   - MesloLGS Nerd Font
font-family = "JetBrainsMono Nerd Font Mono"

# Font size in points
font-size = 14

# Font weight (100-900, or named: thin, light, regular, medium, bold, etc.)
# font-weight = regular
# font-weight-bold = bold

# Enable font ligatures (for fonts that support them like FiraCode)
# font-feature = calt
# font-feature = liga

# Disable specific ligatures if needed
# font-feature = -calt

# ============================================
# Cursor Settings
# ============================================

# Cursor style: block, bar, underline
cursor-style = block

# Cursor blinking: true or false
cursor-style-blink = false

# Cursor color (uses theme color if not set)
# cursor-color = #f8f8f2

# ============================================
# Shell Integration
# ============================================

# Shell integration features
# Options: cursor, sudo, title, no-cursor, no-sudo, no-title
# "no-cursor" disables shell-controlled cursor (recommended if cursor jumps)
shell-integration-features = no-cursor

# Custom shell (uses $SHELL by default)
# command = /opt/homebrew/bin/bash

# ============================================
# Window Settings
# ============================================

# Initial window size in characters
window-width = 155
window-height = 45

# Window padding (space between content and window edge)
window-padding-x = 8
window-padding-y = 6

# Window decorations
# Options: true, false, none
# window-decoration = true

# Remember window size and position
# window-save-state = always

# ============================================
# Theme and Colors
# ============================================

# Built-in theme (overrides individual color settings)
# Run `ghostty +list-themes` to see available themes
# Popular themes:
#   - Dracula
#   - Tokyo Night
#   - Catppuccin Mocha
#   - One Dark
#   - Nord
#   - GitHub Dark Default
#   - Gruvbox Dark
theme = GitHub Dark Default

# Background opacity (0.0 to 1.0)
# Values less than 1.0 enable transparency
background-opacity = 0.85

# Background blur (macOS only)
# Enable blur effect when background is transparent
background-blur = true

# Custom colors (override theme)
# foreground = #c0caf5
# background = #1a1b26
# selection-foreground = #c0caf5
# selection-background = #33467c

# ANSI colors (0-15)
# palette = 0=#1a1b26
# palette = 1=#f7768e
# ... etc

# ============================================
# macOS-Specific Settings
# ============================================

# Title bar style
# Options: transparent, native, hidden, tabs
# macos-titlebar-style = tabs

# Option key behavior
# Options: native, alt, super
macos-option-as-alt = true

# Hide application when last window closes
# quit-after-last-window-closed = true

# ============================================
# Clipboard
# ============================================

# Auto-copy selection to clipboard
# clipboard-read = allow
# clipboard-write = allow

# Confirm paste of multiline or suspicious content
# clipboard-paste-protection = true

# ============================================
# Scrollback
# ============================================

# Scrollback buffer size (lines)
# scrollback-limit = 10000

# ============================================
# Links
# ============================================

# Enable clickable links
# link-url = true

# Modifier key for clicking links
# link-modifier = ctrl

# ============================================
# Keybindings
# ============================================

# Format: keybind = <key>=<action>
# Modifiers: ctrl, alt, shift, super, cmd (macOS)
# Keys: a-z, 0-9, f1-f12, up, down, left, right, etc.

# Tab navigation
keybind = cmd+left=previous_tab
keybind = cmd+right=next_tab

# Move tabs
keybind = shift+cmd+left=move_tab:-1
keybind = shift+cmd+right=move_tab:1

# Split panes
# keybind = cmd+d=new_split:right
# keybind = cmd+shift+d=new_split:down

# Navigate splits
# keybind = cmd+alt+left=goto_split:left
# keybind = cmd+alt+right=goto_split:right
# keybind = cmd+alt+up=goto_split:top
# keybind = cmd+alt+down=goto_split:bottom

# Font size
# keybind = cmd+plus=increase_font_size:1
# keybind = cmd+minus=decrease_font_size:1
# keybind = cmd+0=reset_font_size

# Scrolling
# keybind = shift+page_up=scroll_page_up
# keybind = shift+page_down=scroll_page_down
# keybind = shift+home=scroll_to_top
# keybind = shift+end=scroll_to_bottom

# Copy/paste (defaults work on macOS)
# keybind = cmd+c=copy_to_clipboard
# keybind = cmd+v=paste_from_clipboard

# Open config file
# keybind = cmd+comma=open_config

# Reload config
# keybind = cmd+shift+comma=reload_config

# ============================================
# Advanced Settings
# ============================================

# GPU rendering backend
# Options: auto, metal (macOS), vulkan, opengl
# renderer = auto

# Antialiasing
# font-antialiasing = lcd

# Bold text brightness
# bold-is-bright = false

# Confirm on close when process is running
# confirm-close-surface = true

# ============================================
# Bell
# ============================================

# Visual bell instead of audio
# visual-bell = true

# Disable bell completely
# bell = false
```

## Keybindings

### Default Keybindings

| Key | Action |
|-----|--------|
| ++cmd+t++ | New tab |
| ++cmd+w++ | Close tab |
| ++cmd+n++ | New window |
| ++cmd+shift+n++ | New window (same directory) |
| ++cmd+1++ to ++cmd+9++ | Switch to tab 1-9 |
| ++cmd+left-bracket++ | Previous tab |
| ++cmd+right-bracket++ | Next tab |
| ++cmd+c++ | Copy |
| ++cmd+v++ | Paste |
| ++cmd+plus++ | Increase font size |
| ++cmd+minus++ | Decrease font size |
| ++cmd+0++ | Reset font size |
| ++cmd+comma++ | Open config |
| ++cmd+q++ | Quit |

### Custom Keybindings

Add custom keybindings in your config:

```ini
# Navigation
keybind = cmd+left=previous_tab
keybind = cmd+right=next_tab

# Tab management
keybind = shift+cmd+left=move_tab:-1
keybind = shift+cmd+right=move_tab:1

# Splits
keybind = cmd+d=new_split:right
keybind = cmd+shift+d=new_split:down
keybind = cmd+alt+left=goto_split:left
keybind = cmd+alt+right=goto_split:right

# Quick actions
keybind = cmd+k=clear_screen
keybind = cmd+shift+k=scroll_to_top
```

### Available Actions

```ini
# Window/tab actions
new_window
new_tab
close_surface
close_tab
close_window

# Tab navigation
previous_tab
next_tab
goto_tab:N
move_tab:N

# Split actions
new_split:right
new_split:down
goto_split:left|right|top|bottom
resize_split:left|right|top|bottom,N

# Clipboard
copy_to_clipboard
paste_from_clipboard

# Font
increase_font_size:N
decrease_font_size:N
reset_font_size

# Scrolling
scroll_page_up
scroll_page_down
scroll_to_top
scroll_to_bottom
scroll_line_up
scroll_line_down

# Other
clear_screen
reset
open_config
reload_config
toggle_fullscreen
```

## Themes

### List Available Themes

```bash
ghostty +list-themes
```

### Popular Themes

```ini
# Dark themes
theme = Dracula
theme = Tokyo Night
theme = Catppuccin Mocha
theme = One Dark
theme = Nord
theme = GitHub Dark Default
theme = Gruvbox Dark
theme = Solarized Dark

# Light themes
theme = GitHub Light Default
theme = Solarized Light
theme = One Light
```

### Custom Colors

Override theme colors:

```ini
# Use a base theme
theme = Tokyo Night

# Override specific colors
foreground = #c0caf5
background = #1a1b26
cursor-color = #f8f8f2
selection-background = #33467c
```

### Full Custom Color Scheme

```ini
# No theme - full custom colors
foreground = #c0caf5
background = #1a1b26
selection-foreground = #c0caf5
selection-background = #33467c
cursor-color = #f8f8f2

# ANSI colors (16 color palette)
palette = 0=#1a1b26
palette = 1=#f7768e
palette = 2=#9ece6a
palette = 3=#e0af68
palette = 4=#7aa2f7
palette = 5=#bb9af7
palette = 6=#7dcfff
palette = 7=#a9b1d6
palette = 8=#414868
palette = 9=#f7768e
palette = 10=#9ece6a
palette = 11=#e0af68
palette = 12=#7aa2f7
palette = 13=#bb9af7
palette = 14=#7dcfff
palette = 15=#c0caf5
```

## Font Configuration

### Nerd Fonts

Ghostty works best with Nerd Fonts for icons in prompts (Starship) and TUI applications:

```bash
# Install via Homebrew
brew tap homebrew/cask-fonts
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code-nerd-font
brew install --cask font-hack-nerd-font
```

### Font Ligatures

Enable ligatures for fonts like FiraCode:

```ini
font-family = "FiraCode Nerd Font"
font-feature = calt
font-feature = liga
```

### Disable Specific Ligatures

```ini
font-family = "FiraCode Nerd Font"
font-feature = calt
font-feature = -ss01    # Disable specific stylistic set
```

## Shell Integration

Ghostty includes shell integration for enhanced features like:

- Working directory tracking
- Command duration
- Semantic prompts

### Enable Shell Integration

For bash, add to `~/.bashrc`:

```bash
if [[ -n "$GHOSTTY_RESOURCES_DIR" ]]; then
    source "$GHOSTTY_RESOURCES_DIR/shell-integration/bash/ghostty.bash"
fi
```

For zsh, add to `~/.zshrc`:

```zsh
if [[ -n "$GHOSTTY_RESOURCES_DIR" ]]; then
    source "$GHOSTTY_RESOURCES_DIR/shell-integration/zsh/ghostty.zsh"
fi
```

## Transparency and Blur

### macOS

```ini
background-opacity = 0.85
background-blur = true
```

### Linux (Compositor Required)

```ini
background-opacity = 0.90
# Note: blur depends on compositor (picom, etc.)
```

## Performance Tuning

Ghostty is already optimized, but you can adjust:

```ini
# GPU backend (usually auto is best)
renderer = auto

# Font antialiasing
font-antialiasing = lcd

# Disable unused features
# link-url = false
# visual-bell = false
```

## Multiple Configurations

### Config Includes

```ini
# Include another config file
config-file = ~/.config/ghostty/colors/tokyo-night.conf
```

### Environment-Based Config

```bash
# In shell config
if [[ "$TERM_PROGRAM" == "ghostty" ]]; then
    export TERM=xterm-256color
fi
```

## Troubleshooting

### Font Not Found

```bash
# List available fonts
fc-list | grep -i "jetbrains"

# Verify font name
fc-list : family | sort | uniq | grep -i nerd
```

### Config Not Loading

```bash
# Check config syntax
ghostty +show-config

# Config file location
ls -la ~/.config/ghostty/config
```

### Colors Wrong in tmux

Add to tmux.conf:

```bash
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
```

### Shell Integration Issues

```ini
# Try disabling specific features
shell-integration-features = no-cursor
```

## Comparison with Other Terminals

| Feature | Ghostty | iTerm2 | Alacritty | Kitty |
|---------|---------|--------|-----------|-------|
| GPU accelerated | Yes | Partial | Yes | Yes |
| Native UI | Yes | Yes | No | No |
| Configuration | Simple | GUI + Config | TOML | Conf |
| Font ligatures | Yes | Yes | Yes | Yes |
| Tabs | Yes | Yes | No | Yes |
| Splits | Yes | Yes | No | Yes |
| Transparency | Yes | Yes | Yes | Yes |

## Related Tools

- [tmux](../../tools/tmux.md) - Terminal multiplexer
- [Starship](../starship/index.md) - Cross-shell prompt
- [Neovim](../neovim/index.md) - Terminal editor
