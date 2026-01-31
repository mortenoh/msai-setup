# Installation

Installing and setting up VS Code.

## System Requirements

- **Storage**: 500 MB minimum
- **Memory**: 1 GB RAM minimum
- **OS**: Windows 10+, macOS 10.15+, Linux (Debian, Ubuntu, RHEL, etc.)

## Installation

### macOS (Homebrew)

```bash
brew install --cask visual-studio-code
```

### macOS (Direct Download)

1. Download from [code.visualstudio.com](https://code.visualstudio.com/)
2. Open the `.dmg` file
3. Drag VS Code to Applications

### Linux (Debian/Ubuntu)

```bash
# Via snap
sudo snap install --classic code

# Via apt
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code
```

### Linux (Fedora/RHEL)

```bash
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
sudo dnf install code
```

## Shell Integration

### macOS

Add `code` command to PATH:

1. Open VS Code
2. ++cmd+shift+p++ > "Shell Command: Install 'code' command in PATH"

Or manually:

```bash
export PATH="$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
```

### Verify Installation

```bash
code --version
```

## First Launch

On first launch:

1. Choose color theme
2. Sign in (optional, for settings sync)
3. Install recommended extensions

## Configuration Locations

### Settings Files

| Platform | User Settings |
|----------|--------------|
| macOS | `~/Library/Application Support/Code/User/settings.json` |
| Linux | `~/.config/Code/User/settings.json` |
| Windows | `%APPDATA%\Code\User\settings.json` |

### Alternative Paths

Dotfiles commonly store VS Code settings:

```bash
~/.dotfiles/config/vscode/settings.json
```

Symlink to actual location:

```bash
ln -s ~/.dotfiles/config/vscode/settings.json ~/Library/Application\ Support/Code/User/settings.json
```

### Keybindings

| Platform | Location |
|----------|----------|
| macOS | `~/Library/Application Support/Code/User/keybindings.json` |
| Linux | `~/.config/Code/User/keybindings.json` |

## Initial Setup

### Open Settings

- ++cmd+comma++ (GUI)
- ++cmd+shift+p++ > "Preferences: Open Settings (JSON)"

### Minimal Configuration

```json
{
  "editor.fontSize": 14,
  "editor.fontFamily": "JetBrains Mono, Menlo, monospace",
  "editor.formatOnSave": true,
  "editor.minimap.enabled": false,
  "workbench.colorTheme": "Dracula",
  "telemetry.telemetryLevel": "off"
}
```

## Font Installation

Install a programming font:

```bash
# JetBrains Mono
brew install --cask font-jetbrains-mono

# Fira Code
brew install --cask font-fira-code

# With ligatures
brew install --cask font-fira-code-nerd-font
```

Configure in settings:

```json
{
  "editor.fontFamily": "JetBrains Mono",
  "editor.fontLigatures": true
}
```

## Settings Sync

Sync settings across machines:

1. Sign in with GitHub or Microsoft account
2. ++cmd+shift+p++ > "Settings Sync: Turn On"
3. Choose what to sync:
   - Settings
   - Keybindings
   - Extensions
   - UI State
   - Snippets

### Disable Settings Sync

```json
{
  "settingsSync.ignoredSettings": [
    "editor.fontSize",
    "window.zoomLevel"
  ]
}
```

## Profiles

Create different configurations for different projects:

1. ++cmd+shift+p++ > "Profiles: Create Profile"
2. Name the profile
3. Customize settings/extensions
4. Switch: ++cmd+shift+p++ > "Profiles: Switch Profile"

## Extensions Installation

### Via Command Palette

1. ++cmd+shift+x++ to open Extensions
2. Search for extension
3. Click "Install"

### Via CLI

```bash
# Install extension
code --install-extension ms-python.python

# List installed extensions
code --list-extensions

# Uninstall extension
code --uninstall-extension extension-id
```

## Workspace Settings

Create project-specific settings in `.vscode/settings.json`:

```json
{
  "editor.tabSize": 2,
  "python.defaultInterpreterPath": ".venv/bin/python"
}
```

## Portable Mode

For USB installations:

1. Create `data` folder next to VS Code executable
2. Settings stored in `data/user-data`
3. Extensions in `data/extensions`

## Updating

### macOS (Homebrew)

```bash
brew upgrade --cask visual-studio-code
```

### Built-in Updater

VS Code auto-updates by default. Disable:

```json
{
  "update.mode": "none"
}
```

## Uninstalling

### macOS

```bash
# Remove application
rm -rf /Applications/Visual\ Studio\ Code.app

# Remove settings and extensions
rm -rf ~/Library/Application\ Support/Code
rm -rf ~/.vscode
```

### Homebrew

```bash
brew uninstall --cask visual-studio-code
```

## Troubleshooting

### VS Code Won't Start

1. Reset settings:
   ```bash
   mv ~/Library/Application\ Support/Code ~/Library/Application\ Support/Code.backup
   ```
2. Start in safe mode:
   ```bash
   code --disable-extensions
   ```

### Extensions Not Loading

1. Check extensions folder permissions
2. Reload window: ++cmd+shift+p++ > "Developer: Reload Window"
3. Check Output panel for errors

### High Memory Usage

1. Disable unused extensions
2. Exclude large folders from search:
   ```json
   {
     "files.exclude": {
       "**/node_modules": true
     }
   }
   ```
