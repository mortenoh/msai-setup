# Modern Replacements

Better alternatives to classic Unix tools. These tools offer improved ergonomics, performance, and features while remaining compatible with their predecessors.

## Installation

### macOS (Homebrew)

```bash
brew install eza bat ripgrep fd fzf zoxide btop
```

### Linux (Debian/Ubuntu)

```bash
# Available via apt
sudo apt install bat ripgrep fd-find fzf

# May need cargo or other methods
cargo install eza
sudo snap install btop
```

## eza (formerly exa) - Better ls

Modern replacement for `ls` with colors, icons, and git integration.

### Installation

```bash
brew install eza
```

### Basic Usage

```bash
eza                               # List files
eza -l                            # Long format
eza -la                           # Long + hidden
eza -lh                           # Long + header
eza --icons                       # With icons
eza --tree                        # Tree view
eza --git                         # Git status
```

### Useful Options

```bash
eza -l --no-permissions           # Hide permissions
eza -l --no-user                  # Hide user/group
eza -l --time-style=long-iso      # ISO timestamps
eza -la --group-directories-first # Dirs first
eza -l --sort=modified            # Sort by time
eza -l --sort=size                # Sort by size
eza --tree --level=2              # Tree depth 2
```

### Recommended Aliases

```bash
alias ls='eza'
alias ll='eza -l --icons'
alias la='eza -la --icons'
alias lt='eza -la --sort=modified'
alias tree='eza --tree --icons'
```

### Git Integration

```bash
eza -l --git                      # Shows git status per file
```

Output symbols:

| Symbol | Meaning |
|--------|---------|
| `N` | New (untracked) |
| `M` | Modified |
| `-` | Unmodified |
| `I` | Ignored |

## bat - Better cat

Syntax highlighting, git integration, and automatic paging.

### Installation

```bash
brew install bat
```

### Basic Usage

```bash
bat file.py                       # View with highlighting
bat -n file.py                    # Line numbers only
bat -p file.py                    # Plain (no decorations)
bat -A file.py                    # Show non-printable chars
bat --diff file.py                # Show git changes
bat -l python script              # Force language
bat file1.py file2.py             # Multiple files
```

### Options

```bash
bat --style=numbers               # Only line numbers
bat --style=plain                 # No decorations
bat --style=full                  # Everything
bat --theme=gruvbox-dark          # Change theme
bat --list-themes                 # Show themes
bat --list-languages              # Supported languages
```

### Integration

```bash
# As pager for man
export MANPAGER="sh -c 'col -bx | bat -l man -p'"

# Preview for fzf
fzf --preview 'bat --color=always {}'

# With git
git diff | bat
git show HEAD:file.py | bat -l python
```

### Recommended Aliases

```bash
alias cat='bat -pp'               # Plain, no pager
alias catn='bat -n'               # With line numbers
```

## ripgrep (rg) - Better grep

Extremely fast recursive search that respects .gitignore.

### Installation

```bash
brew install ripgrep
```

### Basic Usage

```bash
rg pattern                        # Search current dir
rg pattern file.txt               # Search specific file
rg pattern dir/                   # Search directory
rg -i pattern                     # Case insensitive
rg -w pattern                     # Whole word
rg -F "literal"                   # Fixed string (no regex)
```

### Output Control

```bash
rg -n pattern                     # Line numbers (default)
rg -l pattern                     # Files only
rg -c pattern                     # Count per file
rg -o pattern                     # Only matching text
rg -C 2 pattern                   # 2 lines context
rg --no-heading pattern           # grep-style output
```

### Filtering

```bash
rg -t py pattern                  # Python files only
rg -T js pattern                  # Exclude JavaScript
rg -g "*.py" pattern              # Glob pattern
rg -g "!test_*" pattern           # Exclude pattern
rg --hidden pattern               # Include hidden files
rg -u pattern                     # Unrestricted (include ignored)
rg -uu pattern                    # Include hidden + ignored
```

### Advanced

```bash
rg -e "pat1" -e "pat2"            # Multiple patterns
rg "pattern" --replace "new"      # Show replacements
rg -U "multi\nline"               # Multiline mode
rg -P "(?<=prefix)\w+"            # PCRE2 regex
rg --stats pattern                # Show statistics
```

### Practical Examples

```bash
# Find TODOs
rg "TODO|FIXME" -t py

# Find function definitions
rg "def \w+\(" -t py

# Count matches
rg -c "import" --type py | sort -t: -k2 -rn

# Find and replace preview
rg "old_name" --replace "new_name"
```

### Recommended Alias

```bash
alias grep='rg'
```

## fd - Better find

See [Finding Files](finding-files.md) for detailed coverage.

Quick reference:

```bash
fd pattern                        # Find by name
fd -e py                          # By extension
fd -t f                           # Files only
fd -t d                           # Directories only
fd -H                             # Include hidden
fd -x cmd                         # Execute command
```

## fzf - Fuzzy Finder

Interactive fuzzy finding for files, history, and more.

### Installation

```bash
brew install fzf
# Install keybindings
$(brew --prefix)/opt/fzf/install
```

### Basic Usage

```bash
fzf                               # Find files
cmd | fzf                         # Filter any list
fzf --preview 'cat {}'            # With preview
fzf -m                            # Multi-select
```

### Keybindings (after install)

| Key | Action |
|-----|--------|
| `Ctrl+T` | Fuzzy find files |
| `Ctrl+R` | Fuzzy search history |
| `Alt+C` | Fuzzy cd to directory |

### Integration Examples

```bash
# Open file in editor
vim $(fzf)

# Kill process
kill $(ps aux | fzf | awk '{print $2}')

# Git checkout branch
git checkout $(git branch | fzf)

# SSH to host
ssh $(grep "Host " ~/.ssh/config | awk '{print $2}' | fzf)
```

### Preview Options

```bash
fzf --preview 'bat --color=always {}'
fzf --preview 'head -50 {}'
fzf --preview-window=right:50%
```

### Custom Commands

```bash
# Find and edit
fe() {
    local file
    file=$(fd -t f | fzf --preview 'bat --color=always {}')
    [[ -n "$file" ]] && ${EDITOR:-vim} "$file"
}

# Find directory and cd
fcd() {
    local dir
    dir=$(fd -t d | fzf --preview 'eza --tree {}')
    [[ -n "$dir" ]] && cd "$dir"
}

# Git log browser
fgl() {
    git log --oneline | fzf --preview 'git show {1}'
}
```

## zoxide - Smarter cd

Jump to frequently used directories.

### Installation

```bash
brew install zoxide
```

### Setup

Add to `.bashrc`:

```bash
eval "$(zoxide init bash)"
```

### Usage

```bash
z pattern                         # Jump to best match
z foo bar                         # Multiple patterns
zi                                # Interactive with fzf
z -                               # Previous directory
```

### How It Works

Zoxide learns from your `cd` usage and ranks directories by "frecency" (frequency + recency).

```bash
# After visiting ~/projects/myapp several times
z myapp                           # Jumps to ~/projects/myapp
z proj app                        # Also works
```

### Commands

```bash
zoxide query pattern              # Show best match
zoxide query -l                   # List all ranked dirs
zoxide add /path                  # Manually add
zoxide remove /path               # Remove from database
```

## btop - Better top

Beautiful, feature-rich system monitor.

### Installation

```bash
brew install btop
```

### Features

- CPU, memory, disk, network graphs
- Per-core CPU usage
- Process tree view
- Mouse support
- Customizable themes

### Keybindings

| Key | Action |
|-----|--------|
| `m` | Toggle memory display |
| `n` | Toggle network display |
| `d` | Toggle disk display |
| `p` | Toggle process display |
| `t` | Toggle tree view |
| `k` | Kill selected process |
| `f` | Filter processes |
| `q` | Quit |

## delta - Better git diff

Syntax highlighting for git diffs.

### Installation

```bash
brew install git-delta
```

### Setup

Add to `~/.gitconfig`:

```ini
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true
    light = false
    line-numbers = true
```

### Features

- Syntax highlighting
- Line numbers
- Side-by-side view
- Word-level diff highlighting

## Comparison Table

| Classic | Modern | Key Benefits |
|---------|--------|--------------|
| `ls` | `eza` | Icons, git, colors |
| `cat` | `bat` | Syntax highlighting, git |
| `grep` | `ripgrep` | Speed, .gitignore |
| `find` | `fd` | Simpler syntax, speed |
| `top` | `btop` | Beautiful UI |
| `cd` | `zoxide` | Frecency-based jumping |
| - | `fzf` | Interactive filtering |
| `diff` | `delta` | Syntax-highlighted diffs |

## Recommended Setup

Add to `~/.bashrc`:

```bash
# Modern tool aliases (if installed)
command -v eza &>/dev/null && alias ls='eza --icons'
command -v bat &>/dev/null && alias cat='bat -pp'
command -v rg &>/dev/null && alias grep='rg'
command -v fd &>/dev/null && alias find='fd'
command -v btop &>/dev/null && alias top='btop'

# Extended aliases
if command -v eza &>/dev/null; then
    alias ll='eza -l --icons'
    alias la='eza -la --icons'
    alias lt='eza -la --sort=modified'
    alias tree='eza --tree --icons'
fi

# Initialize zoxide
command -v zoxide &>/dev/null && eval "$(zoxide init bash)"

# fzf configuration
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
```

## Try It

1. eza:
   ```bash
   eza -la --icons
   eza --tree --level=2
   ```

2. bat:
   ```bash
   bat --list-themes | head
   echo 'print("Hello")' | bat -l python
   ```

3. ripgrep:
   ```bash
   rg --stats "pattern" 2>/dev/null || echo "Install ripgrep"
   ```

4. fzf:
   ```bash
   echo -e "one\ntwo\nthree" | fzf
   ```

These modern tools significantly improve the command-line experience while maintaining compatibility with their classic counterparts.
