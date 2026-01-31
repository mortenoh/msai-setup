# Dotfiles

Dotfiles are configuration files that start with a dot (`.`), making them hidden by default. Understanding which files are loaded when is crucial for proper shell configuration.

## Key Files

| File | Purpose | When Loaded |
|------|---------|-------------|
| `.bash_profile` | Login shell config | SSH, new terminal (macOS) |
| `.bashrc` | Interactive shell config | New bash instance |
| `.profile` | Generic login config | Login shells (sh compatible) |
| `.bash_logout` | Cleanup commands | Logout from login shell |

## Login vs Non-Login Shells

### Login Shell

A login shell is started when you:

- Log in via SSH
- Log in at a console
- Open Terminal.app on macOS (by default)
- Run `bash --login` or `bash -l`

Login shells read:

1. `/etc/profile`
2. First of: `~/.bash_profile`, `~/.bash_login`, or `~/.profile`

### Non-Login (Interactive) Shell

A non-login interactive shell is started when you:

- Open a new tab in most Linux terminals
- Run `bash` from another shell
- Open a subshell

Non-login shells read:

1. `/etc/bash.bashrc` (Linux) or `/etc/bashrc` (some systems)
2. `~/.bashrc`

### Visual Summary

```
┌─────────────────────────────────────────────────┐
│                   Login Shell                    │
│  ┌─────────────────────────────────────────┐    │
│  │  /etc/profile                            │    │
│  │  ~/.bash_profile OR ~/.profile           │    │
│  │       │                                  │    │
│  │       └── sources ~/.bashrc (recommended)│    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              Non-Login Interactive              │
│  ┌─────────────────────────────────────────┐    │
│  │  ~/.bashrc                               │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## Recommended Structure

### ~/.bash_profile

Keep this minimal - just source `.bashrc`:

```bash
# ~/.bash_profile

# Load .bashrc if it exists
if [[ -f ~/.bashrc ]]; then
    source ~/.bashrc
fi

# Login-specific settings (rare)
# Example: start ssh-agent once at login
```

### ~/.bashrc

Main configuration file:

```bash
# ~/.bashrc

# Exit if not interactive
[[ $- != *i* ]] && return

# ──────────────────────────────────────────────
# Shell Options
# ──────────────────────────────────────────────

shopt -s histappend     # Append to history
shopt -s checkwinsize   # Update LINES/COLUMNS
shopt -s globstar       # ** for recursive glob (bash 4+)
shopt -s cdspell        # Autocorrect cd typos

# ──────────────────────────────────────────────
# History
# ──────────────────────────────────────────────

HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoreboth:erasedups

# ──────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────

export EDITOR=vim
export VISUAL=vim
export PAGER=less

# ──────────────────────────────────────────────
# Path
# ──────────────────────────────────────────────

export PATH="$HOME/.local/bin:$PATH"

# ──────────────────────────────────────────────
# Source additional files
# ──────────────────────────────────────────────

for file in ~/.bash_{aliases,functions,prompt}; do
    [[ -r "$file" ]] && source "$file"
done
unset file
```

## Modular Configuration

Split configuration into logical files:

```
~/.bashrc              # Main config, sources others
~/.bash_aliases        # All aliases
~/.bash_functions      # All functions
~/.bash_prompt         # Prompt configuration
~/.bash_local          # Machine-specific (not in git)
```

### ~/.bash_aliases

```bash
# ~/.bash_aliases

# Navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ~='cd ~'

# Listing
alias ls='ls --color=auto'
alias ll='ls -lah'
alias la='ls -A'

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Git
alias g='git'
alias gs='git status'
alias gc='git commit'
```

### ~/.bash_functions

```bash
# ~/.bash_functions

# Create directory and cd into it
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# Extract any archive
extract() {
    if [[ -f "$1" ]]; then
        case "$1" in
            *.tar.bz2) tar xjf "$1" ;;
            *.tar.gz)  tar xzf "$1" ;;
            *.tar.xz)  tar xJf "$1" ;;
            *.bz2)     bunzip2 "$1" ;;
            *.gz)      gunzip "$1" ;;
            *.tar)     tar xf "$1" ;;
            *.tbz2)    tar xjf "$1" ;;
            *.tgz)     tar xzf "$1" ;;
            *.zip)     unzip "$1" ;;
            *.Z)       uncompress "$1" ;;
            *)         echo "Unknown format: $1" ;;
        esac
    else
        echo "Not a file: $1"
    fi
}
```

### ~/.bash_local

Machine-specific configuration (don't commit to git):

```bash
# ~/.bash_local

# Work-specific paths
export PATH="/opt/company-tools/bin:$PATH"

# API keys (better: use a secrets manager)
export API_KEY="xxx"
```

Source it at the end of `.bashrc`:

```bash
[[ -f ~/.bash_local ]] && source ~/.bash_local
```

## Checking Shell Type

In scripts, detect shell type:

```bash
# Is this a login shell?
shopt -q login_shell && echo "Login" || echo "Non-login"

# Is this interactive?
[[ $- == *i* ]] && echo "Interactive" || echo "Non-interactive"
```

## System-Wide Configuration

| File | Purpose |
|------|---------|
| `/etc/profile` | System-wide login shell config |
| `/etc/bash.bashrc` | System-wide interactive shell config |
| `/etc/bashrc` | Alternative location (RHEL/CentOS) |
| `/etc/profile.d/*.sh` | Modular system-wide scripts |

These are read before user dotfiles.

## Platform Differences

### macOS

- Terminal.app opens **login shells** by default
- System uses zsh as default (since Catalina)
- Bash 3.2 included; Bash 5.x via Homebrew

Configure Terminal.app for non-login shells:

Preferences > General > Shells open with: Command `/bin/bash`

### Linux

- Most terminals open **non-login** interactive shells
- Login via console or SSH opens login shell
- Usually has Bash 5.x

### Windows (WSL/Git Bash)

- Similar to Linux behavior
- May have additional files like `.bash_profile.local`

## Debugging Configuration

### See What's Being Read

Add to top of each file:

```bash
echo "Loading ~/.bashrc"
```

### Trace Execution

```bash
bash -x          # Start with tracing
```

Or within a session:

```bash
set -x           # Enable tracing
# do things
set +x           # Disable tracing
```

### Start Fresh

```bash
env -i bash --noprofile --norc
```

## Common Problems

### Changes Don't Take Effect

After editing, reload:

```bash
source ~/.bashrc
# or
. ~/.bashrc
```

### PATH Gets Longer Each Time

Add PATH entries only once:

```bash
[[ ":$PATH:" != *":/new/path:"* ]] && export PATH="/new/path:$PATH"
```

### Bashrc Loaded Twice

Check for multiple source calls in `.bash_profile`.

### Interactive Check Missing

Non-interactive scripts might source `.bashrc`. Guard with:

```bash
# At top of .bashrc
[[ $- != *i* ]] && return
```

## Version Control

Keep dotfiles in git:

```bash
# Initialize dotfiles repo
cd ~
git init --bare ~/.dotfiles

# Alias for managing
alias dotfiles='git --git-dir=$HOME/.dotfiles --work-tree=$HOME'

# Add files
dotfiles add .bashrc
dotfiles commit -m "Add bashrc"
```

Or use a tool like `chezmoi` or `yadm`.

## Try It

1. Check current shell type:
   ```bash
   shopt -q login_shell && echo "Login" || echo "Non-login"
   [[ $- == *i* ]] && echo "Interactive"
   ```

2. Create modular structure:
   ```bash
   # Create separate alias file
   echo 'alias hello="echo Hello from bash_aliases"' > ~/.bash_aliases

   # Source it from .bashrc
   echo '[[ -f ~/.bash_aliases ]] && source ~/.bash_aliases' >> ~/.bashrc

   # Reload and test
   source ~/.bashrc
   hello
   ```

3. Test login vs non-login:
   ```bash
   # Start login shell
   bash --login
   exit

   # Start non-login shell
   bash
   exit
   ```

## Summary

- Use `.bash_profile` for login shells, have it source `.bashrc`
- Put all interactive configuration in `.bashrc`
- Split configuration into modular files
- Use `.bash_local` for machine-specific settings
- Guard `.bashrc` with interactive check
- Version control your dotfiles
