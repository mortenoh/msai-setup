# Prompt Customization

The prompt is what you see before typing commands. Customizing it can improve your workflow by showing useful information at a glance.

## Prompt Variables

| Variable | Purpose |
|----------|---------|
| `PS1` | Primary prompt (what you see) |
| `PS2` | Continuation prompt (after `\`) |
| `PS3` | Select menu prompt |
| `PS4` | Debug trace prefix |

## Basic PS1

Default prompts look like:

```
user@hostname:~$
```

Set a custom prompt:

```bash
PS1='$ '                           # Minimal
PS1='\u@\h:\w\$ '                  # user@host:path$
```

## Escape Sequences

Special sequences expand to information:

| Sequence | Meaning |
|----------|---------|
| `\u` | Username |
| `\h` | Hostname (short) |
| `\H` | Hostname (full) |
| `\w` | Working directory (full) |
| `\W` | Working directory (basename) |
| `\d` | Date (Tue May 26) |
| `\t` | Time (24h HH:MM:SS) |
| `\T` | Time (12h HH:MM:SS) |
| `\@` | Time (12h am/pm) |
| `\A` | Time (24h HH:MM) |
| `\n` | Newline |
| `\r` | Carriage return |
| `\\` | Literal backslash |
| `\$` | `$` for user, `#` for root |
| `\[` | Start non-printing sequence |
| `\]` | End non-printing sequence |
| `\!` | History number |
| `\#` | Command number |
| `\j` | Number of background jobs |

## Color Codes

### ANSI Colors

Wrap colors in `\[` and `\]` so bash knows they don't take space:

```bash
# Format: \[\e[CODEm\]
# Reset: \[\e[0m\]

RED='\[\e[31m\]'
GREEN='\[\e[32m\]'
YELLOW='\[\e[33m\]'
BLUE='\[\e[34m\]'
MAGENTA='\[\e[35m\]'
CYAN='\[\e[36m\]'
WHITE='\[\e[37m\]'
RESET='\[\e[0m\]'

PS1="${GREEN}\u${RESET}@${BLUE}\h${RESET}:${YELLOW}\w${RESET}\$ "
```

### Extended Colors

256 colors and bold/dim:

```bash
# Bold
BOLD='\[\e[1m\]'

# 256 colors: \[\e[38;5;COLORm\]
ORANGE='\[\e[38;5;208m\]'
PURPLE='\[\e[38;5;141m\]'

PS1="${BOLD}${ORANGE}\u${RESET}:${PURPLE}\w${RESET}\$ "
```

## Practical Prompt Examples

### Minimal

```bash
PS1='\$ '
```

```
$
```

### Classic

```bash
PS1='\u@\h:\w\$ '
```

```
user@host:~/projects$
```

### Colorful

```bash
PS1='\[\e[32m\]\u\[\e[0m\]@\[\e[34m\]\h\[\e[0m\]:\[\e[33m\]\w\[\e[0m\]\$ '
```

### Two-Line

```bash
PS1='\[\e[34m\]\w\[\e[0m\]\n\[\e[32m\]\u\[\e[0m\]$ '
```

```
~/projects/myapp
user$
```

### With Time

```bash
PS1='[\A] \u:\w\$ '
```

```
[14:30] user:~/projects$
```

### With Exit Code

```bash
PS1='$(if [ $? -eq 0 ]; then echo "\[\e[32m\]o\[\e[0m\]"; else echo "\[\e[31m\]x\[\e[0m\]"; fi) \w\$ '
```

Shows green `o` for success, red `x` for failure.

## Dynamic Prompts

### Using PROMPT_COMMAND

`PROMPT_COMMAND` runs before each prompt:

```bash
PROMPT_COMMAND='echo -n "$(date +%H:%M) "'
PS1='\w\$ '
```

Or use it to update PS1:

```bash
set_prompt() {
    local exit_code=$?
    local red='\[\e[31m\]'
    local green='\[\e[32m\]'
    local reset='\[\e[0m\]'

    if [[ $exit_code -eq 0 ]]; then
        PS1="${green}>${reset} "
    else
        PS1="${red}>${reset} "
    fi
}
PROMPT_COMMAND=set_prompt
```

### Git Branch in Prompt

Show current git branch:

```bash
parse_git_branch() {
    git branch 2>/dev/null | grep '^*' | sed 's/* //'
}

PS1='\w $(parse_git_branch)\$ '
```

With color and formatting:

```bash
parse_git_branch() {
    local branch
    branch=$(git branch 2>/dev/null | grep '^*' | sed 's/* //')
    [[ -n "$branch" ]] && echo "($branch) "
}

PS1='\[\e[34m\]\w\[\e[0m\] \[\e[33m\]$(parse_git_branch)\[\e[0m\]\$ '
```

```
~/projects/myapp (main) $
```

### Git Status Indicator

```bash
git_prompt() {
    local branch
    branch=$(git branch 2>/dev/null | grep '^*' | sed 's/* //')
    [[ -z "$branch" ]] && return

    local status=""
    git diff --quiet 2>/dev/null || status="*"
    git diff --cached --quiet 2>/dev/null || status="${status}+"

    echo "($branch$status) "
}

PS1='\w $(git_prompt)\$ '
```

Shows `*` for unstaged changes, `+` for staged changes.

## Starship Prompt

[Starship](https://starship.rs) is a modern, cross-shell prompt that's highly recommended:

### Install

```bash
# macOS
brew install starship

# Linux
curl -sS https://starship.rs/install.sh | sh
```

### Enable

Add to end of `~/.bashrc`:

```bash
eval "$(starship init bash)"
```

### Configure

Create `~/.config/starship.toml`:

```toml
# Minimal config
format = """
$directory$git_branch$git_status$character"""

[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"

[directory]
truncation_length = 3
truncate_to_repo = true

[git_branch]
format = "[$branch]($style) "
style = "bold yellow"

[git_status]
format = '([$all_status$ahead_behind]($style) )'
```

### Starship Advantages

- Cross-shell (bash, zsh, fish, PowerShell)
- Fast (written in Rust)
- Extensive customization
- Built-in git, language version, cloud context support
- Active development

## Common Prompt Configurations

### Developer Prompt

```bash
# Shows: user, directory, git, virtualenv
dev_prompt() {
    local git_branch
    git_branch=$(git branch 2>/dev/null | grep '^*' | sed 's/* //')

    local venv=""
    [[ -n "$VIRTUAL_ENV" ]] && venv="($(basename $VIRTUAL_ENV)) "

    PS1="${venv}\[\e[32m\]\u\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]"
    [[ -n "$git_branch" ]] && PS1+=" \[\e[33m\]($git_branch)\[\e[0m\]"
    PS1+="\$ "
}
PROMPT_COMMAND=dev_prompt
```

### Server Prompt

Highlight root and show hostname:

```bash
if [[ $EUID -eq 0 ]]; then
    PS1='\[\e[31m\]\u@\h\[\e[0m\]:\w# '
else
    PS1='\[\e[32m\]\u\[\e[0m\]@\h:\w\$ '
fi
```

### Minimal Fast Prompt

Keep it simple for speed:

```bash
PS1='\w \$ '
```

## PS2, PS3, PS4

### PS2 - Continuation

When command continues to next line:

```bash
PS2='... '
```

```bash
echo "this is \
... a continued line"
```

### PS3 - Select Menu

Used by `select` command:

```bash
PS3="Choose an option: "
select opt in "One" "Two" "Quit"; do
    echo "You chose: $opt"
    [[ $opt == "Quit" ]] && break
done
```

### PS4 - Debug Trace

Prefix for `set -x` output:

```bash
PS4='+ ${BASH_SOURCE}:${LINENO}: '
set -x
echo "debug"
set +x
```

```
+ /home/user/script.sh:10: echo debug
debug
```

## Troubleshooting

### Prompt Wraps Incorrectly

Non-printing characters must be wrapped:

```bash
# Wrong - causes wrapping issues
PS1='\e[32m\u\e[0m$ '

# Correct
PS1='\[\e[32m\]\u\[\e[0m\]$ '
```

### Prompt is Slow

Git operations can slow prompts. Cache or simplify:

```bash
# Fast git branch
__git_ps1() {
    git symbolic-ref --short HEAD 2>/dev/null
}
```

Or use Starship which is optimized for speed.

### Colors Don't Work

Check terminal supports colors:

```bash
echo $TERM       # Should be xterm-256color or similar
tput colors      # Should show 256
```

## Try It

1. Basic customization:
   ```bash
   PS1='\u:\w\$ '
   ```

2. Add colors:
   ```bash
   PS1='\[\e[32m\]\u\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]\$ '
   ```

3. Add git branch:
   ```bash
   parse_git_branch() {
       git branch 2>/dev/null | grep '^*' | sed 's/* / /'
   }
   PS1='\w$(parse_git_branch)\$ '
   ```

4. Try Starship:
   ```bash
   brew install starship
   eval "$(starship init bash)"
   ```

## Summary

| Variable | Purpose |
|----------|---------|
| `PS1` | Main prompt |
| `PS2` | Continuation prompt |
| `PS3` | Select menu prompt |
| `PS4` | Debug trace prefix |
| `PROMPT_COMMAND` | Run before each prompt |

Key escape sequences:

| Sequence | Meaning |
|----------|---------|
| `\u` | Username |
| `\h` | Hostname |
| `\w` | Full path |
| `\W` | Current directory |
| `\$` | $ or # |
| `\[...\]` | Non-printing (colors) |

For most users, **Starship** is recommended for a modern, fast, customizable prompt.
