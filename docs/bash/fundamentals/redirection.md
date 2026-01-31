# Redirection & Pipes

Controlling where command input comes from and where output goes is fundamental to Unix philosophy.

## Standard Streams

Every process has three standard streams:

| Stream | Number | Default | Purpose |
|--------|--------|---------|---------|
| stdin | 0 | Keyboard | Input |
| stdout | 1 | Terminal | Normal output |
| stderr | 2 | Terminal | Error messages |

```
┌──────────┐     ┌─────────┐     ┌──────────┐
│  stdin   │────>│ Command │────>│  stdout  │
│    0     │     │         │────>│  stderr  │
└──────────┘     └─────────┘     └──────────┘
```

## Output Redirection

### Redirect stdout to File

```bash
echo "Hello" > file.txt         # Create/overwrite
echo "World" >> file.txt        # Append
```

### Redirect stderr to File

```bash
command 2> errors.log           # stderr only
command 2>> errors.log          # Append stderr
```

### Redirect Both

```bash
command > output.txt 2>&1       # Both to same file
command &> output.txt           # Shorthand (bash 4+)
command >> output.txt 2>&1      # Append both
command &>> output.txt          # Append shorthand (bash 4+)
```

### Redirect to Different Files

```bash
command > stdout.txt 2> stderr.txt
```

### Discard Output

```bash
command > /dev/null             # Discard stdout
command 2> /dev/null            # Discard stderr
command &> /dev/null            # Discard both
```

## Input Redirection

### From File

```bash
wc -l < file.txt                # File as input
sort < unsorted.txt > sorted.txt
```

### Here Documents (heredoc)

Inline multi-line input:

```bash
cat << EOF
Line 1
Line 2
Line 3
EOF
```

With variable expansion:

```bash
name="World"
cat << EOF
Hello, $name!
EOF
```

```
Hello, World!
```

Without expansion (quote the delimiter):

```bash
cat << 'EOF'
The variable $HOME won't expand
EOF
```

```
The variable $HOME won't expand
```

Indented heredoc (tabs stripped):

```bash
cat <<- EOF
	Indented with tabs
	This tab is removed
EOF
```

### Here Strings

Single-line input:

```bash
grep "pattern" <<< "search in this string"
wc -w <<< "count these words"
```

## Pipes

Connect stdout of one command to stdin of another:

```bash
command1 | command2 | command3
```

### Basic Examples

```bash
ls -l | head -5                 # First 5 lines
cat file.txt | wc -l            # Count lines
history | grep "git"            # Search history
ps aux | grep nginx             # Find process
```

### Practical Pipelines

```bash
# Find 10 largest files
du -sh * | sort -rh | head -10

# Count unique words
cat file.txt | tr ' ' '\n' | sort | uniq -c | sort -rn

# Extract and format data
cat data.csv | cut -d',' -f2 | sort | uniq

# Monitor log for errors
tail -f app.log | grep -i error
```

### Pipe to Multiple Commands (tee)

`tee` writes to both file and stdout:

```bash
command | tee output.txt        # Show and save
command | tee -a output.txt     # Show and append
command | tee file1 file2       # Multiple files
```

Example - save and continue processing:

```bash
cat data.txt | tee backup.txt | sort | uniq
```

### Pipe stderr

By default, pipes only pass stdout. To include stderr:

```bash
command 2>&1 | less             # Combine then pipe
command |& less                 # Shorthand (bash 4+)
```

## Process Substitution

Treat command output as a file:

```bash
diff <(command1) <(command2)
```

### Examples

Compare two command outputs:

```bash
diff <(ls dir1) <(ls dir2)
```

Compare sorted files:

```bash
diff <(sort file1) <(sort file2)
```

Use where file is expected:

```bash
paste <(cut -f1 data.txt) <(cut -f3 data.txt)
```

## File Descriptors

### Creating Custom Descriptors

```bash
exec 3> output.txt              # Open fd 3 for writing
echo "data" >&3                 # Write to fd 3
exec 3>&-                       # Close fd 3
```

```bash
exec 4< input.txt               # Open fd 4 for reading
read line <&4                   # Read from fd 4
exec 4<&-                       # Close fd 4
```

### Read and Write

```bash
exec 3<> file.txt               # Open for both
```

## Common Patterns

### Save stdout and stderr Separately

```bash
command > stdout.log 2> stderr.log
```

### Process Both Streams Separately

```bash
{ command 2>&1 1>&3 | process_stderr; } 3>&1 | process_stdout
```

### Show Output and Save

```bash
script -q /dev/null command     # macOS
command 2>&1 | tee output.log   # Portable
```

### Check if stdin is Terminal

```bash
if [[ -t 0 ]]; then
    echo "Interactive"
else
    echo "Piped input"
fi
```

### Pipeline with Error Checking

By default, pipeline exit status is the last command's. Use `pipefail`:

```bash
set -o pipefail
false | true
echo $?  # 1 (false's exit code)
```

Get individual exit statuses:

```bash
command1 | command2 | command3
echo "${PIPESTATUS[@]}"         # Array of exit codes
```

## Noclobber

Prevent accidental overwrite:

```bash
set -o noclobber
echo "test" > existing.txt      # Error if exists
echo "test" >| existing.txt     # Force overwrite
set +o noclobber                # Disable
```

## xargs - Build Commands from Input

Convert input to arguments:

```bash
find . -name "*.txt" | xargs wc -l
```

Handle spaces in filenames:

```bash
find . -name "*.txt" -print0 | xargs -0 wc -l
```

Limit arguments per command:

```bash
echo 1 2 3 4 5 | xargs -n 2 echo
```

```
1 2
3 4
5
```

Run with placeholder:

```bash
ls *.txt | xargs -I {} cp {} backup/
```

Parallel execution:

```bash
find . -name "*.jpg" | xargs -P 4 -I {} convert {} {}.png
```

## Redirection Order Matters

The order of redirections is processed left to right:

```bash
# These are different:
command > file 2>&1     # stderr goes to same file as stdout
command 2>&1 > file     # stderr goes to terminal, stdout to file
```

## Summary Table

| Syntax | Meaning |
|--------|---------|
| `>` | Redirect stdout (overwrite) |
| `>>` | Redirect stdout (append) |
| `2>` | Redirect stderr |
| `2>>` | Redirect stderr (append) |
| `&>` | Redirect both (bash 4+) |
| `2>&1` | Redirect stderr to stdout |
| `<` | Input from file |
| `<<` | Here document |
| `<<<` | Here string |
| `\|` | Pipe stdout |
| `\|&` | Pipe both (bash 4+) |
| `<()` | Process substitution (input) |
| `>()` | Process substitution (output) |

## Try It

1. Practice basic redirection:
   ```bash
   echo "Hello" > /tmp/test.txt
   echo "World" >> /tmp/test.txt
   cat /tmp/test.txt
   ```

2. Redirect stderr:
   ```bash
   ls /nonexistent 2> /tmp/errors.txt
   cat /tmp/errors.txt
   ls /nonexistent 2> /dev/null   # Silence errors
   ```

3. Use pipes:
   ```bash
   ls -la /usr/bin | head -20
   history | grep "cd" | tail -5
   ```

4. Use tee:
   ```bash
   echo "logged" | tee /tmp/log.txt
   cat /tmp/log.txt
   ```

5. Process substitution:
   ```bash
   diff <(echo -e "a\nb\nc") <(echo -e "a\nx\nc")
   ```

6. Clean up:
   ```bash
   rm /tmp/test.txt /tmp/errors.txt /tmp/log.txt
   ```
