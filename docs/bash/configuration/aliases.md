# Aliases

Aliases are shortcuts for frequently used commands. They save typing and can add default options to commands.

## Basic Syntax

```bash
alias name='command'
alias name="command with $variable"
```

## Creating Aliases

### Simple Shortcuts

```bash
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias cls='clear'
```

### Adding Default Options

```bash
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias df='df -h'
alias du='du -h'
alias free='free -h'
```

### Safety Aliases

```bash
alias rm='rm -i'           # Confirm before delete
alias cp='cp -i'           # Confirm before overwrite
alias mv='mv -i'           # Confirm before overwrite
alias ln='ln -i'           # Confirm before overwrite
```

### Navigation

```bash
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ~='cd ~'
alias -- -='cd -'          # -- needed for -
```

## Working with Aliases

### List All Aliases

```bash
alias
```

```
alias ll='ls -lah'
alias la='ls -A'
...
```

### Show Specific Alias

```bash
alias ll
```

```
alias ll='ls -lah'
```

### Remove Alias

```bash
unalias ll
```

### Remove All Aliases

```bash
unalias -a
```

### Bypass Alias

Use backslash, quotes, or full path:

```bash
\rm file.txt              # Bypass rm alias
'rm' file.txt             # Also bypasses
/bin/rm file.txt          # Use full path
command rm file.txt       # Use command builtin
```

## Alias vs Function

Aliases have limitations - use functions when you need:

- Arguments in the middle of command
- Multiple commands
- Conditional logic

### Alias Limitation

Arguments only go at the end:

```bash
alias greptxt='grep pattern'  # Args appended
greptxt file.txt              # grep pattern file.txt
```

Cannot put arguments elsewhere:

```bash
# This doesn't work as expected
alias myfind='find . -name "*" -type'
# Need a function instead
```

### When to Use Functions

```bash
# Function - can place arguments anywhere
myfind() {
    find . -name "*.$1" -type f
}
myfind txt    # find . -name "*.txt" -type f
```

See [Functions](functions.md) for more.

## Common Alias Collections

### Directory Listing

```bash
# Colors and formatting
alias ls='ls --color=auto'
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias lt='ls -ltr'          # Sort by time
alias lS='ls -lhS'          # Sort by size
```

### Git Aliases

```bash
alias g='git'
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gd='git diff'
alias gco='git checkout'
alias gb='git branch'
alias glog='git log --oneline --graph'
```

### Docker Aliases

```bash
alias d='docker'
alias dc='docker compose'
alias dps='docker ps'
alias dpsa='docker ps -a'
alias di='docker images'
alias dex='docker exec -it'
alias dlog='docker logs -f'
alias drm='docker rm'
alias drmi='docker rmi'
```

### System Commands

```bash
alias h='history'
alias j='jobs -l'
alias path='echo $PATH | tr ":" "\n"'
alias now='date +"%Y-%m-%d %H:%M:%S"'
alias week='date +%V'
alias ports='netstat -tuln'
```

### Network Aliases

```bash
alias ip='curl -s ifconfig.me'
alias localip='ipconfig getifaddr en0'  # macOS
alias ping='ping -c 5'
alias wget='wget -c'                     # Resume downloads
```

### macOS Specific

```bash
alias showfiles='defaults write com.apple.finder AppleShowAllFiles -bool true && killall Finder'
alias hidefiles='defaults write com.apple.finder AppleShowAllFiles -bool false && killall Finder'
alias cleanup='find . -type f -name "*.DS_Store" -delete'
alias flushdns='sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder'
```

### Quick Edits

```bash
alias bashrc='${EDITOR:-vim} ~/.bashrc'
alias aliases='${EDITOR:-vim} ~/.bash_aliases'
alias reload='source ~/.bashrc'
```

## Modern Tool Aliases

Replace classic tools with modern alternatives:

```bash
# If installed, use modern versions
command -v eza &>/dev/null && alias ls='eza'
command -v bat &>/dev/null && alias cat='bat'
command -v rg &>/dev/null && alias grep='rg'
command -v fd &>/dev/null && alias find='fd'
command -v btop &>/dev/null && alias top='btop'
```

Or make them conditional:

```bash
if command -v eza &>/dev/null; then
    alias ls='eza'
    alias ll='eza -lah'
    alias la='eza -a'
    alias lt='eza -lah --sort=modified'
    alias tree='eza --tree'
fi
```

## Organizing Aliases

### Separate File

Create `~/.bash_aliases`:

```bash
# ~/.bash_aliases

# ──────────────────────────────────────────────
# Navigation
# ──────────────────────────────────────────────

alias ..='cd ..'
alias ...='cd ../..'

# ──────────────────────────────────────────────
# Listing
# ──────────────────────────────────────────────

alias ll='ls -lah'
alias la='ls -A'

# ──────────────────────────────────────────────
# Git
# ──────────────────────────────────────────────

alias gs='git status'
alias gc='git commit'
```

Source it from `.bashrc`:

```bash
[[ -f ~/.bash_aliases ]] && source ~/.bash_aliases
```

### Grouped by Purpose

```bash
# ~/.bash_aliases.d/git.sh
# ~/.bash_aliases.d/docker.sh
# ~/.bash_aliases.d/navigation.sh
```

Source all:

```bash
for file in ~/.bash_aliases.d/*.sh; do
    [[ -r "$file" ]] && source "$file"
done
```

## Platform-Specific Aliases

Handle differences between Linux and macOS:

```bash
case "$(uname -s)" in
    Darwin)
        alias ls='ls -G'                    # macOS colors
        alias flushdns='sudo dscacheutil -flushcache'
        ;;
    Linux)
        alias ls='ls --color=auto'          # GNU colors
        alias open='xdg-open'               # Like macOS open
        ;;
esac
```

## Debugging Aliases

### Check What a Command Resolves To

```bash
type ls
```

```
ls is aliased to `ls --color=auto'
```

```bash
type -a ls
```

```
ls is aliased to `ls --color=auto'
ls is /bin/ls
```

### See Expansion

```bash
alias ls
```

```
alias ls='ls --color=auto'
```

## Common Mistakes

### Spaces Around `=`

```bash
alias name = 'command'    # Wrong
alias name='command'      # Correct
```

### Forgetting Quotes

```bash
alias ll=ls -la           # Wrong - only ls is aliased
alias ll='ls -la'         # Correct
```

### Recursive Aliases

Aliases expand to themselves:

```bash
alias ls='ls --color=auto'    # OK - expands once
ls                             # Runs: ls --color=auto
```

If you need to avoid this:

```bash
alias ls='command ls --color=auto'
```

## Try It

1. Create some aliases:
   ```bash
   alias ll='ls -lah'
   alias now='date +"%Y-%m-%d %H:%M:%S"'
   alias myip='curl -s ifconfig.me'
   ```

2. Test them:
   ```bash
   ll
   now
   myip
   ```

3. List and inspect:
   ```bash
   alias
   type ll
   ```

4. Bypass an alias:
   ```bash
   \ll      # Error - ll is not a real command
   \ls -la  # Works - bypasses ls alias
   ```

5. Make permanent:
   ```bash
   echo "alias ll='ls -lah'" >> ~/.bash_aliases
   ```

## Summary

| Action | Syntax |
|--------|--------|
| Create alias | `alias name='command'` |
| List all aliases | `alias` |
| Show specific | `alias name` |
| Remove alias | `unalias name` |
| Bypass alias | `\command` or `command cmd` |

Best practices:

- Use quotes around the command
- No spaces around `=`
- Organize in separate file(s)
- Use functions for complex logic
- Check for tool existence before aliasing
