# Keybindings

Keyboard shortcuts and key customization in Zed.

## Base Keymaps

Zed supports different base keymaps:

```json
{
  "base_keymap": "VSCode"
}
```

Options:

- `VSCode` - VS Code-like keybindings
- `JetBrains` - JetBrains IDE keybindings
- `Sublime Text` - Sublime Text keybindings
- `Atom` - Atom editor keybindings
- `TextMate` - TextMate keybindings

## Essential Shortcuts

### File Operations

| Key | Action |
|-----|--------|
| ++cmd+p++ | Quick open file |
| ++cmd+shift+p++ | Command palette |
| ++cmd+n++ | New file |
| ++cmd+s++ | Save |
| ++cmd+shift+s++ | Save as |
| ++cmd+w++ | Close tab |
| ++cmd+shift+w++ | Close window |

### Navigation

| Key | Action |
|-----|--------|
| ++cmd+g++ | Go to line |
| ++cmd+shift+o++ | Go to symbol |
| ++ctrl+minus++ | Go back |
| ++ctrl+shift+minus++ | Go forward |
| ++cmd+shift+e++ | Focus file explorer |
| ++cmd+b++ | Toggle sidebar |

### Search

| Key | Action |
|-----|--------|
| ++cmd+f++ | Find in file |
| ++cmd+shift+f++ | Find in project |
| ++cmd+h++ | Find and replace |
| ++cmd+shift+h++ | Replace in project |
| ++f3++ / ++shift+f3++ | Find next/previous |
| ++cmd+d++ | Select next occurrence |
| ++cmd+shift+l++ | Select all occurrences |

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
| ++cmd+shift+slash++ | Toggle block comment |

### Multi-Cursor

| Key | Action |
|-----|--------|
| ++cmd+d++ | Add selection to next match |
| ++cmd+shift+l++ | Select all matches |
| ++alt+click++ | Add cursor |
| ++cmd+alt+up++ / ++cmd+alt+down++ | Add cursor above/below |
| ++esc++ | Exit multi-cursor |

### Code

| Key | Action |
|-----|--------|
| ++f12++ | Go to definition |
| ++alt+f12++ | Peek definition |
| ++shift+f12++ | Find references |
| ++f2++ | Rename symbol |
| ++cmd+period++ | Quick fix / code action |
| ++shift+alt+f++ | Format document |
| ++cmd+k+cmd+f++ | Format selection |

### View

| Key | Action |
|-----|--------|
| ++cmd+plus++ / ++cmd+minus++ | Zoom in/out |
| ++cmd+0++ | Reset zoom |
| ++cmd+backslash++ | Split editor right |
| ++cmd+k+cmd+backslash++ | Split editor down |
| ++cmd+1++ / ++cmd+2++ / ++cmd+3++ | Focus editor group |
| ++ctrl+backtick++ | Toggle terminal |

### Panels

| Key | Action |
|-----|--------|
| ++cmd+b++ | Toggle primary sidebar |
| ++cmd+shift+e++ | Show explorer |
| ++cmd+shift+f++ | Show search |
| ++cmd+shift+g++ | Show git |
| ++cmd+shift+x++ | Show extensions |

## Vim Mode

Enable vim mode:

```json
{
  "vim_mode": true
}
```

### Vim Mode Settings

```json
{
  "vim": {
    "use_system_clipboard": "always",
    "use_multiline_find": true,
    "use_smartcase_find": true
  }
}
```

### Vim Keybindings

Standard vim motions work:

| Key | Action |
|-----|--------|
| `h j k l` | Movement |
| `w b e` | Word movement |
| `0 $ ^` | Line movement |
| `gg G` | File start/end |
| `{ }` | Paragraph movement |
| `%` | Matching bracket |

Editing:

| Key | Action |
|-----|--------|
| `i a` | Insert mode |
| `o O` | Open line below/above |
| `d` | Delete |
| `c` | Change |
| `y` | Yank |
| `p P` | Paste after/before |
| `u` | Undo |
| ++ctrl+r++ | Redo |
| `.` | Repeat |

Visual mode:

| Key | Action |
|-----|--------|
| `v` | Visual mode |
| `V` | Visual line |
| ++ctrl+v++ | Visual block |

Text objects:

| Key | Action |
|-----|--------|
| `iw aw` | Inner/around word |
| `i" a"` | Inner/around quotes |
| `i( a(` | Inner/around parens |
| `i{ a{` | Inner/around braces |

### Vim Commands

| Command | Action |
|---------|--------|
| `:w` | Save |
| `:q` | Quit |
| `:wq` | Save and quit |
| `:e <file>` | Edit file |
| `:<number>` | Go to line |
| `:%s/old/new/g` | Replace all |

## Custom Keybindings

Create `~/.config/zed/keymap.json`:

```json
[
  {
    "context": "Editor",
    "bindings": {
      "ctrl+s": "workspace::Save",
      "ctrl+shift+s": "workspace::SaveAs"
    }
  }
]
```

### Binding Structure

```json
{
  "context": "Editor",
  "bindings": {
    "key combination": "action::Name"
  }
}
```

### Contexts

| Context | Description |
|---------|-------------|
| `Editor` | Text editor |
| `Workspace` | Main workspace |
| `Pane` | Editor pane |
| `Terminal` | Terminal panel |
| `ProjectPanel` | File explorer |
| `vim_mode == normal` | Vim normal mode |
| `vim_mode == insert` | Vim insert mode |
| `vim_mode == visual` | Vim visual mode |

### Common Actions

```json
[
  {
    "context": "Editor",
    "bindings": {
      "ctrl+shift+k": "editor::DeleteLine",
      "ctrl+shift+d": "editor::DuplicateLine",
      "ctrl+j": "editor::MoveLineDown",
      "ctrl+k": "editor::MoveLineUp",
      "ctrl+/": "editor::ToggleComments"
    }
  }
]
```

### Vim-Specific Bindings

```json
[
  {
    "context": "Editor && vim_mode == normal",
    "bindings": {
      "space f f": "file_finder::Toggle",
      "space f g": "workspace::NewSearch",
      "space e": "project_panel::ToggleFocus",
      "space g g": "terminal_panel::ToggleFocus"
    }
  }
]
```

### Remove Default Binding

```json
[
  {
    "context": "Editor",
    "bindings": {
      "ctrl+k": null
    }
  }
]
```

### Chord Sequences

```json
[
  {
    "context": "Editor",
    "bindings": {
      "ctrl+k ctrl+c": "editor::ToggleComments",
      "ctrl+k ctrl+u": "editor::UncommentLines"
    }
  }
]
```

## Finding Actions

Use the Command Palette (++cmd+shift+p++) to find action names.

Or check the default keybindings:

```bash
# View default keybindings
open ~/.config/zed/default-keymap.json
```

## Keybinding Examples

### Vim Leader Key

```json
[
  {
    "context": "Editor && vim_mode == normal",
    "bindings": {
      "space space": "file_finder::Toggle",
      "space /": "workspace::NewSearch",
      "space ,": "pane::AlternateFile",
      "space e": "project_panel::ToggleFocus",
      "space w": "workspace::Save",
      "space q": "pane::CloseActiveItem",
      "space b d": "pane::CloseActiveItem",
      "space c a": "editor::ToggleCodeActions",
      "space c r": "editor::Rename"
    }
  }
]
```

### Window Management

```json
[
  {
    "context": "Pane",
    "bindings": {
      "ctrl+h": ["workspace::ActivatePaneInDirection", "Left"],
      "ctrl+l": ["workspace::ActivatePaneInDirection", "Right"],
      "ctrl+k": ["workspace::ActivatePaneInDirection", "Up"],
      "ctrl+j": ["workspace::ActivatePaneInDirection", "Down"]
    }
  }
]
```

### Terminal

```json
[
  {
    "context": "Terminal",
    "bindings": {
      "ctrl+shift+c": "terminal::Copy",
      "ctrl+shift+v": "terminal::Paste",
      "ctrl+shift+n": "terminal::NewTerminal"
    }
  }
]
```

## Troubleshooting

### Key Not Working

1. Check for conflicts in Command Palette
2. Verify context is correct
3. Check action name is valid

### Find Conflicting Bindings

```bash
# Search keybindings
grep -r "ctrl+k" ~/.config/zed/keymap.json
```

### Reset to Defaults

```bash
rm ~/.config/zed/keymap.json
```
