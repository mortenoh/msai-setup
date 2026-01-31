# Keybindings

Keyboard shortcuts and customization in VS Code.

## Essential Shortcuts

### General

| Key | Action |
|-----|--------|
| ++cmd+shift+p++ | Command Palette |
| ++cmd+p++ | Quick Open file |
| ++cmd+comma++ | Settings |
| ++cmd+k+cmd+s++ | Keyboard Shortcuts |
| ++cmd+backtick++ | Toggle Terminal |
| ++cmd+b++ | Toggle Sidebar |
| ++cmd+j++ | Toggle Panel |

### File Operations

| Key | Action |
|-----|--------|
| ++cmd+n++ | New File |
| ++cmd+o++ | Open File |
| ++cmd+s++ | Save |
| ++cmd+shift+s++ | Save As |
| ++cmd+w++ | Close Editor |
| ++cmd+shift+t++ | Reopen Closed Editor |

### Editing

| Key | Action |
|-----|--------|
| ++cmd+x++ | Cut line (no selection) |
| ++cmd+c++ | Copy line (no selection) |
| ++cmd+shift+k++ | Delete line |
| ++cmd+enter++ | Insert line below |
| ++cmd+shift+enter++ | Insert line above |
| ++alt+up++ / ++alt+down++ | Move line up/down |
| ++alt+shift+up++ / ++alt+shift+down++ | Copy line up/down |
| ++cmd+slash++ | Toggle line comment |
| ++alt+shift+a++ | Toggle block comment |
| ++cmd+bracket-left++ / ++cmd+bracket-right++ | Outdent/Indent line |

### Selection

| Key | Action |
|-----|--------|
| ++cmd+d++ | Select word / next occurrence |
| ++cmd+shift+l++ | Select all occurrences |
| ++cmd+l++ | Select line |
| ++ctrl+shift+cmd+left++ / ++ctrl+shift+cmd+right++ | Shrink/Expand selection |
| ++alt+shift+drag++ | Column selection |

### Multi-Cursor

| Key | Action |
|-----|--------|
| ++alt+click++ | Add cursor |
| ++cmd+alt+up++ / ++cmd+alt+down++ | Add cursor above/below |
| ++cmd+d++ | Add selection to next match |
| ++cmd+shift+l++ | Add cursors to all matches |
| ++esc++ | Exit multi-cursor |

### Navigation

| Key | Action |
|-----|--------|
| ++cmd+g++ | Go to Line |
| ++cmd+shift+o++ | Go to Symbol in file |
| ++cmd+t++ | Go to Symbol in workspace |
| ++ctrl+g++ | Go to Line |
| ++ctrl+minus++ | Go Back |
| ++ctrl+shift+minus++ | Go Forward |
| ++cmd+shift+backslash++ | Jump to matching bracket |

### Search

| Key | Action |
|-----|--------|
| ++cmd+f++ | Find |
| ++cmd+h++ | Replace |
| ++cmd+shift+f++ | Search in Files |
| ++cmd+shift+h++ | Replace in Files |
| ++f3++ / ++shift+f3++ | Find Next/Previous |
| ++enter++ / ++shift+enter++ | Find Next/Previous (in find dialog) |
| ++alt+enter++ | Select all matches |

### Code Intelligence

| Key | Action |
|-----|--------|
| ++f12++ | Go to Definition |
| ++alt+f12++ | Peek Definition |
| ++shift+f12++ | Find All References |
| ++cmd+k+f12++ | Open Definition to Side |
| ++f2++ | Rename Symbol |
| ++cmd+period++ | Quick Fix |
| ++ctrl+space++ | Trigger Suggest |
| ++cmd+shift+space++ | Trigger Parameter Hints |
| ++shift+alt+f++ | Format Document |
| ++cmd+k+cmd+f++ | Format Selection |

### View

| Key | Action |
|-----|--------|
| ++cmd+plus++ / ++cmd+minus++ | Zoom In/Out |
| ++cmd+0++ | Reset Zoom |
| ++cmd+backslash++ | Split Editor |
| ++cmd+1++ / ++cmd+2++ / ++cmd+3++ | Focus Editor Group |
| ++cmd+k+left++ / ++cmd+k+right++ | Move Editor to Group |
| ++cmd+w++ | Close Editor |
| ++cmd+k+w++ | Close All Editors |

### Terminal

| Key | Action |
|-----|--------|
| ++ctrl+backtick++ | Toggle Terminal |
| ++ctrl+shift+backtick++ | Create New Terminal |
| ++cmd+backslash++ | Split Terminal |
| ++cmd+up++ / ++cmd+down++ | Scroll Up/Down |

## Custom Keybindings

### Opening Keybindings

1. ++cmd+k+cmd+s++ or
2. ++cmd+shift+p++ > "Preferences: Open Keyboard Shortcuts (JSON)"

### keybindings.json Structure

```json
[
  {
    "key": "cmd+k cmd+c",
    "command": "editor.action.addCommentLine",
    "when": "editorTextFocus"
  }
]
```

### Keybinding Properties

| Property | Description |
|----------|-------------|
| `key` | Key combination |
| `command` | Command to execute |
| `when` | Context condition |
| `args` | Command arguments |

### Key Modifiers

| Modifier | macOS | Windows/Linux |
|----------|-------|---------------|
| ++cmd++ | `cmd` | `ctrl` |
| ++ctrl++ | `ctrl` | `ctrl` |
| ++alt++ | `alt` | `alt` |
| ++shift++ | `shift` | `shift` |

### Chord Sequences

```json
{
  "key": "cmd+k cmd+c",
  "command": "editor.action.addCommentLine"
}
```

### When Clauses

Common contexts:

| Context | Description |
|---------|-------------|
| `editorTextFocus` | Editor has focus |
| `terminalFocus` | Terminal has focus |
| `inDebugMode` | Debugging active |
| `editorHasSelection` | Text is selected |
| `editorLangId == python` | Python file open |

Example:

```json
{
  "key": "cmd+shift+t",
  "command": "python.runFile",
  "when": "editorLangId == python"
}
```

### Remove Default Binding

```json
{
  "key": "cmd+k",
  "command": "-editor.action.addCommentLine"
}
```

## Common Customizations

### Vim-Style Navigation

```json
[
  {
    "key": "ctrl+h",
    "command": "workbench.action.navigateLeft"
  },
  {
    "key": "ctrl+l",
    "command": "workbench.action.navigateRight"
  },
  {
    "key": "ctrl+k",
    "command": "workbench.action.navigateUp"
  },
  {
    "key": "ctrl+j",
    "command": "workbench.action.navigateDown"
  }
]
```

### Quick File Operations

```json
[
  {
    "key": "cmd+shift+d",
    "command": "editor.action.copyLinesDownAction"
  },
  {
    "key": "cmd+shift+c",
    "command": "workbench.action.files.copyPathOfActiveFile"
  }
]
```

### Terminal Shortcuts

```json
[
  {
    "key": "cmd+t",
    "command": "workbench.action.terminal.new",
    "when": "terminalFocus"
  },
  {
    "key": "cmd+w",
    "command": "workbench.action.terminal.kill",
    "when": "terminalFocus"
  }
]
```

## Vim Extension

Install Vim extension for modal editing:

1. ++cmd+shift+x++ > Search "Vim"
2. Install "Vim" by vscodevim

### Vim Settings

```json
{
  "vim.useSystemClipboard": true,
  "vim.hlsearch": true,
  "vim.leader": "<space>",
  "vim.normalModeKeyBindings": [
    {
      "before": ["<leader>", "f", "f"],
      "commands": ["workbench.action.quickOpen"]
    },
    {
      "before": ["<leader>", "f", "g"],
      "commands": ["workbench.action.findInFiles"]
    }
  ]
}
```

### Vim-Specific Bindings

```json
{
  "vim.insertModeKeyBindings": [
    {
      "before": ["j", "k"],
      "after": ["<Esc>"]
    }
  ],
  "vim.normalModeKeyBindingsNonRecursive": [
    {
      "before": ["<leader>", "w"],
      "commands": [":w"]
    },
    {
      "before": ["<leader>", "q"],
      "commands": [":q"]
    }
  ]
}
```

## Finding Commands

### Command Palette

++cmd+shift+p++ shows all commands with their keybindings.

### Keyboard Shortcuts UI

++cmd+k+cmd+s++ to:

- Search commands
- See current bindings
- Record key combination
- Change bindings

### Default Keybindings Reference

++cmd+k+cmd+r++ opens the default keybindings reference.

## Troubleshooting

### Keybinding Not Working

1. Check for conflicts: ++cmd+k+cmd+s++ > Search for key
2. Check `when` clause is satisfied
3. Check extension keybindings

### Find Conflicting Bindings

In Keyboard Shortcuts UI:

1. Click "Record Keys" icon
2. Press the key combination
3. See all commands bound to it

### Reset Keybindings

Delete `keybindings.json` to reset to defaults:

```bash
rm ~/Library/Application\ Support/Code/User/keybindings.json
```

## Platform-Specific

### macOS to Windows/Linux

| macOS | Windows/Linux |
|-------|---------------|
| ++cmd++ | ++ctrl++ |
| ++alt++ | ++alt++ |
| ++ctrl++ | ++ctrl++ |

Most shortcuts use ++cmd++ on macOS and ++ctrl++ on Windows/Linux.

### Sync Across Platforms

VS Code settings sync handles platform-specific keybindings automatically.
