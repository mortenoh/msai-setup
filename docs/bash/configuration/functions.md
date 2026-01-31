# Shell Functions

Functions are reusable blocks of code. They're more powerful than aliases, supporting arguments, conditionals, and multiple commands.

## Basic Syntax

```bash
# Standard syntax
function_name() {
    commands
}

# Alternative syntax (with 'function' keyword)
function function_name {
    commands
}
```

Both work the same. The first is more portable.

## Creating Functions

### Simple Function

```bash
greet() {
    echo "Hello, World!"
}

greet    # Call the function
```

```
Hello, World!
```

### Function with Arguments

Arguments are accessed via `$1`, `$2`, etc.:

```bash
greet() {
    echo "Hello, $1!"
}

greet Alice
```

```
Hello, Alice!
```

### Multiple Arguments

```bash
greet() {
    echo "Hello, $1 and $2!"
}

greet Alice Bob
```

```
Hello, Alice and Bob!
```

### All Arguments

```bash
show_args() {
    echo "Number of args: $#"
    echo "All args: $@"
    for arg in "$@"; do
        echo "  - $arg"
    done
}

show_args one two three
```

```
Number of args: 3
All args: one two three
  - one
  - two
  - three
```

## Return Values

Functions can return exit codes (0-255):

```bash
is_empty() {
    [[ -z "$1" ]] && return 0 || return 1
}

if is_empty ""; then
    echo "Empty!"
fi
```

For returning data, use echo and command substitution:

```bash
add() {
    echo $(( $1 + $2 ))
}

result=$(add 5 3)
echo "Sum: $result"
```

```
Sum: 8
```

## Local Variables

Use `local` to prevent variable leakage:

```bash
# Without local - modifies global scope
bad_function() {
    name="leaked"
}

# With local - scoped to function
good_function() {
    local name="contained"
    echo $name
}

name="original"
bad_function
echo $name      # "leaked" - modified!

name="original"
good_function   # prints "contained"
echo $name      # "original" - unchanged
```

Always use `local` for function variables.

## Common Function Patterns

### Create and Enter Directory

```bash
mkcd() {
    mkdir -p "$1" && cd "$1"
}

mkcd new-project
pwd    # /path/to/new-project
```

### Extract Archives

```bash
extract() {
    if [[ ! -f "$1" ]]; then
        echo "Error: '$1' is not a file"
        return 1
    fi

    case "$1" in
        *.tar.bz2)  tar xjf "$1" ;;
        *.tar.gz)   tar xzf "$1" ;;
        *.tar.xz)   tar xJf "$1" ;;
        *.bz2)      bunzip2 "$1" ;;
        *.gz)       gunzip "$1" ;;
        *.tar)      tar xf "$1" ;;
        *.tbz2)     tar xjf "$1" ;;
        *.tgz)      tar xzf "$1" ;;
        *.zip)      unzip "$1" ;;
        *.Z)        uncompress "$1" ;;
        *.7z)       7z x "$1" ;;
        *.rar)      unrar x "$1" ;;
        *)          echo "Unknown format: '$1'" && return 1 ;;
    esac
}
```

### Backup File

```bash
backup() {
    local file="$1"
    local backup="${file}.$(date +%Y%m%d_%H%M%S).bak"
    cp "$file" "$backup" && echo "Backed up to: $backup"
}

backup important.conf
```

### Find and Edit

```bash
fe() {
    local file
    file=$(find . -type f -name "*$1*" | head -1)
    if [[ -n "$file" ]]; then
        ${EDITOR:-vim} "$file"
    else
        echo "No file matching: $1"
    fi
}

fe config    # Opens first file containing "config"
```

### Quick HTTP Server

```bash
serve() {
    local port="${1:-8000}"
    echo "Serving on http://localhost:$port"
    python3 -m http.server "$port"
}

serve 3000
```

### Git Helpers

```bash
# Commit with message
gcm() {
    git commit -m "$*"
}

# Add all and commit
gac() {
    git add -A && git commit -m "$*"
}

# Push to current branch
gpo() {
    git push origin "$(git branch --show-current)"
}

# Create and switch to branch
gcb() {
    git checkout -b "$1"
}
```

### Docker Helpers

```bash
# Run bash in container
dbash() {
    docker exec -it "$1" /bin/bash
}

# Docker compose shorthand
dcu() { docker compose up -d "$@"; }
dcd() { docker compose down "$@"; }
dcl() { docker compose logs -f "$@"; }

# Clean up docker
docker-clean() {
    docker system prune -af
    docker volume prune -f
}
```

### Navigation Helpers

```bash
# Up multiple directories
up() {
    local levels="${1:-1}"
    local path=""
    for ((i=0; i<levels; i++)); do
        path="../$path"
    done
    cd "$path" || return
}

up 3    # cd ../../..
```

### Search Functions

```bash
# Find files by name
ff() {
    find . -type f -iname "*$1*" 2>/dev/null
}

# Find directories by name
fd() {
    find . -type d -iname "*$1*" 2>/dev/null
}

# Grep recursively
rgrep() {
    grep -rn "$1" . --include="$2"
}

rgrep "TODO" "*.py"
```

## Functions with Options

Parse options using `getopts`:

```bash
greet() {
    local name="World"
    local excited=false

    while getopts "n:e" opt; do
        case $opt in
            n) name="$OPTARG" ;;
            e) excited=true ;;
            *) echo "Usage: greet [-n name] [-e]"; return 1 ;;
        esac
    done

    if $excited; then
        echo "Hello, $name!"
    else
        echo "Hello, $name."
    fi
}

greet                  # Hello, World.
greet -n Alice         # Hello, Alice.
greet -n Alice -e      # Hello, Alice!
```

## Function Documentation

Add usage information:

```bash
deploy() {
    # Deploy application to environment
    # Usage: deploy <environment> [--force]
    # Examples:
    #   deploy staging
    #   deploy production --force

    if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" ]]; then
        grep '^    #' "${BASH_SOURCE[0]}" | grep -A20 "^    # Deploy" | sed 's/^    # //'
        return 0
    fi

    local env="$1"
    local force="${2:-}"

    echo "Deploying to $env..."
}
```

## Organizing Functions

### Separate File

Create `~/.bash_functions`:

```bash
# ~/.bash_functions

# ──────────────────────────────────────────────
# File Operations
# ──────────────────────────────────────────────

mkcd() {
    mkdir -p "$1" && cd "$1"
}

backup() {
    cp "$1" "$1.$(date +%Y%m%d).bak"
}

# ──────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────

serve() {
    python3 -m http.server "${1:-8000}"
}
```

Source from `.bashrc`:

```bash
[[ -f ~/.bash_functions ]] && source ~/.bash_functions
```

### Multiple Files

```bash
# Source all function files
for file in ~/.bash_functions.d/*.sh; do
    [[ -r "$file" ]] && source "$file"
done
```

## Listing and Removing Functions

### List All Functions

```bash
declare -F           # Function names only
declare -f           # Functions with definitions
declare -f funcname  # Specific function
```

### Check If Function Exists

```bash
type funcname
declare -f funcname &>/dev/null && echo "Exists"
```

### Remove Function

```bash
unset -f funcname
```

## Functions vs Scripts

| Feature | Function | Script |
|---------|----------|--------|
| Loading | Sourced into shell | Runs as subprocess |
| Speed | Faster (already loaded) | Slower (new process) |
| Scope | Can modify current shell | Isolated environment |
| Size | Best for small tasks | Better for large programs |
| Reuse | Current shell only | Callable from anywhere |

Use functions for:

- Commands you run frequently
- Operations that modify current shell (cd, export)
- Quick utilities

Use scripts for:

- Complex programs
- Things that need to be callable from other scripts
- Portable tools

## Try It

1. Create a simple function:
   ```bash
   greet() {
       echo "Hello, ${1:-World}!"
   }
   greet
   greet "Alice"
   ```

2. Create mkcd:
   ```bash
   mkcd() {
       mkdir -p "$1" && cd "$1"
   }
   mkcd ~/test-functions
   pwd
   cd ..
   rm -r ~/test-functions
   ```

3. Function with return value:
   ```bash
   add() {
       echo $(( $1 + $2 ))
   }
   result=$(add 10 5)
   echo "Result: $result"
   ```

4. List and inspect:
   ```bash
   declare -F
   declare -f greet
   type greet
   ```

## Summary

| Concept | Syntax |
|---------|--------|
| Define function | `name() { commands; }` |
| Call function | `name arg1 arg2` |
| Arguments | `$1, $2, ..., $@, $#` |
| Local variable | `local var=value` |
| Return status | `return 0` (success) |
| Return data | `echo "result"` + command substitution |
| List functions | `declare -F` |
| Remove function | `unset -f name` |

Best practices:

- Always use `local` for variables
- Quote arguments: `"$1"`, `"$@"`
- Provide meaningful return codes
- Add usage help for complex functions
- Organize in separate file(s)
