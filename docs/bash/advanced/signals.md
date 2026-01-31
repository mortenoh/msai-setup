# Signals

Signals are software interrupts sent to processes. Understanding signals enables graceful shutdown, cleanup, and inter-process communication.

## Common Signals

| Signal | Number | Default Action | Common Use |
|--------|--------|----------------|------------|
| SIGHUP | 1 | Terminate | Terminal closed, reload config |
| SIGINT | 2 | Terminate | Ctrl+C |
| SIGQUIT | 3 | Core dump | Ctrl+\\ |
| SIGKILL | 9 | Terminate | Force kill (cannot catch) |
| SIGTERM | 15 | Terminate | Graceful termination |
| SIGSTOP | 19 | Stop | Pause process (cannot catch) |
| SIGCONT | 18 | Continue | Resume stopped process |
| SIGCHLD | 17 | Ignore | Child process ended |
| SIGUSR1 | 10 | Terminate | User-defined |
| SIGUSR2 | 12 | Terminate | User-defined |

### List All Signals

```bash
kill -l
```

## The trap Command

`trap` sets handlers for signals:

```bash
trap 'commands' SIGNAL [SIGNAL...]
trap 'commands' EXIT              # On any exit
trap 'commands' ERR               # On error (with set -e)
trap 'commands' DEBUG             # Before each command
trap 'commands' RETURN            # After function return
```

### Basic Examples

```bash
# Cleanup on exit
trap 'rm -f $tmpfile' EXIT

# Handle Ctrl+C
trap 'echo "Interrupted"; exit 1' INT

# Handle termination
trap 'echo "Terminated"; exit 0' TERM

# Multiple signals
trap 'cleanup' INT TERM EXIT
```

### Ignore Signal

```bash
trap '' INT                       # Ignore Ctrl+C
trap '' TERM                      # Ignore termination
```

### Reset to Default

```bash
trap - INT                        # Reset INT to default
trap - EXIT                       # Remove EXIT trap
```

### View Current Traps

```bash
trap -p                           # Show all traps
trap -p INT                       # Show INT trap
```

## Cleanup Patterns

### Basic Cleanup

```bash
#!/usr/bin/env bash

cleanup() {
    echo "Cleaning up..."
    rm -f "$tmpfile"
    rm -rf "$tmpdir"
}

trap cleanup EXIT

tmpfile=$(mktemp)
tmpdir=$(mktemp -d)

# Script continues...
# cleanup runs automatically on exit
```

### Cleanup with Exit Code

```bash
#!/usr/bin/env bash

cleanup() {
    local exit_code=$?
    echo "Cleaning up..."
    rm -f "$tmpfile"
    exit $exit_code
}

trap cleanup EXIT

tmpfile=$(mktemp)
# ...
```

### Robust Cleanup

```bash
#!/usr/bin/env bash

declare -a cleanup_tasks=()

add_cleanup() {
    cleanup_tasks+=("$1")
}

run_cleanup() {
    for task in "${cleanup_tasks[@]}"; do
        eval "$task"
    done
}

trap run_cleanup EXIT

# Usage
tmpfile=$(mktemp)
add_cleanup "rm -f $tmpfile"

tmpdir=$(mktemp -d)
add_cleanup "rm -rf $tmpdir"

# All cleanup tasks run on exit
```

## Signal Handling Patterns

### Graceful Shutdown

```bash
#!/usr/bin/env bash

shutdown=false

handle_shutdown() {
    echo "Shutdown requested..."
    shutdown=true
}

trap handle_shutdown TERM INT

while ! $shutdown; do
    echo "Working..."
    sleep 1
done

echo "Graceful shutdown complete"
```

### Timeout with Cleanup

```bash
#!/usr/bin/env bash

timeout=30
child_pid=""

cleanup() {
    [[ -n "$child_pid" ]] && kill "$child_pid" 2>/dev/null
}

trap cleanup EXIT

# Start timeout watcher
(sleep $timeout; kill $$ 2>/dev/null) &
timer_pid=$!

# Do work
long_running_command &
child_pid=$!
wait $child_pid

# Cancel timer if completed
kill $timer_pid 2>/dev/null
```

### Reload Configuration

```bash
#!/usr/bin/env bash

load_config() {
    echo "Loading configuration..."
    source /etc/myapp/config
}

trap load_config HUP

load_config

while true; do
    do_work
    sleep 1
done
```

Send reload signal:

```bash
kill -HUP $(cat /var/run/myapp.pid)
```

## Sending Signals

### kill Command

```bash
kill PID                          # SIGTERM (default)
kill -TERM PID                    # SIGTERM explicitly
kill -15 PID                      # Same (by number)
kill -INT PID                     # SIGINT
kill -9 PID                       # SIGKILL (force)
kill -0 PID                       # Check if running (no signal sent)
```

### killall and pkill

```bash
killall -TERM processname
pkill -TERM -f "pattern"
pkill -HUP nginx
```

### From Script

```bash
# Kill background job
./server.sh &
pid=$!
kill -TERM $pid

# With check
if kill -0 $pid 2>/dev/null; then
    kill -TERM $pid
fi
```

## DEBUG Trap

Execute command before each line:

```bash
trap 'echo "About to run: $BASH_COMMAND"' DEBUG

echo "First"
echo "Second"
```

Output:

```
About to run: echo "First"
First
About to run: echo "Second"
Second
```

### Step-Through Execution

```bash
trap 'read -p "Press Enter for next..."' DEBUG
```

### Timing

```bash
trap 'printf "%(%H:%M:%S)T " -1' DEBUG
```

## ERR Trap

Execute on command failure (with `set -e`):

```bash
#!/usr/bin/env bash
set -e

trap 'echo "Error on line $LINENO"' ERR

command_that_works
command_that_fails     # Triggers trap
echo "Not reached"
```

### Stack Trace on Error

```bash
#!/usr/bin/env bash
set -e

error_handler() {
    echo "Error at line $1"
    echo "Stack trace:"
    local i=0
    while caller $i; do
        ((i++))
    done
}

trap 'error_handler $LINENO' ERR
```

## RETURN Trap

Execute after function or sourced script returns:

```bash
trace_return() {
    trap 'echo "Returned from ${FUNCNAME[0]}"' RETURN
}

my_function() {
    trace_return
    echo "In function"
}

my_function
```

## Signal Best Practices

### Always Clean Up

```bash
trap cleanup EXIT                 # Runs on any exit
```

### Don't Ignore SIGTERM in Production

```bash
# Bad - prevents graceful shutdown
trap '' TERM

# Good - handle it properly
trap 'graceful_shutdown' TERM
```

### Preserve Exit Code

```bash
cleanup() {
    local exit_code=$?
    # cleanup actions
    exit $exit_code
}
trap cleanup EXIT
```

### Re-raise Signal After Handling

```bash
handle_term() {
    cleanup
    trap - TERM    # Reset handler
    kill -TERM $$  # Re-raise signal
}
trap handle_term TERM
```

### Child Process Cleanup

```bash
#!/usr/bin/env bash

child_pids=()

cleanup() {
    for pid in "${child_pids[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait
}

trap cleanup EXIT INT TERM

start_worker() {
    worker_function &
    child_pids+=($!)
}
```

## Practical Examples

### Daemon Script

```bash
#!/usr/bin/env bash

PIDFILE="/var/run/mydaemon.pid"
RUNNING=true

shutdown() {
    echo "Shutting down..."
    RUNNING=false
}

trap shutdown TERM INT
trap 'rm -f $PIDFILE' EXIT

echo $$ > "$PIDFILE"

while $RUNNING; do
    do_work
    sleep 1
done

echo "Daemon stopped"
```

### Lock File with Cleanup

```bash
#!/usr/bin/env bash

LOCKFILE="/var/lock/myapp.lock"

cleanup() {
    rm -f "$LOCKFILE"
}

trap cleanup EXIT

# Acquire lock
if ! mkdir "$LOCKFILE" 2>/dev/null; then
    echo "Another instance is running"
    exit 1
fi

echo "Running with lock"
# ... do work ...
```

### Progress with Interruption

```bash
#!/usr/bin/env bash

interrupted=false
trap 'interrupted=true' INT

for i in {1..100}; do
    if $interrupted; then
        echo "Interrupted at $i%"
        break
    fi
    echo "Progress: $i%"
    sleep 0.1
done

echo "Final: $i%"
```

## Try It

1. Basic trap:
   ```bash
   trap 'echo "Caught INT"' INT
   echo "Press Ctrl+C"
   sleep 10
   ```

2. Cleanup on exit:
   ```bash
   tmpfile=$(mktemp)
   trap 'rm -f $tmpfile; echo "Cleaned up"' EXIT
   echo "Temp: $tmpfile"
   ls -la "$tmpfile"
   exit 0
   ```

3. Debug trap:
   ```bash
   trap 'echo ">> $BASH_COMMAND"' DEBUG
   echo "Hello"
   echo "World"
   trap - DEBUG
   ```

## Summary

| Signal | Trigger | Typical Use |
|--------|---------|-------------|
| `INT` | Ctrl+C | User interrupt |
| `TERM` | `kill PID` | Graceful shutdown |
| `HUP` | Terminal close | Reload config |
| `EXIT` | Any exit | Cleanup |
| `ERR` | Command failure | Error handling |

| trap Command | Purpose |
|--------------|---------|
| `trap 'cmd' SIG` | Set handler |
| `trap '' SIG` | Ignore signal |
| `trap - SIG` | Reset to default |
| `trap -p` | Show traps |

Best practices:

- Always use `trap cleanup EXIT`
- Handle TERM for graceful shutdown
- Preserve and return original exit code
- Clean up child processes
- Use DEBUG for tracing, not production
