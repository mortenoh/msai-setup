# Input/Output

Reading input and producing formatted output in bash scripts.

## Reading Input

### The read Command

```bash
read variable
```

User types input, stored in variable:

```bash
echo "What's your name?"
read name
echo "Hello, $name!"
```

### Prompt with -p

```bash
read -p "Enter your name: " name
echo "Hello, $name!"
```

### Silent Input with -s

For passwords:

```bash
read -sp "Password: " password
echo    # Newline after hidden input
echo "Password has ${#password} characters"
```

### Timeout with -t

```bash
if read -t 5 -p "Quick! Enter something: " answer; then
    echo "You entered: $answer"
else
    echo "Too slow!"
fi
```

### Default Value

```bash
read -p "Name [Anonymous]: " name
name="${name:-Anonymous}"
echo "Hello, $name"
```

### Limit Characters with -n

```bash
read -n 1 -p "Continue? (y/n) " answer
echo
[[ "$answer" == "y" ]] && echo "Continuing..."
```

### Read Array with -a

```bash
read -p "Enter words: " -a words
echo "First word: ${words[0]}"
echo "All words: ${words[@]}"
```

### Read with Delimiter -d

```bash
read -d ':' part < /etc/passwd
echo "First field: $part"
```

### Common Options

| Option | Purpose |
|--------|---------|
| `-p prompt` | Display prompt |
| `-s` | Silent (no echo) |
| `-t seconds` | Timeout |
| `-n count` | Read count characters |
| `-r` | Raw (don't interpret backslashes) |
| `-a array` | Read into array |
| `-d delim` | Use delimiter instead of newline |

## Reading Files

### Line by Line

```bash
while IFS= read -r line; do
    echo "Line: $line"
done < file.txt
```

Components:

- `IFS=` - Don't trim whitespace
- `-r` - Don't interpret backslashes
- `< file.txt` - Input from file

### Read Specific Fields

```bash
# /etc/passwd: user:x:uid:gid:desc:home:shell
while IFS=: read -r user _ uid gid _ home shell; do
    echo "$user (UID: $uid) -> $shell"
done < /etc/passwd
```

### Read from Command Output

```bash
while IFS= read -r file; do
    echo "Found: $file"
done < <(find . -name "*.txt")
```

### Read from Here Document

```bash
while IFS= read -r line; do
    echo "Config: $line"
done << 'EOF'
setting1=value1
setting2=value2
setting3=value3
EOF
```

## Basic Output

### echo

```bash
echo "Hello, World!"
echo -n "No newline"     # No trailing newline
echo -e "Tab:\tNewline:\nDone"  # Interpret escapes
```

Echo escapes (with `-e`):

| Escape | Meaning |
|--------|---------|
| `\n` | Newline |
| `\t` | Tab |
| `\r` | Carriage return |
| `\\` | Backslash |
| `\033[...m` | ANSI color codes |

### printf

More control over formatting:

```bash
printf "Hello, %s!\n" "World"
printf "Number: %d\n" 42
printf "Float: %.2f\n" 3.14159
printf "Hex: %x\n" 255
```

Format specifiers:

| Specifier | Type |
|-----------|------|
| `%s` | String |
| `%d` or `%i` | Integer |
| `%f` | Float |
| `%e` | Scientific notation |
| `%x` / `%X` | Hexadecimal |
| `%o` | Octal |
| `%%` | Literal % |

### printf Width and Alignment

```bash
printf "%-10s %5d\n" "Alice" 25
printf "%-10s %5d\n" "Bob" 30
printf "%-10s %5d\n" "Charlie" 35
```

```
Alice         25
Bob           30
Charlie       35
```

| Format | Meaning |
|--------|---------|
| `%10s` | Right-aligned, width 10 |
| `%-10s` | Left-aligned, width 10 |
| `%05d` | Zero-padded, width 5 |
| `%.2f` | 2 decimal places |
| `%10.2f` | Width 10, 2 decimals |

### printf to Variable

```bash
printf -v greeting "Hello, %s!" "World"
echo "$greeting"    # Hello, World!
```

## Here Documents

Multi-line input:

```bash
cat << EOF
Line 1
Line 2
Line 3
EOF
```

### Variable Expansion

```bash
name="Alice"
cat << EOF
Hello, $name!
Your home is $HOME
EOF
```

### No Expansion (Quoted Delimiter)

```bash
cat << 'EOF'
Variables like $HOME won't expand
Neither will $(commands)
EOF
```

### Indented (Tab Removal)

```bash
cat <<- EOF
	Indented with tabs
	Tabs are stripped
	EOF
```

!!! note "Tabs Only"
    The `<<-` syntax only strips **tabs**, not spaces.

### Here Document to Command

```bash
mysql -u root << EOF
USE mydb;
SELECT * FROM users;
EOF
```

### Here Document to Variable

```bash
read -r -d '' content << 'EOF'
Line 1
Line 2
Line 3
EOF
echo "$content"
```

## Here Strings

Single-line input:

```bash
grep "pattern" <<< "search in this string"

# Equivalent to:
echo "search in this string" | grep "pattern"
```

## Colored Output

### Basic ANSI Colors

```bash
# Colors
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
RESET='\033[0m'

echo -e "${RED}Error${RESET}: Something failed"
echo -e "${GREEN}Success${RESET}: All good"
printf "${YELLOW}Warning${RESET}: Be careful\n"
```

### tput for Portable Colors

```bash
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BOLD=$(tput bold)
RESET=$(tput sgr0)

echo "${RED}Error${RESET}"
echo "${BOLD}${GREEN}Success${RESET}"
```

### Color Functions

```bash
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
blue()   { printf '\033[34m%s\033[0m\n' "$*"; }

error()   { red "Error: $*" >&2; }
success() { green "Success: $*"; }
warn()    { yellow "Warning: $*"; }
info()    { blue "Info: $*"; }
```

### Check for Color Support

```bash
if [[ -t 1 ]] && [[ -n "$TERM" ]] && [[ "$TERM" != "dumb" ]]; then
    # Terminal supports colors
    RED='\033[31m'
    RESET='\033[0m'
else
    RED=''
    RESET=''
fi
```

## Progress Indicators

### Simple Counter

```bash
for i in {1..10}; do
    printf "\rProcessing: %d/10" "$i"
    sleep 0.5
done
echo
```

### Percentage

```bash
total=100
for ((i=1; i<=total; i++)); do
    percent=$((i * 100 / total))
    printf "\r[%-50s] %d%%" $(printf '#%.0s' $(seq 1 $((i/2)))) "$percent"
    sleep 0.05
done
echo
```

### Spinner

```bash
spinner() {
    local pid=$1
    local spin='-\|/'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r[%c] Working..." "${spin:i++%4:1}"
        sleep 0.1
    done
    printf "\rDone!          \n"
}

# Usage
sleep 3 &
spinner $!
```

## Output Formatting

### Tables

```bash
# Header
printf "%-15s %-10s %10s\n" "Name" "Status" "Count"
printf "%-15s %-10s %10s\n" "---------------" "----------" "----------"

# Data
printf "%-15s %-10s %10d\n" "Service A" "Running" 42
printf "%-15s %-10s %10d\n" "Service B" "Stopped" 0
printf "%-15s %-10s %10d\n" "Service C" "Running" 123
```

```
Name            Status          Count
--------------- ---------- ----------
Service A       Running            42
Service B       Stopped             0
Service C       Running           123
```

### Column Command

```bash
echo -e "Name\tAge\tCity
Alice\t25\tNYC
Bob\t30\tLA" | column -t
```

```
Name   Age  City
Alice  25   NYC
Bob    30   LA
```

## Logging Functions

```bash
#!/usr/bin/env bash

LOG_LEVEL="${LOG_LEVEL:-INFO}"

log() {
    local level="$1"
    shift
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    printf "[%s] %-5s %s\n" "$timestamp" "$level" "$*"
}

debug() { [[ "$LOG_LEVEL" == "DEBUG" ]] && log "DEBUG" "$@"; }
info()  { log "INFO" "$@"; }
warn()  { log "WARN" "$@" >&2; }
error() { log "ERROR" "$@" >&2; }
fatal() { log "FATAL" "$@" >&2; exit 1; }

# Usage
info "Starting script"
debug "Debug message (only if LOG_LEVEL=DEBUG)"
warn "This is a warning"
error "This is an error"
```

## Try It

1. Read input:
   ```bash
   read -p "Name: " name
   echo "Hello, $name!"
   ```

2. Formatted output:
   ```bash
   printf "%-10s %5d %8.2f\n" "Item" 42 3.14159
   ```

3. Read file:
   ```bash
   echo -e "one\ntwo\nthree" | while read -r line; do
       echo "Got: $line"
   done
   ```

4. Here document:
   ```bash
   name="World"
   cat << EOF
   Hello, $name!
   Today is $(date)
   EOF
   ```

5. Colored output:
   ```bash
   printf '\033[32mGreen\033[0m and \033[31mRed\033[0m\n'
   ```

## Summary

| Task | Command |
|------|---------|
| Read line | `read var` |
| Read with prompt | `read -p "Prompt: " var` |
| Silent input | `read -s var` |
| Read file | `while read -r line; do ... done < file` |
| Print string | `echo "text"` or `printf "text\n"` |
| Formatted print | `printf "%s %d\n" str num` |
| Here document | `cat << EOF ... EOF` |
| Here string | `cmd <<< "string"` |

Best practices:

- Use `read -r` to prevent backslash interpretation
- Use `IFS=` when reading to preserve whitespace
- Prefer `printf` over `echo` for portability
- Quote here document delimiter to prevent expansion
- Use functions for colored/logging output
