# Modules Overview

Starship's power comes from its modular design. Each module displays specific information and can be independently configured, styled, or disabled. This guide provides an overview of all available modules.

## Module Categories

Starship modules fall into these categories:

| Category | Modules | Purpose |
|----------|---------|---------|
| **Core** | character, directory, line_break | Basic prompt structure |
| **Git** | git_branch, git_commit, git_state, git_status, git_metrics | Version control |
| **Languages** | nodejs, python, rust, go, java, etc. | Development environment |
| **Cloud** | aws, gcloud, kubernetes, terraform | Cloud contexts |
| **System** | time, battery, memory_usage, hostname | System information |
| **Shell** | cmd_duration, jobs, status, shell | Shell state |
| **Custom** | custom, env_var | User-defined modules |

## How Modules Work

### Automatic Detection

Most modules only appear when relevant. For example:

- `git_branch` only shows in Git repositories
- `nodejs` only shows when `package.json` or `.js` files are present
- `python` only shows when `.py` files or `requirements.txt` exist

### Module Order

The default prompt includes modules in a predefined order. Customize with the `format` option:

```toml
format = """
$directory\
$git_branch\
$git_status\
$nodejs\
$python\
$line_break\
$character"""
```

### Common Module Options

All modules share these options:

| Option | Type | Description |
|--------|------|-------------|
| `disabled` | bool | Disable the module |
| `format` | string | Module format string |
| `style` | string | Text styling |

## Core Modules

### character

The prompt symbol that indicates success/failure of the last command.

```toml
[character]
success_symbol = "[->](bold green)"
error_symbol = "[->](bold red)"
vimcmd_symbol = "[<-](bold green)"
vimcmd_replace_symbol = "[<-](bold purple)"
vimcmd_replace_one_symbol = "[<-](bold purple)"
vimcmd_visual_symbol = "[<-](bold yellow)"
```

**Variables:** `symbol`

### directory

Shows the current working directory.

```toml
[directory]
truncation_length = 3
truncate_to_repo = true
truncation_symbol = ".../"
home_symbol = "~"
read_only = " ro"
read_only_style = "red"
style = "bold cyan"
format = "[$path]($style)[$read_only]($read_only_style) "
```

**Key options:**

| Option | Default | Description |
|--------|---------|-------------|
| `truncation_length` | 3 | Directories to keep |
| `truncate_to_repo` | true | Truncate to repo root |
| `home_symbol` | `~` | Symbol for home |
| `fish_style_pwd_dir_length` | 0 | Fish-style truncation |

**Variables:** `path`, `read_only`

### line_break

Inserts a newline in the prompt. Essential for two-line prompts.

```toml
[line_break]
disabled = false
```

## Shell State Modules

### cmd_duration

Shows execution time of the last command.

```toml
[cmd_duration]
min_time = 2000
format = "took [$duration]($style) "
style = "yellow bold"
show_milliseconds = false
show_notifications = false
min_time_to_notify = 45000
```

**Variables:** `duration`

### jobs

Shows the number of background jobs.

```toml
[jobs]
symbol = "+"
number_threshold = 1
symbol_threshold = 1
format = "[$symbol$number]($style) "
style = "bold blue"
```

**Variables:** `symbol`, `number`

### status

Shows the exit code or signal name of the last command.

```toml
[status]
disabled = false
format = "[$symbol$status]($style) "
symbol = "x "
success_symbol = ""
not_executable_symbol = "!"
not_found_symbol = "?"
sigint_symbol = "INT"
signal_symbol = "SIG"
style = "bold red"
map_symbol = true
recognize_signal_code = true
pipestatus = false
```

**Variables:** `status`, `symbol`, `signal_name`, `maybe_int`

### shell

Displays the current shell name.

```toml
[shell]
disabled = false
format = "[$indicator]($style) "
bash_indicator = "bsh"
zsh_indicator = "zsh"
fish_indicator = "fsh"
powershell_indicator = "psh"
style = "white bold"
```

## Information Modules

### username

Shows the current username.

```toml
[username]
disabled = false
show_always = false
format = "[$user]($style) "
style_user = "yellow bold"
style_root = "red bold"
```

**Shows by default when:**

- User is root
- User differs from logged-in user
- Connected via SSH

### hostname

Shows the system hostname.

```toml
[hostname]
disabled = false
ssh_only = true
ssh_symbol = " "
format = "on [$ssh_symbol$hostname]($style) "
style = "bold dimmed green"
trim_at = "."
```

**Variables:** `hostname`, `ssh_symbol`

### localip

Shows the local IP address.

```toml
[localip]
disabled = false
ssh_only = true
format = "@[$localipv4]($style) "
style = "yellow bold"
```

### shlvl

Shows the shell nesting level.

```toml
[shlvl]
disabled = false
threshold = 2
format = "[$symbol$shlvl]($style) "
symbol = ">"
style = "bold yellow"
```

### sudo

Indicates if sudo credentials are cached.

```toml
[sudo]
disabled = false
format = "[as $symbol]($style) "
symbol = "#"
style = "bold blue"
allow_windows = false
```

## Module Quick Reference

### Enabled by Default

These modules display automatically when conditions are met:

- `character`
- `directory`
- `line_break`
- `cmd_duration`
- `git_branch`, `git_commit`, `git_state`, `git_status`
- Most language modules
- `package`

### Disabled by Default

These modules must be explicitly enabled:

```toml
[time]
disabled = false

[battery]
disabled = false

[memory_usage]
disabled = false

[hostname]
ssh_only = false  # Show always, not just SSH

[username]
show_always = true

[status]
disabled = false

[shell]
disabled = false

[sudo]
disabled = false

[shlvl]
disabled = false
```

## Detecting Modules

Check which modules are active:

```bash
starship explain
```

See module timings:

```bash
starship timings
```

## Module Configuration Pattern

Most modules follow this pattern:

```toml
[module_name]
# Whether to show the module
disabled = false

# How the module appears
format = "via [$symbol($version )]($style)"

# The symbol to display
symbol = " "

# Text styling
style = "bold green"

# Module-specific options
# (varies by module)
```

## Related Guides

For detailed module coverage:

- [Git Modules](git-modules.md) - Git integration deep dive
- [Language Modules](language-modules.md) - Programming languages
- [Cloud Modules](cloud-modules.md) - AWS, GCP, Kubernetes
- [System Modules](system-modules.md) - Time, battery, memory
- [Advanced](advanced.md) - Custom modules
