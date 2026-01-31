# Scripting Basics

The fundamentals of writing bash scripts: structure, variables, and quoting.

## Script Structure

A bash script is a text file containing commands:

```bash
#!/usr/bin/env bash

# This is a comment
echo "Hello, World!"
```

### The Shebang

The first line tells the system how to run the script:

```bash
#!/usr/bin/env bash    # Recommended - finds bash in PATH
#!/bin/bash            # Direct path (less portable)
#!/bin/sh              # POSIX shell (more portable, fewer features)
```

Using `env` is more portable across systems where bash might be in different locations.

### Making Scripts Executable

```bash
chmod +x script.sh
./script.sh
```

Or run with bash directly:

```bash
bash script.sh
```

### File Extensions

The `.sh` extension is conventional but not required. What matters is:

1. The shebang line
2. The execute permission

## Variables

### Basic Assignment

```bash
name="Alice"           # No spaces around =
count=42
path=/home/user
```

### Using Variables

```bash
echo $name             # Simple expansion
echo ${name}           # Explicit braces
echo "Hello, $name"    # Inside double quotes
echo "Files: ${count}" # Braces prevent ambiguity
```

### Variable Names

Valid names:

- Start with letter or underscore
- Contain letters, numbers, underscores
- Case-sensitive

```bash
valid_name="yes"
_private="yes"
NAME2="yes"
2invalid="no"          # Error: starts with number
invalid-name="no"      # Error: contains hyphen
```

### Readonly Variables

```bash
readonly PI=3.14159
PI=3                   # Error: readonly variable
```

### Unset Variables

```bash
unset name
echo $name             # Empty
```

## Quoting

Quoting is one of the most important concepts in bash scripting.

### Double Quotes

Variables expand, special characters mostly literal:

```bash
name="World"
echo "Hello, $name"    # Hello, World
echo "Path is $HOME"   # Path is /home/user
echo "Tab:\there"      # Tab:    here
```

### Single Quotes

Everything is literal - no expansion:

```bash
name="World"
echo 'Hello, $name'    # Hello, $name
echo '$HOME'           # $HOME
```

### No Quotes

Word splitting and glob expansion occur:

```bash
files="file1 file2"
rm $files              # Removes file1 AND file2 (word split)
rm "$files"            # Error: no file named "file1 file2"
```

### When to Quote

**Always quote variables** unless you specifically want word splitting:

```bash
# Good
echo "$name"
path="$HOME/documents"
[[ -f "$file" ]]

# Bad - can break on spaces or special chars
echo $name
path=$HOME/documents
[[ -f $file ]]
```

### Escaping

Backslash escapes special characters:

```bash
echo "She said \"Hello\""    # She said "Hello"
echo 'It'\''s working'       # It's working (end quote, escape, new quote)
echo "Cost: \$50"            # Cost: $50
```

### $'...' Quoting

Interprets escape sequences:

```bash
echo $'Line1\nLine2'         # Two lines
echo $'Tab\there'            # Tab character
```

## Special Variables

| Variable | Meaning |
|----------|---------|
| `$0` | Script name |
| `$1` to `$9` | Positional arguments |
| `${10}` | 10th argument (braces required) |
| `$#` | Number of arguments |
| `$@` | All arguments (preserves quoting) |
| `$*` | All arguments (as single word) |
| `$?` | Exit status of last command |
| `$$` | Current shell PID |
| `$!` | PID of last background job |

### Script Arguments

```bash
#!/usr/bin/env bash

echo "Script: $0"
echo "First arg: $1"
echo "Second arg: $2"
echo "All args: $@"
echo "Count: $#"
```

```bash
./script.sh hello world
```

```
Script: ./script.sh
First arg: hello
Second arg: world
All args: hello world
Count: 2
```

### Difference Between $@ and $*

```bash
#!/usr/bin/env bash

echo "Using \$@:"
for arg in "$@"; do
    echo "  '$arg'"
done

echo "Using \$*:"
for arg in "$*"; do
    echo "  '$arg'"
done
```

```bash
./script.sh "hello world" foo
```

```
Using $@:
  'hello world'
  'foo'
Using $*:
  'hello world foo'
```

Always use `"$@"` when passing arguments to other commands.

## Parameter Expansion

### Default Values

```bash
echo ${name:-default}        # Use 'default' if unset or empty
echo ${name:=default}        # Set to 'default' if unset or empty
echo ${name:+alternate}      # Use 'alternate' if set
echo ${name:?error message}  # Error if unset or empty
```

### String Length

```bash
str="hello"
echo ${#str}                 # 5
```

### Substring

```bash
str="hello world"
echo ${str:0:5}              # hello (from 0, length 5)
echo ${str:6}                # world (from 6 to end)
echo ${str: -5}              # world (last 5, note space)
```

### Substitution

```bash
file="document.txt"
echo ${file%.txt}            # document (remove suffix)
echo ${file#doc}             # ument.txt (remove prefix)
echo ${file%.txt}.md         # document.md (change extension)

path="/home/user/file.txt"
echo ${path##*/}             # file.txt (basename)
echo ${path%/*}              # /home/user (dirname)
```

## Command Substitution

Capture command output in a variable:

```bash
# Modern syntax (preferred)
date=$(date +%Y-%m-%d)
files=$(ls *.txt)

# Old syntax (avoid)
date=`date +%Y-%m-%d`
```

Nest command substitutions:

```bash
dirname=$(dirname $(readlink -f "$0"))
```

## Arithmetic

Basic arithmetic (covered in detail in [Arithmetic](arithmetic.md)):

```bash
count=$((count + 1))
total=$((5 * 10))
result=$((10 / 3))           # Integer division: 3
```

## Comments

```bash
# This is a single-line comment

echo "Hello" # Inline comment

: '
This is a
multi-line comment
(actually a null command with a string argument)
'
```

## Exit Status

Every command returns an exit status:

- `0` = success
- `1-255` = failure

```bash
#!/usr/bin/env bash

if command_that_might_fail; then
    echo "Success"
else
    echo "Failed with status: $?"
fi
```

Exit your script with a status:

```bash
exit 0           # Success
exit 1           # General error
exit 2           # Misuse of command
```

## Debugging Shebang

Add flags to shebang for debugging:

```bash
#!/usr/bin/env -S bash -x    # Trace execution
#!/usr/bin/env -S bash -e    # Exit on error
#!/usr/bin/env -S bash -u    # Error on undefined variables
```

Or use `set` in the script:

```bash
#!/usr/bin/env bash
set -x           # Enable tracing
set -e           # Exit on error
set -u           # Error on undefined variables
set -o pipefail  # Pipe failure propagation
```

Combine them:

```bash
set -euo pipefail
```

## Complete Example

```bash
#!/usr/bin/env bash
#
# greet.sh - Greet users with a personalized message
#

set -euo pipefail

# Default values
NAME="${1:-World}"
GREETING="${2:-Hello}"

# Main logic
main() {
    local message="${GREETING}, ${NAME}!"
    echo "$message"

    if [[ "$NAME" == "World" ]]; then
        echo "(Tip: Pass a name as the first argument)"
    fi

    return 0
}

main
```

```bash
chmod +x greet.sh
./greet.sh
./greet.sh Alice
./greet.sh Alice "Good morning"
```

```
Hello, World!
(Tip: Pass a name as the first argument)
Hello, Alice!
Good morning, Alice!
```

## Try It

1. Create a simple script:
   ```bash
   cat > /tmp/hello.sh << 'EOF'
   #!/usr/bin/env bash
   echo "Hello, ${1:-World}!"
   EOF
   chmod +x /tmp/hello.sh
   /tmp/hello.sh
   /tmp/hello.sh Alice
   ```

2. Practice quoting:
   ```bash
   name="Hello World"
   echo $name      # Two arguments to echo
   echo "$name"    # One argument
   echo '$name'    # Literal
   ```

3. Test parameter expansion:
   ```bash
   file="document.backup.txt"
   echo ${file%.txt}
   echo ${file%%.*}
   echo ${file#*.}
   echo ${file##*.}
   ```

## Summary

| Concept | Syntax |
|---------|--------|
| Shebang | `#!/usr/bin/env bash` |
| Variable assignment | `name="value"` |
| Variable usage | `"$name"` or `"${name}"` |
| Command substitution | `$(command)` |
| Arithmetic | `$((expression))` |
| Default value | `${var:-default}` |
| Script arguments | `$1`, `$2`, `$@`, `$#` |
| Exit status | `$?`, `exit N` |

Key rules:

- No spaces around `=` in assignments
- Always quote variables: `"$var"`
- Use `"$@"` for passing arguments
- Start scripts with `set -euo pipefail`
