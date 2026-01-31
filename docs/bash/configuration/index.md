# Configuration

Customize your bash environment for productivity and comfort. This section covers dotfiles, environment variables, aliases, functions, and prompt customization.

## Topics

### [Dotfiles](dotfiles.md)

Understanding `.bashrc`, `.bash_profile`, `.profile`, and when each is loaded. Learn to organize configuration files effectively.

### [Environment Variables](environment.md)

Working with environment variables, especially PATH. Learn about `export`, variable scope, and common environment variables.

### [Aliases](aliases.md)

Create shortcuts for frequently used commands. Organize aliases for readability and maintenance.

### [Functions](functions.md)

Write shell functions for more complex reusable operations that go beyond what aliases can do.

### [Prompt Customization](prompt.md)

Customize your PS1 prompt, from simple username/path displays to complex prompts with git information. Introduction to Starship prompt.

## Configuration Philosophy

Good shell configuration should be:

- **Portable** - Works across machines (Linux, macOS)
- **Modular** - Split into logical files
- **Documented** - Comments explain non-obvious settings
- **Version controlled** - Track changes with git

## Quick Setup

Minimal `.bashrc` for productivity:

```bash
# ~/.bashrc

# History settings
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoreboth:erasedups
shopt -s histappend

# Better defaults
shopt -s checkwinsize
shopt -s globstar 2>/dev/null

# Common aliases
alias ll='ls -lah'
alias la='ls -A'
alias ..='cd ..'
alias ...='cd ../..'

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Prompt
PS1='\u@\h:\w\$ '
```

## Loading Order

Understanding when configuration files load:

```
Login Shell (.bash_profile/.profile)
    │
    └── Sources .bashrc
            │
            └── Your configuration
                    │
                    └── Other sourced files
```

See [Dotfiles](dotfiles.md) for details.

## Modern Tools

This section also covers modern configuration tools:

- **Starship** - Cross-shell customizable prompt
- **direnv** - Directory-specific environments
- **zoxide** - Smarter directory navigation

## What You'll Learn

By the end of this section, you'll be able to:

- Structure your shell configuration files
- Create useful aliases and functions
- Customize your prompt
- Manage environment variables properly
- Keep configuration portable across systems
