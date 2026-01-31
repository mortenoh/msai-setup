# Installation

Installing and setting up Zed on your system.

## System Requirements

- **macOS**: 10.15 (Catalina) or later
- **Linux**: Ubuntu 20.04+, Fedora 36+, Arch (experimental)
- **GPU**: Metal-capable GPU (macOS), Vulkan-capable GPU (Linux)

## Installation

### macOS (Homebrew)

```bash
brew install --cask zed
```

### macOS (Direct Download)

Download from [zed.dev](https://zed.dev) and drag to Applications.

### Linux

```bash
# Download and install
curl -f https://zed.dev/install.sh | sh
```

Or via package manager:

```bash
# Arch Linux (AUR)
yay -S zed-editor

# Flatpak
flatpak install flathub dev.zed.Zed
```

## First Launch

1. Open Zed from Applications or run `zed` in terminal
2. Sign in (optional, required for collaboration features)
3. Configure settings via ++cmd+comma++

## Shell Integration

Add Zed to your PATH for terminal access.

### macOS

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/Applications/Zed.app/Contents/MacOS"

# Or create symlink
sudo ln -s "/Applications/Zed.app/Contents/MacOS/cli" /usr/local/bin/zed
```

### Verify Installation

```bash
zed --version
```

## Configuration Location

Settings are stored in:

| Platform | Location |
|----------|----------|
| macOS | `~/.config/zed/settings.json` |
| Linux | `~/.config/zed/settings.json` |

### Keybindings

Custom keybindings:

| Platform | Location |
|----------|----------|
| macOS | `~/.config/zed/keymap.json` |
| Linux | `~/.config/zed/keymap.json` |

## Initial Setup

### Open Settings

Press ++cmd+comma++ or use Command Palette (++cmd+shift+p++) and search "settings".

### Minimal Configuration

```json
{
  "theme": "One Dark Pro",
  "buffer_font_family": "JetBrains Mono",
  "buffer_font_size": 14,
  "ui_font_family": "JetBrains Mono",
  "ui_font_size": 14,
  "format_on_save": "on",
  "telemetry": {
    "diagnostics": false,
    "metrics": false
  }
}
```

## Font Installation

Zed works best with a Nerd Font for icons:

```bash
# JetBrains Mono Nerd Font
brew install --cask font-jetbrains-mono-nerd-font

# Fira Code Nerd Font
brew install --cask font-fira-code-nerd-font

# Hack Nerd Font
brew install --cask font-hack-nerd-font
```

## Sign In

For collaboration features, sign in with GitHub:

1. Click profile icon (bottom left)
2. Select "Sign In"
3. Authenticate with GitHub

## Extensions

Install extensions for additional language support:

1. Press ++cmd+shift+p++
2. Search "extensions"
3. Browse and install

Or via settings:

```bash
# Open extensions directory
open ~/.config/zed/extensions
```

## Dotfiles Integration

To manage Zed config with dotfiles:

```bash
# Move config to dotfiles
mv ~/.config/zed ~/dotfiles/config/zed

# Create symlink
ln -s ~/dotfiles/config/zed ~/.config/zed
```

## Updating

### macOS (Homebrew)

```bash
brew upgrade --cask zed
```

### Built-in Updater

Zed auto-updates by default. Check for updates:

1. Click Zed menu
2. Select "Check for Updates"

### Disable Auto-Update

```json
{
  "auto_update": false
}
```

## Uninstalling

### macOS

```bash
# Remove application
rm -rf /Applications/Zed.app

# Remove configuration
rm -rf ~/.config/zed

# Remove cache
rm -rf ~/Library/Caches/Zed
rm -rf ~/Library/Application\ Support/Zed
```

### Homebrew

```bash
brew uninstall --cask zed
```

## Troubleshooting Installation

### Zed Won't Start

1. Check system requirements (GPU support)
2. Reset preferences:
   ```bash
   rm -rf ~/.config/zed
   ```
3. Check logs:
   ```bash
   open ~/Library/Logs/Zed
   ```

### CLI Not Found

Ensure PATH includes Zed:

```bash
# Add to shell config
export PATH="$PATH:/Applications/Zed.app/Contents/MacOS"
```

### Font Not Displaying

1. Verify font installed: `fc-list | grep JetBrains`
2. Restart Zed after font installation
3. Check exact font name in Font Book

## Project Setup

### Open Project

```bash
# Open directory
zed ~/projects/myapp

# Open multiple directories
zed ~/project1 ~/project2
```

### Workspace Settings

Create `.zed/settings.json` in project root for project-specific settings:

```json
{
  "tab_size": 2,
  "languages": {
    "JavaScript": {
      "tab_size": 2
    }
  }
}
```
