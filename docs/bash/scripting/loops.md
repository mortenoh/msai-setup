# Loops

Iteration patterns in bash: `for`, `while`, `until`, and loop control.

## For Loops

### Basic Syntax

```bash
for variable in list; do
    commands
done
```

### Iterating Over Words

```bash
for name in Alice Bob Charlie; do
    echo "Hello, $name"
done
```

```
Hello, Alice
Hello, Bob
Hello, Charlie
```

### Iterating Over Files

```bash
for file in *.txt; do
    echo "Processing: $file"
done
```

!!! warning "Empty Glob"
    If no files match, the glob itself becomes the value:
    ```bash
    for file in *.xyz; do
        echo "$file"    # Prints "*.xyz" if no match
    done
    ```
    Fix with `nullglob`:
    ```bash
    shopt -s nullglob
    for file in *.xyz; do
        echo "$file"    # Loop doesn't run if no match
    done
    ```

### Iterating Over Array

```bash
fruits=("apple" "banana" "cherry")
for fruit in "${fruits[@]}"; do
    echo "$fruit"
done
```

### Iterating Over Command Output

```bash
for user in $(cat /etc/passwd | cut -d: -f1); do
    echo "User: $user"
done
```

Better - avoid word splitting issues:

```bash
while IFS=: read -r user _; do
    echo "User: $user"
done < /etc/passwd
```

### C-Style For Loop

```bash
for ((i=0; i<5; i++)); do
    echo "Count: $i"
done
```

```
Count: 0
Count: 1
Count: 2
Count: 3
Count: 4
```

### Range with Brace Expansion

```bash
for i in {1..5}; do
    echo "Number: $i"
done
```

With step:

```bash
for i in {0..10..2}; do
    echo "Even: $i"
done
```

```
Even: 0
Even: 2
Even: 4
Even: 6
Even: 8
Even: 10
```

### Range with seq

```bash
for i in $(seq 1 5); do
    echo "Number: $i"
done

# With step
for i in $(seq 0 2 10); do
    echo "Even: $i"
done
```

## While Loops

### Basic Syntax

```bash
while condition; do
    commands
done
```

### Counter Loop

```bash
count=0
while [[ $count -lt 5 ]]; do
    echo "Count: $count"
    ((count++))
done
```

### Infinite Loop

```bash
while true; do
    echo "Press Ctrl+C to stop"
    sleep 1
done
```

Or:

```bash
while :; do
    # commands
done
```

### Reading Lines from File

```bash
while IFS= read -r line; do
    echo "Line: $line"
done < file.txt
```

Components explained:

- `IFS=` - Preserve leading/trailing whitespace
- `-r` - Don't interpret backslashes
- `line` - Variable to store each line

### Reading with Process Substitution

```bash
while IFS= read -r line; do
    echo "$line"
done < <(command)
```

### Reading Multiple Fields

```bash
# /etc/passwd format: user:x:uid:gid:desc:home:shell
while IFS=: read -r user _ uid gid desc home shell; do
    echo "$user has UID $uid"
done < /etc/passwd
```

### Reading from Pipe

```bash
# Warning: runs in subshell, variables don't persist
echo -e "a\nb\nc" | while read -r line; do
    echo "Got: $line"
done
```

To preserve variables, use process substitution or here string.

## Until Loops

Run until condition is true (opposite of while):

```bash
count=0
until [[ $count -ge 5 ]]; do
    echo "Count: $count"
    ((count++))
done
```

### Waiting for Condition

```bash
# Wait for file to appear
until [[ -f /tmp/ready ]]; do
    echo "Waiting..."
    sleep 1
done
echo "File found!"
```

## Loop Control

### break

Exit the loop immediately:

```bash
for i in {1..10}; do
    if [[ $i -eq 5 ]]; then
        break
    fi
    echo "$i"
done
```

```
1
2
3
4
```

### continue

Skip to next iteration:

```bash
for i in {1..5}; do
    if [[ $i -eq 3 ]]; then
        continue
    fi
    echo "$i"
done
```

```
1
2
4
5
```

### Nested Loop Control

Break/continue outer loops with a number:

```bash
for i in {1..3}; do
    for j in {1..3}; do
        if [[ $j -eq 2 ]]; then
            break 2    # Break both loops
        fi
        echo "$i,$j"
    done
done
```

```
1,1
```

## Common Patterns

### Process All Arguments

```bash
for arg in "$@"; do
    echo "Argument: $arg"
done
```

### Find and Process Files

```bash
# Using find with -exec
find . -name "*.txt" -exec echo "Found: {}" \;

# Using while read (safer for filenames with spaces)
find . -name "*.txt" -print0 | while IFS= read -r -d '' file; do
    echo "Found: $file"
done
```

### Retry Until Success

```bash
max_attempts=5
attempt=1

while [[ $attempt -le $max_attempts ]]; do
    if some_command; then
        echo "Success on attempt $attempt"
        break
    fi
    echo "Attempt $attempt failed, retrying..."
    ((attempt++))
    sleep 2
done

if [[ $attempt -gt $max_attempts ]]; then
    echo "Failed after $max_attempts attempts"
fi
```

### Progress Counter

```bash
total=100
for ((i=1; i<=total; i++)); do
    printf "\rProgress: %d%%" "$((i * 100 / total))"
    sleep 0.1
done
echo
```

### Parallel Processing

Simple parallel with `&`:

```bash
for file in *.txt; do
    process_file "$file" &
done
wait    # Wait for all background jobs
```

With controlled parallelism:

```bash
max_jobs=4
for file in *.txt; do
    while [[ $(jobs -r -p | wc -l) -ge $max_jobs ]]; do
        sleep 0.1
    done
    process_file "$file" &
done
wait
```

### Menu Loop

```bash
while true; do
    echo "1) Option A"
    echo "2) Option B"
    echo "3) Quit"
    read -rp "Choice: " choice

    case "$choice" in
        1) echo "You chose A" ;;
        2) echo "You chose B" ;;
        3) break ;;
        *) echo "Invalid choice" ;;
    esac
done
```

### Accumulator Pattern

```bash
total=0
for num in 1 2 3 4 5; do
    ((total += num))
done
echo "Total: $total"    # 15
```

## Loop Performance

### Avoid External Commands in Loops

```bash
# Slow - calls external command each iteration
for i in {1..1000}; do
    result=$(echo "$i * 2" | bc)
done

# Fast - use bash arithmetic
for i in {1..1000}; do
    ((result = i * 2))
done
```

### Use While Read for Large Files

```bash
# Bad - loads entire file into memory
for line in $(cat huge.txt); do
    echo "$line"
done

# Good - reads line by line
while IFS= read -r line; do
    echo "$line"
done < huge.txt
```

## Select Loop

Create simple menus:

```bash
PS3="Choose a color: "
select color in "Red" "Green" "Blue" "Quit"; do
    case "$color" in
        Red|Green|Blue)
            echo "You chose: $color"
            ;;
        Quit)
            break
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
done
```

```
1) Red
2) Green
3) Blue
4) Quit
Choose a color: 2
You chose: Green
Choose a color: 4
```

## Try It

1. Basic for loop:
   ```bash
   for name in Alice Bob Charlie; do
       echo "Hello, $name!"
   done
   ```

2. File loop:
   ```bash
   for file in /etc/*.conf; do
       echo "Config: $file"
   done | head -5
   ```

3. C-style loop:
   ```bash
   for ((i=1; i<=5; i++)); do
       echo "Square of $i is $((i * i))"
   done
   ```

4. While with counter:
   ```bash
   n=1
   while [[ $n -le 3 ]]; do
       echo "Iteration $n"
       ((n++))
   done
   ```

5. Read file:
   ```bash
   echo -e "line1\nline2\nline3" | while read -r line; do
       echo "Got: $line"
   done
   ```

## Summary

| Loop Type | Use Case |
|-----------|----------|
| `for x in list` | Known list of items |
| `for ((i=0;...))` | Counter-based iteration |
| `while condition` | Until condition is false |
| `until condition` | Until condition is true |
| `select x in list` | User menus |

| Control | Effect |
|---------|--------|
| `break` | Exit loop |
| `break N` | Exit N nested loops |
| `continue` | Skip to next iteration |
| `continue N` | Continue outer loop |

Best practices:

- Quote array expansion: `"${arr[@]}"`
- Use `while IFS= read -r` for files
- Use `-print0` / `-d ''` for filenames with spaces
- Avoid external commands inside loops
- Use `wait` after background jobs
