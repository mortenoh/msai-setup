# Tools

Essential command-line tools for text processing, file finding, and system management. This section covers both classic Unix tools and their modern replacements.

## Topics

### [Text Processing](text-processing.md)

The Unix text processing toolkit: `grep`, `sed`, `awk`, `cut`, `sort`, `uniq`, and `tr`. These commands form the backbone of shell data manipulation.

### [Finding Files](finding-files.md)

Locating files with `find` and modern alternatives like `fd`. Pattern matching, filtering, and executing commands on results.

### [Modern Replacements](modern-replacements.md)

Better alternatives to classic tools: `eza` for `ls`, `bat` for `cat`, `ripgrep` for `grep`, `fd` for `find`, `fzf` for fuzzy finding, and `btop` for system monitoring.

### [JSON Processing](json-processing.md)

Working with JSON data using `jq`. Extracting, filtering, and transforming JSON from APIs and configuration files.

### [Process Management](process-management.md)

Monitoring and controlling processes: `ps`, `top`/`btop`, `kill`, `jobs`, background processes, and system resource monitoring.

### [Networking](networking.md)

Network tools: `curl`, `wget`, `ssh`, `nc` (netcat). Making HTTP requests, downloading files, and network diagnostics.

### [Archives](archives.md)

Working with compressed files and archives: `tar`, `gzip`, `bzip2`, `xz`, `zip`, and `unzip`.

### [Git](git.md)

Comprehensive Git guide covering configuration, workflows, branching strategies, LFS, hooks, and delta integration.

### [tmux](tmux.md)

Terminal multiplexer for managing multiple terminal sessions, windows, and panes. Essential for remote work.

### [uv](uv.md)

Extremely fast Python package installer and resolver written in Rust. Drop-in replacement for pip.

### [Node.js](nodejs.md)

Node.js runtime with nvm version management, npm/pnpm package managers, and project configuration.

### [Deno](deno.md)

Secure JavaScript/TypeScript runtime with built-in tooling, permissions system, and modern APIs.

### [Bun](bun.md)

All-in-one JavaScript runtime, bundler, and package manager. Fast alternative to Node.js.

### [Rust](rust.md)

Rust toolchain management with rustup, cargo, clippy, and rustfmt. Building and cross-compiling.

### [GitHub Actions](github-actions.md)

CI/CD automation with workflow configuration, common patterns, and reusable workflows.

### [Make](make.md)

Build automation with Makefiles. Variables, targets, dependencies, and patterns for any project.

### [Databases](databases.md)

Quick reference for PostgreSQL, Redis, MongoDB, MySQL with Docker commands and CLI usage.

## Tool Philosophy

Unix tools follow key principles:

1. **Do one thing well** - Each tool has a focused purpose
2. **Text as interface** - Tools communicate via text streams
3. **Composability** - Tools combine via pipes and redirection

```bash
# Classic Unix pipeline
cat access.log | grep "404" | cut -d' ' -f7 | sort | uniq -c | sort -rn | head -10
```

## Classic vs Modern

| Classic | Modern | Benefits |
|---------|--------|----------|
| `ls` | `eza` | Colors, git integration, icons |
| `cat` | `bat` | Syntax highlighting, git diff |
| `grep` | `ripgrep (rg)` | Faster, respects .gitignore |
| `find` | `fd` | Simpler syntax, faster |
| `top` | `btop` | Better visualization |
| `cd` | `zoxide` | Smart directory jumping |

Modern tools are optional but improve daily workflow. Classic tools are always available and essential for scripts.

## Installation

Install modern tools on macOS:

```bash
brew install eza bat ripgrep fd fzf btop zoxide jq
```

On Linux (Debian/Ubuntu):

```bash
# Most available via apt
sudo apt install bat ripgrep fd-find fzf jq

# Some may need manual installation or cargo
cargo install eza
```

## Quick Reference

### Text Processing

```bash
grep "pattern" file           # Search for pattern
sed 's/old/new/g' file        # Replace text
awk '{print $1}' file         # Extract columns
cut -d',' -f1,3 file          # Cut fields
sort file                     # Sort lines
uniq                          # Remove duplicates
tr 'a-z' 'A-Z'               # Translate characters
```

### Finding Files

```bash
find . -name "*.txt"          # Find by name
find . -type f -mtime -7      # Modified in last 7 days
fd "pattern"                  # Modern find
```

### Process Management

```bash
ps aux                        # List processes
top                           # Interactive monitor
kill PID                      # Terminate process
jobs                          # List background jobs
```

### Networking

```bash
curl https://api.example.com  # HTTP request
wget https://example.com/file # Download file
ssh user@host                 # Remote shell
```

### Archives

```bash
tar -czf archive.tar.gz dir/  # Create archive
tar -xzf archive.tar.gz       # Extract archive
zip -r archive.zip dir/       # Create zip
unzip archive.zip             # Extract zip
```

## Learning Approach

For each tool, learn:

1. **Basic usage** - The 20% you'll use 80% of the time
2. **Common options** - Frequently used flags
3. **Combination patterns** - How it works with other tools
4. **When to use alternatives** - Modern tools vs classic
