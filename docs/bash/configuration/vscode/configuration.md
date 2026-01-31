# Configuration

Understanding VS Code settings and configuration options.

## Settings Types

### User Settings

Global settings for all projects:

- Location: `~/Library/Application Support/Code/User/settings.json`
- Open: ++cmd+comma++ or ++cmd+shift+p++ > "Preferences: Open User Settings (JSON)"

### Workspace Settings

Project-specific settings:

- Location: `.vscode/settings.json` in project root
- Override user settings for that project

### Folder Settings

For multi-root workspaces:

- Each folder can have its own `.vscode/settings.json`

## Settings UI vs JSON

### GUI Settings

Open with ++cmd+comma++:

- Search settings
- Toggle options
- Visual editing

### JSON Settings

Open with ++cmd+shift+p++ > "Open User Settings (JSON)":

- Direct JSON editing
- Copy/paste configurations
- Version control friendly

## Editor Settings

### Font Configuration

```json
{
  "editor.fontFamily": "JetBrains Mono, Menlo, Monaco, monospace",
  "editor.fontSize": 14,
  "editor.fontWeight": "400",
  "editor.lineHeight": 1.6,
  "editor.fontLigatures": true,
  "editor.letterSpacing": 0
}
```

### Display

```json
{
  "editor.minimap.enabled": false,
  "editor.renderWhitespace": "selection",
  "editor.rulers": [80, 120],
  "editor.wordWrap": "off",
  "editor.cursorStyle": "line",
  "editor.cursorBlinking": "smooth",
  "editor.lineNumbers": "on",
  "editor.glyphMargin": true,
  "editor.scrollBeyondLastLine": false
}
```

### Indentation

```json
{
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.detectIndentation": true,
  "editor.autoIndent": "full"
}
```

### Formatting

```json
{
  "editor.formatOnSave": true,
  "editor.formatOnPaste": false,
  "editor.formatOnType": false,
  "editor.defaultFormatter": null
}
```

### IntelliSense

```json
{
  "editor.suggestSelection": "first",
  "editor.acceptSuggestionOnEnter": "on",
  "editor.quickSuggestions": {
    "other": true,
    "comments": false,
    "strings": false
  },
  "editor.parameterHints.enabled": true,
  "editor.inlayHints.enabled": "on"
}
```

## Workbench Settings

### Theme and Icons

```json
{
  "workbench.colorTheme": "Dracula",
  "workbench.iconTheme": "material-icon-theme",
  "workbench.productIconTheme": "material-product-icons"
}
```

### Startup

```json
{
  "workbench.startupEditor": "none",
  "workbench.editor.untitled.hint": "hidden"
}
```

### Sidebar

```json
{
  "workbench.sideBar.location": "left",
  "workbench.activityBar.location": "side",
  "explorer.compactFolders": false,
  "explorer.confirmDelete": false,
  "explorer.confirmDragAndDrop": false
}
```

### Tabs

```json
{
  "workbench.editor.showTabs": "multiple",
  "workbench.editor.tabSizing": "shrink",
  "workbench.editor.wrapTabs": false,
  "workbench.editor.closeOnFileDelete": true
}
```

## File Settings

### Auto Save

```json
{
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000
}
```

Options:
- `off` - Manual save only
- `afterDelay` - Save after delay
- `onFocusChange` - Save when focus leaves editor
- `onWindowChange` - Save when focus leaves VS Code

### File Associations

```json
{
  "files.associations": {
    "*.env*": "dotenv",
    "Dockerfile*": "dockerfile",
    ".prettierrc": "json"
  }
}
```

### Exclusions

```json
{
  "files.exclude": {
    "**/.git": true,
    "**/.DS_Store": true,
    "**/node_modules": true,
    "**/__pycache__": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true
  }
}
```

### Encoding and Line Endings

```json
{
  "files.encoding": "utf8",
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

## Language-Specific Settings

### Python

```json
{
  "[python]": {
    "editor.tabSize": 4,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic"
}
```

### JavaScript/TypeScript

```json
{
  "[javascript]": {
    "editor.tabSize": 2,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.tabSize": 2,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### JSON

```json
{
  "[json]": {
    "editor.tabSize": 2,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Markdown

```json
{
  "[markdown]": {
    "editor.wordWrap": "on",
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": false
  }
}
```

### HTML/CSS

```json
{
  "[html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[css]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Terminal Settings

```json
{
  "terminal.integrated.fontFamily": "JetBrains Mono",
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.lineHeight": 1.4,
  "terminal.integrated.defaultProfile.osx": "zsh",
  "terminal.integrated.scrollback": 10000,
  "terminal.integrated.copyOnSelection": true
}
```

## Git Settings

```json
{
  "git.enableSmartCommit": true,
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.openRepositoryInParentFolders": "always",
  "diffEditor.ignoreTrimWhitespace": false
}
```

## Privacy Settings

```json
{
  "telemetry.telemetryLevel": "off",
  "redhat.telemetry.enabled": false
}
```

## Workspace Configuration

### .vscode/settings.json

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "editor.tabSize": 2,
  "files.exclude": {
    "**/.coverage": true,
    "**/htmlcov": true
  }
}
```

### .vscode/extensions.json

Recommend extensions for project:

```json
{
  "recommendations": [
    "ms-python.python",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint"
  ]
}
```

## Full Configuration Example

```json
{
  "editor.fontFamily": "JetBrains Mono",
  "editor.fontSize": 14,
  "editor.fontLigatures": true,
  "editor.lineHeight": 1.6,
  "editor.minimap.enabled": false,
  "editor.formatOnSave": true,
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.rulers": [88, 120],
  "editor.renderWhitespace": "selection",
  "editor.suggestSelection": "first",
  "editor.inlayHints.enabled": "on",

  "workbench.colorTheme": "Dracula",
  "workbench.iconTheme": "material-icon-theme",
  "workbench.startupEditor": "none",
  "workbench.editor.showTabs": "multiple",

  "explorer.confirmDelete": false,
  "explorer.confirmDragAndDrop": false,

  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true
  },

  "terminal.integrated.fontFamily": "JetBrains Mono",
  "terminal.integrated.fontSize": 13,

  "git.enableSmartCommit": true,
  "git.autofetch": true,

  "telemetry.telemetryLevel": "off",

  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "python.languageServer": "Pylance",

  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  }
}
```
