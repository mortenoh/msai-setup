# Keyboard Shortcuts

Essential keyboard shortcuts for efficient command-line editing. These work in bash's default Emacs mode.

## Movement

| Shortcut | Action |
|----------|--------|
| `Ctrl+A` | Move to beginning of line |
| `Ctrl+E` | Move to end of line |
| `Ctrl+F` | Move forward one character |
| `Ctrl+B` | Move backward one character |
| `Alt+F` | Move forward one word |
| `Alt+B` | Move backward one word |
| `Ctrl+XX` | Toggle between start and current position |

## Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+D` | Delete character under cursor (or logout if empty) |
| `Ctrl+H` | Delete character before cursor (backspace) |
| `Ctrl+W` | Delete word before cursor |
| `Alt+D` | Delete word after cursor |
| `Ctrl+K` | Delete from cursor to end of line |
| `Ctrl+U` | Delete from cursor to beginning of line |
| `Ctrl+Y` | Paste (yank) last deleted text |
| `Alt+Y` | Rotate through kill ring (after Ctrl+Y) |
| `Ctrl+T` | Swap current and previous character |
| `Alt+T` | Swap current and previous word |
| `Alt+U` | Uppercase word |
| `Alt+L` | Lowercase word |
| `Alt+C` | Capitalize word |

## History

| Shortcut | Action |
|----------|--------|
| `Ctrl+P` | Previous command (same as Up arrow) |
| `Ctrl+N` | Next command (same as Down arrow) |
| `Ctrl+R` | Reverse search history |
| `Ctrl+S` | Forward search history |
| `Ctrl+G` | Cancel search |
| `Alt+.` | Insert last argument of previous command |
| `Alt+N Alt+.` | Insert Nth argument of previous command |
| `!!` | Repeat last command |
| `!$` | Last argument of last command |
| `!*` | All arguments of last command |
| `!cmd` | Most recent command starting with 'cmd' |
| `!?str` | Most recent command containing 'str' |
| `^old^new` | Replace 'old' with 'new' in last command |

## Control

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current command / SIGINT |
| `Ctrl+Z` | Suspend current process / SIGTSTP |
| `Ctrl+D` | End of input (logout if empty line) |
| `Ctrl+L` | Clear screen |
| `Ctrl+S` | Stop output (freeze terminal) |
| `Ctrl+Q` | Resume output (unfreeze terminal) |
| `Ctrl+\` | Quit / SIGQUIT |

## Completion

| Shortcut | Action |
|----------|--------|
| `Tab` | Auto-complete |
| `Tab Tab` | Show all completions |
| `Alt+?` | Show completions (same as Tab Tab) |
| `Alt+*` | Insert all completions |
| `Alt+/` | Complete filename |
| `Ctrl+X /` | List possible filename completions |
| `Alt+~` | Complete username |
| `Alt+@` | Complete hostname |
| `Alt+$` | Complete variable |
| `Alt+!` | Complete command |

## Misc

| Shortcut | Action |
|----------|--------|
| `Ctrl+_` | Undo |
| `Ctrl+X Ctrl+E` | Edit command in $EDITOR |
| `Alt+#` | Comment out line and execute |
| `Ctrl+V` | Insert next character literally |
| `Ctrl+X Ctrl+V` | Display version |

## History Expansion

| Syntax | Meaning |
|--------|---------|
| `!!` | Last command |
| `!n` | Command number n |
| `!-n` | n commands ago |
| `!string` | Most recent command starting with string |
| `!?string` | Most recent command containing string |
| `!!:$` | Last argument of last command |
| `!!:0` | First word (command) of last command |
| `!!:n` | nth argument of last command |
| `!!:n-m` | Arguments n through m |
| `!!:*` | All arguments |
| `!!:s/old/new/` | Substitute in last command |
| `!$` | Last argument (shorthand) |
| `!^` | First argument |
| `!*` | All arguments |

## Examples

### Quick Editing

```bash
$ echo "hello world"
# Cursor at end, want to change "hello" to "hi"
# Press Ctrl+A (go to start)
# Press Alt+D (delete word)
# Type "hi"
$ hi "hello world"
```

### Command History

```bash
# Run previous command
$ !!

# Run previous command with sudo
$ sudo !!

# Replace text in previous command
$ echo hello
$ ^hello^goodbye       # Runs: echo goodbye

# Use last argument
$ mkdir /long/path/to/directory
$ cd !$                # cd /long/path/to/directory

# Use all arguments from last command
$ touch file1 file2 file3
$ rm !*                # rm file1 file2 file3
```

### Reverse Search

```bash
# Press Ctrl+R
(reverse-i-search)`git': git push origin main
# Keep pressing Ctrl+R for more matches
# Press Enter to execute, or Right arrow to edit
```

### Edit Long Command

```bash
$ very-long-command --with --many --options
# Press Ctrl+X Ctrl+E
# Opens in $EDITOR
# Save and exit to execute
```

## Vi Mode

Switch to vi-style editing:

```bash
set -o vi
```

### Vi Mode Shortcuts

| Mode | Shortcut | Action |
|------|----------|--------|
| Insert | `Esc` | Switch to command mode |
| Command | `i` | Insert mode |
| Command | `a` | Append mode |
| Command | `0` | Beginning of line |
| Command | `$` | End of line |
| Command | `w` | Forward word |
| Command | `b` | Backward word |
| Command | `x` | Delete character |
| Command | `dw` | Delete word |
| Command | `dd` | Delete line |
| Command | `k` | Previous history |
| Command | `j` | Next history |
| Command | `/` | Search history |
| Command | `n` | Next search result |
| Command | `N` | Previous search result |

Return to Emacs mode:

```bash
set -o emacs
```

## Configure Readline

Create `~/.inputrc` for custom bindings:

```bash
# ~/.inputrc

# Case-insensitive completion
set completion-ignore-case on

# Show all matches on ambiguous completion
set show-all-if-ambiguous on

# Append slash to directory names
set mark-directories on

# Color for completion
set colored-stats on

# Don't ring bell
set bell-style none

# Custom bindings
"\e[A": history-search-backward    # Up arrow - search history
"\e[B": history-search-forward     # Down arrow - search history
```

Reload:

```bash
bind -f ~/.inputrc
```

## macOS Terminal Notes

Some shortcuts may not work due to terminal app settings:

- **Alt key**: In Terminal.app, use `Esc` instead of `Alt`, or enable "Use Option as Meta key" in Preferences
- **iTerm2**: Preferences > Profiles > Keys > Left Option Key: Esc+

## Try It

1. Line movement:
   - Type a long command
   - Press `Ctrl+A` (start), `Ctrl+E` (end)
   - Press `Alt+B`, `Alt+F` (word movement)

2. Editing:
   - Type `echo hello world`
   - Press `Ctrl+W` (delete word)
   - Press `Ctrl+Y` (paste back)

3. History:
   - Press `Ctrl+R`, type `git`
   - Press `Ctrl+R` again for more matches
   - Press `Enter` or `Ctrl+G` to cancel

4. Last argument:
   - Run `ls /some/path`
   - Type `cd ` then press `Alt+.`
