# Performance

Optimizing bash scripts for speed and efficiency. Know when to optimize and when to use a different tool.

## The First Rule

> Premature optimization is the root of all evil. - Donald Knuth

Before optimizing:

1. Does the script run fast enough?
2. Is the bottleneck in bash or external commands?
3. Would a different language be more appropriate?

## Profiling Scripts

### Simple Timing

```bash
time ./script.sh
```

Output:

```
real    0m5.032s    # Wall clock time
user    0m1.234s    # CPU time in user mode
sys     0m0.567s    # CPU time in kernel mode
```

### Timing Sections

```bash
#!/usr/bin/env bash

start=$(date +%s.%N)
# ... code section ...
end=$(date +%s.%N)
echo "Section took: $(echo "$end - $start" | bc) seconds"
```

### DEBUG Trap Profiling

```bash
#!/usr/bin/env bash

exec 3>&2 2>/tmp/bashprofile.$$
BASH_XTRACEFD=3
PS4='+ $(date +%s.%N) ${FUNCNAME[0]:+${FUNCNAME[0]}():}line $LINENO: '
set -x

# ... your script ...

set +x
exec 2>&3 3>&-
```

### Using time for Loops

```bash
time for i in {1..1000}; do
    some_operation
done
```

## Common Performance Issues

### External Commands in Loops

**Problem**: Each external command forks a new process.

```bash
# Slow - 1000 process forks
for i in {1..1000}; do
    result=$(echo "$i * 2" | bc)
done
```

**Solution**: Use bash built-ins.

```bash
# Fast - no external processes
for i in {1..1000}; do
    ((result = i * 2))
done
```

### Unnecessary Subshells

**Problem**: `$()` creates a subshell.

```bash
# Slow - subshell for simple assignment
var=$(echo "hello")

# Fast - direct assignment
var="hello"
```

### cat Abuse

**Problem**: Useless use of cat.

```bash
# Slow
cat file.txt | grep "pattern"

# Fast
grep "pattern" file.txt

# Also slow
content=$(cat file.txt)

# Fast
content=$(<file.txt)
```

### Reading Files

**Problem**: Loading entire file into memory.

```bash
# Slow and memory-intensive
for line in $(cat hugefile.txt); do
    process "$line"
done
```

**Solution**: Stream processing.

```bash
# Fast and memory-efficient
while IFS= read -r line; do
    process "$line"
done < hugefile.txt
```

### String Operations

**Problem**: External tools for simple strings.

```bash
# Slow
filename=$(basename "$path")
extension=$(echo "$file" | sed 's/.*\.//')

# Fast - parameter expansion
filename="${path##*/}"
extension="${file##*.}"
```

## Built-in vs External

### Use Built-ins When Possible

| Task | External (Slow) | Built-in (Fast) |
|------|-----------------|-----------------|
| Arithmetic | `expr 5 + 3` | `$((5 + 3))` |
| Substring | `echo "$s" \| cut -c1-5` | `${s:0:5}` |
| Replace | `echo "$s" \| sed 's/a/b/'` | `${s/a/b}` |
| Basename | `basename "$p"` | `${p##*/}` |
| Dirname | `dirname "$p"` | `${p%/*}` |
| Length | `echo "$s" \| wc -c` | `${#s}` |
| Uppercase | `echo "$s" \| tr a-z A-Z` | `${s^^}` |
| Test file | `test -f "$f"` | `[[ -f "$f" ]]` |

### When External is Faster

For large-scale text processing, specialized tools beat bash:

```bash
# For processing large files, awk is faster
awk '{sum += $1} END {print sum}' hugefile.txt

# Faster than
sum=0
while read num; do
    ((sum += num))
done < hugefile.txt
```

## Array Performance

### Appending to Arrays

```bash
# Slow - recreates array each time
for i in {1..1000}; do
    arr=("${arr[@]}" "$i")
done

# Fast - append operator
for i in {1..1000}; do
    arr+=("$i")
done
```

### Array vs String

```bash
# For many items, arrays are cleaner but not always faster
# Consider the actual use case
```

## Loop Optimizations

### Move Invariants Out

```bash
# Slow - calculates every iteration
for file in *.txt; do
    base_dir=$(pwd)
    process "$base_dir/$file"
done

# Fast - calculate once
base_dir=$(pwd)
for file in *.txt; do
    process "$base_dir/$file"
done
```

### Batch External Commands

```bash
# Slow - one process per file
for file in *.txt; do
    wc -l "$file"
done

# Fast - one process for all
wc -l *.txt
```

### Use find -exec + or xargs

```bash
# Slow - one process per file
find . -name "*.txt" -exec wc -l {} \;

# Fast - batch processing
find . -name "*.txt" -exec wc -l {} +

# Or with xargs
find . -name "*.txt" | xargs wc -l
```

## Conditional Optimizations

### Short-Circuit Evaluation

```bash
# Check cheap conditions first
if [[ -f "$file" ]] && expensive_check "$file"; then
    process
fi
```

### Case vs If-Elif

For many conditions, `case` can be faster:

```bash
# Many elif branches
if [[ "$cmd" == "start" ]]; then
    start
elif [[ "$cmd" == "stop" ]]; then
    stop
elif [[ "$cmd" == "restart" ]]; then
    restart
fi

# case - often faster for string matching
case "$cmd" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
esac
```

## I/O Optimizations

### Batch Output

```bash
# Slow - many small writes
for i in {1..1000}; do
    echo "$i" >> output.txt
done

# Fast - single write
{
    for i in {1..1000}; do
        echo "$i"
    done
} > output.txt
```

### Avoid Repeated File Opens

```bash
# Slow - opens file 1000 times
for i in {1..1000}; do
    echo "$i" >> output.txt
done

# Fast - opens once
exec 3>>output.txt
for i in {1..1000}; do
    echo "$i" >&3
done
exec 3>&-
```

## Process Substitution vs Temp Files

```bash
# With temp file
cmd1 > /tmp/temp.txt
cmd2 < /tmp/temp.txt
rm /tmp/temp.txt

# With process substitution - no temp file
cmd2 < <(cmd1)
```

## Parallel Execution

### Simple Parallelism

```bash
cmd1 &
cmd2 &
cmd3 &
wait
```

### Controlled Parallelism

```bash
max_jobs=4
for item in "${items[@]}"; do
    while (( $(jobs -rp | wc -l) >= max_jobs )); do
        sleep 0.1
    done
    process "$item" &
done
wait
```

### Using GNU Parallel

```bash
parallel -j4 process {} ::: "${items[@]}"
```

## When Not to Use Bash

Consider other languages when:

- Processing large data sets
- Complex data structures needed
- Floating-point math required
- Performance is critical
- Cross-platform compatibility needed

### Better Alternatives

| Task | Better Tool |
|------|-------------|
| JSON processing | `jq`, Python |
| Large text processing | `awk`, `sed`, Python |
| Complex logic | Python, Ruby |
| Numerical computing | Python, R |
| Web requests | Python, curl |

## Benchmarking

### Compare Approaches

```bash
#!/usr/bin/env bash

echo "Testing external command:"
time for i in {1..1000}; do
    result=$(expr $i + 1)
done

echo "Testing arithmetic expansion:"
time for i in {1..1000}; do
    ((result = i + 1))
done
```

### Iterations Matter

Run enough iterations to get meaningful results:

```bash
# Too few - noise dominates
time for i in {1..10}; do operation; done

# Better
time for i in {1..10000}; do operation; done
```

## Summary

### Quick Wins

| Instead of | Use |
|------------|-----|
| `$(echo "$var")` | `"$var"` |
| `cat file \| cmd` | `cmd < file` |
| `$(cat file)` | `$(<file)` |
| `expr $a + $b` | `$((a + b))` |
| `basename "$p"` | `${p##*/}` |
| `echo "$s" \| wc -c` | `${#s}` |

### Performance Checklist

1. Avoid external commands in loops
2. Use parameter expansion for strings
3. Use `(( ))` for arithmetic
4. Batch I/O operations
5. Use `[[ ]]` instead of `[ ]`
6. Consider parallel execution
7. Use appropriate tools for large data
8. Profile before optimizing

### Rules of Thumb

- External command: ~10ms overhead per call
- Subshell: ~1-5ms overhead
- Built-in operations: microseconds
- File operations: depends on I/O

Remember: Clarity often matters more than micro-optimizations. Optimize only when necessary and profile to find real bottlenecks.
