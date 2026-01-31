# Git Modules

Starship provides comprehensive Git integration through several modules. Together, they display branch information, repository state, and working tree status directly in your prompt.

## Git Modules Overview

| Module | Purpose | Example Output |
|--------|---------|----------------|
| `git_branch` | Current branch name | `main` |
| `git_commit` | Current commit hash/tag | `abc1234` |
| `git_state` | Repository state (rebase, merge) | `REBASING 2/3` |
| `git_status` | Working tree status | `[+!?]` |
| `git_metrics` | Lines added/deleted | `+10 -5` |

## git_branch

Displays the active branch name.

### Configuration

```toml
[git_branch]
format = "on [$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"
truncation_length = 9223372036854775807
truncation_symbol = "..."
only_attached = false
always_show_remote = false
ignore_branches = []
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `symbol` | ` ` | Symbol before branch name |
| `style` | `bold purple` | Text style |
| `truncation_length` | max | Max branch name length |
| `truncation_symbol` | `...` | Symbol for truncated names |
| `only_attached` | false | Only show when attached to branch |
| `always_show_remote` | false | Always show remote branch |
| `ignore_branches` | `[]` | Branches to hide |

### Variables

| Variable | Description |
|----------|-------------|
| `branch` | Current branch name |
| `remote_name` | Remote name |
| `remote_branch` | Remote branch name |
| `symbol` | The symbol |
| `style` | The style |

### Examples

**Minimal branch display:**

```toml
[git_branch]
format = "[$branch]($style) "
symbol = ""
```

Output: `main `

**Show remote when different:**

```toml
[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
always_show_remote = true
```

Output: ` main:origin/main `

**Truncate long branch names:**

```toml
[git_branch]
truncation_length = 20
truncation_symbol = ".."
```

Output: `feature/very-long-..`

**Ignore specific branches:**

```toml
[git_branch]
ignore_branches = ["main", "master"]
```

## git_commit

Shows the current commit hash and/or tag.

### Configuration

```toml
[git_commit]
format = "[$hash$tag]($style) "
style = "bold green"
commit_hash_length = 7
only_detached = true
tag_disabled = true
tag_symbol = " "
tag_max_candidates = 0
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `commit_hash_length` | 7 | Hash display length |
| `only_detached` | true | Only show in detached HEAD |
| `tag_disabled` | true | Disable tag display |
| `tag_symbol` | ` ` | Symbol before tag |
| `tag_max_candidates` | 0 | Tags to search (0 = exact) |

### Variables

| Variable | Description |
|----------|-------------|
| `hash` | Commit hash |
| `tag` | Tag name if present |
| `style` | The style |

### Examples

**Always show commit hash:**

```toml
[git_commit]
only_detached = false
tag_disabled = false
format = "[#$hash$tag]($style) "
```

Output: `#abc1234 v1.2.3 `

**Show only when tagged:**

```toml
[git_commit]
tag_disabled = false
tag_max_candidates = 3
format = "[$tag]($style) "
```

## git_state

Shows the current repository state during operations like rebase, merge, or cherry-pick.

### Configuration

```toml
[git_state]
format = '\([$state( $progress_current/$progress_total)]($style)\) '
style = "bold yellow"
rebase = "REBASING"
merge = "MERGING"
revert = "REVERTING"
cherry_pick = "CHERRY-PICKING"
bisect = "BISECTING"
am = "AM"
am_or_rebase = "AM/REBASE"
```

### Options

All state labels are customizable:

| Option | Default | Description |
|--------|---------|-------------|
| `rebase` | `REBASING` | Rebase in progress |
| `merge` | `MERGING` | Merge in progress |
| `revert` | `REVERTING` | Revert in progress |
| `cherry_pick` | `CHERRY-PICKING` | Cherry-pick in progress |
| `bisect` | `BISECTING` | Bisect in progress |
| `am` | `AM` | `git am` in progress |
| `am_or_rebase` | `AM/REBASE` | Ambiguous state |

### Variables

| Variable | Description |
|----------|-------------|
| `state` | Current state |
| `progress_current` | Current step |
| `progress_total` | Total steps |
| `style` | The style |

### Examples

**Compact state display:**

```toml
[git_state]
format = "[$state]($style) "
rebase = "RB"
merge = "MG"
cherry_pick = "CP"
bisect = "BS"
```

Output during rebase: `RB `

**Detailed with progress:**

```toml
[git_state]
format = '[$state: $progress_current of $progress_total]($style) '
style = "bold red"
```

Output: `REBASING: 2 of 5 `

## git_status

Shows the working tree status with symbols for different states.

### Configuration

```toml
[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"
stashed = "$"
ahead = "up${count}"
behind = "down${count}"
up_to_date = ""
diverged = "div${ahead_count}${behind_count}"
conflicted = "="
deleted = "x"
renamed = "r"
modified = "!"
staged = "+"
untracked = "?"
typechanged = ""
ignore_submodules = false
```

### Status Symbols

| Option | Default | Git State |
|--------|---------|-----------|
| `conflicted` | `=` | Merge conflicts |
| `ahead` | `up` | Commits ahead of remote |
| `behind` | `down` | Commits behind remote |
| `diverged` | `div` | Both ahead and behind |
| `up_to_date` | (empty) | In sync with remote |
| `untracked` | `?` | Untracked files |
| `stashed` | `$` | Stashed changes |
| `modified` | `!` | Modified files |
| `staged` | `+` | Staged changes |
| `renamed` | `r` | Renamed files |
| `deleted` | `x` | Deleted files |

### Variables

| Variable | Description |
|----------|-------------|
| `all_status` | Combined status symbols |
| `ahead_behind` | Ahead/behind status |
| `conflicted` | Conflict count |
| `untracked` | Untracked count |
| `stashed` | Stash count |
| `modified` | Modified count |
| `staged` | Staged count |
| `renamed` | Renamed count |
| `deleted` | Deleted count |

### Examples

**Detailed with counts:**

```toml
[git_status]
format = '[$all_status$ahead_behind]($style) '
conflicted = "=${count} "
ahead = "up${count} "
behind = "dn${count} "
diverged = "div(up${ahead_count} dn${behind_count}) "
untracked = "?${count} "
stashed = "*${count} "
modified = "!${count} "
staged = "+${count} "
renamed = "r${count} "
deleted = "x${count} "
```

Output: `+2 !3 ?1 up4 `

**Minimal symbols:**

```toml
[git_status]
format = '[$all_status$ahead_behind]($style)'
ahead = "^"
behind = "v"
diverged = "^v"
conflicted = "!"
untracked = "?"
modified = "*"
staged = "+"
renamed = ">"
deleted = "x"
stashed = "$"
```

Output: `+*?^`

**Clean/dirty indicator only:**

```toml
[git_status]
format = '([$all_status]($style))'
conflicted = "dirty"
ahead = ""
behind = ""
diverged = ""
untracked = "dirty"
stashed = ""
modified = "dirty"
staged = "dirty"
renamed = "dirty"
deleted = "dirty"
style = "red"
```

Output: `dirty` (or nothing if clean)

## git_metrics

Shows lines added and deleted since the last commit.

### Configuration

```toml
[git_metrics]
disabled = true
format = "([+$added]($added_style) )([-$deleted]($deleted_style) )"
added_style = "bold green"
deleted_style = "bold red"
only_nonzero_diffs = true
ignore_submodules = false
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `disabled` | true | Disabled by default |
| `added_style` | `bold green` | Style for additions |
| `deleted_style` | `bold red` | Style for deletions |
| `only_nonzero_diffs` | true | Hide if no changes |
| `ignore_submodules` | false | Ignore submodule changes |

### Variables

| Variable | Description |
|----------|-------------|
| `added` | Lines added |
| `deleted` | Lines deleted |

### Examples

**Enable git metrics:**

```toml
[git_metrics]
disabled = false
format = "[+$added/-$deleted]($added_style) "
```

Output: `+15/-3 `

## Complete Git Configuration

A comprehensive Git setup for your prompt:

```toml
# Include Git in format
format = """
$directory\
$git_branch\
$git_commit\
$git_state\
$git_metrics\
$git_status\
$line_break\
$character"""

[git_branch]
format = "on [$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"
truncation_length = 30

[git_commit]
format = "[($hash$tag)]($style) "
style = "bold green"
only_detached = false
tag_disabled = false
tag_symbol = " "

[git_state]
format = '\([$state( $progress_current/$progress_total)]($style)\) '
style = "bold yellow"

[git_metrics]
disabled = false
format = "([+$added]($added_style) )([-$deleted]($deleted_style) )"
added_style = "bold green"
deleted_style = "bold red"

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"
ahead = "up${count}"
behind = "dn${count}"
diverged = "div"
conflicted = "conflict${count}"
untracked = "?${count}"
stashed = "*${count}"
modified = "!${count}"
staged = "+${count}"
renamed = "r${count}"
deleted = "x${count}"
```

**Example output:**

```
~/projects/app on  main (abc1234  v1.0.0) (+15 -3) [+2 !1 ?3 up4]
->
```

## Performance Considerations

Git status can be slow in large repositories. Options to improve performance:

```toml
[git_status]
# Skip submodule status (faster)
ignore_submodules = true

[git_metrics]
# Disable if not needed
disabled = true
```

For very large repositories, consider disabling git_status entirely:

```toml
[git_status]
disabled = true
```

## Troubleshooting

### Module not showing

1. Verify you're in a Git repository: `git status`
2. Check if module is disabled in config
3. Run `starship explain` to see module state

### Status symbols not appearing

- Ensure changes exist: `git status`
- Check format string includes `$all_status`
- Verify style is visible against terminal background

### Slow prompt in large repos

- Enable `ignore_submodules = true`
- Disable `git_metrics`
- Consider `git_status.disabled = true` for very large repos

See [Troubleshooting](troubleshooting.md) for more solutions.
