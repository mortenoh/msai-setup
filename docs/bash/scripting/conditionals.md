# Conditionals

Making decisions in scripts with `if`, `test`, and `case` statements.

## The if Statement

Basic syntax:

```bash
if condition; then
    commands
fi
```

With else:

```bash
if condition; then
    commands
else
    other_commands
fi
```

With elif:

```bash
if condition1; then
    commands1
elif condition2; then
    commands2
else
    default_commands
fi
```

## Test Commands

### The [[ ]] Syntax

The `[[ ]]` is bash's improved test command (preferred):

```bash
if [[ -f "$file" ]]; then
    echo "File exists"
fi
```

### The [ ] Syntax

The traditional test command (POSIX compatible):

```bash
if [ -f "$file" ]; then
    echo "File exists"
fi
```

### [[ ]] vs [ ]

| Feature | `[[ ]]` | `[ ]` |
|---------|---------|-------|
| Word splitting | No | Yes |
| Glob expansion | No | Yes |
| Pattern matching | `==`, `=~` | No |
| Logical operators | `&&`, `\|\|` | `-a`, `-o` |
| Quoting required | Usually no | Always |

**Use `[[ ]]`** in bash scripts. Use `[ ]` only for POSIX compatibility.

```bash
# [[ ]] - safer, no quoting issues
file="my file.txt"
[[ -f $file ]] && echo "exists"

# [ ] - requires careful quoting
[ -f "$file" ] && echo "exists"
```

## String Tests

| Test | True if... |
|------|------------|
| `-z "$str"` | String is empty |
| `-n "$str"` | String is not empty |
| `"$a" == "$b"` | Strings are equal |
| `"$a" != "$b"` | Strings are not equal |
| `"$a" < "$b"` | a sorts before b |
| `"$a" > "$b"` | a sorts after b |

```bash
name="Alice"

if [[ -z "$name" ]]; then
    echo "Name is empty"
elif [[ "$name" == "Alice" ]]; then
    echo "Hello, Alice!"
else
    echo "Hello, stranger"
fi
```

### Pattern Matching

```bash
# Glob patterns with ==
if [[ "$file" == *.txt ]]; then
    echo "Text file"
fi

# Regex with =~
if [[ "$email" =~ ^[a-z]+@[a-z]+\.[a-z]+$ ]]; then
    echo "Valid email format"
fi
```

Regex matches are stored in `BASH_REMATCH`:

```bash
if [[ "user@example.com" =~ ^([a-z]+)@(.+)$ ]]; then
    echo "User: ${BASH_REMATCH[1]}"    # user
    echo "Domain: ${BASH_REMATCH[2]}"  # example.com
fi
```

## Numeric Tests

| Test | True if... |
|------|------------|
| `$a -eq $b` | Equal |
| `$a -ne $b` | Not equal |
| `$a -lt $b` | Less than |
| `$a -le $b` | Less than or equal |
| `$a -gt $b` | Greater than |
| `$a -ge $b` | Greater than or equal |

```bash
count=5

if [[ $count -gt 10 ]]; then
    echo "Large"
elif [[ $count -gt 0 ]]; then
    echo "Small"
else
    echo "Zero or negative"
fi
```

### Arithmetic Conditionals

For numeric comparisons, `(( ))` is cleaner:

```bash
if (( count > 10 )); then
    echo "Large"
fi

if (( count >= 1 && count <= 10 )); then
    echo "In range"
fi
```

## File Tests

| Test | True if... |
|------|------------|
| `-e "$file"` | Exists |
| `-f "$file"` | Is a regular file |
| `-d "$file"` | Is a directory |
| `-L "$file"` | Is a symbolic link |
| `-r "$file"` | Is readable |
| `-w "$file"` | Is writable |
| `-x "$file"` | Is executable |
| `-s "$file"` | Has size > 0 |
| `-O "$file"` | Owned by current user |
| `-G "$file"` | Owned by current group |

```bash
if [[ -f "$config" ]]; then
    source "$config"
elif [[ -d "$config" ]]; then
    echo "Error: $config is a directory"
else
    echo "Error: $config not found"
fi
```

### File Comparisons

| Test | True if... |
|------|------------|
| `"$a" -nt "$b"` | a is newer than b |
| `"$a" -ot "$b"` | a is older than b |
| `"$a" -ef "$b"` | Same file (hard links) |

```bash
if [[ "$source" -nt "$target" ]]; then
    echo "Source is newer, rebuilding..."
fi
```

## Logical Operators

### Inside [[ ]]

```bash
# AND
if [[ -f "$file" && -r "$file" ]]; then
    echo "File exists and is readable"
fi

# OR
if [[ -z "$name" || "$name" == "default" ]]; then
    name="guest"
fi

# NOT
if [[ ! -f "$file" ]]; then
    echo "File does not exist"
fi
```

### Outside Conditionals

```bash
# AND - run second only if first succeeds
mkdir mydir && cd mydir

# OR - run second only if first fails
cd mydir || mkdir mydir

# Combined
cd mydir || { mkdir mydir && cd mydir; }
```

## Case Statements

Pattern matching for multiple conditions:

```bash
case "$variable" in
    pattern1)
        commands
        ;;
    pattern2)
        commands
        ;;
    *)
        default_commands
        ;;
esac
```

### Basic Example

```bash
case "$1" in
    start)
        echo "Starting..."
        ;;
    stop)
        echo "Stopping..."
        ;;
    restart)
        echo "Restarting..."
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
```

### Pattern Features

```bash
case "$input" in
    # Multiple patterns
    yes|y|Y)
        echo "Affirmative"
        ;;

    # Glob patterns
    *.txt)
        echo "Text file"
        ;;

    # Character class
    [0-9]*)
        echo "Starts with number"
        ;;

    # Range
    [a-z])
        echo "Single lowercase letter"
        ;;

    # Default
    *)
        echo "Unknown"
        ;;
esac
```

### Fall-through (Bash 4+)

```bash
case "$grade" in
    A)
        echo "Excellent"
        ;&  # Fall through
    B)
        echo "Good"
        ;;
    *)
        echo "Needs improvement"
        ;;
esac
```

## Conditional Expressions

### Ternary-like Syntax

```bash
# Using && and ||
[[ -f "$file" ]] && echo "exists" || echo "missing"

# Be careful - || also runs if && command fails
# Better:
if [[ -f "$file" ]]; then
    echo "exists"
else
    echo "missing"
fi
```

### Inline Variable Assignment

```bash
# Set default
: "${name:=default}"

# Conditional assignment
[[ -z "$name" ]] && name="default"
```

## Common Patterns

### Check Command Exists

```bash
if command -v docker &>/dev/null; then
    echo "Docker is installed"
else
    echo "Docker not found"
fi
```

### Check Running as Root

```bash
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi
```

### Validate Arguments

```bash
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

if [[ ! -f "$1" ]]; then
    echo "Error: File not found: $1"
    exit 1
fi
```

### Check Variable Set

```bash
# Check if set (even if empty)
if [[ -v varname ]]; then
    echo "Variable is set"
fi

# Check if set and not empty
if [[ -n "${varname:-}" ]]; then
    echo "Variable is set and not empty"
fi
```

### Interactive Check

```bash
if [[ -t 0 ]]; then
    echo "Running interactively"
else
    echo "Running from pipe or file"
fi
```

## Try It

1. String tests:
   ```bash
   name="Alice"
   [[ "$name" == "Alice" ]] && echo "Match"
   [[ "$name" == A* ]] && echo "Starts with A"
   [[ -z "$undefined" ]] && echo "Empty"
   ```

2. File tests:
   ```bash
   [[ -f /etc/passwd ]] && echo "File exists"
   [[ -d /tmp ]] && echo "Directory exists"
   [[ -x /bin/bash ]] && echo "Executable"
   ```

3. Numeric tests:
   ```bash
   count=5
   (( count > 3 )) && echo "Greater than 3"
   [[ $count -le 10 ]] && echo "At most 10"
   ```

4. Case statement:
   ```bash
   read -p "Enter yes or no: " answer
   case "$answer" in
       yes|y) echo "You said yes" ;;
       no|n) echo "You said no" ;;
       *) echo "Invalid answer" ;;
   esac
   ```

## Summary

| Test Type | Syntax |
|-----------|--------|
| String empty | `[[ -z "$str" ]]` |
| String not empty | `[[ -n "$str" ]]` |
| String equal | `[[ "$a" == "$b" ]]` |
| Pattern match | `[[ "$str" == pattern ]]` |
| Regex match | `[[ "$str" =~ regex ]]` |
| Number equal | `[[ $a -eq $b ]]` |
| Number less | `[[ $a -lt $b ]]` |
| Arithmetic | `(( a > b ))` |
| File exists | `[[ -e "$file" ]]` |
| Is file | `[[ -f "$file" ]]` |
| Is directory | `[[ -d "$file" ]]` |
| Is readable | `[[ -r "$file" ]]` |
| AND | `[[ cond1 && cond2 ]]` |
| OR | `[[ cond1 \|\| cond2 ]]` |
| NOT | `[[ ! condition ]]` |

Best practices:

- Use `[[ ]]` instead of `[ ]`
- Quote variables in `[ ]`, optional in `[[ ]]`
- Use `(( ))` for arithmetic comparisons
- Use `case` for multiple pattern matches
