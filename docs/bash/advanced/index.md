# Advanced

Deep dive into advanced bash concepts: job control, subshells, signals, and performance optimization.

## Topics

### [Job Control](job-control.md)

Managing background processes, `nohup`, `disown`, and running jobs after terminal close.

### [Subshells](subshells.md)

Understanding subshells, command substitution, process substitution, and their implications for variable scope.

### [Signals](signals.md)

Unix signals, the `trap` command, handling interrupts, and graceful shutdown patterns.

### [Performance](performance.md)

Optimizing bash scripts: avoiding common performance pitfalls, when to use external tools, and profiling techniques.

## Prerequisites

This section assumes familiarity with:

- Basic scripting (variables, conditionals, loops)
- Functions and scope
- Process concepts (PIDs, exit codes)
- Basic I/O redirection

## Why These Topics Matter

### Job Control

Essential for:

- Running long processes without tying up the terminal
- Managing multiple concurrent tasks
- Keeping processes alive after SSH disconnect
- Development workflows with background servers

### Subshells

Understanding subshells prevents bugs related to:

- Variables not persisting after pipes
- Unexpected process isolation
- Performance from unnecessary forks
- Proper use of `$()` and `()`

### Signals

Critical for:

- Graceful shutdown handling
- Cleanup on script interruption
- Inter-process communication
- Robust production scripts

### Performance

Important for:

- Scripts that process large files
- Avoiding unnecessary external commands
- Understanding when bash is (not) the right tool
- Production script optimization

## Key Concepts Preview

### Job Control

```bash
# Run in background
./server.sh &

# Keep running after logout
nohup ./server.sh &
disown

# Wait for background jobs
wait
```

### Subshells

```bash
# Subshell - variables don't persist
(cd /tmp && pwd)  # Back to original after

# Command substitution runs in subshell
output=$(some_command)

# Pipe creates subshell
echo "data" | while read line; do
    var="$line"  # Won't persist!
done
```

### Signals

```bash
# Cleanup on exit
trap 'rm -f $tmpfile' EXIT

# Handle Ctrl+C
trap 'echo "Interrupted"; exit 1' INT

# Ignore signal
trap '' TERM
```

### Performance

```bash
# Slow - external command in loop
for i in {1..1000}; do
    result=$(echo "$i * 2" | bc)
done

# Fast - bash arithmetic
for i in {1..1000}; do
    ((result = i * 2))
done
```

## Common Patterns

These topics combine into powerful patterns:

### Daemon Script

```bash
#!/usr/bin/env bash

cleanup() {
    echo "Shutting down..."
    kill $worker_pid 2>/dev/null
    rm -f "$pidfile"
}

trap cleanup EXIT INT TERM

pidfile="/var/run/mydaemon.pid"
echo $$ > "$pidfile"

while true; do
    do_work &
    worker_pid=$!
    wait $worker_pid
    sleep 60
done
```

### Parallel Processing

```bash
#!/usr/bin/env bash

max_jobs=4
for file in *.txt; do
    while (( $(jobs -r -p | wc -l) >= max_jobs )); do
        sleep 0.1
    done
    process "$file" &
done
wait
```

### Graceful Timeout

```bash
#!/usr/bin/env bash

timeout=30
( sleep $timeout; kill $$ 2>/dev/null ) &
timer_pid=$!

trap "kill $timer_pid 2>/dev/null" EXIT

# Long running work here
do_work

# Completed before timeout
kill $timer_pid 2>/dev/null
```

## When to Use What

| Situation | Approach |
|-----------|----------|
| Long-running task | Background job + `disown` |
| Need output later | `nohup` with output file |
| Cleanup required | `trap EXIT` |
| Handle Ctrl+C | `trap INT` |
| Parallel processing | Background jobs + `wait` |
| Variable in pipe | Process substitution or here-string |
| Isolated environment | Subshell `()` |
