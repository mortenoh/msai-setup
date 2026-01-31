# Error Handling

Writing robust scripts that handle errors gracefully and fail safely.

## Exit Codes

Every command returns an exit code:

- `0` = Success
- `1-255` = Failure (meaning varies by command)

```bash
ls /etc/passwd
echo $?    # 0 (success)

ls /nonexistent
echo $?    # 1 or 2 (failure)
```

### Common Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Misuse of shell command |
| 126 | Command not executable |
| 127 | Command not found |
| 128 | Invalid exit argument |
| 128+n | Fatal signal n |
| 130 | Ctrl+C (128 + 2) |
| 255 | Exit status out of range |

### Setting Exit Code

```bash
#!/usr/bin/env bash

if [[ ! -f "$1" ]]; then
    echo "Error: File not found: $1" >&2
    exit 1
fi

# Process file...
exit 0
```

## The set Command

Configure shell behavior for error handling.

### set -e (Exit on Error)

Exit immediately if any command fails:

```bash
#!/usr/bin/env bash
set -e

cp source.txt dest.txt    # If this fails...
echo "This won't run"     # ...this never executes
```

!!! warning "set -e Caveats"
    Commands that "fail" intentionally can exit your script:
    ```bash
    set -e
    grep "pattern" file.txt   # Exits if no match!
    diff file1 file2          # Exits if files differ!
    ```

    Fix with explicit handling:
    ```bash
    grep "pattern" file.txt || true
    # or
    if grep -q "pattern" file.txt; then
        echo "Found"
    fi
    ```

### set -u (Undefined Variables)

Exit on undefined variable:

```bash
#!/usr/bin/env bash
set -u

echo "$undefined_var"    # Error: undefined_var: unbound variable
```

Use default values:

```bash
set -u
echo "${undefined_var:-default}"    # Uses "default"
echo "${undefined_var:=default}"    # Sets and uses "default"
```

### set -o pipefail

Without `pipefail`, only last command's exit code matters:

```bash
false | true
echo $?    # 0 (true succeeded)
```

With `pipefail`, fail if any pipe command fails:

```bash
set -o pipefail
false | true
echo $?    # 1 (false failed)
```

### Recommended Combination

```bash
#!/usr/bin/env bash
set -euo pipefail
```

Or on shebang:

```bash
#!/usr/bin/env -S bash -euo pipefail
```

## Error Messages

### Write to stderr

```bash
echo "Error: Something went wrong" >&2
```

### Error Function

```bash
error() {
    echo "Error: $*" >&2
}

die() {
    echo "Error: $*" >&2
    exit 1
}

# Usage
[[ -f "$config" ]] || die "Config file not found: $config"
```

### Include Context

```bash
die() {
    echo "Error: $*" >&2
    echo "  at ${BASH_SOURCE[1]}:${BASH_LINENO[0]} in ${FUNCNAME[1]}" >&2
    exit 1
}
```

## The trap Command

Execute commands when script receives signals or exits.

### Cleanup on Exit

```bash
#!/usr/bin/env bash

cleanup() {
    echo "Cleaning up..."
    rm -f "$temp_file"
}

trap cleanup EXIT

temp_file=$(mktemp)
echo "Working with $temp_file"
# Script continues...
# cleanup runs automatically when script exits
```

### Handle Signals

```bash
#!/usr/bin/env bash

handle_interrupt() {
    echo "Interrupted!"
    exit 130
}

trap handle_interrupt INT TERM

echo "Running... Press Ctrl+C to stop"
while true; do
    sleep 1
done
```

### Common Signals

| Signal | Number | Trigger |
|--------|--------|---------|
| EXIT | - | Script exit (always) |
| ERR | - | Command error (with set -e) |
| INT | 2 | Ctrl+C |
| TERM | 15 | kill command |
| HUP | 1 | Terminal closed |

### Trap on Error

```bash
#!/usr/bin/env bash
set -e

on_error() {
    echo "Error on line $1"
    exit 1
}

trap 'on_error $LINENO' ERR

false    # Triggers error trap
```

### Multiple Traps

```bash
cleanup() {
    rm -f "$temp_file"
}

on_exit() {
    cleanup
    echo "Script finished"
}

trap on_exit EXIT
trap 'echo "Interrupted"; cleanup; exit 130' INT TERM
```

## Checking Commands

### Validate External Commands

```bash
require_command() {
    command -v "$1" &>/dev/null || die "Required command not found: $1"
}

require_command docker
require_command git
require_command jq
```

### Check File Exists

```bash
[[ -f "$file" ]] || die "File not found: $file"
[[ -r "$file" ]] || die "File not readable: $file"
[[ -w "$dir" ]]  || die "Directory not writable: $dir"
```

### Validate Arguments

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: $0 <input-file> <output-file>"
    exit 1
}

[[ $# -eq 2 ]] || usage
[[ -f "$1" ]] || die "Input file not found: $1"
[[ -d "$(dirname "$2")" ]] || die "Output directory doesn't exist"

input="$1"
output="$2"
```

## Defensive Programming

### Check Return Values

```bash
# Instead of:
output=$(command)

# Check explicitly:
if ! output=$(command); then
    die "Command failed"
fi

# Or with ||:
output=$(command) || die "Command failed"
```

### Use Variables Safely

```bash
# Dangerous - if $dir is empty, deletes everything in /
rm -rf "$dir/"*

# Safe - check first
[[ -n "$dir" ]] && rm -rf "$dir/"*

# Or use parameter expansion
rm -rf "${dir:?'dir is empty'}"/*
```

### Safe Temporary Files

```bash
# Create secure temp file
temp_file=$(mktemp)
trap 'rm -f "$temp_file"' EXIT

# Create secure temp directory
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT
```

## Pipelines and Errors

### PIPESTATUS

Check individual pipeline command statuses:

```bash
cmd1 | cmd2 | cmd3
echo "${PIPESTATUS[@]}"    # Array of exit codes
```

### Handle Pipeline Failures

```bash
set -o pipefail

if ! output=$(cmd1 | cmd2); then
    echo "Pipeline failed: ${PIPESTATUS[*]}"
fi
```

## Retry Logic

```bash
retry() {
    local max_attempts=$1
    local delay=$2
    shift 2
    local cmd=("$@")

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if "${cmd[@]}"; then
            return 0
        fi
        echo "Attempt $attempt failed, retrying in ${delay}s..."
        ((attempt++))
        sleep "$delay"
    done

    echo "All $max_attempts attempts failed"
    return 1
}

# Usage
retry 3 5 curl -f https://example.com/api
```

## Complete Error Handling Template

```bash
#!/usr/bin/env bash
#
# script.sh - Description
#

set -euo pipefail

# Colors (if terminal)
if [[ -t 2 ]]; then
    RED='\033[31m'
    RESET='\033[0m'
else
    RED=''
    RESET=''
fi

# Logging
log()   { echo "[$(date '+%H:%M:%S')] $*"; }
error() { echo -e "${RED}Error: $*${RESET}" >&2; }
die()   { error "$@"; exit 1; }

# Cleanup
cleanup() {
    [[ -n "${temp_file:-}" ]] && rm -f "$temp_file"
}
trap cleanup EXIT

# Signal handling
handle_signal() {
    error "Received signal, cleaning up..."
    exit 130
}
trap handle_signal INT TERM

# Validate environment
require_command() {
    command -v "$1" &>/dev/null || die "Required command not found: $1"
}

# Main function
main() {
    # Validate arguments
    [[ $# -ge 1 ]] || die "Usage: $0 <argument>"

    # Validate input
    local input="$1"
    [[ -f "$input" ]] || die "File not found: $input"

    # Create temp file
    temp_file=$(mktemp)
    log "Created temp file: $temp_file"

    # Do work...
    log "Processing $input"

    log "Done"
}

main "$@"
```

## Try It

1. Test exit codes:
   ```bash
   ls /etc/passwd; echo "Exit: $?"
   ls /nonexistent; echo "Exit: $?"
   ```

2. Test set options:
   ```bash
   set -u
   echo "${undefined:-safe}"
   ```

3. Create trap:
   ```bash
   trap 'echo "Exiting..."' EXIT
   echo "Running"
   exit 0
   ```

4. Test pipefail:
   ```bash
   set -o pipefail
   false | true; echo "Exit: $?"
   set +o pipefail
   false | true; echo "Exit: $?"
   ```

## Summary

| Option | Purpose |
|--------|---------|
| `set -e` | Exit on error |
| `set -u` | Error on undefined variable |
| `set -o pipefail` | Fail on pipe error |
| `trap CMD EXIT` | Run CMD on exit |
| `trap CMD ERR` | Run CMD on error |
| `trap CMD INT` | Run CMD on Ctrl+C |

Best practices:

- Start with `set -euo pipefail`
- Always clean up temp files with `trap`
- Write errors to stderr: `>&2`
- Validate inputs and arguments
- Check command availability
- Use meaningful exit codes
- Provide context in error messages
