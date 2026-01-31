# Presets

Starship presets are pre-configured themes that you can apply instantly. This guide covers built-in presets and how to create your own.

## Using Presets

### Apply a Preset

Use the `starship preset` command to apply a built-in preset:

```bash
starship preset nerd-font-symbols -o ~/.config/starship.toml
```

!!! warning
    This overwrites your existing configuration. Back up first:
    ```bash
    cp ~/.config/starship.toml ~/.config/starship.toml.backup
    ```

### Preview a Preset

View preset contents without applying:

```bash
starship preset nerd-font-symbols
```

### List Available Presets

```bash
starship preset --list
```

## Built-in Presets

### Nerd Font Symbols

Replaces text with Nerd Font symbols throughout.

```bash
starship preset nerd-font-symbols -o ~/.config/starship.toml
```

**Characteristics:**

- Uses Nerd Font icons for all modules
- Minimal text, maximum symbols
- Requires Nerd Font installed

### Plain Text Symbols

ASCII-only symbols for terminals without Nerd Fonts.

```bash
starship preset plain-text-symbols -o ~/.config/starship.toml
```

**Characteristics:**

- No special fonts required
- Works on any terminal
- Uses text abbreviations

### No Nerd Font

Modern look without requiring Nerd Fonts.

```bash
starship preset no-nerd-font -o ~/.config/starship.toml
```

**Characteristics:**

- Unicode symbols only
- Clean, modern appearance
- Good compatibility

### Bracketed Segments

Each module wrapped in brackets with distinct styling.

```bash
starship preset bracketed-segments -o ~/.config/starship.toml
```

**Characteristics:**

- Clear module separation
- `[module]` format
- Easy to scan

### Pure

Minimal prompt inspired by [Pure](https://github.com/sindresorhus/pure).

```bash
starship preset pure-preset -o ~/.config/starship.toml
```

**Characteristics:**

- Clean, minimal design
- Two-line prompt
- Shows only essential info

### Pastel Powerline

Powerline-style segments with pastel colors.

```bash
starship preset pastel-powerline -o ~/.config/starship.toml
```

**Characteristics:**

- Powerline arrows between segments
- Soft pastel colors
- Requires Nerd Font for arrows

### Tokyo Night

Based on the Tokyo Night color scheme.

```bash
starship preset tokyo-night -o ~/.config/starship.toml
```

**Characteristics:**

- Dark theme colors
- Cohesive palette
- Modern aesthetic

### Gruvbox Rainbow

Gruvbox colors with rainbow-style module backgrounds.

```bash
starship preset gruvbox-rainbow -o ~/.config/starship.toml
```

**Characteristics:**

- Gruvbox color palette
- Colorful backgrounds
- High visibility

### Jetpack

Compact prompt with emoji indicators.

```bash
starship preset jetpack -o ~/.config/starship.toml
```

**Characteristics:**

- Uses emoji icons
- Compact layout
- Playful style

## Creating Custom Presets

### Starting from Scratch

Create a complete configuration in `~/.config/starship.toml`:

```toml
# Custom preset: Minimal Developer

format = """
$directory\
$git_branch\
$git_status\
$character"""

add_newline = false

[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"

[directory]
truncation_length = 2
style = "bold cyan"

[git_branch]
format = "[$branch]($style) "
style = "bold purple"

[git_status]
format = "[$all_status]($style)"
style = "red"
conflicted = "!"
ahead = "^"
behind = "v"
diverged = "^v"
untracked = "?"
stashed = "*"
modified = "~"
staged = "+"
renamed = ">"
deleted = "x"
```

### Extending a Preset

Apply a preset then customize specific parts:

```bash
# Start with a preset
starship preset plain-text-symbols -o ~/.config/starship.toml

# Then edit to customize
```

Add your customizations at the end of the file:

```toml
# ... preset content above ...

# My customizations
[directory]
truncation_length = 4

[time]
disabled = false
format = "[$time]($style)"
```

### Sharing Presets

Share your preset by:

1. Saving the TOML file
2. Sharing via dotfiles repo
3. Contributing to Starship presets (see [contributing guide](https://github.com/starship/starship/blob/master/CONTRIBUTING.md))

## Preset Examples

### Minimal Single-Line

```toml
# Minimal single-line prompt
format = "$directory$git_branch$character"
add_newline = false

[character]
success_symbol = " [>](green)"
error_symbol = " [>](red)"

[directory]
format = "[$path]($style)"
truncation_length = 1
style = "cyan"

[git_branch]
format = " [$branch]($style)"
style = "purple"
```

Output: `mydir main >`

### Developer Two-Line

```toml
# Two-line developer prompt
format = """
$directory$git_branch$git_status$nodejs$python$rust$golang
$character"""

[character]
success_symbol = "[->](bold green)"
error_symbol = "[->](bold red)"

[directory]
format = "[$path]($style) "
truncation_length = 3
style = "bold blue"

[git_branch]
format = "on [$symbol$branch]($style) "
symbol = ""
style = "bold purple"

[git_status]
format = '([$all_status$ahead_behind]($style) )'
style = "bold red"

[nodejs]
format = "via [$symbol$version]($style) "
symbol = "node "
style = "green"

[python]
format = 'via [$symbol$version(\($virtualenv\))]($style) '
symbol = "py "
style = "yellow"

[rust]
format = "via [$symbol$version]($style) "
symbol = "rs "
style = "red"

[golang]
format = "via [$symbol$version]($style) "
symbol = "go "
style = "cyan"
```

### Server/SSH Focused

```toml
# Server-focused prompt with host info
format = """
$username@$hostname $directory $git_branch$git_status
$character"""

[username]
show_always = true
format = "[$user]($style)"
style_user = "yellow"
style_root = "bold red"

[hostname]
ssh_only = false
format = "[$hostname]($style)"
style = "bold green"

[directory]
format = "[$path]($style)"
truncation_length = 3
style = "cyan"

[character]
success_symbol = "[\\$](green)"
error_symbol = "[\\$](red)"

# Disable unnecessary modules for servers
[package]
disabled = true

[nodejs]
disabled = true

[python]
disabled = true
```

### Git-Centric

```toml
# Detailed git information
format = """
$directory
$git_branch$git_commit$git_state$git_metrics$git_status
$character"""

add_newline = true

[directory]
format = "[$path]($style)"
truncation_length = 5
style = "bold blue"

[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
symbol = "branch:"
style = "bold purple"

[git_commit]
format = "[commit:$hash$tag]($style) "
style = "green"
only_detached = false
tag_disabled = false

[git_state]
format = '[\($state( $progress_current/$progress_total)\)]($style) '
style = "bold yellow"

[git_metrics]
disabled = false
format = "([+$added]($added_style) )([-$deleted]($deleted_style) )"
added_style = "green"
deleted_style = "red"

[git_status]
format = '([$all_status$ahead_behind]($style))'
style = "bold red"
ahead = " up:${count}"
behind = " down:${count}"
diverged = " diverged"
conflicted = " conflict:${count}"
untracked = " ?:${count}"
stashed = " stash:${count}"
modified = " mod:${count}"
staged = " staged:${count}"
renamed = " ren:${count}"
deleted = " del:${count}"

[character]
success_symbol = "[->](bold green)"
error_symbol = "[->](bold red)"
```

### Cloud DevOps

```toml
# Cloud and DevOps focused
format = """
$directory$git_branch$git_status
$aws$gcloud$kubernetes$docker_context$terraform
$character"""

[directory]
truncation_length = 2
style = "bold blue"

[git_branch]
format = "[$branch]($style) "
style = "purple"

[git_status]
format = "[$all_status]($style) "
style = "red"

[aws]
format = '[$symbol$profile(\($region\))]($style) '
symbol = "aws:"
style = "bold yellow"

[aws.region_aliases]
us-east-1 = "ue1"
us-west-2 = "uw2"
eu-west-1 = "ew1"

[gcloud]
format = '[$symbol$project]($style) '
symbol = "gcp:"
style = "bold blue"

[kubernetes]
disabled = false
format = '[$symbol$context(:$namespace)]($style) '
symbol = "k8s:"
style = "bold cyan"

[kubernetes.context_aliases]
"arn:aws:eks:*:*:cluster/prod-*" = "prod"
"arn:aws:eks:*:*:cluster/stage-*" = "stage"

[docker_context]
format = '[$symbol$context]($style) '
symbol = "docker:"
only_with_files = true

[terraform]
format = '[$symbol$workspace]($style) '
symbol = "tf:"

[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"
```

## Preset Organization

### Storing Multiple Presets

Keep multiple configurations and switch between them:

```bash
# Directory structure
~/.config/starship/
  minimal.toml
  developer.toml
  server.toml
  current.toml -> minimal.toml  # symlink
```

**Switch script:**

```bash
#!/bin/bash
# ~/.local/bin/starship-preset

PRESET_DIR="$HOME/.config/starship"
CONFIG="$HOME/.config/starship.toml"

case "$1" in
  minimal|developer|server)
    cp "$PRESET_DIR/$1.toml" "$CONFIG"
    echo "Switched to $1 preset"
    ;;
  *)
    echo "Usage: starship-preset [minimal|developer|server]"
    ;;
esac
```

### Per-Machine Configuration

Use environment variables for machine-specific configs:

```bash
# In .bashrc or .zshrc
export STARSHIP_CONFIG="$HOME/.config/starship/$HOSTNAME.toml"

# Fallback to default if not found
if [[ ! -f "$STARSHIP_CONFIG" ]]; then
  export STARSHIP_CONFIG="$HOME/.config/starship.toml"
fi

eval "$(starship init bash)"
```
