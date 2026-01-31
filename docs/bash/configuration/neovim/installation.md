# Installation

Setting up Neovim with LazyVim from scratch.

## Prerequisites

Ensure the following tools are installed:

```bash
# macOS
brew install neovim git curl

# Required for plugins
brew install ripgrep fd lazygit

# Optional but recommended
brew install node npm python3
```

### Minimum Versions

- Neovim >= 0.9.0 (0.10+ recommended)
- Git >= 2.19.0
- A Nerd Font for icons (recommended)

### Install a Nerd Font

```bash
# Install JetBrains Mono Nerd Font
brew install --cask font-jetbrains-mono-nerd-font
```

Configure your terminal to use the Nerd Font.

## Installing Neovim

### macOS (Homebrew)

```bash
brew install neovim
```

### Linux (Ubuntu/Debian)

```bash
# Via apt (may not be latest)
sudo apt install neovim

# Via AppImage (latest)
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage
chmod u+x nvim.appimage
sudo mv nvim.appimage /usr/local/bin/nvim
```

### Verify Installation

```bash
nvim --version
# Should show v0.9+ or v0.10+
```

## Installing LazyVim

### Backup Existing Configuration

```bash
# Required backup
mv ~/.config/nvim ~/.config/nvim.bak

# Optional: backup runtime data
mv ~/.local/share/nvim ~/.local/share/nvim.bak
mv ~/.local/state/nvim ~/.local/state/nvim.bak
mv ~/.cache/nvim ~/.cache/nvim.bak
```

### Clone LazyVim Starter

```bash
git clone https://github.com/LazyVim/starter ~/.config/nvim
```

### Remove Git History (Optional)

To start fresh without starter's git history:

```bash
rm -rf ~/.config/nvim/.git
```

### First Launch

```bash
nvim
```

On first launch:

1. lazy.nvim (plugin manager) bootstraps itself
2. LazyVim plugins are installed
3. Language servers are downloaded via Mason

This may take a few minutes. Press `q` to close any prompts and let it finish.

## Post-Installation

### Health Check

Run inside Neovim:

```vim
:checkhealth
```

Address any warnings or errors shown.

### Install Language Servers

Open Mason UI:

```vim
:Mason
```

Navigate and install language servers for your languages.

### Set Up Shell Alias

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias vim='nvim'
alias vi='nvim'
```

## Updating

### Update Plugins

Inside Neovim:

```vim
:Lazy sync
```

Or press `S` in the Lazy UI (`:Lazy`).

### Update Neovim

```bash
brew upgrade neovim
```

### Update LazyVim

LazyVim updates automatically with `:Lazy sync`. To check the version:

```vim
:LazyVersion
```

## Uninstalling

### Remove Configuration

```bash
rm -rf ~/.config/nvim
```

### Remove Runtime Data

```bash
rm -rf ~/.local/share/nvim
rm -rf ~/.local/state/nvim
rm -rf ~/.cache/nvim
```

### Restore Backup

```bash
mv ~/.config/nvim.bak ~/.config/nvim
```

## Directory Structure

After installation:

```
~/.config/nvim/
├── init.lua              # Entry point
├── lazy-lock.json        # Plugin version lockfile
├── lazyvim.json          # LazyVim extras config
├── lua/
│   ├── config/
│   │   ├── autocmds.lua  # Auto commands
│   │   ├── keymaps.lua   # Custom keybindings
│   │   ├── lazy.lua      # Plugin manager setup
│   │   └── options.lua   # Editor options
│   └── plugins/
│       └── *.lua         # Custom plugin specs
└── stylua.toml           # Lua formatter config
```

## Dotfiles Integration

To manage your Neovim config with dotfiles:

```bash
# Move config to dotfiles
mv ~/.config/nvim ~/dotfiles/config/nvim

# Create symlink
ln -s ~/dotfiles/config/nvim ~/.config/nvim
```

Or use a dotfiles manager like `stow`:

```bash
cd ~/dotfiles
stow -t ~ config
```
