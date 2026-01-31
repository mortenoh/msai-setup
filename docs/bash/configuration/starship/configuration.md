# Configuration

Starship is configured through a single TOML file. This guide covers the configuration file structure, format strings, and how to customize modules.

## Configuration File

### Location

Starship looks for configuration in this order:

1. `$STARSHIP_CONFIG` environment variable
2. `~/.config/starship.toml`
3. `$XDG_CONFIG_HOME/starship.toml`

**Create the default configuration file:**

```bash
mkdir -p ~/.config
touch ~/.config/starship.toml
```

**Use a custom location:**

```bash
export STARSHIP_CONFIG=~/dotfiles/starship.toml
```

### TOML Basics

Starship uses [TOML](https://toml.io/) format. Key syntax:

```toml
# This is a comment

# Top-level options
add_newline = true
command_timeout = 500

# Module configuration (section headers)
[directory]
truncation_length = 3

# Nested tables
[git_status]
ahead = "up "
behind = "down "
```

## Root Options

These options are set at the top level of the configuration file:

```toml
# Add blank line before prompt
add_newline = true

# Custom prompt format (overrides default)
format = "$all"

# Right-side prompt format
right_format = "$time"

# Continuation prompt for multi-line input
continuation_prompt = "[>](bright-black) "

# Timeout for commands (milliseconds)
command_timeout = 500

# Follow symlinks when determining directories
scan_timeout = 30

# Custom palette
palette = "catppuccin_mocha"
```

### The Format String

The `format` option defines the order and content of your prompt. By default, Starship uses a predefined order of all enabled modules.

**Default format (simplified):**

```toml
format = """
$username\
$hostname\
$directory\
$git_branch\
$git_status\
$character"""
```

**Customize module order:**

```toml
format = """
$directory\
$git_branch\
$git_status\
$nodejs\
$python\
$rust\
$line_break\
$character"""
```

**Add static text:**

```toml
format = """
[myserver](bold blue) \
$directory\
$git_branch\
$character"""
```

## Module Configuration

Each module has its own configuration section. Common options shared across modules:

| Option | Description | Example |
|--------|-------------|---------|
| `disabled` | Disable the module | `disabled = true` |
| `format` | Module's format string | `format = "via [$symbol]($style)"` |
| `style` | Text styling | `style = "bold green"` |
| `symbol` | Symbol displayed | `symbol = " "` |

### Enabling and Disabling Modules

**Disable a module:**

```toml
[package]
disabled = true

[battery]
disabled = true
```

**Enable a disabled-by-default module:**

```toml
[hostname]
ssh_only = false
disabled = false
```

### Format Strings

Module format strings define how the module is displayed. They contain:

- **Variables** - Dynamic content in `$variable` or `${variable}` syntax
- **Text** - Static text
- **Styled sections** - Text in `[text](style)` syntax
- **Conditionals** - Optional sections in `(content)` syntax

**Example breakdown:**

```toml
[git_branch]
format = "on [$symbol$branch(:$remote_branch)]($style) "
#       |   |       |        |              |      |
#       |   |       |        |              |      +-- space after module
#       |   |       |        |              +-- style for entire bracket
#       |   |       |        +-- remote branch if different
#       |   |       +-- branch name variable
#       |   +-- symbol variable
#       +-- static text
```

**Available variables vary by module.** Check the [Reference](reference.md) or official docs.

### Conditional Groups

Parentheses `()` create optional groups that only display if all variables inside have values:

```toml
[git_branch]
# Only shows remote if it differs from local
format = "[$branch(:$remote_branch)]($style)"
```

### Variable Formatting

Variables can include formatting modifiers:

```toml
# Padding
${variable:padding}

# Example: Right-pad to 10 characters
[directory]
format = "[$path](bold blue)${read_only:>2}"
```

## Styling

Styles are defined as strings with space-separated attributes:

```toml
[directory]
style = "bold bright-blue underline"
```

**Available attributes:**

- Colors: `black`, `red`, `green`, `yellow`, `blue`, `purple`, `cyan`, `white`
- Bright variants: `bright-black`, `bright-red`, etc.
- Modifiers: `bold`, `italic`, `underline`, `dimmed`, `inverted`, `blink`
- Hex colors: `#ff5733`
- 256 colors: `color123`

**Foreground and background:**

```toml
style = "fg:green bg:blue"
style = "fg:#ff5733 bg:black"
```

See the [Styling Guide](styling.md) for comprehensive coverage.

## Common Configuration Patterns

### Minimal Prompt

```toml
add_newline = false

format = """$directory$character"""

[directory]
truncation_length = 1

[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"
```

Output: `mydir>`

### Two-Line Prompt

```toml
format = """
$directory$git_branch$git_status
$character"""

[character]
success_symbol = "[->](bold green)"
error_symbol = "[->](bold red)"
```

Output:
```
~/projects/app main [!]
->
```

### Right-Side Prompt

```toml
right_format = "$time$cmd_duration"

[time]
disabled = false
format = "[$time]($style)"
style = "dimmed"

[cmd_duration]
min_time = 500
format = "took [$duration]($style)"
```

### Git-Focused Prompt

```toml
format = """
$directory\
$git_branch\
$git_commit\
$git_state\
$git_status\
$line_break\
$character"""

[git_branch]
format = "on [$symbol$branch(:$remote_branch)]($style) "
symbol = ""

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
conflicted = "="
ahead = "up${count}"
behind = "down${count}"
diverged = "diverged"
untracked = "?"
stashed = "$"
modified = "!"
staged = "+"
renamed = "r"
deleted = "x"
```

### Developer Prompt with Languages

```toml
format = """
$directory\
$git_branch\
$git_status\
$nodejs\
$python\
$rust\
$golang\
$docker_context\
$line_break\
$character"""

[nodejs]
format = "via [$symbol($version )]($style)"
symbol = " "

[python]
format = 'via [${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'
symbol = " "

[rust]
format = "via [$symbol($version )]($style)"
symbol = " "

[golang]
format = "via [$symbol($version )]($style)"
symbol = " "
```

## Environment Variables

Starship respects these environment variables:

| Variable | Description |
|----------|-------------|
| `STARSHIP_CONFIG` | Path to config file |
| `STARSHIP_CACHE` | Path to cache directory |
| `STARSHIP_SESSION_KEY` | Random key for session-based features |

**Set in shell config:**

```bash
export STARSHIP_CONFIG=~/dotfiles/starship.toml
export STARSHIP_CACHE=~/.cache/starship
```

## Configuration Debugging

### Explain Current Configuration

```bash
starship explain
```

Shows which modules are active and why.

### Print Configuration

```bash
starship print-config
```

Outputs the merged configuration (defaults + your customizations).

### Time Module Rendering

```bash
starship timings
```

Shows how long each module takes to render (useful for optimization).

### Check for Errors

```bash
starship bug-report
```

Generates debug information for troubleshooting.

## Complete Example Configuration

```toml
# General
add_newline = true
command_timeout = 1000

# Prompt format
format = """
$username\
$hostname\
$directory\
$git_branch\
$git_commit\
$git_state\
$git_status\
$docker_context\
$nodejs\
$python\
$rust\
$golang\
$terraform\
$kubernetes\
$aws\
$line_break\
$jobs\
$status\
$character"""

# Right prompt
right_format = "$time"

# Character
[character]
success_symbol = "[->](bold green)"
error_symbol = "[->](bold red)"
vimcmd_symbol = "[<-](bold green)"

# Directory
[directory]
truncation_length = 3
truncate_to_repo = true
style = "bold cyan"

# Git
[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"

# Time (right prompt)
[time]
disabled = false
format = "[$time]($style)"
style = "dimmed white"
time_format = "%H:%M"

# Command duration
[cmd_duration]
min_time = 2000
format = "took [$duration]($style) "
style = "yellow"

# Disabled modules
[package]
disabled = true

[line_break]
disabled = false
```

## Next Steps

- [Learn about all modules](modules.md)
- [Configure Git modules](git-modules.md)
- [Master styling](styling.md)
- [Explore presets](presets.md)
