# Subshells

Understanding subshells is crucial for avoiding bugs related to variable scope and process isolation.

## What is a Subshell?

A subshell is a child process that runs a copy of the current shell. It inherits:

- Environment variables (exported)
- Current directory
- File descriptors

It does NOT share:

- Shell variables (non-exported)
- Shell options
- Function definitions (unless exported)

## Creating Subshells

### Explicit Subshell with ()

```bash
(commands)
```

Commands run in a separate process:

```bash
var="original"
(var="changed"; echo "Inside: $var")   # Inside: changed
echo "Outside: $var"                    # Outside: original
```

The change doesn't persist.

### Directory Change in Subshell

```bash
(cd /tmp && pwd)                       # /tmp
pwd                                    # Still in original directory
```

Useful for temporary directory operations.

### Command Substitution

```bash
result=$(command)
```

The command runs in a subshell:

```bash
var="outer"
result=$(var="inner"; echo "$var")
echo "$result"                          # inner
echo "$var"                             # outer (unchanged)
```

### Pipes Create Subshells

Each part of a pipeline runs in a subshell:

```bash
var="original"
echo "data" | {
    read line
    var="changed"
    echo "Inside pipe: $var"           # Inside pipe: changed
}
echo "Outside: $var"                    # Outside: original
```

This is a common source of bugs!

## The Pipe Subshell Problem

### The Bug

```bash
count=0
cat file.txt | while read line; do
    ((count++))
done
echo "Lines: $count"                    # Lines: 0 (wrong!)
```

The `while` loop runs in a subshell, so `count` changes are lost.

### Solutions

#### Process Substitution

```bash
count=0
while read line; do
    ((count++))
done < <(cat file.txt)
echo "Lines: $count"                    # Correct!
```

#### Here String

```bash
count=0
while read line; do
    ((count++))
done <<< "$(cat file.txt)"
echo "Lines: $count"
```

#### Redirect from File

```bash
count=0
while read line; do
    ((count++))
done < file.txt
echo "Lines: $count"
```

#### lastpipe Option (Bash 4.2+)

```bash
shopt -s lastpipe
count=0
cat file.txt | while read line; do
    ((count++))
done
echo "Lines: $count"                    # Works with lastpipe
```

!!! note "lastpipe Requirement"
    `lastpipe` only works when job control is disabled (non-interactive shells or `set +m`).

## Process Substitution

### Input Process Substitution <()

Treat command output as a file:

```bash
diff <(sort file1.txt) <(sort file2.txt)
```

The `<(command)` creates a file descriptor that reads from the command's output.

### Output Process Substitution >()

Send output to a command as if to a file:

```bash
tee >(grep error > errors.log) >(grep warn > warnings.log) > full.log
```

### Practical Examples

```bash
# Compare directory listings
diff <(ls dir1) <(ls dir2)

# Join on processed data
join <(sort -k1 file1) <(sort -k1 file2)

# Multiple outputs
command | tee >(gzip > output.gz) | head
```

## Subshell vs Brace Group

### Subshell ()

Runs in separate process:

```bash
(var=1; echo $var)                      # Runs in subshell
echo $var                               # Empty
```

### Brace Group {}

Runs in current shell:

```bash
{ var=1; echo $var; }                   # Same shell (note spaces and semicolon)
echo $var                               # 1
```

### When to Use Which

Use **subshell** `()` when you want:

- Isolated environment
- Temporary directory change
- Parallel execution

Use **brace group** `{}` when you want:

- Grouping for redirection
- Variable changes to persist
- Conditional execution

```bash
# Redirect group
{ echo "header"; cat file; echo "footer"; } > output.txt

# Conditional group
[[ -f file ]] && { process; cleanup; notify; }
```

## Detecting Subshells

```bash
echo "Current shell PID: $$"
echo "Actual PID: $BASHPID"

(echo "Subshell BASHPID: $BASHPID")      # Different from $$
```

`$$` is the parent shell PID (constant), `$BASHPID` is the actual current process.

```bash
# In a subshell?
if [[ $$ != $BASHPID ]]; then
    echo "Running in subshell"
fi
```

## Environment vs Shell Variables

### Shell Variables (Not Inherited)

```bash
myvar="hello"
(echo "$myvar")                         # Empty in subshell
```

### Environment Variables (Inherited)

```bash
export myvar="hello"
(echo "$myvar")                         # hello

# Or inline export
myvar="hello" bash -c 'echo "$myvar"'   # hello
```

## Functions and Subshells

### Functions Not Available

```bash
myfunc() { echo "Hello"; }
(myfunc)                                # Error: command not found
```

### Export Functions

```bash
myfunc() { echo "Hello"; }
export -f myfunc
(myfunc)                                # Hello
bash -c 'myfunc'                        # Hello
```

## Common Patterns

### Isolated Operations

```bash
# Temporary environment
(
    export PATH="/custom/path:$PATH"
    export DEBUG=1
    ./script.sh
)
# Original environment unchanged
```

### Parallel Execution

```bash
# Run in parallel
(task1) &
(task2) &
(task3) &
wait
```

### Safe Directory Operations

```bash
# Process in different directory without cd-ing
(cd /data && tar -czf backup.tar.gz *)

# Extract to specific location
(cd /target && tar -xzf /path/to/archive.tar.gz)
```

### Error Isolation

```bash
# Errors in subshell don't exit parent
(
    set -e
    risky_command
    another_command
) || echo "Subshell failed but we continue"
```

### Capture Output with Side Effects

```bash
# Get output and exit code
output=$(command; echo "::$?")
exit_code="${output##*::}"
output="${output%::*}"
```

## Performance Considerations

Subshells have overhead (process creation). Avoid in tight loops:

```bash
# Slow - subshell per iteration
for i in {1..1000}; do
    result=$(echo "$i * 2" | bc)
done

# Fast - no subshell
for i in {1..1000}; do
    ((result = i * 2))
done
```

## Try It

1. Variable scope:
   ```bash
   var="outer"
   (var="inner"; echo "Inside: $var")
   echo "Outside: $var"
   ```

2. Pipe problem:
   ```bash
   count=0
   echo -e "a\nb\nc" | while read line; do ((count++)); done
   echo "Count: $count"  # 0!

   count=0
   while read line; do ((count++)); done < <(echo -e "a\nb\nc")
   echo "Count: $count"  # 3
   ```

3. Process substitution:
   ```bash
   diff <(echo -e "a\nb\nc") <(echo -e "a\nx\nc")
   ```

4. Subshell PID:
   ```bash
   echo "Shell PID: $$"
   echo "Current: $BASHPID"
   (echo "Subshell: $BASHPID")
   ```

## Summary

| Construct | Creates Subshell | Variables Persist |
|-----------|-----------------|-------------------|
| `(commands)` | Yes | No |
| `$(command)` | Yes | No |
| `cmd1 \| cmd2` | Yes (both sides) | No |
| `{ commands; }` | No | Yes |
| `< <(command)` | Yes (for command) | Yes (for loop) |

Common pitfalls:

- Variables set in pipes don't persist
- Functions need `export -f` for subshells
- `$$` vs `$BASHPID` differ in subshells
- Subshells have process creation overhead

Solutions:

- Use process substitution `< <(cmd)` instead of pipes
- Use `lastpipe` option (Bash 4.2+)
- Use brace groups `{}` when persistence needed
- Export functions for subshell access
