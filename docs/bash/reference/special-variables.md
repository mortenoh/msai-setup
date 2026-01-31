# Special Variables

Bash provides many special variables for script information, arguments, and process management.

## Positional Parameters

| Variable | Description |
|----------|-------------|
| `$0` | Script name or shell name |
| `$1` - `$9` | Positional arguments 1-9 |
| `${10}` | 10th argument (braces required for 10+) |
| `$#` | Number of positional arguments |
| `$@` | All arguments as separate words |
| `$*` | All arguments as a single word |

### $@ vs $*

```bash
#!/usr/bin/env bash
# Called with: ./script.sh "hello world" foo bar

echo "Using \$@:"
for arg in "$@"; do
    echo "  $arg"
done
# Output:
#   hello world
#   foo
#   bar

echo "Using \$*:"
for arg in "$*"; do
    echo "  $arg"
done
# Output:
#   hello world foo bar
```

**Rule**: Always use `"$@"` to preserve argument boundaries.

### shift Command

Move positional parameters:

```bash
echo "$1"    # first
shift
echo "$1"    # second (was $2)
shift 2
echo "$1"    # fourth (was $4)
```

## Exit Status

| Variable | Description |
|----------|-------------|
| `$?` | Exit status of last command |
| `${PIPESTATUS[@]}` | Exit statuses of pipeline commands |

```bash
ls /nonexistent
echo $?     # 1 (error)

ls /
echo $?     # 0 (success)

# Pipeline statuses
false | true | false
echo "${PIPESTATUS[@]}"    # 1 0 1
```

## Process IDs

| Variable | Description |
|----------|-------------|
| `$$` | Current shell's PID |
| `$!` | PID of last background command |
| `$BASHPID` | Actual current process PID (differs in subshells) |
| `$PPID` | Parent process PID |

```bash
echo "Shell PID: $$"
echo "Parent PID: $PPID"

sleep 10 &
echo "Background PID: $!"

(echo "Subshell BASHPID: $BASHPID")
echo "Main BASHPID: $BASHPID"
```

### $$ vs $BASHPID

```bash
echo "$$: $$, BASHPID: $BASHPID"
(echo "Subshell - $$: $$, BASHPID: $BASHPID")
# $$ stays the same, $BASHPID changes
```

## Miscellaneous

| Variable | Description |
|----------|-------------|
| `$_` | Last argument of previous command |
| `$-` | Current shell options |
| `$IFS` | Internal Field Separator |

```bash
echo "hello" "world"
echo $_              # world

echo $-              # himBH (varies)
# h - hash commands
# i - interactive
# m - monitor mode
# B - brace expansion
# H - history expansion
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `$HOME` | User's home directory |
| `$USER` | Current username |
| `$LOGNAME` | Login name |
| `$SHELL` | User's default shell |
| `$PATH` | Executable search path |
| `$PWD` | Current working directory |
| `$OLDPWD` | Previous working directory |
| `$HOSTNAME` | System hostname |
| `$HOSTTYPE` | Host architecture |
| `$OSTYPE` | Operating system type |
| `$MACHTYPE` | Machine type (arch-vendor-os) |
| `$TERM` | Terminal type |
| `$LANG` | Language/locale |
| `$TZ` | Timezone |
| `$EDITOR` | Default text editor |
| `$VISUAL` | Visual editor |
| `$PAGER` | Default pager |
| `$BROWSER` | Default web browser |

## Bash-Specific Variables

### Shell Information

| Variable | Description |
|----------|-------------|
| `$BASH` | Path to bash |
| `$BASH_VERSION` | Bash version string |
| `$BASH_VERSINFO` | Version array |
| `$BASH_SOURCE` | Source filename array |
| `$BASH_LINENO` | Line number array |
| `$FUNCNAME` | Function name array |
| `$SHELLOPTS` | Enabled shell options |
| `$BASHOPTS` | Enabled shopt options |

```bash
echo "$BASH_VERSION"    # 5.2.15(1)-release

echo "${BASH_VERSINFO[0]}"   # 5 (major)
echo "${BASH_VERSINFO[1]}"   # 2 (minor)
```

### History

| Variable | Description |
|----------|-------------|
| `$HISTSIZE` | History entries in memory |
| `$HISTFILESIZE` | History entries in file |
| `$HISTFILE` | History file path |
| `$HISTCONTROL` | History control (ignoredups, etc.) |
| `$HISTIGNORE` | Patterns to ignore |
| `$HISTTIMEFORMAT` | Timestamp format |

### Prompt

| Variable | Description |
|----------|-------------|
| `$PS1` | Primary prompt |
| `$PS2` | Continuation prompt |
| `$PS3` | Select prompt |
| `$PS4` | Debug trace prompt |
| `$PROMPT_COMMAND` | Command run before prompt |

### Random

| Variable | Description |
|----------|-------------|
| `$RANDOM` | Random number 0-32767 |
| `$SRANDOM` | Random 32-bit number (Bash 5.1+) |

```bash
echo $RANDOM              # 12345
echo $((RANDOM % 100))    # 0-99
```

### Time

| Variable | Description |
|----------|-------------|
| `$SECONDS` | Seconds since shell start |
| `$EPOCHSECONDS` | Unix timestamp (Bash 5.0+) |
| `$EPOCHREALTIME` | Unix timestamp with microseconds (Bash 5.0+) |

```bash
echo "Shell running for $SECONDS seconds"
echo "Current timestamp: $EPOCHSECONDS"
```

### Debugging

| Variable | Description |
|----------|-------------|
| `$LINENO` | Current line number |
| `$FUNCNAME` | Array of function names |
| `$BASH_SOURCE` | Array of source files |
| `$BASH_LINENO` | Array of line numbers |
| `$BASH_COMMAND` | Command being executed |

```bash
debug() {
    echo "Function: ${FUNCNAME[1]}"
    echo "Line: ${BASH_LINENO[0]}"
    echo "File: ${BASH_SOURCE[1]}"
}
```

### Completion

| Variable | Description |
|----------|-------------|
| `$COMP_WORDS` | Array of words in current line |
| `$COMP_CWORD` | Index of current word |
| `$COMP_LINE` | Current command line |
| `$COMP_POINT` | Cursor position |
| `$COMPREPLY` | Array of completions |

## Read-Only Variables

Some variables cannot be changed:

```bash
UID         # Real user ID
EUID        # Effective user ID
GROUPS      # Group memberships
HOSTNAME    # Hostname
HOSTTYPE    # Host type
OSTYPE      # OS type
MACHTYPE    # Machine type
```

## Default Values

Set defaults for potentially unset variables:

| Syntax | Meaning |
|--------|---------|
| `${var:-default}` | Use default if unset/empty |
| `${var:=default}` | Set and use default if unset/empty |
| `${var:+alternate}` | Use alternate if set |
| `${var:?message}` | Error with message if unset/empty |

```bash
# Use default
name="${1:-Anonymous}"

# Set default
: "${config:=/etc/default.conf}"

# Error if missing
: "${required_var:?Must be set}"
```

## Indirect References

Access variable by name:

```bash
name="value"
var="name"
echo "${!var}"           # value

# List variables matching prefix
echo "${!BASH@}"         # BASH BASHOPTS BASHPID BASH_...
```

## Arrays Special Variables

| Syntax | Description |
|--------|-------------|
| `${arr[@]}` | All elements |
| `${arr[*]}` | All elements as single string |
| `${!arr[@]}` | All indices |
| `${#arr[@]}` | Number of elements |
| `${#arr[0]}` | Length of first element |

## Try It

1. Positional parameters:
   ```bash
   show_args() {
       echo "Count: $#"
       echo "All: $@"
       echo "First: $1"
   }
   show_args one two three
   ```

2. Exit status:
   ```bash
   ls /etc/passwd
   echo "Exit: $?"
   ls /nonexistent
   echo "Exit: $?"
   ```

3. Process IDs:
   ```bash
   echo "Current: $$"
   sleep 1 &
   echo "Background: $!"
   ```

4. Shell info:
   ```bash
   echo "Version: $BASH_VERSION"
   echo "Running: $SECONDS seconds"
   echo "Random: $RANDOM"
   ```

## Summary

### Most Used

| Variable | Purpose |
|----------|---------|
| `$1-$9` | Script arguments |
| `$@` | All arguments (use quoted) |
| `$#` | Argument count |
| `$?` | Last exit code |
| `$$` | Current PID |
| `$!` | Last background PID |
| `$0` | Script name |
| `$_` | Last argument |

### Environment

| Variable | Purpose |
|----------|---------|
| `$HOME` | Home directory |
| `$PATH` | Executable path |
| `$PWD` | Current directory |
| `$USER` | Username |

### Debugging

| Variable | Purpose |
|----------|---------|
| `$LINENO` | Current line |
| `$FUNCNAME` | Function names |
| `$BASH_SOURCE` | Source files |
| `$BASH_COMMAND` | Current command |
