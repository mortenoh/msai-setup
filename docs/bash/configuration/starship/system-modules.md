# System Modules

System modules display information about your environment, machine state, and shell session. These modules help you track time, system resources, and environmental context.

## Time Module

Shows the current time.

### Configuration

```toml
[time]
disabled = true  # Disabled by default
format = "at [$time]($style) "
style = "bold yellow"
use_12hr = false
time_format = "%T"  # Hour:Minute:Second
utc_time_offset = "local"
time_range = "-"
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `disabled` | true | Must be enabled |
| `format` | `at [$time]($style) ` | Display format |
| `use_12hr` | false | Use 12-hour format |
| `time_format` | `%T` | Time format string |
| `utc_time_offset` | `local` | UTC offset |
| `time_range` | `-` | When to show (always) |

### Time Format Strings

Uses [chrono strftime](https://docs.rs/chrono/latest/chrono/format/strftime/index.html):

| Format | Output | Description |
|--------|--------|-------------|
| `%T` | `09:30:45` | Hour:Min:Sec (24h) |
| `%H:%M` | `09:30` | Hour:Min (24h) |
| `%I:%M %p` | `09:30 AM` | 12-hour with AM/PM |
| `%R` | `09:30` | Same as %H:%M |
| `%r` | `09:30:45 AM` | 12-hour with seconds |

### Examples

**Enable with 24-hour format:**

```toml
[time]
disabled = false
format = "[$time]($style) "
time_format = "%H:%M"
style = "dimmed white"
```

Output: `14:30 `

**12-hour format:**

```toml
[time]
disabled = false
use_12hr = true
format = "[$time]($style) "
```

Output: `2:30 PM `

**Show in right prompt:**

```toml
right_format = "$time"

[time]
disabled = false
format = "[$time]($style)"
time_format = "%H:%M:%S"
style = "dimmed"
```

**Only show during certain hours:**

```toml
[time]
disabled = false
time_range = "09:00:00-17:00:00"  # Work hours only
```

## Command Duration

Shows how long the last command took to execute.

### Configuration

```toml
[cmd_duration]
min_time = 2000  # Milliseconds
format = "took [$duration]($style) "
style = "bold yellow"
show_milliseconds = false
disabled = false
show_notifications = false
min_time_to_notify = 45000
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `min_time` | 2000 | Minimum time to show (ms) |
| `show_milliseconds` | false | Show ms precision |
| `show_notifications` | false | Desktop notifications |
| `min_time_to_notify` | 45000 | Min time for notification |

### Examples

**Show for commands over 5 seconds:**

```toml
[cmd_duration]
min_time = 5000
format = "[took $duration]($style) "
style = "yellow"
```

**With milliseconds:**

```toml
[cmd_duration]
min_time = 500
show_milliseconds = true
format = "[$duration]($style) "
```

Output: `523ms ` or `1m 23s 456ms `

**Desktop notifications for long commands:**

```toml
[cmd_duration]
min_time = 2000
show_notifications = true
min_time_to_notify = 30000  # 30 seconds
```

## Battery Module

Shows battery level and charging status.

### Configuration

```toml
[battery]
disabled = true  # Disabled by default
format = "[$symbol$percentage]($style) "
full_symbol = " "
charging_symbol = " "
discharging_symbol = " "
unknown_symbol = " "
empty_symbol = " "
```

### Display Thresholds

Configure when to show battery and styling at different levels:

```toml
[[battery.display]]
threshold = 10
style = "bold red"

[[battery.display]]
threshold = 30
style = "bold yellow"

[[battery.display]]
threshold = 100
style = "bold green"
```

### Examples

**Enable with thresholds:**

```toml
[battery]
disabled = false
format = "[$symbol$percentage]($style) "

[[battery.display]]
threshold = 15
style = "bold red"
discharging_symbol = " "

[[battery.display]]
threshold = 50
style = "bold yellow"

[[battery.display]]
threshold = 100
style = "green"
```

**Show only when low:**

```toml
[battery]
disabled = false

[[battery.display]]
threshold = 20
style = "bold red"
# Only shows when battery is below 20%
```

## Memory Usage

Shows current memory consumption.

### Configuration

```toml
[memory_usage]
disabled = true  # Disabled by default
threshold = 75
format = "via $symbol[$ram( | $swap)]($style) "
symbol = " "
style = "bold dimmed white"
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `threshold` | 75 | Show above this % |
| `symbol` | ` ` | Memory symbol |
| `format` | Shows RAM and swap | Display format |

### Variables

| Variable | Description |
|----------|-------------|
| `ram` | Current RAM usage |
| `ram_pct` | RAM percentage |
| `swap` | Current swap usage |
| `swap_pct` | Swap percentage |

### Examples

**Enable memory display:**

```toml
[memory_usage]
disabled = false
threshold = 50
format = "[$symbol$ram_pct]($style) "
symbol = "mem "
style = "bold dimmed"
```

Output when above threshold: `mem 67% `

**Show RAM and swap:**

```toml
[memory_usage]
disabled = false
threshold = 0  # Always show
format = "[$ram | $swap]($style) "
```

Output: `3.2G/16G | 0B/8G `

## Hostname

Shows the system hostname.

### Configuration

```toml
[hostname]
disabled = false
ssh_only = true
ssh_symbol = " "
trim_at = "."
format = "[$ssh_symbol$hostname]($style) "
style = "bold dimmed green"
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `ssh_only` | true | Only show via SSH |
| `ssh_symbol` | ` ` | Symbol for SSH |
| `trim_at` | `.` | Trim hostname at char |

### Examples

**Always show hostname:**

```toml
[hostname]
ssh_only = false
format = "on [$hostname]($style) "
style = "bold green"
```

**Show full hostname:**

```toml
[hostname]
trim_at = ""
format = "[$hostname]($style) "
```

**SSH indicator:**

```toml
[hostname]
ssh_only = true
format = "[$ssh_symbol$hostname]($style) "
ssh_symbol = "[SSH] "
style = "bold yellow"
```

## Username

Shows the current username.

### Configuration

```toml
[username]
disabled = false
show_always = false
format = "[$user]($style) "
style_user = "yellow bold"
style_root = "red bold"
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `show_always` | false | Always show username |
| `style_user` | `yellow bold` | Style for normal user |
| `style_root` | `red bold` | Style for root |

**Shows by default when:**

- User is root
- Current user differs from logged-in user
- Connected via SSH

### Examples

**Always show username:**

```toml
[username]
show_always = true
format = "[$user]($style)@"
```

**Highlight root:**

```toml
[username]
format = "[$user]($style) "
style_root = "bold red blink"
```

## Local IP

Shows the machine's local IP address.

### Configuration

```toml
[localip]
disabled = true
ssh_only = true
format = "[$localipv4]($style) "
style = "bold yellow"
```

### Examples

**Enable local IP:**

```toml
[localip]
disabled = false
ssh_only = false
format = "ip:[$localipv4]($style) "
```

## OS Info

Shows the operating system.

### Configuration

```toml
[os]
disabled = true
format = "[$symbol]($style)"
style = "bold white"
```

### OS Symbols

```toml
[os.symbols]
Alpine = " "
Amazon = " "
Android = " "
Arch = " "
CentOS = " "
Debian = " "
Fedora = " "
FreeBSD = " "
Linux = " "
Macos = " "
Manjaro = " "
Mint = " "
NixOS = " "
openSUSE = " "
Pop = " "
Raspbian = " "
Redhat = " "
RedHatEnterprise = " "
Ubuntu = " "
Windows = " "
```

### Examples

**Enable OS display:**

```toml
[os]
disabled = false
format = "[$symbol]($style) "

[os.symbols]
Macos = "mac "
Ubuntu = "ubu "
```

## Environment Variables

Display custom environment variables.

### Configuration

```toml
[env_var.VARIABLE_NAME]
disabled = false
variable = "VARIABLE_NAME"
default = "unknown"
format = "with [$env_value]($style) "
style = "bold yellow"
description = ""
```

### Examples

**Show custom variable:**

```toml
[env_var.ENVIRONMENT]
format = "[$env_value]($style) "
style = "bold green"
default = "local"
```

**Multiple environment variables:**

```toml
[env_var.AWS_PROFILE]
format = "aws:[$env_value]($style) "
style = "yellow"

[env_var.NODE_ENV]
format = "node:[$env_value]($style) "
style = "green"
```

**Show shell level:**

```toml
[env_var.SHLVL]
format = "shell:[$env_value]($style) "
style = "bold cyan"
```

## Shell Level (shlvl)

Shows nested shell depth.

### Configuration

```toml
[shlvl]
disabled = true
threshold = 2
format = "[$symbol$shlvl]($style) "
symbol = ">"
repeat = false
style = "bold yellow"
```

### Examples

**Enable shell level:**

```toml
[shlvl]
disabled = false
threshold = 2
format = "[$symbol$shlvl]($style) "
symbol = "shell:"
```

**Visual depth indicator:**

```toml
[shlvl]
disabled = false
threshold = 1
repeat = true
symbol = ">"
format = "[$symbol]($style) "
```

Output at level 3: `>>> `

## Jobs

Shows background job count.

### Configuration

```toml
[jobs]
disabled = false
threshold = 1
symbol_threshold = 1
number_threshold = 2
format = "[$symbol$number]($style) "
symbol = "+"
style = "bold blue"
```

### Examples

**Show job count:**

```toml
[jobs]
threshold = 1
format = "[jobs:$number]($style) "
```

**Symbol only:**

```toml
[jobs]
format = "[$symbol]($style) "
symbol = "bg "
```

## Complete System Configuration

A comprehensive system-focused configuration:

```toml
format = """
$username\
$hostname\
$localip\
$directory\
$git_branch\
$git_status\
$line_break\
$jobs\
$battery\
$character"""

right_format = """
$cmd_duration\
$memory_usage\
$time"""

# Username (show on SSH or when root)
[username]
format = "[$user]($style)@"
style_user = "yellow"
style_root = "bold red"

# Hostname
[hostname]
ssh_only = true
format = "[$hostname]($style) "
style = "bold green"

# Local IP (SSH only)
[localip]
disabled = false
ssh_only = true
format = "([$localipv4]($style)) "
style = "dimmed"

# Jobs
[jobs]
threshold = 1
format = "[bg:$number]($style) "
style = "bold blue"

# Battery (show when low)
[battery]
disabled = false

[[battery.display]]
threshold = 20
style = "bold red"

[[battery.display]]
threshold = 50
style = "yellow"

# Command duration (right side)
[cmd_duration]
min_time = 2000
format = "[$duration]($style) "
style = "yellow"

# Memory (right side, show when high)
[memory_usage]
disabled = false
threshold = 70
format = "[$ram_pct]($style) "
style = "dimmed red"

# Time (right side)
[time]
disabled = false
format = "[$time]($style)"
time_format = "%H:%M"
style = "dimmed white"
```

**Example output:**

```
user@server (192.168.1.10) ~/project main [!]
bg:2 ->                                   1m 23s 75% 14:30
```
