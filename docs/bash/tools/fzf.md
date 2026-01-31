# fzf - Fuzzy Finder

fzf is a general-purpose command-line fuzzy finder that enables interactive filtering of any list: files, command history, processes, git branches, and more.

## Installation

### macOS (Homebrew)

```bash
brew install fzf

# Install shell keybindings and completion
$(brew --prefix)/opt/fzf/install
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install fzf

# Or install from git for latest features
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install
```

## Basic Usage

```bash
fzf                               # Find files interactively
fzf -m                            # Multi-select mode (Tab to select)
cmd | fzf                         # Filter any list
fzf < list.txt                    # Filter from file
```

### Search Syntax

| Pattern | Match Type |
|---------|------------|
| `abc` | Fuzzy match |
| `'abc` | Exact match (quoted) |
| `^abc` | Prefix match |
| `abc$` | Suffix match |
| `!abc` | Inverse match |
| `!^abc` | Inverse prefix |
| `abc | def` | OR operator |

Combine patterns with spaces (AND):

```bash
# Files containing "test" AND "spec"
fzf --query "test spec"

# Python files with "config" but not "test"
fzf --query ".py config !test"
```

## Environment Variables

### FZF_DEFAULT_COMMAND

Defines the default command used when fzf is launched without input:

```bash
# Use fd for better performance and .gitignore support
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'

# With ripgrep (file list mode)
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'

# Traditional find (slower, no .gitignore support)
export FZF_DEFAULT_COMMAND='find . -type f'
```

### FZF_DEFAULT_OPTS

Default options applied to all fzf invocations:

```bash
export FZF_DEFAULT_OPTS='
  --height=40%
  --layout=reverse
  --border=rounded
  --info=inline
  --margin=1
  --padding=1
'
```

### Shell Integration Variables

```bash
# Ctrl+T: File search
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="
  --preview 'bat --color=always --line-range :500 {}'
  --bind 'ctrl-/:toggle-preview'
"

# Ctrl+R: History search
export FZF_CTRL_R_OPTS="
  --preview 'echo {}'
  --preview-window up:3:hidden:wrap
  --bind 'ctrl-/:toggle-preview'
  --bind 'ctrl-y:execute-silent(echo -n {2..} | pbcopy)+abort'
"

# Alt+C: Directory navigation
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
export FZF_ALT_C_OPTS="
  --preview 'eza --tree --color=always {} | head -200'
"
```

## Shell Keybindings

After running the install script, these keybindings are available:

| Key | Action |
|-----|--------|
| ++ctrl+t++ | Paste selected file path(s) |
| ++ctrl+r++ | Search command history |
| ++alt+c++ | cd to selected directory |

### Keybindings Inside fzf

| Key | Action |
|-----|--------|
| ++enter++ | Accept selection |
| ++tab++ | Mark item (multi-select) |
| ++shift+tab++ | Unmark item |
| ++ctrl+a++ | Select all |
| ++ctrl+d++ | Deselect all |
| ++ctrl+j++ / ++ctrl+k++ | Move down/up |
| ++ctrl+slash++ | Toggle preview |
| ++ctrl+c++ / ++esc++ | Cancel |

## Preview Options

Add a preview window to see file contents:

```bash
# Basic preview with bat
fzf --preview 'bat --color=always {}'

# Preview with line numbers
fzf --preview 'bat --color=always --style=numbers {}'

# Preview window positioning
fzf --preview-window=right:60%        # Right side, 60% width
fzf --preview-window=up:40%           # Top, 40% height
fzf --preview-window=down:50%:wrap    # Bottom with word wrap
fzf --preview-window=hidden           # Hidden by default

# Toggle preview with Ctrl+/
fzf --preview 'bat --color=always {}' --bind 'ctrl-/:toggle-preview'
```

### Preview for Different Content Types

```bash
# Files with syntax highlighting
fzf --preview 'bat --color=always --line-range :500 {}'

# Directories with tree view
fzf --preview 'eza --tree --color=always --level=2 {}'

# Git commits
git log --oneline | fzf --preview 'git show --color=always {1}'

# Processes
ps aux | fzf --preview 'echo {}' --preview-window=wrap
```

## Integration with fd

fd and fzf work together for faster file finding:

```bash
# Use fd as the default command
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'

# Find and open files
fd --type f | fzf --preview 'bat --color=always {}' | xargs -r nvim

# Find specific extensions
fd -e py | fzf --preview 'bat --color=always {}'

# Find directories
fd --type d | fzf --preview 'eza --tree {}'
```

## Tab Completion

fzf provides fuzzy completion for common commands:

```bash
# Enable in bash
source /opt/homebrew/opt/fzf/shell/completion.bash

# Enable in zsh
source /opt/homebrew/opt/fzf/shell/completion.zsh
```

### Trigger Completion

Use `**` as the trigger sequence:

```bash
# File/directory completion
vim **<TAB>
cd ~/projects/**<TAB>

# Process completion
kill **<TAB>

# Host completion
ssh **<TAB>

# Environment variable
export **<TAB>
```

### Custom Completion

```bash
# Custom completion for git checkout
_fzf_complete_git() {
    if [[ "$@" == "git checkout"* ]]; then
        _fzf_complete --preview 'git log --oneline -20 {}' -- "$@" < <(
            git branch --all | sed 's/^..//' | sed 's#remotes/origin/##'
        )
    else
        eval "zle ${fzf_default_completion:-expand-or-complete}"
    fi
}
```

## Advanced Usage

### Multi-Select Operations

```bash
# Select multiple files to edit
nvim $(fzf -m)

# Select multiple files to delete
fzf -m | xargs rm

# Select multiple files with preview
fzf -m --preview 'bat --color=always {}' --bind 'ctrl-a:select-all'
```

### Header and Prompt

```bash
fzf --header 'Select a file to edit'
fzf --prompt 'Files> '
fzf --pointer '>'
fzf --marker '+'
```

### Custom Bindings

```bash
# Execute command on selection
fzf --bind 'enter:execute(nvim {})'

# Execute and close
fzf --bind 'ctrl-o:execute-silent(code {})+abort'

# Reload results
fzf --bind 'ctrl-r:reload(fd --type f)'

# Chain multiple actions
fzf --bind 'ctrl-y:execute-silent(echo {} | pbcopy)+abort'
```

## Theming

### Built-in Color Schemes

```bash
# Dark theme
export FZF_DEFAULT_OPTS='--color=dark'

# Light theme
export FZF_DEFAULT_OPTS='--color=light'

# 16 color mode
export FZF_DEFAULT_OPTS='--color=16'
```

### Custom Colors

```bash
export FZF_DEFAULT_OPTS='
  --color=fg:#c0caf5,bg:#1a1b26,hl:#bb9af7
  --color=fg+:#c0caf5,bg+:#292e42,hl+:#7dcfff
  --color=info:#7aa2f7,prompt:#7dcfff,pointer:#7dcfff
  --color=marker:#9ece6a,spinner:#9ece6a,header:#9ece6a
'
```

### Popular Theme: Tokyo Night

```bash
export FZF_DEFAULT_OPTS='
  --color=fg:#c0caf5,bg:#24283b,hl:#ff9e64
  --color=fg+:#c0caf5,bg+:#292e42,hl+:#ff9e64
  --color=info:#7aa2f7,prompt:#7dcfff,pointer:#7dcfff
  --color=marker:#9ece6a,spinner:#9ece6a,header:#9ece6a
  --color=border:#27a1b9
'
```

### Popular Theme: Catppuccin Mocha

```bash
export FZF_DEFAULT_OPTS='
  --color=bg+:#313244,bg:#1e1e2e,spinner:#f5e0dc,hl:#f38ba8
  --color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc
  --color=marker:#f5e0dc,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8
'
```

## Custom Functions

### Find and Edit

```bash
# Find file and open in editor
fe() {
    local file
    file=$(fd --type f --hidden --follow --exclude .git | \
           fzf --preview 'bat --color=always --line-range :500 {}')
    [[ -n "$file" ]] && ${EDITOR:-nvim} "$file"
}
```

### Find and cd

```bash
# Find directory and cd
fcd() {
    local dir
    dir=$(fd --type d --hidden --follow --exclude .git | \
          fzf --preview 'eza --tree --color=always {} | head -200')
    [[ -n "$dir" ]] && cd "$dir"
}
```

### Git Integration

```bash
# Checkout branch
fco() {
    local branch
    branch=$(git branch --all | grep -v HEAD | sed 's/.* //' | \
             sed 's#remotes/origin/##' | sort -u | \
             fzf --preview 'git log --oneline -20 {}')
    [[ -n "$branch" ]] && git checkout "$branch"
}

# Browse git log
fgl() {
    git log --oneline --color=always | \
    fzf --ansi --preview 'git show --color=always {1}' \
        --bind 'enter:execute(git show {1} | less -R)'
}

# Add files interactively
fga() {
    local files
    files=$(git status --short | \
            fzf -m --preview 'git diff --color=always {2}' | \
            awk '{print $2}')
    [[ -n "$files" ]] && echo "$files" | xargs git add
}
```

### Process Management

```bash
# Kill process
fkill() {
    local pid
    pid=$(ps aux | sed 1d | fzf -m --preview 'echo {}' | awk '{print $2}')
    [[ -n "$pid" ]] && echo "$pid" | xargs kill -${1:-9}
}
```

### Docker Integration

```bash
# Docker container shell
fdsh() {
    local container
    container=$(docker ps --format '{{.Names}}' | fzf --preview 'docker inspect {}')
    [[ -n "$container" ]] && docker exec -it "$container" sh
}

# Docker logs
fdl() {
    local container
    container=$(docker ps -a --format '{{.Names}}' | fzf)
    [[ -n "$container" ]] && docker logs -f "$container"
}
```

### SSH Host Selection

```bash
# SSH to host from config
fssh() {
    local host
    host=$(grep "^Host " ~/.ssh/config | awk '{print $2}' | \
           fzf --preview 'grep -A5 "^Host {}" ~/.ssh/config')
    [[ -n "$host" ]] && ssh "$host"
}
```

## Recommended Configuration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Use fd for file finding (faster, respects .gitignore)
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'

# Default options
export FZF_DEFAULT_OPTS='
  --height=60%
  --layout=reverse
  --border=rounded
  --info=inline
  --preview-window=right:50%:hidden
  --bind ctrl-/:toggle-preview
  --bind ctrl-a:select-all
  --bind ctrl-d:deselect-all
'

# Ctrl+T: File preview with bat
export FZF_CTRL_T_OPTS="
  --preview 'bat --color=always --style=numbers --line-range :500 {}'
"

# Alt+C: Directory preview with eza
export FZF_ALT_C_OPTS="
  --preview 'eza --tree --color=always --level=2 {} | head -200'
"

# Ctrl+R: History search
export FZF_CTRL_R_OPTS="
  --preview 'echo {}'
  --preview-window down:3:hidden:wrap
  --bind 'ctrl-y:execute-silent(echo -n {2..} | pbcopy)+abort'
"
```

## Performance Tips

1. **Use fd instead of find**: Much faster, respects `.gitignore`
2. **Limit preview scope**: Use `--line-range` with bat to limit file preview
3. **Hide preview by default**: Use `--preview-window=hidden` for large directories
4. **Exclude unnecessary directories**: Use `--exclude` to skip node_modules, .git, etc.

## Troubleshooting

### Keybindings Not Working

Ensure shell integration is sourced:

```bash
# Bash
source /opt/homebrew/opt/fzf/shell/key-bindings.bash

# Zsh
source /opt/homebrew/opt/fzf/shell/key-bindings.zsh
```

### Alt+C Not Working on macOS

Option/Alt key might be mapped differently. In iTerm2:

1. Preferences > Profiles > Keys
2. Set "Left Option Key" to "Esc+"

### Preview Not Showing

Check if bat is installed:

```bash
brew install bat
```

For directory previews, check if eza is installed:

```bash
brew install eza
```

## Related Tools

- [fd](finding-files.md) - Fast file finder
- [ripgrep](modern-replacements.md#ripgrep-rg-better-grep) - Fast grep
- [bat](modern-replacements.md#bat-better-cat) - Syntax highlighting
- [eza](modern-replacements.md#eza-formerly-exa-better-ls) - Modern ls
