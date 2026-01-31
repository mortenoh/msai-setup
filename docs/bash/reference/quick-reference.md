# Quick Reference

A concise cheat sheet for bash commands, syntax, and patterns.

## Navigation

```bash
pwd                     # Print working directory
cd dir                  # Change directory
cd                      # Home directory
cd -                    # Previous directory
cd ..                   # Parent directory
pushd dir               # Push and change
popd                    # Pop and return
dirs                    # Show directory stack
```

## File Operations

```bash
ls -la                  # List all with details
cp src dst              # Copy file
cp -r src dst           # Copy directory
mv old new              # Move/rename
rm file                 # Remove file
rm -rf dir              # Remove directory (careful!)
mkdir dir               # Create directory
mkdir -p a/b/c          # Create nested directories
touch file              # Create/update timestamp
ln -s target link       # Create symlink
```

## File Viewing

```bash
cat file                # Display file
less file               # Page through file
head -n 10 file         # First 10 lines
tail -n 10 file         # Last 10 lines
tail -f file            # Follow file updates
wc -l file              # Count lines
file filename           # Identify file type
```

## Text Processing

```bash
grep pattern file       # Search for pattern
grep -r pattern dir     # Recursive search
grep -i pattern file    # Case insensitive
grep -v pattern file    # Invert match
sed 's/old/new/g' file  # Replace all
awk '{print $1}' file   # Print first column
sort file               # Sort lines
uniq                    # Remove duplicates
cut -d',' -f1 file      # Extract field
tr 'a-z' 'A-Z'          # Translate characters
```

## Variables

```bash
var="value"             # Assign
echo "$var"             # Use (always quote!)
export var="value"      # Export to environment
unset var               # Remove
readonly var="value"    # Constant
${var:-default}         # Default if unset
${var:=default}         # Set default if unset
${#var}                 # String length
${var:0:5}              # Substring
${var/old/new}          # Replace first
${var//old/new}         # Replace all
${var#pattern}          # Remove prefix (shortest)
${var##pattern}         # Remove prefix (longest)
${var%pattern}          # Remove suffix (shortest)
${var%%pattern}         # Remove suffix (longest)
```

## Special Variables

```bash
$0                      # Script name
$1, $2...               # Positional arguments
$#                      # Number of arguments
$@                      # All arguments (array)
$*                      # All arguments (string)
$?                      # Last exit code
$$                      # Current PID
$!                      # Last background PID
$_                      # Last argument
```

## Arrays

```bash
arr=(a b c)             # Create array
${arr[0]}               # First element
${arr[@]}               # All elements
${#arr[@]}              # Array length
${!arr[@]}              # All indices
arr+=(d)                # Append
unset arr[0]            # Remove element
```

## Conditionals

```bash
if [[ condition ]]; then
    commands
elif [[ condition ]]; then
    commands
else
    commands
fi

# Test operators
[[ -f file ]]           # Is file
[[ -d dir ]]            # Is directory
[[ -e path ]]           # Exists
[[ -r file ]]           # Readable
[[ -w file ]]           # Writable
[[ -x file ]]           # Executable
[[ -z "$str" ]]         # String empty
[[ -n "$str" ]]         # String not empty
[[ "$a" == "$b" ]]      # String equal
[[ "$a" != "$b" ]]      # String not equal
[[ "$a" == pattern ]]   # Pattern match
[[ "$a" =~ regex ]]     # Regex match
[[ $n -eq $m ]]         # Numbers equal
[[ $n -lt $m ]]         # Less than
[[ $n -gt $m ]]         # Greater than
[[ cond && cond ]]      # AND
[[ cond || cond ]]      # OR
[[ ! cond ]]            # NOT
```

## Arithmetic

```bash
((count++))             # Increment
((count--))             # Decrement
((result = a + b))      # Calculate
$((a + b))              # Arithmetic expansion
(( a > b ))             # Comparison (for if)
```

## Loops

```bash
# For loop
for item in list; do
    commands
done

for ((i=0; i<10; i++)); do
    commands
done

for file in *.txt; do
    commands
done

# While loop
while [[ condition ]]; do
    commands
done

while read -r line; do
    commands
done < file

# Loop control
break                   # Exit loop
continue                # Next iteration
```

## Functions

```bash
func_name() {
    local var="value"   # Local variable
    echo "$1"           # First argument
    return 0            # Return status
}

func_name arg1 arg2     # Call function
```

## Redirection

```bash
cmd > file              # stdout to file
cmd >> file             # Append stdout
cmd 2> file             # stderr to file
cmd &> file             # Both to file
cmd 2>&1                # stderr to stdout
cmd < file              # stdin from file
cmd1 | cmd2             # Pipe
cmd <<< "string"        # Here string
```

## Process Control

```bash
cmd &                   # Background
jobs                    # List jobs
fg %1                   # Foreground
bg %1                   # Background
Ctrl+Z                  # Suspend
Ctrl+C                  # Interrupt
kill PID                # Terminate
kill -9 PID             # Force kill
nohup cmd &             # Ignore hangup
disown                  # Remove from shell
wait                    # Wait for background
```

## Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    # cleanup code
}
trap cleanup EXIT

main() {
    # main code
}

main "$@"
```

## Error Handling

```bash
set -e                  # Exit on error
set -u                  # Error on undefined var
set -o pipefail         # Pipe fail propagation
trap 'cmd' EXIT         # Run on exit
trap 'cmd' ERR          # Run on error
trap 'cmd' INT          # Run on Ctrl+C
command || exit 1       # Exit if fails
command || true         # Ignore failure
```

## Useful Patterns

```bash
# Check command exists
command -v cmd &>/dev/null

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default argument
arg="${1:-default}"

# Read file into variable
content=$(<file)

# Process lines
while IFS= read -r line; do
    echo "$line"
done < file

# Safe temp file
tmpfile=$(mktemp)
trap 'rm -f $tmpfile' EXIT

# Check root
[[ $EUID -eq 0 ]] || exit 1

# Yes/No prompt
read -rp "Continue? [y/N] " answer
[[ "$answer" =~ ^[Yy] ]] || exit 1
```

## Common Commands

```bash
# Finding
find . -name "*.txt"
find . -type f -mtime -7
fd pattern              # Modern find

# Searching
grep -r pattern .
rg pattern              # Modern grep

# Archives
tar -czvf archive.tar.gz dir/
tar -xzvf archive.tar.gz
zip -r archive.zip dir/
unzip archive.zip

# Network
curl -s URL
curl -X POST -d 'data' URL
wget URL
ssh user@host
scp file user@host:path

# JSON
jq '.key' file.json
jq -r '.array[]' file.json

# Processes
ps aux | grep name
pgrep name
pkill name
top / htop / btop
```
