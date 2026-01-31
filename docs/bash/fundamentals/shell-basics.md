# Shell Basics

Understanding what bash is and how it fits into the larger picture of terminals, shells, and command-line interfaces.

## What is a Shell?

A **shell** is a program that interprets commands and communicates with the operating system. It's the layer between you and the kernel:

```
┌─────────────────────────────────────┐
│           User (you)                │
├─────────────────────────────────────┤
│     Terminal Emulator (UI)          │
├─────────────────────────────────────┤
│     Shell (bash, zsh, fish)         │
├─────────────────────────────────────┤
│     Operating System Kernel         │
├─────────────────────────────────────┤
│           Hardware                  │
└─────────────────────────────────────┘
```

The shell:

- Reads commands you type
- Interprets and expands them (variables, globs, etc.)
- Executes programs
- Returns output to you

## Terminal vs Shell

These terms are often confused:

**Terminal** (or terminal emulator)

- The application window you type in
- Examples: Terminal.app, iTerm2, Alacritty, Windows Terminal
- Handles display, fonts, colors, keyboard input

**Shell**

- The program running inside the terminal
- Interprets your commands
- Examples: bash, zsh, fish, sh

You can run different shells in the same terminal, and the same shell in different terminals.

## What is Bash?

**Bash** (Bourne Again SHell) is:

- The default shell on most Linux distributions
- Available on macOS (though zsh is now default)
- A superset of the original Bourne shell (`sh`)
- Both an interactive shell and a scripting language

Check your current shell:

```bash
echo $SHELL
```

```
/bin/bash
```

Or see what shell you're currently in:

```bash
echo $0
```

```
-bash
```

## Bash Versions

Version matters for scripting:

```bash
bash --version
```

```
GNU bash, version 5.2.15(1)-release (aarch64-apple-darwin23.0.0)
```

| Version | Notable Features |
|---------|-----------------|
| 3.2 | macOS default, last GPLv2 version |
| 4.0 | Associative arrays, `mapfile`, `&>>` |
| 4.2 | `declare -g`, negative array indices |
| 4.3 | `declare -n` (namerefs) |
| 4.4 | `${var@operator}` transformations |
| 5.0 | `EPOCHSECONDS`, improved arrays |

macOS ships with Bash 3.2 due to licensing. Install Bash 5.x with Homebrew:

```bash
brew install bash
```

## Interactive vs Non-Interactive

**Interactive shell**: You type commands, shell responds

```bash
$ ls
Documents  Downloads  Pictures
$ echo "Hello"
Hello
```

**Non-interactive shell**: Runs a script without user input

```bash
#!/bin/bash
echo "This runs automatically"
```

This distinction matters for configuration files (covered in [Dotfiles](../configuration/dotfiles.md)).

## Login vs Non-Login Shells

**Login shell**: First shell when you log in

- Opens when you SSH into a server
- Reads `.bash_profile` or `.profile`

**Non-login shell**: Shells started after login

- Opening a new terminal tab
- Running `bash` from another shell
- Reads `.bashrc`

Check if current shell is a login shell:

```bash
shopt -q login_shell && echo "Login" || echo "Non-login"
```

## Basic Command Structure

Commands follow this pattern:

```
command [options] [arguments]
```

Examples:

```bash
ls                      # command only
ls -l                   # command + option
ls -l /home             # command + option + argument
ls -la /home /tmp       # command + options + multiple arguments
```

### Options

**Short options** start with single dash:

```bash
ls -l           # long format
ls -a           # show hidden files
ls -la          # combined: -l and -a
```

**Long options** start with double dash:

```bash
ls --long       # same as -l
ls --all        # same as -a
```

### Arguments

Arguments are the targets of the command:

```bash
cat file.txt            # file.txt is the argument
cp source.txt dest.txt  # two arguments
```

## Getting Help

### man Pages

The manual (`man`) provides detailed documentation:

```bash
man ls
```

Navigate with:

- `Space` or `f` - page forward
- `b` - page backward
- `/pattern` - search forward
- `n` - next search result
- `q` - quit

### --help Flag

Most commands support `--help`:

```bash
ls --help
```

### help Built-in

For shell built-ins, use `help`:

```bash
help cd
help echo
```

### type Command

Find out what a command is:

```bash
type ls
```

```
ls is /bin/ls
```

```bash
type cd
```

```
cd is a shell builtin
```

```bash
type ll
```

```
ll is aliased to `ls -l'
```

## Command Execution

When you type a command, bash:

1. **Parses** the input (splits into words)
2. **Expands** variables, globs, etc.
3. **Searches** for the command:
   - Aliases
   - Functions
   - Built-ins
   - External programs (via PATH)
4. **Executes** the command
5. **Returns** output and exit status

### Exit Status

Every command returns an exit status:

- `0` = success
- `1-255` = failure (specific meaning varies)

Check the last command's exit status:

```bash
ls /
echo $?
```

```
0
```

```bash
ls /nonexistent
echo $?
```

```
ls: /nonexistent: No such file or directory
1
```

## Running Multiple Commands

### Sequential (`;`)

Run commands one after another, regardless of success:

```bash
echo "first"; echo "second"; echo "third"
```

### Conditional AND (`&&`)

Run next command only if previous succeeded:

```bash
mkdir mydir && cd mydir
```

### Conditional OR (`||`)

Run next command only if previous failed:

```bash
cd mydir || mkdir mydir
```

### Combining

```bash
cd mydir || mkdir mydir && echo "In mydir"
```

## Comments

Comments start with `#`:

```bash
# This is a comment
echo "Hello"  # This is an inline comment
```

## Try It

1. Check your current shell and version:
   ```bash
   echo $SHELL
   bash --version
   ```

2. Explore the `type` command:
   ```bash
   type echo
   type type
   type ls
   ```

3. Practice getting help:
   ```bash
   man bash
   help help
   ls --help
   ```

4. Test exit codes:
   ```bash
   true; echo $?
   false; echo $?
   ```

## Summary

- A **shell** interprets commands; a **terminal** displays them
- **Bash** is the most common shell on Linux
- Commands follow `command [options] [arguments]`
- **Exit status 0** means success; non-zero means failure
- Use `man`, `--help`, and `help` for documentation
