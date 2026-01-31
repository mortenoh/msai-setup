# tmux

tmux is a terminal multiplexer that lets you run multiple terminal sessions within a single window. It keeps sessions alive when you disconnect, making it essential for remote work and complex workflows.

## Overview

tmux lets you:

- Split terminal into multiple panes
- Create multiple sessions (workspaces)
- Detach and reattach sessions without losing state
- Share sessions across SSH connections
- Customize every aspect of your terminal experience

### Why tmux?

- Native terminal multiplexing without GUI overhead
- Persistent sessions survive SSH disconnections
- Keyboard-driven workflow (no mouse needed)
- Highly customizable with powerful scripting
- Works seamlessly across macOS, Linux, and remote systems

## Installation

### macOS (Homebrew)

```bash
brew install tmux
```

### Linux

```bash
# Debian/Ubuntu
sudo apt install tmux

# Fedora
sudo dnf install tmux

# Arch Linux
sudo pacman -S tmux
```

## Norwegian Keyboard Layout

### The Problem

The Norwegian layout has key differences from US layout that cause issues with tmux:

| Character | US Key | Norwegian |
|-----------|--------|-----------|
| ae | Alt+Z | a (U+00E5) |
| o | Alt+L | o (U+00F8) |
| a | Alt+A | a (U+00E5) |

This causes issues because:

1. Default `Ctrl+b` prefix requires reaching for `b` key
2. Keybindings using these characters may not work as expected
3. Escape sequences for special characters can interfere with tmux commands
4. Copy/paste operations may fail for Norwegian text

### Solution: Change Prefix to Ctrl+Space

```bash
# Add to ~/.tmux.conf
unbind C-b
set-option -g prefix C-Space
bind C-Space send-prefix
```

Benefits:

- Space is large, comfortable key on all keyboards
- No conflict with Norwegian characters (ae, o, a)
- Familiar macOS keyboard shortcut pattern
- Works consistently across local and remote sessions

## Quick Start

```bash
# Create new named session
tmux new -s dev

# Attach to existing session
tmux attach -t dev
tmux a -t dev           # Short form

# List sessions
tmux ls

# Kill session
tmux kill-session -t dev
```

## Core Concepts

tmux organizes terminals in a hierarchy:

```
Server (runs in background)
-- Session (named workspace)
    -- Window (like browser tabs)
        -- Pane (split within a window)
```

- **Session**: A collection of windows, persists when detached
- **Window**: A full terminal screen within a session
- **Pane**: A split section within a window

## Prefix Key

All tmux commands start with the **prefix key**.

- Default: `Ctrl+b`
- Recommended for Norwegian: `Ctrl+Space`

```
Prefix + <command>
```

For example, to split horizontally: `Ctrl+Space` then `h`

## Complete Configuration for Norwegian Layout

```bash
# ~/.tmux.conf - Norwegian-optimized tmux configuration

# ============================================
# Prefix Key (Norwegian-friendly)
# ============================================

# Change prefix from Ctrl+b to Ctrl+Space
unbind C-b
set-option -g prefix C-Space

# Bind Ctrl+Space to send prefix to nested tmux
bind C-Space send-prefix

# ============================================
# General Settings
# ============================================

# Enable mouse support (scrolling, pane selection, window selection)
set -g mouse on

# Set terminal type for proper color support
set -g default-terminal "screen-256color"

# Enable true color support (for Neovim, etc.)
set -ga terminal-overrides ",xterm-256color:Tc"

# Start window numbering at 1 (easier to reach on keyboard)
set -g base-index 1

# Start pane numbering at 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Increase scrollback buffer size
set -g history-limit 50000

# Reduce escape time (important for Vim/Neovim)
set -sg escape-time 0

# Increase display time for messages
set -g display-time 4000

# Refresh status bar more often
set -g status-interval 5

# Focus events for Vim/Neovim autoread
set -g focus-events on

# Don't rename windows automatically
set -g allow-rename off

# Enable vi mode
set -g mode-keys vi

# UTF-8 support
set -g status-utf8 on

# ============================================
# Norwegian-Friendly Key Bindings
# ============================================

# Pane navigation (h,j,k,l - home row, no conflicts with Norwegian)
bind h select-pane -L
bind C-h select-pane -L
bind j select-pane -D
bind C-j select-pane -D
bind k select-pane -U
bind C-k select-pane -U
bind l select-pane -R
bind C-l select-pane -R

# Pane splitting (use current directory)
bind v split-window -h -c "#{pane_current_path}"
bind s split-window -v -c "#{pane_current_path}"

# Unbind default split keys
unbind '"'
unbind %

# Window navigation
bind -n C-n next-window
bind -n C-p previous-window

# Create new window in current directory
bind c new-window -c "#{pane_current_path}"

# Resize panes
bind -r Left resize-pane -L 5
bind -r Right resize-pane -R 5
bind -r Up resize-pane -U 5
bind -r Down resize-pane -D 5

bind -r H resize-pane -L 10
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 10

# Kill pane/window without confirmation
bind x kill-pane
bind X kill-window

# Reload config
bind r source-file ~/.tmux.conf \; display-message "Config reloaded!"

# Zoom pane
bind z resize-pane -Z

# Detach
bind d detach-client

# ============================================
# Copy Mode (Vi-style)
# ============================================

# Enter copy mode
bind [ copy-mode
bind ] copy-mode

# Vi-style selection and copy
bind -T copy-mode-vi v send-keys -X begin-selection
bind -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "pbcopy"

# Mouse selection copies to clipboard
bind -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel "pbcopy"

# ============================================
# Status Bar
# ============================================

# Status bar position
set -g status-position bottom

# Status bar colors (Tokyo Night theme)
set -g status-style 'bg=#1a1b26 fg=#a9b1d6'

# Status bar content
set -g status-left-length 40
set -g status-right-length 60

# Left: session name
set -g status-left '#[fg=#7aa2f7,bold] #S #[default]'

# Right: date and time
set -g status-right '#[fg=#565f89]%Y-%m-%d #[fg=#7aa2f7]%H:%M '

# Window status format
setw -g window-status-format '#[fg=#565f89] #I:#W '
setw -g window-status-current-format '#[fg=#7aa2f7,bold] #I:#W '

# ============================================
# Pane Borders
# ============================================

set -g pane-border-style 'fg=#3b4261'
set -g pane-active-border-style 'fg=#7aa2f7'

# ============================================
# Messages
# ============================================

set -g message-style 'bg=#1a1b26 fg=#7aa2f7'

# ============================================
# Activity Monitoring
# ============================================

# Don't show activity notifications
set -g visual-activity off
set -g visual-bell off
set -g visual-silence off
setw -g monitor-activity off
set -g bell-action none

# ============================================
# Plugins (using TPM)
# ============================================

# Install TPM: git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# set -g @plugin 'tmux-plugins/tpm'
# set -g @plugin 'tmux-plugins/tmux-sensible'
# set -g @plugin 'tmux-plugins/tmux-resurrect'
# set -g @plugin 'tmux-plugins/tmux-continuum'
# set -g @plugin 'tmux-plugins/tmux-yank'

# Initialize TPM (keep at bottom)
# run '~/.tmux/plugins/tpm/tpm'
```

## Key Bindings Reference

### Norwegian-Optimized Bindings

With `Ctrl+Space` as prefix:

| Key | Action |
|-----|--------|
| `Ctrl+Space h` | Select left pane |
| `Ctrl+Space j` | Select down pane |
| `Ctrl+Space k` | Select up pane |
| `Ctrl+Space l` | Select right pane |
| `Ctrl+Space v` | Split vertically |
| `Ctrl+Space s` | Split horizontally |
| `Ctrl+Space c` | Create new window |
| `Ctrl+Space x` | Kill pane |
| `Ctrl+Space X` | Kill window |
| `Ctrl+Space d` | Detach session |
| `Ctrl+Space [` | Enter copy mode |
| `Ctrl+Space z` | Toggle pane zoom |
| `Ctrl+Space r` | Reload config |
| `Ctrl+Space :` | Command prompt |
| `Ctrl+Space ?` | List all key bindings |

### Session Management

| Key | Action |
|-----|--------|
| `Ctrl+Space d` | Detach from session |
| `Ctrl+Space s` | List sessions |
| `Ctrl+Space $` | Rename session |
| `Ctrl+Space (` | Switch to previous session |
| `Ctrl+Space )` | Switch to next session |

### Window Management

| Key | Action |
|-----|--------|
| `Ctrl+Space c` | Create new window |
| `Ctrl+Space ,` | Rename window |
| `Ctrl+Space n` | Next window |
| `Ctrl+Space p` | Previous window |
| `Ctrl+Space 0-9` | Switch to window by number |
| `Ctrl+Space w` | List windows |
| `Ctrl+Space &` | Kill window |

### Pane Management

| Key | Action |
|-----|--------|
| `Ctrl+Space v` | Split vertically |
| `Ctrl+Space s` | Split horizontally |
| `Ctrl+Space h/j/k/l` | Navigate panes |
| `Ctrl+Space x` | Kill pane |
| `Ctrl+Space z` | Toggle zoom (fullscreen) |
| `Ctrl+Space {` | Move pane left |
| `Ctrl+Space }` | Move pane right |
| `Ctrl+Space space` | Cycle pane layouts |
| `Ctrl+Space q` | Show pane numbers |

### Copy Mode (Vi-style)

| Key | Action |
|-----|--------|
| `Ctrl+Space [` | Enter copy mode |
| `q` | Exit copy mode |
| `v` | Start selection |
| `V` | Line selection |
| `y` | Copy selection |
| `Enter` | Copy selection |
| `Ctrl+Space ]` | Paste buffer |
| `j/k` | Move down/up |
| `g/G` | Go to top/bottom |
| `w/b` | Next/previous word |
| `/` | Search forward |
| `?` | Search backward |
| `n/N` | Next/previous match |

## Remote Server Usage

### SSH with tmux Auto-Start

Configure `~/.ssh/config`:

```ssh
Host prod-server
    User dev-user
    HostName prod.example.com
    RemoteCommand tmux new -A -s prod
    RequestTTY yes
    SendEnv LANG LC_ALL

Host dev-server
    User dev-user
    HostName dev.example.com
    RemoteCommand tmux new -A -s dev
    RequestTTY yes
    SendEnv LANG LC_ALL
```

Usage:

```bash
# Connect to production (starts tmux session automatically)
ssh prod-server

# Detach: Ctrl+Space d
# Reconnect: ssh prod-server (resumes session)
```

### Keyboard Layout on Remote Servers

**The Problem:**

When SSHing from macOS (Norwegian) to Linux (US/Default):

1. macOS sends Norwegian keycodes
2. Remote tmux interprets with US keyboard mapping
3. Result: Wrong characters and broken keybindings

**Solutions:**

**Solution 1: Set remote keyboard to Norwegian**

```bash
# On remote Linux system
sudo dpkg-reconfigure keyboard-configuration

# Or set specifically
setxkbmap -layout "no"

# Make persistent
echo 'setxkbmap -layout "no"' >> ~/.bashrc
```

**Solution 2: Use SSH -X for forwarding**

```bash
# Forward special characters properly
ssh -X user@remote-server
```

**Solution 3: Sync tmux config**

```bash
# Sync config to remote
rsync -avz ~/.tmux.conf user@remote-server:~/.tmux.conf

# Or use Git dotfiles
```

### Nested tmux Sessions

When SSH'ing into a server with tmux, use different prefixes:

```bash
# Local: Ctrl+Space
# Remote: Ctrl+a (add to remote ~/.tmux.conf)
set -g prefix C-a
unbind C-b
bind C-a send-prefix
```

Now local tmux uses `Ctrl+Space` and remote uses `Ctrl+a`.

## Session Commands

```bash
# Create session
tmux new-session -s dev
tmux new -s dev                 # Short form

# Create detached session
tmux new -d -s background

# List sessions
tmux list-sessions
tmux ls

# Attach to session
tmux attach -t dev
tmux a -t dev

# Attach or create if doesn't exist
tmux new -A -s dev

# Kill session
tmux kill-session -t dev

# Kill all sessions
tmux kill-server

# Rename session
tmux rename-session -t old new
```

## Window Commands

```bash
# Create window
tmux new-window -t dev
tmux new-window -t dev -n logs  # Named window

# Rename window
tmux rename-window -t dev:1 editor

# Kill window
tmux kill-window -t dev:1

# Select window
tmux select-window -t dev:2
```

## Pane Commands

```bash
# Split panes
tmux split-window -h            # Horizontal
tmux split-window -v            # Vertical

# Resize pane
tmux resize-pane -D 10          # Down 10 lines
tmux resize-pane -U 10          # Up 10 lines
tmux resize-pane -L 10          # Left 10 columns
tmux resize-pane -R 10          # Right 10 columns
```

## Layouts

tmux has built-in layouts:

| Layout | Description |
|--------|-------------|
| `even-horizontal` | Panes spread left to right |
| `even-vertical` | Panes spread top to bottom |
| `main-horizontal` | Large pane on top, smaller below |
| `main-vertical` | Large pane on left, smaller on right |
| `tiled` | Even grid |

Cycle layouts with `Ctrl+Space space` or set directly:

```bash
tmux select-layout main-vertical
```

## Plugins with TPM

### Install TPM

```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

### Essential Plugins

Add to `~/.tmux.conf`:

```bash
# Plugin manager
set -g @plugin 'tmux-plugins/tpm'

# Sensible defaults
set -g @plugin 'tmux-plugins/tmux-sensible'

# Save and restore sessions
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'

# Better copy/paste (important for Norwegian text)
set -g @plugin 'tmux-plugins/tmux-yank'

# Initialize (keep at bottom)
run '~/.tmux/plugins/tpm/tpm'
```

### TPM Commands

| Key | Action |
|-----|--------|
| `Ctrl+Space I` | Install plugins |
| `Ctrl+Space U` | Update plugins |
| `Ctrl+Space Alt+u` | Uninstall plugins |

### tmux-yank Configuration

Essential for proper Norwegian text copy/paste:

```bash
# macOS clipboard integration
set -g @yank-selection-command 'pbcopy'
set -g @yank-selection-primary-command 'pbcopy'
set -g @yank-action 'copy-pipe-no-clear'
```

### tmux-resurrect and tmux-continuum

Save and restore sessions across restarts:

```bash
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'

# Auto-restore on tmux start
set -g @continuum-restore 'on'

# Save interval in minutes
set -g @continuum-save-interval '10'

# Restore vim/neovim sessions
set -g @resurrect-strategy-vim 'session'
set -g @resurrect-strategy-nvim 'session'
```

| Key | Action |
|-----|--------|
| `Ctrl+Space Ctrl+s` | Save session |
| `Ctrl+Space Ctrl+r` | Restore session |

## Profile-Based Sessions

### Development Profile

Create `~/.tmux/profiles/dev.sh`:

```bash
#!/bin/bash
SESSION="dev"

tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
    # Create session with editor window
    tmux new-session -d -s $SESSION -n editor
    tmux send-keys -t $SESSION:editor "nvim" Enter

    # Shell window
    tmux new-window -t $SESSION -n shell

    # Server window
    tmux new-window -t $SESSION -n server
    tmux send-keys -t $SESSION:server "npm run dev" Enter

    # Logs window with splits
    tmux new-window -t $SESSION -n logs
    tmux split-window -h -t $SESSION:logs
    tmux send-keys -t $SESSION:logs.0 "tail -f app.log" Enter
    tmux send-keys -t $SESSION:logs.1 "tail -f error.log" Enter

    # Select editor window
    tmux select-window -t $SESSION:editor
fi

tmux attach -t $SESSION
```

### Shell Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias tmux-dev='~/.tmux/profiles/dev.sh'
alias tmux-prod='~/.tmux/profiles/prod.sh'
```

## Troubleshooting Norwegian Layout Issues

### Characters Not Appearing

**Problem:** Norwegian characters (ae, o, a) don't appear or show as different symbols.

**Solutions:**

1. Check terminal font support:
```bash
echo "ae o a O A AE"
```

2. Verify UTF-8:
```bash
# In ~/.bashrc
export LANG="nb_NO.UTF-8"
export LC_ALL="nb_NO.UTF-8"
```

3. In tmux config:
```bash
set -g default-terminal "screen-256color"
```

### Prefix Key Not Working

**Problem:** `Ctrl+Space` doesn't respond.

**Solutions:**

1. Check for conflicting bindings:
```bash
tmux list-keys | grep "C-Space"
```

2. Test prefix in fresh session:
```bash
tmux -f /dev/null new-session
```

3. Verify terminal sends correct codes (use Ghostty, iTerm2, or Alacritty)

### Copy/Paste Issues

**Problem:** Can't copy Norwegian text or paste doesn't work.

**Solutions:**

1. Use tmux-yank plugin:
```bash
set -g @plugin 'tmux-plugins/tmux-yank'
set -g @yank-selection-command 'pbcopy'
```

2. Enable OSC 52:
```bash
set -g set-clipboard on
```

3. In iTerm2: Preferences > Profiles > General > Enable "Applications in terminal may access clipboard"

### Slow Escape Key

Add to config:

```bash
set -sg escape-time 0
```

### Colors Not Working

```bash
# Check terminal supports 256 colors
echo $TERM

# In tmux.conf
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
```

## Performance Optimization

```bash
# Reduce input lag
set -s escape-time 0
set -g status-interval 5

# Limit history
set -g history-limit 10000

# Disable bells
set -g bell-action none
set -g visual-bell off

# Disable activity monitoring
set -g visual-activity off
setw -g monitor-activity off
```

## Quick Reference

### Essential Commands

```bash
tmux new -s name              # New session
tmux attach -t name           # Attach to session
tmux ls                       # List sessions
tmux kill-session -t name     # Kill session
tmux source-file ~/.tmux.conf # Reload config
tmux list-keys                # Show keybindings
```

### Common Workflows

**Development workflow:**

```bash
# Start dev session
tmux new -s dev

# Split into panes:
# Ctrl+Space v (vertical split) - left: editor
# Ctrl+Space s (horizontal split) - top right: server
# Ctrl+Space s (horizontal split) - bottom right: tests

# Navigate between panes
# Ctrl+Space h/j/k/l

# Create new window for different service
# Ctrl+Space c
```

**Multi-project workflow:**

```bash
# Named sessions for each project
tmux new -s project-a
tmux new -s project-b

# Switch between projects
tmux ls
tmux switch-client -t project-a

# Each session maintains its own layout
```

## Summary Checklist for Norwegian Layout

- [ ] Change prefix from `Ctrl+b` to `Ctrl+Space`
- [ ] Use terminal with good keyboard handling (Ghostty, iTerm2, Alacritty)
- [ ] Configure SSH hosts for proper locale (`SendEnv LANG LC_ALL`)
- [ ] Install tmux-yank for macOS clipboard
- [ ] Configure tmux-resurrect for session persistence
- [ ] Use h/j/k/l navigation (avoids Norwegian character conflicts)
- [ ] Test Norwegian character input in copy mode
- [ ] Document your custom configuration

## Related Tools

- [Ghostty](../configuration/ghostty/index.md) - Modern terminal with good keyboard support
- [Neovim](../configuration/neovim/index.md) - Terminal editor that works well with tmux
- [Starship](../configuration/starship/index.md) - Cross-shell prompt
- [lazygit](lazygit.md) - Git TUI that works in tmux panes
