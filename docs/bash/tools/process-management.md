# Process Management

Monitoring and controlling processes on Unix systems.

## Viewing Processes

### ps - Process Status

```bash
ps                                # Current terminal processes
ps aux                            # All processes (BSD style)
ps -ef                            # All processes (POSIX style)
```

#### Common Options (BSD style)

```bash
ps aux                            # All processes, user-oriented
ps auxf                           # With process tree (Linux)
ps aux --sort=-%mem               # Sort by memory
ps aux --sort=-%cpu               # Sort by CPU
ps aux | head -20                 # Top 20 processes
```

#### Output Columns

| Column | Meaning |
|--------|---------|
| USER | Process owner |
| PID | Process ID |
| %CPU | CPU usage |
| %MEM | Memory usage |
| VSZ | Virtual memory (KB) |
| RSS | Resident memory (KB) |
| TTY | Terminal |
| STAT | Process state |
| START | Start time |
| TIME | CPU time |
| COMMAND | Command |

#### Process States

| State | Meaning |
|-------|---------|
| R | Running |
| S | Sleeping (interruptible) |
| D | Sleeping (uninterruptible) |
| T | Stopped |
| Z | Zombie |

### Finding Specific Processes

```bash
ps aux | grep nginx               # Find nginx processes
ps aux | grep -v grep | grep nginx # Exclude grep itself
pgrep nginx                       # Get PIDs only
pgrep -l nginx                    # With names
pgrep -a nginx                    # Full command line
```

### Process Tree

```bash
pstree                            # All processes as tree
pstree -p                         # With PIDs
pstree -u                         # With usernames
pstree user                       # Processes of user
pstree -p $$                      # Current shell tree
```

## Interactive Monitors

### top

Real-time process monitor:

```bash
top
```

#### top Keybindings

| Key | Action |
|-----|--------|
| `q` | Quit |
| `k` | Kill process |
| `r` | Renice process |
| `M` | Sort by memory |
| `P` | Sort by CPU |
| `T` | Sort by time |
| `c` | Toggle full command |
| `1` | Toggle per-CPU stats |
| `h` | Help |

#### top Options

```bash
top -o cpu                        # Sort by CPU (macOS)
top -o %CPU                       # Sort by CPU (Linux)
top -p 1234                       # Monitor specific PID
top -u username                   # Processes by user
```

### htop

Better interactive monitor (needs install):

```bash
brew install htop                 # macOS
apt install htop                  # Debian/Ubuntu
```

Features:

- Color-coded display
- Mouse support
- Horizontal and vertical scrolling
- Tree view
- Easy process management

### btop

Modern, beautiful system monitor:

```bash
brew install btop
btop
```

See [Modern Replacements](modern-replacements.md) for details.

## System Resources

### Memory

```bash
free -h                           # Memory usage (Linux)
vm_stat                           # Memory stats (macOS)
```

### Disk I/O

```bash
iostat                            # I/O statistics
iotop                             # I/O by process (Linux, needs root)
```

### CPU

```bash
uptime                            # Load averages
mpstat                            # CPU statistics (Linux)
```

## Terminating Processes

### kill

Send signals to processes:

```bash
kill PID                          # Send SIGTERM (graceful)
kill -9 PID                       # Send SIGKILL (force)
kill -15 PID                      # SIGTERM explicitly
kill -HUP PID                     # SIGHUP (reload config)
kill -STOP PID                    # Pause process
kill -CONT PID                    # Resume process
```

### Common Signals

| Signal | Number | Purpose |
|--------|--------|---------|
| SIGHUP | 1 | Hangup / reload |
| SIGINT | 2 | Interrupt (Ctrl+C) |
| SIGQUIT | 3 | Quit with core dump |
| SIGKILL | 9 | Force kill (cannot catch) |
| SIGTERM | 15 | Graceful termination |
| SIGSTOP | 19 | Pause (cannot catch) |
| SIGCONT | 18 | Continue |

### killall

Kill by name:

```bash
killall nginx                     # Kill all nginx processes
killall -9 nginx                  # Force kill all
killall -u user                   # Kill user's processes
```

### pkill

Kill by pattern:

```bash
pkill nginx                       # Kill matching processes
pkill -9 "python.*script"         # Force kill with regex
pkill -u user                     # Kill by user
pkill -t pts/0                    # Kill by terminal
```

### Graceful Shutdown

```bash
# Try graceful first, then force
kill PID
sleep 5
kill -0 PID 2>/dev/null && kill -9 PID
```

## Job Control

### Background Jobs

```bash
command &                         # Run in background
./long_script.sh &                # Start backgrounded
```

### jobs

List background jobs:

```bash
jobs                              # List jobs
jobs -l                           # With PIDs
jobs -r                           # Running only
jobs -s                           # Stopped only
```

### fg and bg

```bash
Ctrl+Z                            # Suspend current job
bg                                # Resume in background
bg %1                             # Resume job 1 in background
fg                                # Bring to foreground
fg %1                             # Bring job 1 to foreground
```

### Job Specifiers

| Specifier | Meaning |
|-----------|---------|
| `%1` | Job number 1 |
| `%+` or `%%` | Current job |
| `%-` | Previous job |
| `%string` | Job starting with string |
| `%?string` | Job containing string |

### nohup

Continue running after logout:

```bash
nohup command &                   # Ignore hangup signal
nohup ./script.sh > output.log 2>&1 &
```

### disown

Remove from shell's job table:

```bash
command &
disown                            # Disown last job
disown %1                         # Disown job 1
disown -h %1                      # Don't send SIGHUP
```

## Wait for Processes

### wait

```bash
command1 &
command2 &
wait                              # Wait for all background jobs
wait $!                           # Wait for last background job
wait %1                           # Wait for job 1
```

### Check Process Running

```bash
# Check if PID exists
kill -0 PID 2>/dev/null && echo "Running"

# Wait for process to end
while kill -0 PID 2>/dev/null; do
    sleep 1
done
echo "Process ended"
```

## Process Priority

### nice

Start with adjusted priority:

```bash
nice command                      # Default nice (10)
nice -n 10 command                # Nice value 10
nice -n -10 command               # Higher priority (needs root)
nice -n 19 command                # Lowest priority
```

Nice values: -20 (highest priority) to 19 (lowest priority)

### renice

Change running process priority:

```bash
renice 10 PID                     # Set nice to 10
renice -n 10 -p PID               # Same
renice -n -5 -p PID               # Higher priority (needs root)
renice -n 10 -u user              # All processes of user
```

## Resource Limits

### ulimit

View and set resource limits:

```bash
ulimit -a                         # Show all limits
ulimit -n                         # Open files limit
ulimit -u                         # Max processes
ulimit -v                         # Virtual memory
ulimit -n 4096                    # Set open files limit
```

## Practical Patterns

### Kill All User Processes

```bash
pkill -u username
# or
ps -u username -o pid= | xargs kill
```

### Find Memory Hogs

```bash
ps aux --sort=-%mem | head -10
```

### Find CPU Hogs

```bash
ps aux --sort=-%cpu | head -10
```

### Watch Process

```bash
watch -n 1 'ps aux | grep nginx'
```

### Start Process and Get PID

```bash
command &
pid=$!
echo "Started with PID: $pid"
```

### Timeout Command

```bash
timeout 60 long_command           # Kill after 60 seconds
timeout --signal=KILL 60 command  # SIGKILL after timeout
```

### Parallel Processing

```bash
# Process files in parallel
for file in *.txt; do
    process "$file" &
done
wait

# Limit parallelism
max_jobs=4
for file in *.txt; do
    while [[ $(jobs -r -p | wc -l) -ge $max_jobs ]]; do
        sleep 0.1
    done
    process "$file" &
done
wait
```

### Daemon Pattern

```bash
#!/usr/bin/env bash
run_daemon() {
    while true; do
        do_work
        sleep 60
    done
}

# Daemonize
run_daemon &
echo $! > /var/run/mydaemon.pid
disown
```

## Try It

1. List processes:
   ```bash
   ps aux | head -5
   pgrep -l bash
   ```

2. Job control:
   ```bash
   sleep 100 &
   jobs
   fg
   # Press Ctrl+Z
   bg
   jobs
   kill %1
   ```

3. Monitor:
   ```bash
   top -n 1 | head -20
   ```

4. Find resource usage:
   ```bash
   ps aux --sort=-%mem | head -5
   ```

## Summary

| Task | Command |
|------|---------|
| List processes | `ps aux` |
| Find by name | `pgrep name` |
| Interactive monitor | `top`, `htop`, `btop` |
| Graceful kill | `kill PID` |
| Force kill | `kill -9 PID` |
| Kill by name | `killall name` |
| Background job | `command &` |
| List jobs | `jobs` |
| Foreground | `fg %N` |
| Background | `bg %N` |
| Ignore hangup | `nohup command &` |
| Remove from shell | `disown` |
| Wait for jobs | `wait` |
| Set priority | `nice -n N command` |
| Change priority | `renice N PID` |
