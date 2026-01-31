# Git

Git is the distributed version control system that powers modern software development. This guide covers configuration, common workflows, and integration with tools like delta for enhanced diffs.

## Installation

### macOS (Homebrew)

```bash
brew install git git-lfs delta
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install git git-lfs
# Delta requires manual installation
cargo install git-delta
```

## Configuration

Git configuration lives in `~/.gitconfig` (global) and `.git/config` (per-repository).

### Complete Annotated Configuration

```ini
# ~/.gitconfig - Git global configuration

# ============================================
# User Identity
# ============================================
[user]
    # Your name as it appears in commits
    name = Your Name

    # Email address for commits (use your GitHub noreply email for privacy)
    email = your.email@example.com

# ============================================
# GitHub Integration
# ============================================
[github]
    # GitHub username for gh CLI and hub integration
    user = yourusername

# ============================================
# Core Settings
# ============================================
[core]
    # Default editor for commit messages, interactive rebase, etc.
    # Options: nvim, vim, code --wait, nano
    editor = nvim

    # Line ending handling:
    # - input: Convert CRLF to LF on commit (recommended for macOS/Linux)
    # - true: Convert LF to CRLF on checkout (Windows)
    # - false: No conversion
    autocrlf = input

    # Enable filesystem protection on Windows
    protectNTFS = true

    # Pager for git output (use delta for syntax highlighting)
    # pager = delta

# ============================================
# Colors
# ============================================
[color]
    # Enable colorized output in the Git UI
    ui = true

# ============================================
# Aliases - Shortcuts for Common Commands
# ============================================
[alias]
    # Status shortcuts
    st = status
    s = status --short --branch

    # Commit shortcuts
    ci = commit
    cm = commit -m
    ca = commit --amend
    can = commit --amend --no-edit

    # Checkout/switch shortcuts
    co = checkout
    sw = switch
    swc = switch -c

    # Branch operations
    br = branch
    bra = branch -a
    brd = branch -d
    brD = branch -D

    # Diff shortcuts
    d = diff
    dc = diff --cached
    ds = diff --staged

    # Log visualization
    # Graph with short hashes and decoration
    logg = log --graph --oneline --decorate --abbrev-commit

    # Log with graph for all branches
    loga = log --graph --oneline --decorate --all

    # View last N commits
    last = log -n 10 --oneline

    # Detailed log with stats
    ll = log --pretty=format:'%C(yellow)%h%Creset %s %C(cyan)<%an>%Creset %C(green)(%cr)%Creset' --abbrev-commit

    # Stash shortcuts
    ss = stash
    sp = stash pop
    sl = stash list

    # Undo operations
    unstage = reset HEAD --
    uncommit = reset --soft HEAD~1
    discard = checkout --

    # Show files in a commit
    files = diff-tree --no-commit-id --name-only -r

    # Show contributors
    contributors = shortlog --summary --numbered

    # Find commits by message
    find = log --all --grep

    # Today's commits
    today = log --since=midnight --author='Your Name' --oneline

    # Interactive add
    ai = add --interactive
    ap = add --patch

# ============================================
# Push Configuration
# ============================================
[push]
    # Push current branch to same-named remote branch
    default = current

    # Push tags along with commits
    followTags = true

    # Automatically set upstream when pushing new branches
    autoSetupRemote = true

# ============================================
# Pull Configuration
# ============================================
[pull]
    # How to reconcile divergent branches when pulling:
    # - false: merge (creates merge commits)
    # - true: rebase (linear history)
    rebase = false

# ============================================
# Fetch Configuration
# ============================================
[fetch]
    # Remove deleted remote branches on fetch
    prune = true

    # Remove deleted remote tags on fetch
    pruneTags = true

# ============================================
# Merge Configuration
# ============================================
[merge]
    # Conflict style:
    # - merge: standard 2-way markers
    # - diff3: includes original text (recommended)
    # - zdiff3: improved diff3 (Git 2.35+)
    conflictstyle = diff3

    # Default merge tool
    tool = nvim -d

# ============================================
# Diff Configuration
# ============================================
[diff]
    # Detect renames and copies
    renames = true

    # Better diff output for moved code
    indentHeuristic = true

    # Algorithm: histogram often produces cleaner diffs
    # Options: myers (default), minimal, patience, histogram
    algorithm = histogram

    # Color moved lines differently
    colorMoved = default

# ============================================
# Log Configuration
# ============================================
[log]
    # Relative dates (e.g., "2 days ago")
    date = relative

# ============================================
# Init Configuration
# ============================================
[init]
    # Default branch name for new repositories
    defaultBranch = main

# ============================================
# Credential Storage
# ============================================
[credential]
    # macOS: use Keychain
    helper = osxkeychain

    # Linux: use libsecret or cache
    # helper = libsecret
    # helper = cache --timeout=3600

# ============================================
# Rebase Configuration
# ============================================
[rebase]
    # Auto-stash before rebase and pop after
    autoStash = true

    # Auto-squash fixup! and squash! commits
    autoSquash = true

# ============================================
# Large File Storage (LFS)
# ============================================
[filter "lfs"]
    required = true
    clean = git-lfs clean -- %f
    smudge = git-lfs smudge -- %f
    process = git-lfs filter-process

# ============================================
# Delta - Enhanced Diff Viewer (Optional)
# ============================================
# Uncomment to use delta for syntax-highlighted diffs
# [core]
#     pager = delta
#
# [interactive]
#     diffFilter = delta --color-only
#
# [delta]
#     navigate = true
#     light = false
#     side-by-side = true
#     line-numbers = true
#     syntax-theme = Dracula
#
# [merge]
#     conflictstyle = diff3
#
# [diff]
#     colorMoved = default
```

## Essential Commands

### Repository Basics

```bash
# Initialize a new repository
git init

# Clone a repository
git clone https://github.com/user/repo.git
git clone git@github.com:user/repo.git    # SSH

# Clone with depth (shallow clone for faster downloads)
git clone --depth 1 https://github.com/user/repo.git
```

### Staging and Committing

```bash
# Stage files
git add file.txt              # Single file
git add src/                  # Directory
git add .                     # All changes
git add -p                    # Interactive staging (patch mode)

# Commit
git commit -m "feat: add user authentication"
git commit -am "fix: resolve null pointer"  # Stage + commit tracked files
git commit --amend            # Modify last commit
git commit --amend --no-edit  # Amend without changing message
```

### Viewing History

```bash
# Log variations
git log                       # Full log
git log --oneline             # Compact
git log --graph --oneline --all  # Visual branch history
git log -p                    # With diffs
git log --stat                # With file stats
git log --author="name"       # By author
git log --since="2 weeks ago" # Time-based
git log -- path/to/file       # File history

# Show a commit
git show abc123               # Full commit details
git show abc123:file.txt      # File at specific commit

# Diff
git diff                      # Working directory vs staging
git diff --staged             # Staging vs last commit
git diff HEAD~3               # Last 3 commits
git diff branch1..branch2     # Between branches
```

### Branching

```bash
# Create and switch branches
git branch feature-login      # Create branch
git switch feature-login      # Switch to branch
git switch -c feature-login   # Create and switch
git checkout -b feature-login # Old syntax (still works)

# List branches
git branch                    # Local branches
git branch -a                 # All branches (including remote)
git branch -vv                # With upstream info

# Delete branches
git branch -d feature-login   # Safe delete (must be merged)
git branch -D feature-login   # Force delete

# Rename branch
git branch -m old-name new-name
git branch -m new-name        # Rename current branch
```

### Merging and Rebasing

```bash
# Merge
git merge feature-branch      # Merge into current branch
git merge --no-ff feature     # Force merge commit
git merge --squash feature    # Squash all commits into one

# Rebase
git rebase main               # Rebase current onto main
git rebase -i HEAD~5          # Interactive rebase last 5 commits
git rebase --abort            # Cancel in-progress rebase
git rebase --continue         # Continue after resolving conflicts
```

### Remote Operations

```bash
# View remotes
git remote -v

# Add remote
git remote add origin https://github.com/user/repo.git
git remote add upstream https://github.com/original/repo.git

# Fetch and pull
git fetch                     # Download changes without merging
git fetch --all               # From all remotes
git pull                      # Fetch + merge
git pull --rebase             # Fetch + rebase

# Push
git push                      # Push current branch
git push -u origin main       # Set upstream and push
git push --force-with-lease   # Safer force push
git push origin --delete branch  # Delete remote branch
```

### Stashing

```bash
# Stash changes
git stash                     # Stash working directory
git stash push -m "WIP: feature"  # With message
git stash -u                  # Include untracked files

# List and apply
git stash list                # Show all stashes
git stash show -p             # Show stash diff
git stash pop                 # Apply and remove
git stash apply               # Apply and keep
git stash drop                # Remove stash
git stash clear               # Remove all stashes
```

### Undoing Changes

```bash
# Unstage files
git restore --staged file.txt # Unstage (keep changes)
git reset HEAD file.txt       # Old syntax

# Discard changes
git restore file.txt          # Discard working directory changes
git checkout -- file.txt      # Old syntax

# Reset commits
git reset --soft HEAD~1       # Undo commit, keep staged
git reset --mixed HEAD~1      # Undo commit, keep changes unstaged (default)
git reset --hard HEAD~1       # Undo commit, discard changes

# Revert (creates new commit)
git revert abc123             # Revert specific commit
git revert HEAD               # Revert last commit
```

## Git LFS (Large File Storage)

Track large files without bloating your repository.

```bash
# Install and initialize
git lfs install

# Track file types
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "models/*.bin"

# View tracked patterns
git lfs track

# View tracked files
git lfs ls-files

# Migrate existing files
git lfs migrate import --include="*.psd"
```

Add to `.gitattributes`:

```gitattributes
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
models/*.bin filter=lfs diff=lfs merge=lfs -text
```

## Git Hooks

Hooks automate tasks at specific Git events. Located in `.git/hooks/`.

### Common Hooks

```bash
# pre-commit: Run before commit is created
# - Lint code, run tests, check formatting

# commit-msg: Validate commit message
# - Enforce conventional commits format

# pre-push: Run before push
# - Run full test suite

# post-merge: Run after merge
# - Install dependencies if package.json changed
```

### Example: Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run linting
npm run lint
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Check for debug statements
if git diff --cached | grep -E "(console\.log|debugger|binding\.pry)" > /dev/null; then
    echo "Warning: Debug statements found!"
    exit 1
fi

exit 0
```

### Example: Commit-msg Hook (Conventional Commits)

```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format."
    echo "Use: type(scope): description"
    echo "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert"
    exit 1
fi
```

### Using Pre-commit Framework

For more robust hook management, use [pre-commit](https://pre-commit.com/):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
```

## Branching Strategies

### Git Flow

```
main ─────────────────────────────────────────────►
       │                              ▲
       ▼                              │
develop ──────────────────────────────┼─────────►
          │                  ▲        │
          ▼                  │        │
feature/login ───────────────┘        │
                                      │
                     hotfix/security ─┘
```

```bash
# Feature branch
git switch -c feature/login develop
# ... work ...
git switch develop
git merge --no-ff feature/login

# Hotfix
git switch -c hotfix/security main
# ... fix ...
git switch main
git merge --no-ff hotfix/security
git switch develop
git merge --no-ff hotfix/security
```

### GitHub Flow (Simpler)

```bash
# 1. Create feature branch from main
git switch -c feature/add-search main

# 2. Make changes and commit
git add .
git commit -m "feat: add search functionality"

# 3. Push and create PR
git push -u origin feature/add-search
gh pr create

# 4. After review, merge via GitHub UI

# 5. Clean up
git switch main
git pull
git branch -d feature/add-search
```

### Trunk-Based Development

```bash
# Short-lived feature branches (1-2 days max)
git switch -c small-feature main
# ... minimal changes ...
git push -u origin small-feature
# Create PR immediately, merge quickly
```

## Delta Integration

Delta provides syntax highlighting and side-by-side diffs.

### Installation

```bash
brew install git-delta        # macOS
cargo install git-delta       # Via Cargo
```

### Configuration

Add to `~/.gitconfig`:

```ini
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true           # Use n/N to navigate between files
    light = false             # Dark terminal background
    side-by-side = true       # Side-by-side view
    line-numbers = true       # Show line numbers
    syntax-theme = Dracula    # Color theme

[merge]
    conflictstyle = diff3

[diff]
    colorMoved = default
```

### Delta Themes

```bash
# List available themes
delta --list-syntax-themes

# Preview a theme
delta --syntax-theme="OneHalfDark" < file.diff
```

## Useful Git Commands

### Search and Find

```bash
# Search commit messages
git log --grep="bug fix"

# Search code changes
git log -p -S "function_name"    # When string was added/removed
git log -p -G "regex_pattern"    # Regex search

# Find who changed a line
git blame file.txt
git blame -L 10,20 file.txt      # Lines 10-20

# Find when a bug was introduced
git bisect start
git bisect bad                   # Current commit is bad
git bisect good v1.0             # v1.0 was good
# Git will checkout commits for you to test
git bisect reset                 # When done
```

### Clean Up

```bash
# Remove untracked files
git clean -n                     # Dry run
git clean -f                     # Force remove files
git clean -fd                    # Remove files and directories
git clean -fdx                   # Also remove ignored files

# Garbage collection
git gc                           # Clean up and optimize
git gc --aggressive              # More thorough
```

### Submodules

```bash
# Add submodule
git submodule add https://github.com/user/lib.git libs/lib

# Clone with submodules
git clone --recurse-submodules https://github.com/user/repo.git

# Update submodules
git submodule update --init --recursive
git submodule update --remote    # Get latest from remote
```

### Worktrees

Work on multiple branches simultaneously without switching:

```bash
# Create worktree for a branch
git worktree add ../feature-branch feature-branch

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../feature-branch
```

## Related Tools

- [lazygit](lazygit.md) - Terminal UI for Git
- [GitHub CLI](https://cli.github.com/) - GitHub from the command line
- [GitHub Actions](github-actions.md) - CI/CD automation
