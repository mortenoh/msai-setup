# Bash Tutorial

A comprehensive guide to bash shell usage, from fundamentals to advanced scripting and modern tooling.

## What You'll Learn

This tutorial covers everything from basic command-line navigation to writing production-ready scripts:

- **Fundamentals** - Shell basics, file operations, permissions, and I/O redirection
- **Configuration** - Dotfiles, environment variables, aliases, and prompt customization
- **Scripting** - Variables, conditionals, loops, arrays, and error handling
- **Tools** - Text processing, file finding, modern replacements, and JSON handling
- **Advanced** - Job control, subshells, signals, and performance optimization
- **Reference** - Quick reference cards and cheat sheets

## Learning Path

### Beginner

If you're new to the command line, start here:

1. [Shell Basics](fundamentals/shell-basics.md) - Understanding shells and terminals
2. [Navigation](fundamentals/navigation.md) - Moving around the filesystem
3. [Files & Directories](fundamentals/files-directories.md) - Basic file operations
4. [Viewing Files](fundamentals/viewing-files.md) - Reading file contents
5. [Permissions](fundamentals/permissions.md) - Understanding Unix permissions
6. [Redirection & Pipes](fundamentals/redirection.md) - Connecting commands

### Intermediate

Once comfortable with basics:

1. [Dotfiles](configuration/dotfiles.md) - Configuring your shell
2. [Environment Variables](configuration/environment.md) - PATH and exports
3. [Aliases](configuration/aliases.md) - Creating shortcuts
4. [Shell Functions](configuration/functions.md) - Reusable commands
5. [Scripting Basics](scripting/basics.md) - Writing your first scripts
6. [Conditionals](scripting/conditionals.md) - Decision making
7. [Loops](scripting/loops.md) - Iteration patterns

### Advanced

For deeper understanding:

1. [Arrays](scripting/arrays.md) - Working with collections
2. [Error Handling](scripting/error-handling.md) - Robust scripts
3. [Job Control](advanced/job-control.md) - Background processes
4. [Signals](advanced/signals.md) - Process communication
5. [Performance](advanced/performance.md) - Optimization techniques

## Prerequisites

- A terminal emulator (Terminal.app on macOS, or any Linux terminal)
- Bash 3.2+ (macOS default) or 5.0+ (Linux/Homebrew)
- Basic computer literacy

Check your bash version:

```bash
bash --version
```

## macOS Note

macOS ships with Bash 3.2 due to licensing (GPLv2 vs GPLv3). For modern features like associative arrays and `mapfile`, install Bash 5.x via Homebrew:

```bash
brew install bash
```

This tutorial notes when features require Bash 4.0+.

## Modern Tools

Throughout this tutorial, we highlight modern replacements for classic Unix tools:

| Classic | Modern | Benefits |
|---------|--------|----------|
| `ls` | `eza` | Colors, git integration, tree view |
| `cat` | `bat` | Syntax highlighting, line numbers |
| `grep` | `ripgrep` | Faster, respects .gitignore |
| `find` | `fd` | Simpler syntax, faster |
| `top` | `btop` | Better visualization |

See [Modern Replacements](tools/modern-replacements.md) for installation and usage.

## Conventions Used

### Code Blocks

Commands to type:

```bash
echo "Hello, World!"
```

Expected output:

```
Hello, World!
```

### Prompts

The `$` symbol represents your shell prompt - don't type it:

```bash
$ whoami    # Type only: whoami
user
```

### Placeholders

Angle brackets indicate values you should replace:

```bash
cp <source> <destination>
```

### Notes and Warnings

!!! tip "Pro Tip"
    Helpful suggestions for better workflows.

!!! warning "Caution"
    Important warnings about potential issues.

!!! note "Note"
    Additional context or explanations.

## Quick Start

If you're impatient, here's the minimum to get productive:

```bash
# Navigate
cd ~/projects        # Change directory
pwd                  # Print working directory
ls -la               # List files with details

# Files
cat file.txt         # View file
cp src dest          # Copy
mv old new           # Move/rename
rm file              # Remove (careful!)

# Search
grep "pattern" file  # Find in file
find . -name "*.md"  # Find files

# Help
man command          # Manual page
command --help       # Quick help
```

Now dive into [Shell Basics](fundamentals/shell-basics.md) for the full journey.
