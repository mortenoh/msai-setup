# Advanced Configuration

This guide covers advanced Starship features including custom commands, conditional logic, performance optimization, and complex configurations.

## Custom Commands

The `custom` module allows you to display output from any command.

### Basic Custom Command

```toml
[custom.mycommand]
command = "echo hello"
when = true
format = "[$output]($style) "
style = "bold green"
```

### Custom Command Options

| Option | Description |
|--------|-------------|
| `command` | Command to execute |
| `when` | Condition to show module |
| `shell` | Shell to use |
| `format` | Output format |
| `style` | Text style |
| `description` | Module description |
| `detect_files` | Show when files exist |
| `detect_folders` | Show when folders exist |
| `detect_extensions` | Show when extensions exist |
| `symbol` | Symbol to display |
| `disabled` | Disable the module |

### Examples

**Show npm scripts count:**

```toml
[custom.npm_scripts]
command = "jq '.scripts | keys | length' package.json 2>/dev/null"
when = "test -f package.json"
format = "[$symbol$output scripts]($style) "
symbol = " "
style = "bold yellow"
```

**Show todo count:**

```toml
[custom.todos]
command = "grep -r 'TODO' --include='*.{js,ts,py,rs}' . 2>/dev/null | wc -l | tr -d ' '"
when = "test -d .git"
format = "[$symbol$output TODOs]($style) "
symbol = " "
style = "bold yellow"
```

**Show Docker container count:**

```toml
[custom.docker_running]
command = "docker ps -q 2>/dev/null | wc -l | tr -d ' '"
when = "command -v docker"
format = "[$symbol$output containers]($style) "
symbol = " "
style = "bold blue"
```

**Show current WiFi network:**

```toml
[custom.wifi]
command = "networksetup -getairportnetwork en0 2>/dev/null | cut -d: -f2 | xargs"
when = "test $(uname) = Darwin"
format = "[$symbol$output]($style) "
symbol = " "
style = "bold cyan"
os = "macos"
```

**Show git stash count:**

```toml
[custom.git_stash]
command = "git stash list 2>/dev/null | wc -l | tr -d ' '"
when = "git rev-parse --git-dir 2>/dev/null"
format = "[$symbol$output stashed]($style) "
symbol = " "
style = "bold yellow"
```

### Shell Selection

Specify which shell runs the command:

```toml
[custom.mycommand]
command = "my-command"
shell = ["bash", "--noprofile", "--norc"]
# or
shell = ["zsh", "-c"]
# or just use default
shell = "sh"
```

### Detection-Based Triggers

Show custom commands only in specific contexts:

```toml
[custom.python_project]
command = "python --version | cut -d' ' -f2"
detect_files = ["pyproject.toml", "setup.py", "requirements.txt"]
format = "[$symbol$output]($style) "
symbol = " "
style = "yellow"

[custom.node_project]
command = "node --version"
detect_files = ["package.json"]
format = "[$symbol$output]($style) "
symbol = " "
style = "green"
```

## Conditional Display

### Using `when` Condition

The `when` option accepts a shell command that determines if the module shows:

```toml
[custom.production_warning]
command = "echo PRODUCTION"
when = "test \"$AWS_PROFILE\" = \"production\""
format = "[$output]($style) "
style = "bold red blink"
```

### Environment-Based Display

```toml
[custom.env_indicator]
command = "echo $ENVIRONMENT"
when = "test -n \"$ENVIRONMENT\""
format = "[env:$output]($style) "
style = "bold yellow"
```

### Directory-Based Display

```toml
[custom.work_indicator]
command = "echo WORK"
when = "pwd | grep -q '/work/'"
format = "[$output]($style) "
style = "bold blue"
```

## Multi-Line and Complex Prompts

### Three-Line Prompt

```toml
format = """
$directory$git_branch$git_status
$nodejs$python$rust$golang$docker_context$kubernetes
$time$cmd_duration$line_break$character"""

[line_break]
disabled = false
```

### Segment-Based Layout

```toml
format = """
[](#9A348E)\
$os\
$username\
[](bg:#DA627D fg:#9A348E)\
$directory\
[](fg:#DA627D bg:#FCA17D)\
$git_branch\
$git_status\
[](fg:#FCA17D bg:#86BBD8)\
$nodejs\
$rust\
$golang\
[](fg:#86BBD8 bg:#06969A)\
$docker_context\
[](fg:#06969A bg:#33658A)\
$time\
[ ](fg:#33658A)\
$character"""
```

### Right Prompt

```toml
format = "$all"
right_format = """
$cmd_duration\
$memory_usage\
$time"""

[cmd_duration]
format = "[$duration]($style)"
style = "yellow"

[memory_usage]
disabled = false
format = "[$symbol$ram]($style) "
threshold = 70
style = "red"

[time]
disabled = false
format = "[$time]($style)"
time_format = "%H:%M"
style = "dimmed"
```

## Performance Optimization

### Identify Slow Modules

```bash
starship timings
```

Sample output:
```
 aws           -  1ms  -
 directory     -  2ms  -   ~/projects/app
 git_branch    -  3ms  -    main
 git_status    - 45ms  -   [!?]
```

### Disable Slow Modules

```toml
[git_status]
disabled = true  # Disable if too slow

[package]
disabled = true  # Often slow, rarely needed
```

### Optimize Git Status

```toml
[git_status]
# Skip submodule status checks
ignore_submodules = true
```

### Set Command Timeout

```toml
# Global timeout (milliseconds)
command_timeout = 500

# Commands exceeding this are skipped
```

### Reduce Detection Overhead

```toml
[nodejs]
# Only detect on specific files
detect_extensions = []
detect_files = ["package.json"]
detect_folders = []
```

### Cache Directory

Set a fast cache location:

```bash
export STARSHIP_CACHE=/tmp/starship
```

## Environment-Specific Configs

### Different Config Per Machine

```bash
# In .bashrc/.zshrc
case "$(hostname)" in
  workstation*)
    export STARSHIP_CONFIG=~/.config/starship/work.toml
    ;;
  server*)
    export STARSHIP_CONFIG=~/.config/starship/server.toml
    ;;
  *)
    export STARSHIP_CONFIG=~/.config/starship.toml
    ;;
esac

eval "$(starship init bash)"
```

### SSH Detection

Different prompt when connected via SSH:

```toml
[hostname]
ssh_only = true
ssh_symbol = " "
format = "[$ssh_symbol$hostname]($style) "
style = "bold yellow"

[username]
show_always = false  # Only show on SSH or as root
format = "[$user]($style)@"
```

### Container Detection

Show when running inside a container:

```toml
[container]
disabled = false
format = "[$symbol]($style) "
symbol = " "
style = "bold red"
```

## Debugging

### Explain Active Modules

```bash
starship explain
```

Shows which modules are active and why.

### Print Full Configuration

```bash
starship print-config
```

Shows merged configuration (defaults + your customizations).

### Bug Report

```bash
starship bug-report
```

Generates debug information for troubleshooting.

### Verbose Mode

Temporarily see more information:

```bash
STARSHIP_LOG=trace starship prompt
```

## Advanced Format Strings

### Nested Conditionals

```toml
[git_branch]
# Only show remote if different from local
format = "[$symbol$branch(:$remote_branch)]($style) "
# $remote_branch only appears if set and different
```

### Variable Formatting

```toml
[directory]
# Pad/truncate variables
format = "[$path](bold blue)${read_only:>5}"
```

### Escaping Special Characters

```toml
[character]
# Escape $ with backslash
success_symbol = "[\\$](bold green)"

# Use double quotes for special chars
error_symbol = "[\\$](bold red)"
```

## Integration Examples

### tmux Integration

Show Starship info in tmux status:

```bash
# In .tmux.conf
set -g status-right '#(starship prompt --status=$? --cmd-duration=0)'
```

### Screen Integration

```bash
# In .screenrc
hardstatus string '%{= kG}[ %{G}%H %{g}][%= %{= kw}%?%-Lw%?%{r}(%{W}%n*%f%t%?(%u)%?%{r})%{w}%?%+Lw%?%?%= %{g}][%{B} %d/%m %{W}%c %{g}]'
```

### VS Code Terminal

VS Code may need specific configuration:

```json
// settings.json
{
  "terminal.integrated.fontFamily": "FiraCode Nerd Font",
  "terminal.integrated.fontSize": 14
}
```

## Complete Advanced Configuration

```toml
# Advanced developer configuration
command_timeout = 1000
add_newline = true

# Custom format with right prompt
format = """
$username\
$hostname\
$directory\
$git_branch\
$git_commit\
$git_state\
$git_status\
$docker_context\
$package\
$nodejs\
$python\
$rust\
$golang\
$terraform\
$aws\
$kubernetes\
$line_break\
$jobs\
$status\
$character"""

right_format = """
$cmd_duration\
$time"""

# Character with vi mode support
[character]
success_symbol = "[->](bold green)"
error_symbol = "[->](bold red)"
vimcmd_symbol = "[<-](bold green)"

# Directory
[directory]
truncation_length = 4
truncate_to_repo = true
style = "bold cyan"

# Git
[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"
truncation_length = 30

[git_commit]
format = "[($hash$tag)]($style) "
only_detached = false
tag_disabled = false

[git_status]
format = '([$all_status$ahead_behind]($style) )'
style = "bold red"
ignore_submodules = true

# Languages
[nodejs]
format = "[$symbol($version )]($style)"
symbol = " "

[python]
format = '[${symbol}${version}(\($virtualenv\) )]($style)'
symbol = " "

[rust]
format = "[$symbol($version )]($style)"
symbol = " "

# Cloud
[aws]
format = '[$symbol($profile)(\($region\))]($style) '
symbol = " "

[aws.region_aliases]
us-east-1 = "ue1"
us-west-2 = "uw2"

[kubernetes]
disabled = false
format = '[$symbol$context(:$namespace)]($style) '
symbol = " "

# System
[jobs]
threshold = 1
format = "[$symbol$number]($style) "
symbol = "bg:"

[status]
disabled = false
format = "[$symbol$status]($style) "
symbol = "x:"

[cmd_duration]
min_time = 2000
format = "[$duration]($style) "
style = "yellow"

[time]
disabled = false
format = "[$time]($style)"
time_format = "%H:%M"
style = "dimmed"

# Custom modules
[custom.git_stash]
command = "git stash list 2>/dev/null | wc -l | tr -d ' '"
when = "git rev-parse --git-dir 2>/dev/null"
format = "[stash:$output]($style) "
style = "bold yellow"

[custom.docker_running]
command = "docker ps -q 2>/dev/null | wc -l | tr -d ' '"
when = "command -v docker >/dev/null"
format = "[containers:$output]($style) "
symbol = " "
style = "bold blue"

# Disabled modules
[package]
disabled = true
```
