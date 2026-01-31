# Installation

Starship can be installed on virtually any platform through multiple methods. This guide covers installation and shell configuration for all major environments.

## Prerequisites

### Nerd Fonts (Recommended)

Starship uses symbols that require a patched font for proper display. Install a Nerd Font for the best experience:

**Popular choices:**

- FiraCode Nerd Font
- JetBrainsMono Nerd Font
- Hack Nerd Font
- MesloLGS Nerd Font

**Installation:**

=== "macOS (Homebrew)"

    ```bash
    brew tap homebrew/cask-fonts
    brew install --cask font-fira-code-nerd-font
    ```

=== "Linux"

    Download from [nerdfonts.com](https://www.nerdfonts.com/font-downloads) and install to `~/.local/share/fonts/`:

    ```bash
    mkdir -p ~/.local/share/fonts
    cd ~/.local/share/fonts
    curl -fLo "FiraCode Nerd Font Regular.ttf" \
      https://github.com/ryanoasis/nerd-fonts/raw/HEAD/patched-fonts/FiraCode/Regular/FiraCodeNerdFont-Regular.ttf
    fc-cache -fv
    ```

After installation, configure your terminal emulator to use the Nerd Font.

!!! tip "No Nerd Font?"
    Starship works without Nerd Fonts, but some symbols won't display correctly. You can configure text-only symbols in your configuration. See the [Styling](styling.md) guide for alternatives.

## Installation Methods

### Package Managers

=== "macOS (Homebrew)"

    ```bash
    brew install starship
    ```

=== "macOS (MacPorts)"

    ```bash
    sudo port install starship
    ```

=== "Linux (Homebrew)"

    ```bash
    brew install starship
    ```

=== "Arch Linux"

    ```bash
    pacman -S starship
    ```

=== "Fedora"

    ```bash
    dnf install starship
    ```

=== "Ubuntu/Debian"

    Starship is not in the default repositories. Use the install script or Cargo:

    ```bash
    curl -sS https://starship.rs/install.sh | sh
    ```

=== "Alpine"

    ```bash
    apk add starship
    ```

=== "Windows (Scoop)"

    ```powershell
    scoop install starship
    ```

=== "Windows (Chocolatey)"

    ```powershell
    choco install starship
    ```

=== "Windows (winget)"

    ```powershell
    winget install --id Starship.Starship
    ```

### Install Script

The official install script works on Linux and macOS:

```bash
curl -sS https://starship.rs/install.sh | sh
```

**With options:**

```bash
# Install to custom location
curl -sS https://starship.rs/install.sh | sh -s -- --bin-dir /usr/local/bin

# Install specific version
curl -sS https://starship.rs/install.sh | sh -s -- --version v1.16.0

# Force reinstall
curl -sS https://starship.rs/install.sh | sh -s -- --force
```

### Cargo (Rust)

If you have Rust installed:

```bash
cargo install starship --locked
```

**Update existing installation:**

```bash
cargo install starship --locked --force
```

### Binary Download

Download precompiled binaries from the [GitHub releases page](https://github.com/starship/starship/releases):

```bash
# Example for Linux x86_64
curl -LO https://github.com/starship/starship/releases/latest/download/starship-x86_64-unknown-linux-gnu.tar.gz
tar xzf starship-x86_64-unknown-linux-gnu.tar.gz
sudo mv starship /usr/local/bin/
```

## Shell Configuration

After installing the binary, configure your shell to use Starship.

### Bash

Add to the **end** of `~/.bashrc`:

```bash
eval "$(starship init bash)"
```

!!! note "Login vs Non-Login Shells"
    On some systems, you may need to add this to `~/.bash_profile` as well for login shells.

### Zsh

Add to the **end** of `~/.zshrc`:

```zsh
eval "$(starship init zsh)"
```

### Fish

Add to `~/.config/fish/config.fish`:

```fish
starship init fish | source
```

### PowerShell

Add to your PowerShell profile (find location with `$PROFILE`):

```powershell
Invoke-Expression (&starship init powershell)
```

### Nushell

Add to your Nushell config:

```nu
mkdir ~/.cache/starship
starship init nu | save -f ~/.cache/starship/init.nu
```

Then add to `config.nu`:

```nu
use ~/.cache/starship/init.nu
```

### Cmd (Windows)

Requires [Clink](https://chrisant996.github.io/clink/). Add to the Clink startup script:

```lua
load(io.popen('starship init cmd'):read("*a"))()
```

## Configuration File

Create the configuration directory and file:

```bash
mkdir -p ~/.config
touch ~/.config/starship.toml
```

**Alternative locations:**

Starship looks for configuration in this order:

1. `$STARSHIP_CONFIG` environment variable
2. `~/.config/starship.toml`
3. `$XDG_CONFIG_HOME/starship.toml`

**Use a custom location:**

```bash
export STARSHIP_CONFIG=~/dotfiles/starship.toml
```

## Verifying Installation

Check the installed version:

```bash
starship --version
```

Test the initialization:

```bash
starship init bash  # or zsh, fish, etc.
```

This should output initialization code. If it does, restart your shell or source your configuration:

```bash
source ~/.bashrc  # or ~/.zshrc
```

## Updating Starship

=== "Homebrew"

    ```bash
    brew upgrade starship
    ```

=== "Install Script"

    ```bash
    curl -sS https://starship.rs/install.sh | sh
    ```

=== "Cargo"

    ```bash
    cargo install starship --locked --force
    ```

## Uninstalling

### Remove the Binary

=== "Homebrew"

    ```bash
    brew uninstall starship
    ```

=== "Manual"

    ```bash
    sudo rm /usr/local/bin/starship
    ```

=== "Cargo"

    ```bash
    cargo uninstall starship
    ```

### Clean Up Configuration

Remove the shell initialization line from your shell config file.

Optionally remove the configuration:

```bash
rm ~/.config/starship.toml
```

## Platform-Specific Notes

### macOS

- Use iTerm2 or another terminal that supports true color
- Configure the font in Terminal Preferences or iTerm2 Profiles
- The default Terminal.app has limited color support

### Linux

- Most modern terminals support true color
- If using a tiling window manager, ensure your terminal supports Nerd Fonts
- On servers, consider using a minimal configuration without Nerd Font symbols

### Windows

- Windows Terminal is recommended for best results
- Ensure you're using PowerShell 7+ for full feature support
- WSL works well with Starship (configure your Linux shell inside WSL)

### SSH Sessions

Starship works over SSH, but:

- The remote server needs Starship installed
- Your local terminal needs the Nerd Font configured
- Consider a minimal configuration for slow connections

## Next Steps

- [Configure your prompt](configuration.md)
- [Explore available modules](modules.md)
- [Apply a preset](presets.md)
