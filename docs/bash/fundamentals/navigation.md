# Navigation

Moving around the filesystem efficiently is fundamental to command-line productivity.

## The Filesystem Hierarchy

Unix filesystems are organized as a tree starting from root (`/`):

```
/
├── bin/          # Essential binaries
├── etc/          # System configuration
├── home/         # User home directories (Linux)
├── Users/        # User home directories (macOS)
├── tmp/          # Temporary files
├── usr/          # User programs and data
│   ├── bin/      # User binaries
│   ├── local/    # Locally installed software
│   └── share/    # Shared data
└── var/          # Variable data (logs, etc.)
```

## Print Working Directory (pwd)

Always know where you are:

```bash
pwd
```

```
/Users/username/projects
```

## Change Directory (cd)

Move to a different directory:

```bash
cd /etc           # Absolute path
cd projects       # Relative path
cd                # Go to home directory
cd ~              # Also home directory
cd -              # Previous directory
cd ..             # Parent directory
cd ../..          # Two levels up
```

### Home Directory Shortcuts

```bash
cd                # Home
cd ~              # Home
cd ~/Documents    # Documents in home
cd ~username      # Another user's home
```

### Previous Directory

The `-` shortcut toggles between last two directories:

```bash
cd /var/log
pwd
```

```
/var/log
```

```bash
cd /etc
pwd
```

```
/etc
```

```bash
cd -
pwd
```

```
/var/log
```

## Absolute vs Relative Paths

**Absolute paths** start from root (`/`):

```bash
cd /home/username/projects
cd /etc/nginx
```

**Relative paths** start from current directory:

```bash
cd projects          # Same as ./projects
cd ./projects        # Explicit relative
cd ../sibling        # Up one, then into sibling
```

### Special Directory References

| Symbol | Meaning |
|--------|---------|
| `/` | Root directory |
| `~` | Home directory |
| `.` | Current directory |
| `..` | Parent directory |
| `-` | Previous directory (cd only) |

## Directory Stack (pushd/popd)

When working across multiple directories, the directory stack helps you jump back:

### pushd - Push and Change

```bash
pwd
```

```
/home/user
```

```bash
pushd /var/log
```

```
/var/log /home/user
```

```bash
pushd /etc
```

```
/etc /var/log /home/user
```

The stack shows most recent first.

### popd - Pop and Return

```bash
popd
```

```
/var/log /home/user
```

```bash
pwd
```

```
/var/log
```

### dirs - View Stack

```bash
dirs
```

```
/var/log /home/user
```

With line numbers:

```bash
dirs -v
```

```
 0  /var/log
 1  /home/user
```

### Jump to Stack Position

```bash
pushd +1    # Jump to position 1
pushd -0    # Jump to last position
```

### Clear the Stack

```bash
dirs -c
```

## Tab Completion

Bash can complete paths when you press `Tab`:

```bash
cd /usr/lo<Tab>
# Completes to: cd /usr/local/
```

Double-tab shows options:

```bash
cd /usr/<Tab><Tab>
# Shows: bin/  include/  lib/  local/  share/
```

## Wildcards in Paths

Navigate with glob patterns:

```bash
cd ~/Doc*           # Matches ~/Documents
cd /etc/ssh*        # First match starting with ssh
```

## CDPATH Variable

Define directories to search when using `cd`:

```bash
export CDPATH=".:~:~/projects"
```

Now from anywhere:

```bash
cd myproject        # Finds ~/projects/myproject
```

!!! warning "CDPATH Caveat"
    CDPATH can cause confusion in scripts. Consider using it only interactively.

## Practical Navigation Patterns

### Quick Project Access

Add to your `.bashrc`:

```bash
# Quick project navigation
proj() {
    cd ~/projects/"$1" 2>/dev/null || echo "Project not found: $1"
}
```

Usage:

```bash
proj myapp
```

### Bookmark Directories

```bash
# Save current directory
alias mark='pwd > ~/.marked_dir'

# Return to marked directory
alias back='cd "$(cat ~/.marked_dir)"'
```

### Create and Enter Directory

```bash
mkcd() {
    mkdir -p "$1" && cd "$1"
}
```

Usage:

```bash
mkcd new-project
```

## Navigation with Modern Tools

### autojump / z / zoxide

These tools learn your habits and let you jump to frequent directories:

```bash
# After visiting ~/projects/myapp several times
z myapp             # Jumps to ~/projects/myapp
```

Install zoxide (recommended):

```bash
brew install zoxide
```

Add to `.bashrc`:

```bash
eval "$(zoxide init bash)"
```

### fzf for Directory Navigation

Fuzzy find directories:

```bash
cd "$(find . -type d | fzf)"
```

Or with a function:

```bash
fcd() {
    local dir
    dir=$(find ${1:-.} -type d 2>/dev/null | fzf) && cd "$dir"
}
```

## Common Mistakes

### Spaces in Paths

Quote paths with spaces:

```bash
cd "My Documents"       # Correct
cd My\ Documents        # Also correct (escaped space)
cd My Documents         # Wrong - tries cd to "My"
```

### Case Sensitivity

Linux is case-sensitive; macOS is case-insensitive by default:

```bash
# Linux
cd Documents    # Different from
cd documents    # This one

# macOS (default) - both work
```

### Missing Directories

Check if directory exists before changing:

```bash
[[ -d /some/path ]] && cd /some/path || echo "Not found"
```

## Try It

1. Practice basic navigation:
   ```bash
   cd /var/log
   pwd
   cd ..
   pwd
   cd -
   ```

2. Use the directory stack:
   ```bash
   pushd /etc
   pushd /var
   pushd /tmp
   dirs -v
   popd
   popd
   popd
   ```

3. Create the `mkcd` function and test it:
   ```bash
   mkcd() { mkdir -p "$1" && cd "$1"; }
   mkcd ~/test-navigation
   pwd
   cd ..
   rm -r ~/test-navigation
   ```

## Summary

| Command | Purpose |
|---------|---------|
| `pwd` | Show current directory |
| `cd <path>` | Change directory |
| `cd` or `cd ~` | Go home |
| `cd -` | Previous directory |
| `cd ..` | Parent directory |
| `pushd <path>` | Push to stack and change |
| `popd` | Pop stack and return |
| `dirs` | Show directory stack |
