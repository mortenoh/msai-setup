# Extensions

Essential VS Code extensions for development.

## Managing Extensions

### Install Extension

1. ++cmd+shift+x++ to open Extensions
2. Search for extension
3. Click "Install"

### Via Command Line

```bash
# Install
code --install-extension ms-python.python

# List installed
code --list-extensions

# Uninstall
code --uninstall-extension extension-id
```

### Extension Recommendations

Create `.vscode/extensions.json` in project:

```json
{
  "recommendations": [
    "ms-python.python",
    "esbenp.prettier-vscode"
  ],
  "unwantedRecommendations": [
    "some.extension"
  ]
}
```

## Essential Extensions

### Python

**Python** (`ms-python.python`)

Core Python extension:

- IntelliSense
- Debugging
- Code navigation
- Jupyter support

**Pylance** (`ms-python.vscode-pylance`)

Fast Python language server:

- Type checking
- Auto-imports
- Rich completions

**Black Formatter** (`ms-python.black-formatter`)

Python code formatter.

**Ruff** (`charliermarsh.ruff`)

Fast Python linter:

```json
{
  "ruff.lint.args": ["--config=pyproject.toml"]
}
```

### JavaScript/TypeScript

**ESLint** (`dbaeumer.vscode-eslint`)

JavaScript/TypeScript linting:

```json
{
  "eslint.validate": ["javascript", "typescript", "javascriptreact", "typescriptreact"]
}
```

**Prettier** (`esbenp.prettier-vscode`)

Code formatter for multiple languages:

```json
{
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Rust

**rust-analyzer** (`rust-lang.rust-analyzer`)

Rust language support:

- IntelliSense
- Code actions
- Debugging support

```json
{
  "rust-analyzer.checkOnSave.command": "clippy"
}
```

### Go

**Go** (`golang.go`)

Official Go extension:

- IntelliSense
- Debugging
- Testing support

```json
{
  "go.formatTool": "gofmt",
  "go.lintTool": "golangci-lint"
}
```

### Docker

**Docker** (`ms-azuretools.vscode-docker`)

Docker support:

- Dockerfile syntax
- Docker Compose
- Container management
- Image exploration

### Git

**GitLens** (`eamodio.gitlens`)

Git supercharged:

- Blame annotations
- Code authorship
- Rich history
- Visual diff

```json
{
  "gitlens.currentLine.enabled": false,
  "gitlens.hovers.enabled": false
}
```

**Git Graph** (`mhutchie.git-graph`)

Visual git history:

- Branch visualization
- Interactive rebasing

## Language Support

### HTML/CSS

**HTML CSS Support** (`ecmel.vscode-html-css`)

CSS IntelliSense in HTML.

**CSS Peek** (`pranaygp.vscode-css-peek`)

Jump to CSS definitions.

### Markdown

**Markdown All in One** (`yzhang.markdown-all-in-one`)

Markdown tools:

- Shortcuts
- Table of contents
- Preview

**markdownlint** (`davidanson.vscode-markdownlint`)

Markdown linting.

### YAML

**YAML** (`redhat.vscode-yaml`)

YAML language support with schema validation.

```json
{
  "yaml.schemas": {
    "https://json.schemastore.org/github-workflow": ".github/workflows/*.yml"
  }
}
```

### TOML

**Even Better TOML** (`tamasfe.even-better-toml`)

TOML language support.

## Productivity

### Code Spell Checker

**Code Spell Checker** (`streetsidesoftware.code-spell-checker`)

Spell checking for code:

```json
{
  "cSpell.userWords": ["pytest", "asyncio"]
}
```

### Path Intellisense

**Path Intellisense** (`christian-kohler.path-intellisense`)

Autocomplete file paths.

### Bracket Pair Colorizer

Built into VS Code now:

```json
{
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true
}
```

### Todo Tree

**Todo Tree** (`gruntfuggly.todo-tree`)

Track TODOs and FIXMEs:

```json
{
  "todo-tree.general.tags": ["TODO", "FIXME", "HACK", "XXX"]
}
```

### Error Lens

**Error Lens** (`usernamehw.errorlens`)

Show diagnostics inline:

```json
{
  "errorLens.enabledDiagnosticLevels": ["error", "warning"]
}
```

## Themes

### Popular Themes

- **Dracula Official** (`dracula-theme.theme-dracula`)
- **One Dark Pro** (`zhuangtongfa.material-theme`)
- **Tokyo Night** (`enkia.tokyo-night`)
- **Catppuccin** (`catppuccin.catppuccin-vsc`)
- **GitHub Theme** (`github.github-vscode-theme`)
- **Gruvbox Theme** (`jdinhlife.gruvbox`)

### Icon Themes

- **Material Icon Theme** (`pkief.material-icon-theme`)
- **vscode-icons** (`vscode-icons-team.vscode-icons`)

## Remote Development

### Remote - SSH

**Remote - SSH** (`ms-vscode-remote.remote-ssh`)

Edit on remote machines:

```json
{
  "remote.SSH.defaultExtensions": [
    "ms-python.python"
  ]
}
```

### Dev Containers

**Dev Containers** (`ms-vscode-remote.remote-containers`)

Develop inside containers:

- `.devcontainer/devcontainer.json` configuration
- Reproducible environments

### WSL

**WSL** (`ms-vscode-remote.remote-wsl`)

Edit in Windows Subsystem for Linux.

## Testing

### Test Explorer UI

**Test Explorer UI** (`hbenl.vscode-test-explorer`)

Unified test interface.

### Python Testing

Pytest support built into Python extension:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

## Extension Packs

### Python Extension Pack

Multiple Python extensions bundled.

### Remote Development

All remote extensions in one pack.

## Extension Settings

### Per-Extension Configuration

```json
{
  "prettier.singleQuote": true,
  "prettier.tabWidth": 2,
  "gitlens.currentLine.enabled": false,
  "eslint.validate": ["javascript", "typescript"]
}
```

### Disable Extension for Workspace

1. ++cmd+shift+x++
2. Find extension
3. Click gear icon
4. "Disable (Workspace)"

## Recommended Setup

### Python Development

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-toolsai.jupyter"
  ]
}
```

### Web Development

```json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "formulahendry.auto-rename-tag"
  ]
}
```

### DevOps

```json
{
  "recommendations": [
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "hashicorp.terraform"
  ]
}
```

## Performance Tips

1. **Disable unused extensions**: Right-click > Disable
2. **Use workspace recommendations**: Only enable what you need
3. **Check extension impact**: Help > Process Explorer
