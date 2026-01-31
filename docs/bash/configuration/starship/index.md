# Starship Prompt

Starship is a minimal, blazing-fast, and infinitely customizable prompt for any shell. It shows information you need while you work, staying out of your way when you don't.

## Why Starship?

### Speed

Starship is written in Rust and optimized for speed. It renders prompts asynchronously, meaning your shell stays responsive even when displaying complex information like git status or cloud contexts.

### Cross-Shell

One configuration works across all major shells:

- Bash
- Zsh
- Fish
- PowerShell
- Nushell
- Cmd (via Clink)

### Intelligent Defaults

Starship automatically detects your environment and shows relevant information:

- Git branch and status when in a repository
- Programming language versions when relevant files are present
- Cloud provider context when configured
- Command execution time for long-running commands

### Highly Customizable

Every aspect of the prompt can be configured through a single TOML file. Enable, disable, or customize any module to match your workflow.

## Quick Start

### Installation

Install via package manager or shell script:

=== "macOS (Homebrew)"

    ```bash
    brew install starship
    ```

=== "Linux (curl)"

    ```bash
    curl -sS https://starship.rs/install.sh | sh
    ```

=== "Cargo"

    ```bash
    cargo install starship --locked
    ```

### Shell Setup

Add the initialization to your shell configuration:

=== "Bash"

    Add to `~/.bashrc`:

    ```bash
    eval "$(starship init bash)"
    ```

=== "Zsh"

    Add to `~/.zshrc`:

    ```bash
    eval "$(starship init zsh)"
    ```

=== "Fish"

    Add to `~/.config/fish/config.fish`:

    ```fish
    starship init fish | source
    ```

### Create Configuration

Create the configuration file:

```bash
mkdir -p ~/.config
touch ~/.config/starship.toml
```

### Verify Installation

Restart your shell or source your configuration:

```bash
source ~/.bashrc  # or ~/.zshrc
```

You should see a new prompt with the default Starship styling.

## Default Prompt

Out of the box, Starship shows:

```
~/projects/myapp on  main [!?] via  v18.17.0
```

This indicates:

| Element | Meaning |
|---------|---------|
| `~/projects/myapp` | Current directory (truncated) |
| `main` | Git branch |
| `[!?]` | Git status (modified, untracked) |
| `v18.17.0` | Node.js version (detected from package.json) |

## Configuration Overview

Starship is configured through `~/.config/starship.toml`. Here's a minimal example:

```toml
# Don't print a new line at the start of the prompt
add_newline = false

# Customize the prompt character
[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"

# Disable the package module
[package]
disabled = true
```

## Documentation Structure

This guide is organized into the following sections:

| Section | Description |
|---------|-------------|
| [Installation](installation.md) | Detailed installation for all platforms |
| [Configuration](configuration.md) | Configuration file and format strings |
| [Modules](modules.md) | Overview of all available modules |
| [Git Modules](git-modules.md) | Git branch, status, and state |
| [Language Modules](language-modules.md) | Programming language version display |
| [Cloud Modules](cloud-modules.md) | AWS, GCP, Kubernetes contexts |
| [System Modules](system-modules.md) | Time, battery, memory, and more |
| [Styling](styling.md) | Colors, fonts, and visual customization |
| [Presets](presets.md) | Built-in and custom presets |
| [Advanced](advanced.md) | Custom commands and conditional logic |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [Reference](reference.md) | Quick reference card |

## Resources

- [Official Documentation](https://starship.rs/)
- [GitHub Repository](https://github.com/starship/starship)
- [Configuration Reference](https://starship.rs/config/)
- [Preset Gallery](https://starship.rs/presets/)
