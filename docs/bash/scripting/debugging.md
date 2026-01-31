# Debugging

Techniques for finding and fixing problems in bash scripts.

## Trace Execution

### set -x

Print each command before execution:

```bash
#!/usr/bin/env bash
set -x

name="Alice"
echo "Hello, $name"
```

Output:

```
+ name=Alice
+ echo 'Hello, Alice'
Hello, Alice
```

### Toggle Tracing

```bash
# Enable
set -x

# Commands are traced here...

# Disable
set +x
```

### Trace Specific Section

```bash
#!/usr/bin/env bash

echo "Normal output"

set -x
# This section is traced
important_function
set +x

echo "Back to normal"
```

### Run Script with Tracing

```bash
bash -x script.sh
```

## Customizing Trace Output

### PS4 Variable

Customize the trace prefix (default is `+ `):

```bash
PS4='+ ${BASH_SOURCE}:${LINENO}: '
set -x
echo "Hello"
```

Output:

```
+ ./script.sh:3: echo Hello
Hello
```

### Rich Debugging

```bash
export PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
set -x
```

Shows file, line, and function name.

### Timestamp in Trace

```bash
PS4='+ $(date "+%H:%M:%S") ${BASH_SOURCE}:${LINENO}: '
```

## Verbose Mode

### set -v

Print lines as they're read (before expansion):

```bash
#!/usr/bin/env bash
set -v

name="Alice"
echo "Hello, $name"
```

Output:

```
name="Alice"
echo "Hello, $name"
Hello, Alice
```

Difference from `-x`: `-v` shows raw lines, `-x` shows after expansion.

## Print Debugging

### Strategic Echo

```bash
#!/usr/bin/env bash

debug() {
    [[ "${DEBUG:-}" == "1" ]] && echo "DEBUG: $*" >&2
}

debug "Starting script"
debug "Variable: $some_var"
```

Run with: `DEBUG=1 ./script.sh`

### Variable Inspection

```bash
debug_var() {
    local name="$1"
    local value="${!name}"
    echo "DEBUG: $name = '$value'" >&2
}

my_var="hello world"
debug_var my_var
# DEBUG: my_var = 'hello world'
```

### Function Entry/Exit

```bash
trace_func() {
    echo "ENTER: ${FUNCNAME[1]} ($*)" >&2
}

my_function() {
    trace_func "$@"
    # function body
    echo "EXIT: ${FUNCNAME[0]}" >&2
}
```

## ShellCheck

Static analysis tool for shell scripts.

### Installation

```bash
# macOS
brew install shellcheck

# Debian/Ubuntu
apt install shellcheck
```

### Usage

```bash
shellcheck script.sh
```

### Example Output

```bash
$ cat script.sh
#!/bin/bash
echo $1

$ shellcheck script.sh
In script.sh line 2:
echo $1
     ^-- SC2086: Double quote to prevent globbing and word splitting.
```

### ShellCheck Directives

Disable specific warnings:

```bash
# shellcheck disable=SC2086
echo $unquoted_var

# Or for the whole script
# shellcheck disable=SC2086,SC2034
```

### Editor Integration

ShellCheck integrates with:

- VS Code (shellcheck extension)
- Vim/Neovim (via ALE or coc)
- Sublime Text
- Most IDEs

## Interactive Debugging

### Breakpoints with read

```bash
#!/usr/bin/env bash

echo "Before the issue"
read -p "Press Enter to continue..."
problematic_function
read -p "After function, press Enter..."
echo "After the issue"
```

### Step Through with DEBUG Trap

```bash
#!/usr/bin/env bash

step() {
    echo ">> $BASH_COMMAND"
    read -p "Press Enter for next command..."
}

trap step DEBUG

# Your script commands here
echo "Line 1"
echo "Line 2"
echo "Line 3"
```

### Conditional Breakpoint

```bash
#!/usr/bin/env bash

trap '[[ $count -eq 5 ]] && read -p "Count is 5, continue?"' DEBUG

for ((count=1; count<=10; count++)); do
    echo "Count: $count"
done
```

## Debugging Functions

### Caller Information

```bash
debug_caller() {
    local frame=0
    while caller $frame; do
        ((frame++))
    done
}

function_a() {
    function_b
}

function_b() {
    debug_caller
}

function_a
```

Output:

```
4 function_b ./script.sh
8 function_a ./script.sh
11 main ./script.sh
```

### Stack Trace

```bash
stack_trace() {
    local i
    echo "Stack trace:" >&2
    for ((i=1; i<${#FUNCNAME[@]}; i++)); do
        echo "  at ${FUNCNAME[$i]}() in ${BASH_SOURCE[$i]}:${BASH_LINENO[$((i-1))]}" >&2
    done
}

die() {
    echo "Error: $*" >&2
    stack_trace
    exit 1
}
```

## Debugging Techniques

### Binary Search

Find where script breaks:

```bash
echo "Checkpoint 1"
# half of code
echo "Checkpoint 2"
# other half
echo "Checkpoint 3"
```

Keep narrowing down until you find the problematic line.

### Minimal Reproduction

Extract the failing code into a minimal script:

```bash
#!/usr/bin/env bash
set -x

# Only the relevant variables
input="problematic value"

# Only the failing command
process "$input"
```

### Compare Working vs Broken

```bash
# Works
bash -x working.sh 2>&1 | tee working.log

# Broken
bash -x broken.sh 2>&1 | tee broken.log

# Compare
diff working.log broken.log
```

## Common Issues

### Unexpected Token

```bash
$ ./script.sh
./script.sh: line 5: syntax error near unexpected token `('
```

Often caused by:

- Windows line endings (`\r\n` instead of `\n`)
- Missing shebang
- Incompatible bash version

Fix Windows line endings:

```bash
sed -i 's/\r$//' script.sh
# or
dos2unix script.sh
```

### Command Not Found

```bash
$ ./script.sh
./script.sh: line 10: mycommand: command not found
```

Check:

- Is command installed?
- Is command in PATH?
- Is there a typo?

```bash
type mycommand
which mycommand
echo $PATH
```

### Unbound Variable

```bash
$ ./script.sh
./script.sh: line 5: var: unbound variable
```

With `set -u`, undefined variables cause errors:

```bash
# Use default
${var:-default}

# Or check first
if [[ -v var ]]; then
    echo "$var"
fi
```

### Bad Substitution

```bash
$ ./script.sh
./script.sh: line 3: ${var,,}: bad substitution
```

Often bash version issue (feature requires newer bash):

```bash
bash --version
# Might need bash 4.0+ for certain features
```

### Arithmetic Errors

```bash
# Division by zero
echo $((10 / 0))
# bash: 10 / 0: division by 0

# Octal interpretation
num="08"
echo $((num + 1))
# bash: 08: value too great for base
# Fix: use 10# prefix
echo $((10#$num + 1))
```

## Debugging Subshells

Subshells can hide errors:

```bash
# This runs in subshell, won't exit main script with set -e
output=$(
    failing_command
    echo "This still runs"
)

# Better - capture exit status
if ! output=$(failing_command); then
    echo "Command failed"
fi
```

## Logging for Debugging

```bash
#!/usr/bin/env bash

LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_FILE="${LOG_FILE:-/dev/stderr}"

declare -A LOG_LEVELS=([DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3)

log() {
    local level="$1"
    shift
    if [[ ${LOG_LEVELS[$level]} -ge ${LOG_LEVELS[$LOG_LEVEL]} ]]; then
        printf "[%s] %-5s %s\n" "$(date '+%H:%M:%S')" "$level" "$*" >> "$LOG_FILE"
    fi
}

# Usage
log DEBUG "Detailed debugging info"
log INFO "Normal information"
log WARN "Warning message"
log ERROR "Error message"
```

Run with: `LOG_LEVEL=DEBUG ./script.sh`

## Try It

1. Enable tracing:
   ```bash
   set -x
   echo "Hello, World"
   name="Test"
   echo "Name: $name"
   set +x
   ```

2. Custom PS4:
   ```bash
   PS4='+ Line $LINENO: '
   set -x
   echo "One"
   echo "Two"
   set +x
   ```

3. Test ShellCheck:
   ```bash
   echo 'echo $1' > /tmp/test.sh
   shellcheck /tmp/test.sh
   ```

4. Debug function:
   ```bash
   debug() {
       [[ "${DEBUG:-}" == "1" ]] && echo "DEBUG: $*" >&2
   }
   DEBUG=1 bash -c 'source /dev/stdin; debug "test"' <<< "$(declare -f debug)"
   ```

## Summary

| Technique | Purpose |
|-----------|---------|
| `set -x` | Trace execution |
| `set -v` | Verbose (show raw lines) |
| `PS4='...'` | Customize trace prefix |
| `ShellCheck` | Static analysis |
| `DEBUG trap` | Step through |
| `caller` | Stack information |

Best practices:

- Always use ShellCheck
- Add debug logging to complex scripts
- Use `set -x` for quick debugging
- Create minimal reproductions
- Check bash version for feature compatibility
- Use editor integration for real-time checking
