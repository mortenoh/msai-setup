# Finding Files

Locating files by name, type, size, date, and other criteria.

## find - The Classic Tool

### Basic Syntax

```bash
find [path] [expression]
```

### Find by Name

```bash
find . -name "*.txt"              # Exact pattern (case sensitive)
find . -iname "*.txt"             # Case insensitive
find . -name "config*"            # Starts with config
find /home -name ".bashrc"        # Absolute path
```

### Find by Type

```bash
find . -type f                    # Regular files
find . -type d                    # Directories
find . -type l                    # Symbolic links
find . -type f -name "*.py"       # Python files
```

| Type | Meaning |
|------|---------|
| `f` | Regular file |
| `d` | Directory |
| `l` | Symbolic link |
| `b` | Block device |
| `c` | Character device |
| `s` | Socket |
| `p` | Named pipe |

### Find by Size

```bash
find . -size +100M                # Larger than 100MB
find . -size -1k                  # Smaller than 1KB
find . -size 50M                  # Exactly 50MB
find . -type f -size +1G          # Large files
```

| Suffix | Unit |
|--------|------|
| `c` | Bytes |
| `k` | Kilobytes |
| `M` | Megabytes |
| `G` | Gigabytes |

### Find by Time

```bash
# Modified time
find . -mtime -7                  # Modified in last 7 days
find . -mtime +30                 # Modified more than 30 days ago
find . -mtime 1                   # Modified exactly 1 day ago

# Accessed time
find . -atime -7                  # Accessed in last 7 days

# Changed time (metadata)
find . -ctime -7                  # Changed in last 7 days

# Minutes instead of days
find . -mmin -60                  # Modified in last 60 minutes

# Newer than file
find . -newer reference.txt       # Newer than reference.txt
```

### Find by Permissions

```bash
find . -perm 644                  # Exactly 644
find . -perm -644                 # At least 644
find . -perm /644                 # Any of these bits
find . -perm -u+x                 # User executable
find . -type f -perm /111         # Any executable
```

### Find by Owner

```bash
find . -user alice                # Owned by alice
find . -group staff               # Group staff
find . -uid 1000                  # By user ID
find . -nouser                    # No owner (orphaned)
```

### Combining Conditions

```bash
# AND (implicit)
find . -type f -name "*.log" -size +1M

# AND (explicit)
find . -type f -a -name "*.log"

# OR
find . -name "*.txt" -o -name "*.md"

# NOT
find . -type f ! -name "*.log"
find . -not -name "*.log"

# Complex
find . \( -name "*.txt" -o -name "*.md" \) -mtime -7
```

### Execute Commands

```bash
# -exec (runs once per file)
find . -name "*.log" -exec rm {} \;
find . -type f -exec chmod 644 {} \;

# -exec with + (batch mode - faster)
find . -name "*.txt" -exec wc -l {} +

# -ok (prompt before each)
find . -name "*.tmp" -ok rm {} \;

# Using xargs (often faster)
find . -name "*.txt" | xargs wc -l
find . -name "*.txt" -print0 | xargs -0 wc -l  # Handle spaces
```

### Limiting Depth

```bash
find . -maxdepth 1 -type f        # Current directory only
find . -maxdepth 2 -name "*.py"   # At most 2 levels deep
find . -mindepth 2 -type d        # At least 2 levels deep
```

### Excluding Paths

```bash
# Exclude directory
find . -path "./node_modules" -prune -o -name "*.js" -print

# Exclude multiple
find . \( -path "./node_modules" -o -path "./.git" \) -prune -o -type f -print

# Exclude pattern
find . -name "*.txt" ! -path "*/backup/*"
```

### Practical Examples

```bash
# Find large files
find / -type f -size +100M 2>/dev/null

# Find recent modifications
find . -type f -mtime -1

# Find and delete old logs
find /var/log -name "*.log" -mtime +30 -delete

# Find empty files/directories
find . -type f -empty
find . -type d -empty

# Find broken symlinks
find . -type l ! -exec test -e {} \; -print

# Find files with specific permissions
find . -type f -perm 777

# Find and count by extension
find . -type f -name "*.py" | wc -l

# Find duplicates by name
find . -type f -name "*.txt" -exec basename {} \; | sort | uniq -d
```

## fd - Modern Alternative

`fd` is a faster, more user-friendly alternative to `find`.

### Installation

```bash
# macOS
brew install fd

# Debian/Ubuntu
apt install fd-find    # Command may be 'fdfind'
```

### Basic Usage

```bash
fd pattern                        # Search current dir
fd pattern /path                  # Search specific path
fd "\.txt$"                       # Regex pattern
```

### Key Differences from find

| find | fd |
|------|-----|
| `find . -name "*.txt"` | `fd -e txt` or `fd "\.txt$"` |
| `find . -type f` | `fd -t f` |
| `find . -type d` | `fd -t d` |
| Includes hidden | Excludes hidden/gitignored by default |

### Common Options

```bash
fd -e py                          # By extension
fd -t f                           # Files only
fd -t d                           # Directories only
fd -H                             # Include hidden
fd -I                             # Don't ignore .gitignore
fd -a                             # Absolute paths
fd -l                             # Long listing (like ls -l)
fd -x command                     # Execute command
fd -X command                     # Execute in batch
```

### Search Control

```bash
fd -d 2 pattern                   # Max depth 2
fd -E "*.bak"                     # Exclude pattern
fd -E node_modules                # Exclude directory
fd --changed-within 1d            # Modified in last day
fd --changed-before 1w            # Modified before last week
fd -S +1M                         # Size greater than 1MB
```

### Execute Commands

```bash
fd -e txt -x wc -l                # Count lines in each
fd -e jpg -x convert {} {.}.png   # Convert images
fd -t f -X rm                     # Delete all files (batch)
```

Placeholders:

| Placeholder | Meaning |
|-------------|---------|
| `{}` | Full path |
| `{/}` | Basename |
| `{//}` | Parent directory |
| `{.}` | Path without extension |
| `{/.}` | Basename without extension |

### Practical Examples

```bash
# Find Python files
fd -e py

# Find recent changes
fd --changed-within 1h

# Find large files
fd -t f -S +100M

# Find and open in editor
fd -e md -x code {}

# Find with preview
fd -e txt | fzf --preview 'head -20 {}'
```

## locate - Database Search

Fast filename search using pre-built database.

### Setup

```bash
# Update database (usually runs via cron)
sudo updatedb                     # Linux
sudo /usr/libexec/locate.updatedb # macOS
```

### Usage

```bash
locate filename                   # Search database
locate -i filename                # Case insensitive
locate -n 10 filename             # Limit results
locate -c filename                # Count only
locate -e filename                # Only existing files
```

!!! note "Database Freshness"
    `locate` uses a database that may be outdated. Use `find` or `fd` for real-time results.

## Combining with Other Tools

### With grep

```bash
# Find files containing pattern
find . -type f -name "*.py" -exec grep -l "import os" {} +

# Using fd
fd -e py -x grep -l "import os"
```

### With xargs

```bash
# Handle filenames with spaces
find . -name "*.txt" -print0 | xargs -0 wc -l

# Parallel processing
find . -name "*.jpg" -print0 | xargs -0 -P 4 -I {} convert {} {}.png
```

### With fzf

```bash
# Interactive file selection
find . -type f | fzf

# With preview
fd -t f | fzf --preview 'cat {}'

# Open selected file
vim $(fd -t f | fzf)
```

## Comparison

| Feature | find | fd | locate |
|---------|------|-----|--------|
| Speed | Slow | Fast | Fastest |
| Real-time | Yes | Yes | No (database) |
| Regex | Basic | Full | Limited |
| Ignores .git | No | Yes | No |
| Ignores hidden | No | Yes | No |
| Colored output | No | Yes | No |
| Portability | Universal | Needs install | Usually installed |

## Try It

1. find basics:
   ```bash
   find /tmp -type f -name "*.txt" 2>/dev/null | head
   find ~ -maxdepth 1 -type f
   ```

2. find by time:
   ```bash
   find . -mmin -5 -type f
   ```

3. fd basics:
   ```bash
   fd --version && fd -e md
   ```

4. Execute commands:
   ```bash
   find . -name "*.txt" -exec echo "Found: {}" \;
   ```

## Summary

| Task | find | fd |
|------|------|-----|
| By name | `-name "*.txt"` | `-e txt` or `"\.txt$"` |
| Files only | `-type f` | `-t f` |
| Directories | `-type d` | `-t d` |
| Max depth | `-maxdepth N` | `-d N` |
| Execute | `-exec cmd {} \;` | `-x cmd` |
| Batch execute | `-exec cmd {} +` | `-X cmd` |
| By size | `-size +1M` | `-S +1M` |
| By time | `-mtime -1` | `--changed-within 1d` |
| Exclude | `-path ... -prune` | `-E pattern` |
| Include hidden | (default) | `-H` |

Best practices:

- Use `fd` for interactive work (faster, prettier)
- Use `find` for scripts (portable, always available)
- Use `locate` when database is fresh and you need speed
- Always handle spaces: `-print0` with `xargs -0`
