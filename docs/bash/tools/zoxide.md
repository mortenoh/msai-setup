# zoxide

zoxide is a smarter cd command that learns your habits and lets you jump to directories with minimal keystrokes.

## How It Works

```
cd ~/projects/myapp/frontend/src/components
cd ~/another/path
cd ~/projects/myapp/backend

# Later, from anywhere:
z components
# -> ~/projects/myapp/frontend/src/components

z backend
# -> ~/projects/myapp/backend
```

zoxide tracks directory usage and frecency (frequency + recency) to predict where you want to go.

## Installation

### macOS

```bash
brew install zoxide
```

### Linux

```bash
curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash
```

### Cargo

```bash
cargo install zoxide --locked
```

## Shell Integration

### Bash

```bash
# ~/.bashrc
eval "$(zoxide init bash)"
```

### Zsh

```bash
# ~/.zshrc
eval "$(zoxide init zsh)"
```

### Fish

```fish
# ~/.config/fish/config.fish
zoxide init fish | source
```

### Aliases

By default, zoxide creates the `z` command. To also replace `cd`:

```bash
# Bash/Zsh
eval "$(zoxide init bash --cmd cd)"

# This makes cd smart
cd myproject  # Works like z
```

## Basic Usage

### Jump to Directory

```bash
# Jump to best match for "project"
z project

# Jump to "backend" in a project
z backend

# Multiple keywords (AND match)
z project backend
# -> ~/projects/myapp/backend
```

### Interactive Selection

```bash
# Use fzf for interactive selection
zi

# Filter interactively
zi project
```

Requires fzf installed:
```bash
brew install fzf  # macOS
apt install fzf   # Debian/Ubuntu
```

### Query Without Jumping

```bash
# Show where z would jump
zoxide query project

# Show all matches with scores
zoxide query project --list
```

## Commands

### z - Jump

```bash
z foo      # Jump to highest-ranked directory matching foo
z foo bar  # Jump to directory matching foo AND bar
z foo/     # Jump to subdirectory starting with foo
```

### zi - Interactive

```bash
zi         # Open interactive selector
zi foo     # Interactive selector filtered by foo
```

### zoxide - Direct

```bash
# Add directory to database
zoxide add /path/to/dir

# Remove directory from database
zoxide remove /path/to/dir

# Query database
zoxide query foo
zoxide query foo --list

# Import from other tools
zoxide import --from autojump /path/to/autojump/db
zoxide import --from z /path/to/z/data
```

## Algorithm

zoxide uses "frecency" scoring:

```
score = frequency * recency_factor
```

- **Frequency**: How often you visit
- **Recency**: How recently you visited (exponential decay)

Recent visits are weighted more heavily than old ones.

## Database

### Location

```bash
# Default locations
~/.local/share/zoxide/db.zo     # Linux
~/Library/Application Support/zoxide/db.zo  # macOS
```

### Manage Database

```bash
# View all entries
zoxide query --list

# Remove stale entries (directories that no longer exist)
zoxide remove /old/path

# Add directory manually
zoxide add /frequently/used/path
```

### Backup/Restore

```bash
# Backup
cp ~/.local/share/zoxide/db.zo ~/backup/

# Restore
cp ~/backup/db.zo ~/.local/share/zoxide/
```

## Configuration

### Environment Variables

```bash
# Custom database location
export _ZO_DATA_DIR="$HOME/.zoxide"

# Exclude directories
export _ZO_EXCLUDE_DIRS="$HOME:$HOME/private/*"

# Max entries
export _ZO_MAXAGE=10000

# Resolve symlinks
export _ZO_RESOLVE_SYMLINKS=1
```

### Exclude Directories

```bash
# ~/.bashrc or ~/.zshrc
export _ZO_EXCLUDE_DIRS="$HOME"            # Exclude home
export _ZO_EXCLUDE_DIRS="/tmp/*:$HOME/tmp" # Multiple patterns
```

## fzf Integration

### Custom fzf Options

```bash
# ~/.bashrc or ~/.zshrc
export _ZO_FZF_OPTS="
  --height 40%
  --layout=reverse
  --border
  --preview 'eza --tree --level 2 --color=always {2..}'
"
```

### Preview Directory Contents

```bash
# Using eza (modern ls)
export _ZO_FZF_OPTS="--preview 'eza -la --color=always {2..}'"

# Using tree
export _ZO_FZF_OPTS="--preview 'tree -L 2 -C {2..}'"
```

## Integration Examples

### With tmux

```bash
# Jump to project and create/attach tmux session
function tp() {
  z "$@" && tmux new-session -A -s "$(basename "$PWD")"
}
```

### With Editor

```bash
# Jump to directory and open in editor
function zv() {
  z "$@" && nvim .
}

function zc() {
  z "$@" && code .
}
```

### With Git

```bash
# Jump to git root of matching directory
function zg() {
  z "$@" && cd "$(git rev-parse --show-toplevel)"
}
```

## Migration

### From autojump

```bash
zoxide import --from autojump ~/.local/share/autojump/autojump.txt
```

### From z.lua or z.sh

```bash
zoxide import --from z ~/.z
```

### From fasd

```bash
zoxide import --from fasd ~/.fasd
```

## Tips

### Prime the Database

When starting fresh, visit your common directories:

```bash
# Manually add important directories
zoxide add ~/projects/main-project
zoxide add ~/documents/notes
zoxide add ~/.config
```

### Use Specific Keywords

```bash
# "backend" might match multiple projects
z myapp backend    # More specific
z api              # If unique enough
```

### Tab Completion

```bash
# Type partial and press Tab
z pro<Tab>  # Shows matches
```

## Troubleshooting

### Not Finding Directory

```bash
# Check if it's in the database
zoxide query mydir --list

# Add it manually if missing
zoxide add /path/to/mydir
```

### Wrong Directory

```bash
# Use more specific query
z project backend  # Instead of just: z backend

# Or use interactive mode
zi backend
```

### Reset Database

```bash
rm ~/.local/share/zoxide/db.zo
# Start fresh, database rebuilds as you use cd
```

## See Also

- [Shell Configuration](../configuration/shell.md)
- [fzf](fzf.md) - Fuzzy finder
- [tmux](tmux.md) - Terminal multiplexer
