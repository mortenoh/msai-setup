# Environment Variables

Environment variables store configuration that programs can access. Understanding how they work is essential for proper shell configuration.

## What Are Environment Variables?

Environment variables are:

- Key-value pairs available to all processes
- Inherited by child processes
- Used to configure program behavior

```bash
# View an environment variable
echo $HOME
```

```
/Users/username
```

## Shell vs Environment Variables

There's an important distinction:

**Shell variables** - Local to current shell:

```bash
myvar="hello"           # Not exported
echo $myvar             # Works in this shell
bash -c 'echo $myvar'   # Empty - not inherited
```

**Environment variables** - Inherited by child processes:

```bash
export myvar="hello"    # Exported
bash -c 'echo $myvar'   # Works - inherited
```

## Setting Variables

### Basic Assignment

```bash
NAME="value"            # No spaces around =
NAME=value              # Quotes optional if no spaces
NAME="value with spaces"
NAME='literal $value'   # Single quotes: no expansion
```

### Export

Make variable available to child processes:

```bash
export PATH="/new/path:$PATH"
export EDITOR=vim

# Or combine
export NAME="value"
```

### One-Time Environment

Set for single command:

```bash
DEBUG=1 ./script.sh     # DEBUG only for this command
```

### Unset

Remove a variable:

```bash
unset VARNAME
```

## Common Environment Variables

### System Variables

| Variable | Purpose |
|----------|---------|
| `HOME` | User's home directory |
| `USER` | Current username |
| `SHELL` | User's default shell |
| `PWD` | Current working directory |
| `OLDPWD` | Previous directory |
| `HOSTNAME` | Machine hostname |
| `TERM` | Terminal type |
| `LANG` | Language/locale |
| `TZ` | Timezone |

### Shell Configuration

| Variable | Purpose |
|----------|---------|
| `PATH` | Executable search path |
| `PS1` | Primary prompt |
| `PS2` | Continuation prompt |
| `HISTSIZE` | History length |
| `HISTFILE` | History file location |
| `HISTCONTROL` | History behavior |

### Program Configuration

| Variable | Purpose |
|----------|---------|
| `EDITOR` | Default text editor |
| `VISUAL` | Visual editor |
| `PAGER` | Default pager (less, more) |
| `BROWSER` | Default web browser |
| `MANPATH` | Manual page search path |

## The PATH Variable

`PATH` tells the shell where to find executables:

```bash
echo $PATH
```

```
/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

Directories are separated by colons, searched left to right.

### Adding to PATH

```bash
# Prepend (searched first)
export PATH="$HOME/.local/bin:$PATH"

# Append (searched last)
export PATH="$PATH:/opt/myapp/bin"
```

### Best Practice

Check before adding to avoid duplicates:

```bash
# Add only if not already present
add_to_path() {
    [[ ":$PATH:" != *":$1:"* ]] && export PATH="$1:$PATH"
}

add_to_path "$HOME/.local/bin"
```

### Finding Commands

```bash
which python          # First match in PATH
type python           # What python resolves to
command -v python     # POSIX way to check
```

## Viewing Variables

### All Environment Variables

```bash
env                   # Environment variables only
printenv              # Same as env
export                # Exported variables with values
```

### All Variables (including shell)

```bash
set                   # All variables and functions
declare -p            # Variables with types
```

### Specific Variable

```bash
echo $VARNAME
printenv VARNAME
```

## Variable Scope

### Global (Exported)

Available everywhere after export:

```bash
export GLOBAL="accessible"
```

### Local to Script

Not exported, only in current shell:

```bash
LOCAL="only here"
```

### Local to Function

Using `local` keyword:

```bash
myfunc() {
    local myvar="function scope"
    echo $myvar
}
myfunc           # "function scope"
echo $myvar      # Empty
```

## Default Values

### Use Default if Unset

```bash
echo ${NAME:-default}      # Use 'default' if NAME unset
echo ${NAME:=default}      # Set and use 'default' if unset
echo ${NAME:+alternate}    # Use 'alternate' if NAME IS set
echo ${NAME:?error msg}    # Error if NAME unset
```

Examples:

```bash
unset NAME
echo ${NAME:-John}         # John

NAME="Alice"
echo ${NAME:-John}         # Alice

echo ${UNDEFINED:?Must be set}  # Error: Must be set
```

## Persistent Configuration

### For Interactive Shells

Add to `~/.bashrc`:

```bash
export EDITOR=vim
export PAGER=less
```

### For Login Sessions

Add to `~/.bash_profile` (sources `.bashrc`):

```bash
# ~/.bash_profile
source ~/.bashrc
```

### System-Wide

Add to `/etc/environment` or `/etc/profile.d/*.sh`:

```bash
# /etc/profile.d/custom.sh
export COMPANY_ENV="production"
```

## Common Patterns

### XDG Base Directories

Standard locations for application data:

```bash
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
```

### Language-Specific

```bash
# Python
export PYTHONPATH="$HOME/lib/python"
export VIRTUAL_ENV="$HOME/.venv"

# Node.js
export NODE_PATH="$HOME/.node_modules"
export NPM_CONFIG_PREFIX="$HOME/.npm-global"

# Go
export GOPATH="$HOME/go"
export GOBIN="$GOPATH/bin"

# Rust
export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"
```

### Development

```bash
export DEBUG=1
export LOG_LEVEL=debug
export API_URL="https://api.example.com"
```

## Special Variables

Variables set by bash:

| Variable | Meaning |
|----------|---------|
| `$?` | Last command exit status |
| `$$` | Current shell PID |
| `$!` | Last background job PID |
| `$0` | Script name |
| `$#` | Number of arguments |
| `$@` | All arguments (individually quoted) |
| `$*` | All arguments (as single word) |
| `$_` | Last argument of previous command |

See [Special Variables](../reference/special-variables.md) for complete reference.

## Security Considerations

### Never Export Secrets

Don't put sensitive data in shell config:

```bash
# Bad - visible in ps, env dumps
export API_KEY="secret123"

# Better - use files with restricted permissions
chmod 600 ~/.secrets
source ~/.secrets
```

### Sanitize User Input

When using variables in commands:

```bash
# Quote to prevent word splitting and globbing
rm "$file"              # Not: rm $file

# Validate before use
[[ "$input" =~ ^[a-z]+$ ]] || exit 1
```

## Debugging

### Trace Variable Expansion

```bash
set -x                  # Show commands as executed
echo $PATH
set +x
```

### Check If Set

```bash
[[ -v VARNAME ]] && echo "Set"
[[ -z "$VARNAME" ]] && echo "Empty or unset"
[[ -n "$VARNAME" ]] && echo "Not empty"
```

## Try It

1. Explore current environment:
   ```bash
   env | sort | head -20
   echo $PATH | tr ':' '\n'
   ```

2. Practice variable scope:
   ```bash
   myvar="local"
   echo $myvar
   bash -c 'echo $myvar'   # Empty

   export myvar
   bash -c 'echo $myvar'   # Works now
   ```

3. Use defaults:
   ```bash
   unset NAME
   echo "Hello, ${NAME:-World}"

   NAME="Alice"
   echo "Hello, ${NAME:-World}"
   ```

4. Modify PATH:
   ```bash
   echo $PATH
   export PATH="$HOME/test-bin:$PATH"
   echo $PATH
   ```

## Summary

| Action | Syntax |
|--------|--------|
| Set shell variable | `VAR=value` |
| Export to environment | `export VAR=value` |
| View variable | `echo $VAR` |
| View all environment | `env` or `printenv` |
| View all variables | `set` |
| Unset variable | `unset VAR` |
| Default if unset | `${VAR:-default}` |
| Set default if unset | `${VAR:=default}` |
| Prepend to PATH | `export PATH="$NEW:$PATH"` |
