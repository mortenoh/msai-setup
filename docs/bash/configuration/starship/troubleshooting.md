# Troubleshooting

This guide covers common Starship issues and their solutions.

## Installation Issues

### Command Not Found

**Symptom:** `starship: command not found`

**Solutions:**

1. Verify installation:
   ```bash
   which starship
   ls /usr/local/bin/starship
   ```

2. Check PATH:
   ```bash
   echo $PATH
   ```

3. Reinstall:
   ```bash
   curl -sS https://starship.rs/install.sh | sh
   ```

4. Add to PATH manually:
   ```bash
   export PATH="/usr/local/bin:$PATH"
   ```

### Permission Denied

**Symptom:** Permission errors during installation

**Solution:**

```bash
# Use sudo with install script
curl -sS https://starship.rs/install.sh | sh -s -- --yes

# Or install to user directory
curl -sS https://starship.rs/install.sh | sh -s -- --bin-dir ~/.local/bin
```

Add `~/.local/bin` to PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Configuration Issues

### Config File Not Loading

**Symptom:** Changes to starship.toml have no effect

**Diagnosis:**

1. Check config location:
   ```bash
   echo $STARSHIP_CONFIG
   starship config
   ```

2. Verify file exists:
   ```bash
   ls -la ~/.config/starship.toml
   ```

3. Check for syntax errors:
   ```bash
   starship print-config
   ```

**Solutions:**

1. Ensure correct path:
   ```bash
   # Default location
   mkdir -p ~/.config
   touch ~/.config/starship.toml
   ```

2. Set explicit config path:
   ```bash
   export STARSHIP_CONFIG=~/.config/starship.toml
   ```

3. Restart shell or source config:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

### TOML Syntax Errors

**Symptom:** Starship shows errors or uses defaults

**Diagnosis:**

```bash
starship print-config 2>&1 | head -20
```

**Common syntax issues:**

```toml
# Wrong: Missing quotes on strings with spaces
style = bold green

# Correct
style = "bold green"

# Wrong: Using = inside section header
[git_branch = something]

# Correct
[git_branch]
something = value

# Wrong: Unclosed brackets
format = "[$branch($style)"

# Correct
format = "[$branch]($style)"
```

### Module Not Showing

**Symptom:** A module doesn't appear when expected

**Diagnosis:**

```bash
starship explain
```

**Common causes:**

1. **Module disabled:**
   ```toml
   [module_name]
   disabled = false  # Explicitly enable
   ```

2. **Detection not triggered:**
   ```bash
   # Check if files exist that trigger detection
   ls package.json  # For nodejs
   ls Cargo.toml    # For rust
   ```

3. **Not in format string:**
   ```toml
   format = """
   $directory\
   $git_branch\
   $nodejs\  # Make sure module is listed
   $character"""
   ```

4. **Conditional not met:**
   ```toml
   [hostname]
   ssh_only = true  # Only shows via SSH

   [time]
   disabled = true  # Disabled by default
   ```

## Display Issues

### Symbols Not Rendering

**Symptom:** Boxes, question marks, or wrong characters instead of symbols

**Cause:** Missing Nerd Font

**Solutions:**

1. Install a Nerd Font:
   ```bash
   # macOS
   brew tap homebrew/cask-fonts
   brew install --cask font-fira-code-nerd-font
   ```

2. Configure terminal to use the font:
   - iTerm2: Preferences > Profiles > Text > Font
   - Terminal.app: Preferences > Profiles > Font
   - VS Code: Settings > Terminal > Integrated: Font Family

3. Use text-only symbols:
   ```toml
   [git_branch]
   symbol = "git:"

   [nodejs]
   symbol = "node:"

   [python]
   symbol = "py:"
   ```

### Colors Not Showing

**Symptom:** Prompt appears in plain text without colors

**Causes:**

1. **Terminal doesn't support colors:**
   ```bash
   echo $TERM
   # Should show something like xterm-256color
   ```

2. **True color not supported:**
   ```bash
   # Test true color support
   printf "\x1b[38;2;255;100;0mTRUECOLOR\x1b[0m\n"
   ```

**Solutions:**

1. Set TERM correctly:
   ```bash
   export TERM=xterm-256color
   ```

2. Use basic colors in config:
   ```toml
   # Instead of hex colors
   style = "bold blue"
   # Not
   style = "bold #61afef"
   ```

### Prompt Appears on Wrong Line

**Symptom:** Text wrapping issues or cursor on wrong line

**Cause:** Hidden characters not properly escaped

**Solution:**

Check shell-specific escaping. The init script usually handles this, but manual configurations may need:

```bash
# Bash: \[ and \] around non-printing chars
# Zsh: %{ and %} around non-printing chars
```

Starship handles this automatically - ensure you're using the proper init:

```bash
eval "$(starship init bash)"  # or zsh, fish
```

### Garbled Output in tmux

**Symptom:** Prompt looks wrong in tmux

**Solutions:**

1. Set proper TERM in tmux:
   ```bash
   # In .tmux.conf
   set -g default-terminal "screen-256color"
   set -ga terminal-overrides ",xterm-256color:Tc"
   ```

2. Reload tmux:
   ```bash
   tmux source-file ~/.tmux.conf
   ```

## Performance Issues

### Slow Prompt

**Symptom:** Noticeable delay before prompt appears

**Diagnosis:**

```bash
starship timings
```

**Solutions:**

1. **Disable slow modules:**
   ```toml
   [git_status]
   disabled = true

   [package]
   disabled = true
   ```

2. **Reduce git_status scope:**
   ```toml
   [git_status]
   ignore_submodules = true
   ```

3. **Set command timeout:**
   ```toml
   command_timeout = 500
   ```

4. **Reduce detection:**
   ```toml
   [nodejs]
   detect_extensions = []
   detect_files = ["package.json"]
   detect_folders = []
   ```

### Very Slow in Large Repos

**Symptom:** Multi-second delay in large Git repositories

**Solutions:**

1. Disable git_status:
   ```toml
   [git_status]
   disabled = true
   ```

2. Configure Git for large repos:
   ```bash
   git config core.commitGraph true
   git config gc.writeCommitGraph true
   git commit-graph write --reachable
   ```

3. Use sparse checkout for very large repos

## Shell-Specific Issues

### Bash Completion Broken

**Symptom:** Tab completion stops working after enabling Starship

**Solution:**

Ensure Starship init is at the END of .bashrc, after completion setup:

```bash
# Load completions first
source /etc/bash_completion

# Starship LAST
eval "$(starship init bash)"
```

### Zsh Slow Startup

**Symptom:** Shell takes long to start

**Diagnosis:**

```bash
time zsh -i -c exit
```

**Solutions:**

1. Use async loading (with zinit or similar)

2. Profile startup:
   ```bash
   zsh -xv 2>&1 | head -100
   ```

3. Compile Starship init:
   ```bash
   # In .zshrc before eval
   starship init zsh > ~/.config/starship/init.zsh
   source ~/.config/starship/init.zsh
   ```

### Fish Issues

**Symptom:** Starship not loading in Fish

**Solution:**

Ensure init is in the right file:

```fish
# ~/.config/fish/config.fish
starship init fish | source
```

## Git Issues

### Git Branch Not Showing

**Symptom:** No branch displayed in Git repo

**Diagnosis:**

```bash
git branch
git rev-parse --git-dir
```

**Solutions:**

1. Verify you're in a Git repo
2. Check if git_branch is disabled:
   ```toml
   [git_branch]
   disabled = false
   ```

3. Ensure Git is installed and in PATH

### Wrong Git Status

**Symptom:** Status symbols incorrect or missing

**Solutions:**

1. Check actual Git status:
   ```bash
   git status
   ```

2. Verify format includes all_status:
   ```toml
   [git_status]
   format = '[$all_status$ahead_behind]($style) '
   ```

3. Check individual status symbols:
   ```toml
   [git_status]
   untracked = "?"
   modified = "!"
   staged = "+"
   # etc.
   ```

## Custom Module Issues

### Custom Command Not Working

**Symptom:** Custom module doesn't appear or shows wrong output

**Diagnosis:**

1. Test command manually:
   ```bash
   # Run the exact command from your config
   echo $(your-command)
   ```

2. Check `when` condition:
   ```bash
   # Test the when condition
   test -f package.json && echo "would show"
   ```

**Solutions:**

1. Ensure command is available:
   ```toml
   [custom.mymodule]
   command = "/full/path/to/command"
   ```

2. Fix when condition:
   ```toml
   [custom.mymodule]
   # Use proper shell syntax
   when = "command -v mycommand >/dev/null"
   ```

3. Specify shell:
   ```toml
   [custom.mymodule]
   shell = ["bash", "-c"]
   ```

## Getting Help

### Generate Bug Report

```bash
starship bug-report
```

This generates diagnostic information including:

- Starship version
- Shell information
- Configuration
- Environment variables

### Check Version

```bash
starship --version
```

### Official Resources

- [GitHub Issues](https://github.com/starship/starship/issues)
- [Discord Community](https://discord.gg/starship)
- [Documentation](https://starship.rs/)

### Debugging Steps

1. **Check explain output:**
   ```bash
   starship explain
   ```

2. **View timings:**
   ```bash
   starship timings
   ```

3. **Print config:**
   ```bash
   starship print-config
   ```

4. **Enable logging:**
   ```bash
   STARSHIP_LOG=trace starship prompt
   ```

5. **Test minimal config:**
   ```bash
   # Backup current config
   mv ~/.config/starship.toml ~/.config/starship.toml.bak

   # Test with empty config
   touch ~/.config/starship.toml

   # Restart shell and check if issue persists
   ```
