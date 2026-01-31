# lazygit

lazygit is a terminal UI for git commands, providing a visual interface for staging, committing, branching, and more.

## Installation

### macOS (Homebrew)

```bash
brew install lazygit
```

### Linux

```bash
# Ubuntu/Debian (via PPA)
LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
curl -Lo lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
tar xf lazygit.tar.gz lazygit
sudo install lazygit /usr/local/bin

# Arch Linux
pacman -S lazygit
```

### Verify Installation

```bash
lazygit --version
```

## Basic Usage

### Launch

```bash
# In a git repository
lazygit

# Short alias
lg
```

### Interface Layout

```
+------------------+------------------+
|     Status       |    Staged        |
|     (1)          |    Changes (3)   |
+------------------+------------------+
|     Files        |    Main Panel    |
|     (2)          |    (5)           |
+------------------+------------------+
|   Local Branches |                  |
|     (3)          |                  |
+------------------+                  |
|   Remote Branches|                  |
|     (4)          |                  |
+------------------+------------------+
```

### Panel Navigation

| Key | Action |
|-----|--------|
| ++1++ - ++5++ | Jump to panel |
| ++h++ / ++l++ | Previous/next panel |
| ++j++ / ++k++ | Move up/down in list |
| ++bracket-left++ / ++bracket-right++ | Scroll main panel |
| ++tab++ | Switch focus |
| ++question++ | Show keybindings |

## Files Panel

### Staging

| Key | Action |
|-----|--------|
| ++space++ | Stage/unstage file |
| ++a++ | Stage all |
| ++d++ | Discard changes |
| ++e++ | Edit file |
| ++o++ | Open file in editor |
| ++i++ | Add to .gitignore |
| ++enter++ | Stage individual hunks |

### Viewing Changes

| Key | Action |
|-----|--------|
| ++enter++ | View file diff |
| ++ctrl+o++ | Copy file path |

## Staging Individual Hunks

Press ++enter++ on a file to enter hunk staging mode:

| Key | Action |
|-----|--------|
| ++space++ | Stage/unstage hunk |
| ++v++ | Toggle range select |
| ++a++ | Stage/unstage all hunks |
| ++esc++ | Return to files |

## Commits

### Creating Commits

| Key | Action |
|-----|--------|
| ++c++ | Commit |
| ++shift+c++ | Commit with editor |
| ++shift+a++ | Amend last commit |
| ++ctrl+o++ | Copy commit SHA |

### Viewing Commits

| Key | Action |
|-----|--------|
| ++enter++ | View commit diff |
| ++o++ | Open commit in browser |
| ++y++ | Copy commit SHA |

### Commit Operations

| Key | Action |
|-----|--------|
| ++r++ | Reword commit |
| ++d++ | Drop commit |
| ++e++ | Edit commit |
| ++s++ | Squash into previous |
| ++f++ | Fixup into previous |
| ++shift+p++ | Pick commit (for rebase) |

## Branches

### Branch Navigation

| Key | Action |
|-----|--------|
| ++space++ | Checkout branch |
| ++n++ | New branch |
| ++d++ | Delete branch |
| ++shift+m++ | Merge into current |
| ++r++ | Rebase onto current |
| ++shift+r++ | Rename branch |
| ++f++ | Fetch branch |
| ++u++ | Set upstream |

### Creating Branches

1. Press ++n++ for new branch
2. Type branch name
3. Press ++enter++

### Merging

1. Select source branch
2. Press ++shift+m++ to merge into current branch

### Rebasing

1. Select branch to rebase onto
2. Press ++r++ to start rebase

## Stash

| Key | Action |
|-----|--------|
| ++s++ | Stash changes |
| ++shift+s++ | Stash staged only |
| ++space++ | Apply stash |
| ++g++ | Pop stash |
| ++d++ | Drop stash |

## Remotes

| Key | Action |
|-----|--------|
| ++f++ | Fetch |
| ++shift+f++ | Fetch all |
| ++p++ | Pull |
| ++shift+p++ | Push |
| ++space++ | Checkout remote branch |

### Force Push

Press ++shift+p++ then select "Force push" when needed.

## Interactive Rebase

Start interactive rebase:

1. In commits panel, select base commit
2. Press ++e++ to start interactive rebase

During rebase:

| Key | Action |
|-----|--------|
| ++p++ | Pick |
| ++r++ | Reword |
| ++e++ | Edit |
| ++s++ | Squash |
| ++f++ | Fixup |
| ++d++ | Drop |
| ++ctrl+j++ / ++ctrl+k++ | Move commit |
| ++m++ | Continue rebase |

## Search

| Key | Action |
|-----|--------|
| ++slash++ | Start search |
| ++n++ | Next match |
| ++shift+n++ | Previous match |

## Configuration

### Config File Location

```
~/.config/lazygit/config.yml
```

### Example Configuration

```yaml
gui:
  theme:
    lightTheme: false
    activeBorderColor:
      - green
      - bold
    inactiveBorderColor:
      - white
  showFileTree: true
  showRandomTip: false
  showCommandLog: true

git:
  paging:
    colorArg: always
    pager: delta --dark --paging=never
  commit:
    signOff: false
  merging:
    manualCommit: false
    args: ""
  pull:
    mode: rebase
  autoFetch: true
  autoRefresh: true
  branchLogCmd: "git log --graph --color=always --abbrev-commit --decorate --date=relative --pretty=medium {{branchName}} --"

os:
  editCommand: nvim
  editCommandTemplate: "{{editor}} {{filename}}"

keybinding:
  universal:
    quit: q
    quit-alt1: <c-c>
    return: <esc>
    scrollUpMain: <pgup>
    scrollDownMain: <pgdown>
```

### Editor Integration

```yaml
os:
  editCommand: nvim
  # Or for VS Code
  # editCommand: code
  # editCommandTemplate: "{{editor}} --wait {{filename}}"
```

### Use Delta for Diffs

```yaml
git:
  paging:
    colorArg: always
    pager: delta --dark --paging=never
```

## Custom Commands

Add custom commands in config:

```yaml
customCommands:
  - key: "<c-f>"
    command: "git fetch --all"
    context: "global"
    description: "Fetch all remotes"

  - key: "<c-r>"
    command: "gh pr create --fill"
    context: "global"
    description: "Create PR"

  - key: "C"
    command: "git commit -m '{{index .PromptResponses 0}}'"
    context: "files"
    prompts:
      - type: "input"
        title: "Commit message"
```

## Editor Integration

### Neovim/LazyVim

lazygit is integrated with LazyVim. Press ++space+g+g++ to open.

### VS Code

Install "lazygit" extension or use terminal:

```json
{
  "terminal.integrated.profiles.osx": {
    "lazygit": {
      "path": "lazygit"
    }
  }
}
```

### Zed

Use terminal panel:

```bash
lazygit
```

## Recommended Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias lg='lazygit'
alias lzg='lazygit'
```

## Global Keybindings

| Key | Action |
|-----|--------|
| ++question++ | Show all keybindings |
| ++x++ | Show command menu |
| ++z++ | Undo |
| ++ctrl+z++ | Redo |
| ++escape++ | Cancel/return |
| ++q++ | Quit |
| ++ctrl+c++ | Quit |
| ++plus++ | Expand diff context |
| ++minus++ | Shrink diff context |

## Common Workflows

### Quick Commit

1. Stage files: ++space++ on each or ++a++ for all
2. Commit: ++c++
3. Type message, ++enter++

### Fix Last Commit

1. Make changes
2. Stage: ++space++
3. Amend: ++shift+a++

### Cherry Pick

1. Go to commits panel
2. Select commit, press ++c++ to copy
3. Switch to target branch
4. Press ++shift+v++ to paste (cherry-pick)

### Resolve Conflicts

1. Conflicts shown in files panel
2. Press ++enter++ to view conflict
3. Choose resolution:
   - ++b++ for both
   - ++o++ for ours
   - ++t++ for theirs
4. Stage resolved files
5. Continue merge/rebase

### Clean Up Branches

1. Go to branches panel
2. Select old branch
3. Press ++d++ to delete

## Troubleshooting

### Reset Config

```bash
rm ~/.config/lazygit/config.yml
```

### Increase Log Verbosity

```bash
lazygit --debug
```

### Update

```bash
brew upgrade lazygit
```
