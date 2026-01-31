# Language Modules

Starship automatically detects programming environments and displays version information. Language modules appear when relevant files are present in the current directory or its parents.

## How Language Detection Works

Each language module has **detection criteria** that determine when it appears:

- File extensions (`.py`, `.js`, `.rs`)
- Configuration files (`package.json`, `Cargo.toml`, `pyproject.toml`)
- Directories (`node_modules`, `venv`, `.git`)
- Environment variables

Detection happens automatically - no manual configuration needed.

## Common Configuration Pattern

All language modules share similar options:

```toml
[language_name]
disabled = false
format = "via [$symbol($version )]($style)"
version_format = "v${raw}"
symbol = " "
style = "bold green"
detect_extensions = ["ext1", "ext2"]
detect_files = ["file1", "file2"]
detect_folders = ["folder1"]
```

| Option | Description |
|--------|-------------|
| `format` | Module display format |
| `version_format` | Version number format |
| `symbol` | Language symbol |
| `style` | Text styling |
| `detect_extensions` | File extensions to detect |
| `detect_files` | Files to detect |
| `detect_folders` | Folders to detect |

## Node.js

Detects Node.js projects and displays the runtime version.

### Configuration

```toml
[nodejs]
format = "via [$symbol($version )]($style)"
version_format = "v${raw}"
symbol = " "
style = "bold green"
disabled = false
not_capable_style = "bold red"
detect_extensions = ["js", "mjs", "cjs", "ts", "mts", "cts"]
detect_files = ["package.json", ".node-version", ".nvmrc"]
detect_folders = ["node_modules"]
```

### Version Managers

Starship detects versions from:

- `node --version` (system)
- `.nvmrc` (nvm)
- `.node-version` (nodenv, asdf)
- `package.json` engines field

### Examples

**Show only when package.json exists:**

```toml
[nodejs]
detect_extensions = []
detect_files = ["package.json"]
detect_folders = []
```

**Show npm/yarn info:**

```toml
[nodejs]
format = "via [$symbol($version)($engines_version )]($style)"
```

**Minimal display:**

```toml
[nodejs]
format = "[$symbol]($style)"
symbol = "node "
```

## Python

Shows Python version and virtual environment information.

### Configuration

```toml
[python]
format = 'via [${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'
version_format = "v${raw}"
symbol = " "
style = "yellow bold"
pyenv_version_name = false
pyenv_prefix = "pyenv "
python_binary = ["python", "python3", "python2"]
detect_extensions = ["py"]
detect_files = [".python-version", "Pipfile", "__init__.py", "pyproject.toml", "requirements.txt", "setup.py", "tox.ini"]
detect_folders = []
```

### Virtual Environments

Starship displays the active virtual environment name:

```toml
[python]
format = '[${symbol}${version}(\($virtualenv\))]($style) '
```

Output with venv: ` 3.11.4(myproject) `

### Version Managers

Detects versions from:

- `python --version`
- `.python-version` (pyenv)
- `pyproject.toml` (poetry, PDM)
- Active virtual environment

### Examples

**Hide virtual environment:**

```toml
[python]
format = "via [$symbol$version]($style) "
```

**Show conda environment:**

```toml
[conda]
disabled = false
format = "[$symbol$environment]($style) "
symbol = " "
style = "bold green"
```

**Custom virtual environment display:**

```toml
[python]
format = '[$symbol$version( \[$virtualenv\])]($style) '
style = "bold blue"
```

## Rust

Displays Rust toolchain version.

### Configuration

```toml
[rust]
format = "via [$symbol($version )]($style)"
version_format = "v${raw}"
symbol = " "
style = "bold red"
disabled = false
detect_extensions = ["rs"]
detect_files = ["Cargo.toml"]
detect_folders = []
```

### Toolchain Detection

Shows the active toolchain from:

- `rustc --version`
- `rust-toolchain` or `rust-toolchain.toml`
- Directory overrides (`rustup override`)

### Examples

**Show toolchain channel:**

```toml
[rust]
format = "via [$symbol($version-$toolchain )]($style)"
```

**Minimal:**

```toml
[rust]
format = "[$symbol]($style)"
symbol = "rs "
```

## Go

Shows Go version information.

### Configuration

```toml
[golang]
format = "via [$symbol($version )]($style)"
version_format = "v${raw}"
symbol = " "
style = "bold cyan"
disabled = false
not_capable_style = "bold red"
detect_extensions = ["go"]
detect_files = ["go.mod", "go.sum", "go.work", ".go-version"]
detect_folders = ["Godeps"]
```

### Go Version Detection

Detects from:

- `go version`
- `go.mod` module version
- `.go-version` (goenv)

### Examples

**Show mod version:**

```toml
[golang]
format = "via [$symbol($version )($mod_version )]($style)"
```

## Java

Displays Java/JDK version.

### Configuration

```toml
[java]
format = "via [$symbol($version )]($style)"
version_format = "v${raw}"
symbol = " "
style = "red dimmed"
disabled = false
detect_extensions = ["java", "class", "gradle", "jar", "cljs", "cljc"]
detect_files = ["pom.xml", "build.gradle.kts", "build.sbt", ".java-version", "deps.edn", "project.clj", "build.boot", ".sdkmanrc"]
detect_folders = []
```

### SDKMAN Integration

Starship detects Java versions from SDKMAN configuration.

### Examples

**Show JDK vendor:**

```toml
[java]
format = "via [$symbol($version )]($style)"
symbol = " "
```

## Additional Language Modules

### Ruby

```toml
[ruby]
format = "via [$symbol($version )]($style)"
symbol = " "
style = "bold red"
detect_extensions = ["rb"]
detect_files = ["Gemfile", ".ruby-version"]
detect_folders = []
```

### PHP

```toml
[php]
format = "via [$symbol($version )]($style)"
symbol = " "
style = "purple bold"
detect_extensions = ["php"]
detect_files = ["composer.json", ".php-version"]
detect_folders = []
```

### Elixir

```toml
[elixir]
format = 'via [$symbol($version \(OTP $otp_version\) )]($style)'
symbol = " "
style = "bold purple"
detect_extensions = ["ex", "exs"]
detect_files = ["mix.exs"]
detect_folders = []
```

### C/C++

```toml
[c]
format = "via [$symbol($version(-$name) )]($style)"
symbol = " "
style = "bold 149"
disabled = false
detect_extensions = ["c", "h"]
detect_files = []
detect_folders = []
commands = [["cc", "--version"], ["gcc", "--version"], ["clang", "--version"]]
```

### Lua

```toml
[lua]
format = "via [$symbol($version )]($style)"
symbol = " "
style = "bold blue"
detect_extensions = ["lua"]
detect_files = [".lua-version"]
detect_folders = ["lua"]
lua_binary = "lua"
```

### Zig

```toml
[zig]
format = "via [$symbol($version )]($style)"
symbol = " "
style = "bold yellow"
detect_extensions = ["zig"]
detect_files = []
detect_folders = []
```

### Deno

```toml
[deno]
format = "via [$symbol($version )]($style)"
symbol = " "
style = "green bold"
detect_extensions = []
detect_files = ["deno.json", "deno.jsonc", "mod.ts", "deps.ts", "mod.js", "deps.js"]
detect_folders = []
```

### Bun

```toml
[bun]
format = "via [$symbol($version )]($style)"
symbol = " "
style = "bold red"
detect_extensions = []
detect_files = ["bun.lockb", "bunfig.toml"]
detect_folders = []
```

## Package Module

Shows the version from the project's package manifest.

```toml
[package]
format = "is [$symbol$version]($style) "
symbol = " "
style = "bold 208"
display_private = false
disabled = false
version_format = "v${raw}"
```

Detects versions from:

- `package.json` (Node.js)
- `Cargo.toml` (Rust)
- `pyproject.toml` (Python)
- `composer.json` (PHP)
- And many more

**Disable to reduce clutter:**

```toml
[package]
disabled = true
```

## All Language Modules List

| Module | Symbol | Languages/Tools |
|--------|--------|-----------------|
| `bun` | ` ` | Bun runtime |
| `c` | ` ` | C |
| `cmake` | `cmake ` | CMake |
| `cobol` | `cobol ` | COBOL |
| `crystal` | ` ` | Crystal |
| `daml` | `daml ` | DAML |
| `dart` | ` ` | Dart |
| `deno` | ` ` | Deno |
| `dotnet` | ` ` | .NET |
| `elixir` | ` ` | Elixir |
| `elm` | ` ` | Elm |
| `erlang` | ` ` | Erlang |
| `fennel` | `fennel ` | Fennel |
| `golang` | ` ` | Go |
| `gradle` | `gradle ` | Gradle |
| `haskell` | ` ` | Haskell |
| `haxe` | `haxe ` | Haxe |
| `helm` | `helm ` | Helm charts |
| `java` | ` ` | Java |
| `julia` | ` ` | Julia |
| `kotlin` | ` ` | Kotlin |
| `lua` | ` ` | Lua |
| `meson` | `meson ` | Meson |
| `nim` | ` ` | Nim |
| `nix_shell` | ` ` | Nix shell |
| `nodejs` | ` ` | Node.js |
| `ocaml` | ` ` | OCaml |
| `opa` | `opa ` | Open Policy Agent |
| `perl` | ` ` | Perl |
| `php` | ` ` | PHP |
| `pulumi` | `pulumi ` | Pulumi |
| `purescript` | ` ` | PureScript |
| `python` | ` ` | Python |
| `rlang` | ` ` | R |
| `red` | `red ` | Red |
| `ruby` | ` ` | Ruby |
| `rust` | ` ` | Rust |
| `scala` | ` ` | Scala |
| `solidity` | `solidity ` | Solidity |
| `swift` | ` ` | Swift |
| `vlang` | `vlang ` | V |
| `vagrant` | `vagrant ` | Vagrant |
| `zig` | ` ` | Zig |

## Optimizing Language Display

### Show Only Relevant Languages

Disable languages you don't use:

```toml
[ruby]
disabled = true

[php]
disabled = true

[java]
disabled = true
```

### Minimal Language Display

Show only symbols without versions:

```toml
[nodejs]
format = "[$symbol]($style)"

[python]
format = "[$symbol]($style)"

[rust]
format = "[$symbol]($style)"
```

### Combined Developer Configuration

```toml
# Web development focus
format = """
$directory\
$git_branch\
$git_status\
$nodejs\
$deno\
$bun\
$python\
$rust\
$golang\
$line_break\
$character"""

[nodejs]
format = "[$symbol($version)]($style) "
symbol = "node "

[python]
format = '[$symbol$version(\($virtualenv\))]($style) '
symbol = "py "

[rust]
format = "[$symbol($version)]($style) "
symbol = "rs "

[golang]
format = "[$symbol($version)]($style) "
symbol = "go "

# Disable unused
[ruby]
disabled = true

[php]
disabled = true

[java]
disabled = true
```
