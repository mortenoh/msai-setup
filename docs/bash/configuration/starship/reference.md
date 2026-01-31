# Quick Reference

A condensed reference for Starship configuration.

## Installation

```bash
# macOS/Linux
curl -sS https://starship.rs/install.sh | sh

# Homebrew
brew install starship

# Cargo
cargo install starship --locked
```

## Shell Setup

=== "Bash"

    ```bash
    # ~/.bashrc
    eval "$(starship init bash)"
    ```

=== "Zsh"

    ```bash
    # ~/.zshrc
    eval "$(starship init zsh)"
    ```

=== "Fish"

    ```fish
    # ~/.config/fish/config.fish
    starship init fish | source
    ```

=== "PowerShell"

    ```powershell
    # $PROFILE
    Invoke-Expression (&starship init powershell)
    ```

## Configuration File

**Location:** `~/.config/starship.toml`

**Custom location:**
```bash
export STARSHIP_CONFIG=~/path/to/starship.toml
```

## Style Syntax

```
style = "attribute color"
style = "fg:color bg:color"
style = "bold italic underline dimmed fg:#hex"
```

### Colors

| Type | Examples |
|------|----------|
| Basic | `black`, `red`, `green`, `yellow`, `blue`, `purple`, `cyan`, `white` |
| Bright | `bright-red`, `bright-green`, etc. |
| Hex | `#ff5733`, `#2e3440` |
| 256 | `208`, `39`, `156` |

### Attributes

`bold`, `italic`, `underline`, `dimmed`, `inverted`, `blink`

## Format Strings

```toml
format = "text [$variable]($style) "
format = "[$symbol$version]($style)"
format = "(optional content)"  # Shows only if variables have values
```

## Common Modules

### Character

```toml
[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"
vimcmd_symbol = "[<](bold green)"
```

### Directory

```toml
[directory]
truncation_length = 3
truncate_to_repo = true
style = "bold cyan"
format = "[$path]($style)[$read_only]($read_only_style) "
```

### Git Branch

```toml
[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"
truncation_length = 30
```

### Git Status

```toml
[git_status]
format = '([$all_status$ahead_behind]($style) )'
style = "bold red"
ahead = "up${count}"
behind = "dn${count}"
conflicted = "!"
untracked = "?"
modified = "*"
staged = "+"
renamed = ">"
deleted = "x"
stashed = "$"
```

### Time

```toml
[time]
disabled = false
format = "[$time]($style)"
time_format = "%H:%M"
style = "dimmed"
```

### Command Duration

```toml
[cmd_duration]
min_time = 2000
format = "[$duration]($style) "
style = "yellow"
```

## Language Modules

```toml
[nodejs]
format = "[$symbol($version )]($style)"
symbol = " "

[python]
format = '[$symbol$version(\($virtualenv\))]($style) '
symbol = " "

[rust]
format = "[$symbol($version )]($style)"
symbol = " "

[golang]
format = "[$symbol($version )]($style)"
symbol = " "
```

## Cloud Modules

```toml
[aws]
format = '[$symbol($profile)(\($region\))]($style) '
symbol = " "

[kubernetes]
disabled = false
format = '[$symbol$context(:$namespace)]($style) '
symbol = " "

[docker_context]
format = '[$symbol$context]($style) '
symbol = " "
```

## System Modules

```toml
[hostname]
ssh_only = true
format = "[$hostname]($style) "

[username]
show_always = false
format = "[$user]($style)@"

[battery]
disabled = false
[[battery.display]]
threshold = 20
style = "bold red"

[memory_usage]
disabled = false
threshold = 70
format = "[$ram_pct]($style) "
```

## Custom Modules

```toml
[custom.name]
command = "echo output"
when = "test condition"
format = "[$symbol$output]($style) "
style = "bold green"
symbol = " "
detect_files = ["file.txt"]
```

## Disable Modules

```toml
[package]
disabled = true

[battery]
disabled = true
```

## Enable Disabled-by-Default

```toml
[time]
disabled = false

[status]
disabled = false

[hostname]
ssh_only = false
```

## Presets

```bash
# List presets
starship preset --list

# Apply preset (overwrites config!)
starship preset nerd-font-symbols -o ~/.config/starship.toml

# Preview preset
starship preset nerd-font-symbols
```

## Debugging

```bash
# Show active modules
starship explain

# Show timings
starship timings

# Print merged config
starship print-config

# Generate bug report
starship bug-report

# Verbose logging
STARSHIP_LOG=trace starship prompt
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `STARSHIP_CONFIG` | Config file path |
| `STARSHIP_CACHE` | Cache directory |
| `STARSHIP_LOG` | Log level (trace, debug, info) |

## Common Patterns

### Minimal Prompt

```toml
add_newline = false
format = "$directory$character"

[character]
success_symbol = "[>](green)"
error_symbol = "[>](red)"

[directory]
truncation_length = 1
```

### Two-Line Prompt

```toml
format = """
$directory$git_branch$git_status
$character"""
```

### Right Prompt

```toml
right_format = "$time$cmd_duration"
```

### Developer Prompt

```toml
format = """
$directory$git_branch$git_status
$nodejs$python$rust$golang
$character"""
```

### Server Prompt

```toml
format = """
$username@$hostname $directory$git_branch
$character"""

[username]
show_always = true

[hostname]
ssh_only = false
```

## Nerd Font Symbols

| Module | Symbol |
|--------|--------|
| Git |  |
| Node.js |  |
| Python |  |
| Rust |  |
| Go |  |
| Docker |  |
| Kubernetes |  |
| AWS |  |
| Directory |  |
| Time |  |

## Text-Only Symbols

```toml
[git_branch]
symbol = "git:"

[nodejs]
symbol = "node:"

[python]
symbol = "py:"

[rust]
symbol = "rs:"

[golang]
symbol = "go:"

[docker_context]
symbol = "docker:"

[kubernetes]
symbol = "k8s:"

[aws]
symbol = "aws:"
```

## Links

- [Official Docs](https://starship.rs/)
- [Configuration Reference](https://starship.rs/config/)
- [Presets](https://starship.rs/presets/)
- [GitHub](https://github.com/starship/starship)
