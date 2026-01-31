# Scripting

Transform your shell knowledge into reusable scripts. This section covers everything from basic script structure to advanced error handling and debugging.

## Topics

### [Basics](basics.md)

Script structure, the shebang line, variables, quoting rules, and making scripts executable.

### [Conditionals](conditionals.md)

Decision making with `if/else`, test commands (`[[ ]]`), and `case` statements.

### [Loops](loops.md)

Iteration with `for`, `while`, and `until` loops. Loop control with `break` and `continue`.

### [Arrays](arrays.md)

Working with indexed and associative arrays for managing collections of data.

### [Strings](strings.md)

String manipulation, pattern matching, and parameter expansion techniques.

### [Arithmetic](arithmetic.md)

Mathematical operations using `$(( ))`, `let`, and external tools like `bc`.

### [Input/Output](io.md)

Reading user input, formatted output with `printf`, and working with heredocs.

### [Error Handling](error-handling.md)

Making scripts robust with `set -e`, `trap`, proper exit codes, and defensive programming.

### [Debugging](debugging.md)

Finding and fixing problems with `set -x`, `PS4`, ShellCheck, and systematic debugging techniques.

## Script Template

Start new scripts with this template:

```bash
#!/usr/bin/env bash
#
# script-name - Brief description of what it does
#
# Usage: script-name [options] <arguments>
#

set -euo pipefail

# Constants
readonly SCRIPT_NAME="${0##*/}"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options] <argument>

Description of what the script does.

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output

Examples:
    $SCRIPT_NAME file.txt
    $SCRIPT_NAME -v directory/
EOF
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            *)
                break
                ;;
        esac
    done

    # Main logic here
    echo "Running $SCRIPT_NAME"
}

main "$@"
```

## Learning Path

Work through these topics in order:

1. **Basics** - Understand script structure
2. **Conditionals** - Make decisions
3. **Loops** - Repeat operations
4. **Strings** - Manipulate text
5. **Arithmetic** - Perform calculations
6. **Arrays** - Handle collections
7. **I/O** - Interact with users and files
8. **Error Handling** - Make scripts robust
9. **Debugging** - Find and fix issues

## Best Practices Preview

Throughout this section, you'll learn:

- Always quote variables: `"$var"` not `$var`
- Use `[[ ]]` instead of `[ ]` for tests
- Start scripts with `set -euo pipefail`
- Use functions to organize code
- Handle errors explicitly
- Test scripts with ShellCheck

## Portability Notes

This tutorial focuses on bash. Some features are bash-specific:

| Feature | Bash Version | POSIX Alternative |
|---------|-------------|-------------------|
| `[[ ]]` | All | `[ ]` |
| `$(( ))` | All | `expr` |
| Arrays | All | Not available |
| `${var,,}` | 4.0+ | `tr` |
| Associative arrays | 4.0+ | Not available |
| `mapfile` | 4.0+ | `while read` loop |

For maximum portability, use POSIX sh syntax. For practical scripts on modern systems, use bash.
