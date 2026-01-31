# Job Control

Managing background processes and keeping commands running after terminal close.

## Background Jobs

### Starting Background Jobs

```bash
command &                         # Run in background
./server.sh &                     # Start server backgrounded
sleep 100 &                       # Example
```

The shell returns immediately while the command runs.

### Listing Jobs

```bash
jobs                              # List all jobs
jobs -l                           # Include PIDs
jobs -p                           # PIDs only
jobs -r                           # Running jobs only
jobs -s                           # Stopped jobs only
```

Output:

```
[1]   Running                 sleep 100 &
[2]-  Running                 sleep 200 &
[3]+  Stopped                 vim file.txt
```

- `[N]` - Job number
- `+` - Current job
- `-` - Previous job

## Foreground and Background

### Suspend Current Job

Press `Ctrl+Z` to suspend (stop) the foreground job:

```bash
$ vim file.txt
# Press Ctrl+Z
[1]+  Stopped                 vim file.txt
```

### Resume in Background

```bash
bg                                # Resume last suspended job in background
bg %1                             # Resume job 1 in background
bg %vim                           # By command name
```

### Bring to Foreground

```bash
fg                                # Bring current job to foreground
fg %1                             # Bring job 1 to foreground
fg %+                             # Current job (same as fg)
fg %-                             # Previous job
```

### Job Specifiers

| Specifier | Meaning |
|-----------|---------|
| `%N` | Job number N |
| `%+` or `%%` | Current job |
| `%-` | Previous job |
| `%string` | Job starting with string |
| `%?string` | Job containing string |

## Keeping Jobs Running

### The Problem

When you close a terminal or SSH connection, the shell sends `SIGHUP` to all jobs, which typically terminates them.

### nohup

Ignore the hangup signal:

```bash
nohup command &
```

Output goes to `nohup.out` by default:

```bash
nohup ./long_task.sh &
# Output in: nohup.out

nohup ./task.sh > output.log 2>&1 &
# Custom output file
```

### disown

Remove job from shell's job table:

```bash
./server.sh &
disown                            # Disown last job
disown %1                         # Disown job 1
disown -h %1                      # Mark to not receive SIGHUP
disown -a                         # Disown all jobs
```

### Combining nohup and disown

```bash
# Most robust approach
nohup ./command.sh > output.log 2>&1 &
disown
```

### When Already Running

If you started a job and forgot `nohup`:

```bash
./long_task.sh
# Press Ctrl+Z
bg
disown -h
```

Now safe to close terminal.

## Process Substitution for Background Jobs

### Get PID

```bash
./command.sh &
pid=$!                            # PID of last background job
echo "Started with PID: $pid"
```

### Wait for Completion

```bash
./task1.sh &
./task2.sh &
./task3.sh &
wait                              # Wait for all background jobs
echo "All done"
```

Wait for specific job:

```bash
./task.sh &
pid=$!
wait $pid
exit_code=$?
echo "Task exited with: $exit_code"
```

### Check If Running

```bash
./command.sh &
pid=$!

# Check if still running
if kill -0 $pid 2>/dev/null; then
    echo "Still running"
else
    echo "Finished"
fi
```

## Parallel Processing

### Simple Parallelism

```bash
for file in *.txt; do
    process "$file" &
done
wait
```

### Limited Parallelism

```bash
max_jobs=4

for file in *.txt; do
    # Wait if too many jobs running
    while (( $(jobs -r -p | wc -l) >= max_jobs )); do
        sleep 0.1
    done
    process "$file" &
done
wait
```

### With xargs

```bash
# Parallel execution with xargs
find . -name "*.txt" -print0 | xargs -0 -P 4 -I {} process {}
```

### With GNU Parallel

```bash
# Install: brew install parallel
parallel process {} ::: *.txt
parallel -j 4 process {} ::: *.txt  # 4 jobs
```

## Screen and tmux

For long-running interactive sessions, use terminal multiplexers.

### screen

```bash
screen                            # Start new session
screen -S name                    # Named session
screen -ls                        # List sessions
screen -r                         # Reattach
screen -r name                    # Reattach to named

# Inside screen:
# Ctrl+A D - Detach
# Ctrl+A C - New window
# Ctrl+A N - Next window
```

### tmux

```bash
tmux                              # Start new session
tmux new -s name                  # Named session
tmux ls                           # List sessions
tmux attach                       # Reattach
tmux attach -t name               # Reattach to named

# Inside tmux:
# Ctrl+B D - Detach
# Ctrl+B C - New window
# Ctrl+B N - Next window
# Ctrl+B % - Split horizontal
# Ctrl+B " - Split vertical
```

## Practical Patterns

### Start Server and Verify

```bash
./server.sh &
pid=$!
sleep 2
if kill -0 $pid 2>/dev/null; then
    echo "Server started successfully (PID: $pid)"
else
    echo "Server failed to start"
    exit 1
fi
```

### Timeout for Command

```bash
timeout_cmd() {
    local timeout=$1
    shift

    "$@" &
    local pid=$!

    (sleep "$timeout"; kill $pid 2>/dev/null) &
    local timer_pid=$!

    wait $pid 2>/dev/null
    local exit_code=$?

    kill $timer_pid 2>/dev/null
    return $exit_code
}

timeout_cmd 30 ./long_task.sh
```

Or use the `timeout` command:

```bash
timeout 30 ./long_task.sh
timeout --signal=KILL 30 ./task.sh
```

### PID File Management

```bash
#!/usr/bin/env bash
PIDFILE="/var/run/myapp.pid"

start() {
    if [[ -f "$PIDFILE" ]]; then
        if kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
            echo "Already running"
            return 1
        fi
    fi

    ./myapp &
    echo $! > "$PIDFILE"
    echo "Started with PID $(cat "$PIDFILE")"
}

stop() {
    if [[ -f "$PIDFILE" ]]; then
        kill "$(cat "$PIDFILE")" 2>/dev/null
        rm -f "$PIDFILE"
        echo "Stopped"
    else
        echo "Not running"
    fi
}

case "$1" in
    start) start ;;
    stop) stop ;;
    *) echo "Usage: $0 {start|stop}" ;;
esac
```

### Process Pool

```bash
#!/usr/bin/env bash
declare -a pids=()
max_workers=4
queue=("${@}")

run_worker() {
    local item="$1"
    process "$item"
}

# Start workers
for ((i=0; i<max_workers && i<${#queue[@]}; i++)); do
    run_worker "${queue[$i]}" &
    pids+=($!)
done

# Process remaining with worker reuse
idx=$max_workers
while (( ${#pids[@]} > 0 )); do
    wait -n -p finished_pid
    # Remove finished PID
    pids=("${pids[@]/$finished_pid}")

    # Start next item
    if (( idx < ${#queue[@]} )); then
        run_worker "${queue[$idx]}" &
        pids+=($!)
        ((idx++))
    fi
done
```

## Try It

1. Basic job control:
   ```bash
   sleep 100 &
   jobs
   fg
   # Press Ctrl+Z
   bg
   jobs
   kill %1
   ```

2. Multiple jobs:
   ```bash
   sleep 10 &
   sleep 20 &
   sleep 30 &
   jobs -l
   wait
   echo "All done"
   ```

3. Check background job:
   ```bash
   sleep 5 &
   pid=$!
   while kill -0 $pid 2>/dev/null; do
       echo "Still running..."
       sleep 1
   done
   echo "Finished"
   ```

## Summary

| Task | Command |
|------|---------|
| Run in background | `command &` |
| List jobs | `jobs` |
| Suspend foreground | `Ctrl+Z` |
| Resume in background | `bg %N` |
| Bring to foreground | `fg %N` |
| Keep after logout | `nohup command &` |
| Remove from shell | `disown %N` |
| Get last PID | `$!` |
| Wait for jobs | `wait` |
| Wait for specific | `wait $pid` |
| Kill job | `kill %N` |

Best practices:

- Use `nohup` + `disown` for jobs that must survive logout
- Always `wait` before script exits if using background jobs
- Use PID files for daemon management
- Consider `tmux`/`screen` for interactive long-running work
- Limit parallelism to avoid overwhelming system
