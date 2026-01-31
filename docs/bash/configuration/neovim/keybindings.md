# Keybindings

Essential LazyVim keybindings for efficient editing.

## Leader Key

The leader key is ++space++. Most LazyVim commands start with the leader key.

Press ++space++ and wait to see available commands via which-key.

## Norwegian Keyboard Considerations

On Norwegian keyboards, several keys used frequently in Vim are harder to reach:

| Character | Norwegian Key | Vim Usage |
|-----------|---------------|-----------|
| `[` | ++alt+8++ | Navigation (prev) |
| `]` | ++alt+9++ | Navigation (next) |
| `` ` `` | ++shift+backslash++ | Marks |
| `\` | ++alt+shift+7++ | Some mappings |
| `{` | ++alt+shift+8++ | Paragraph motion |
| `}` | ++alt+shift+9++ | Paragraph motion |
| `~` | ++alt+k++ | Change case |

### Recommended Remappings

Add to `~/.config/nvim/lua/config/keymaps.lua`:

```lua
-- Norwegian keyboard-friendly navigation
-- Use ø and æ for bracket navigation (they're on the home row!)
vim.keymap.set({ "n", "x", "o" }, "ø", "[", { remap = true, desc = "[ key" })
vim.keymap.set({ "n", "x", "o" }, "æ", "]", { remap = true, desc = "] key" })

-- This means:
-- ø + d = previous diagnostic
-- æ + d = next diagnostic
-- ø + h = previous git hunk
-- æ + h = next git hunk
-- ø + b = previous buffer
-- æ + b = next buffer

-- Alternative: Leader-based navigation (works without remapping ø/æ)
vim.keymap.set("n", "<leader>dp", vim.diagnostic.goto_prev, { desc = "Prev diagnostic" })
vim.keymap.set("n", "<leader>dn", vim.diagnostic.goto_next, { desc = "Next diagnostic" })

-- Navigate quickfix
vim.keymap.set("n", "<leader>qp", "<cmd>cprev<cr>", { desc = "Prev quickfix" })
vim.keymap.set("n", "<leader>qn", "<cmd>cnext<cr>", { desc = "Next quickfix" })

-- Navigate buffers without brackets
vim.keymap.set("n", "<S-h>", "<cmd>bprevious<cr>", { desc = "Prev buffer" })
vim.keymap.set("n", "<S-l>", "<cmd>bnext<cr>", { desc = "Next buffer" })

-- Easier marks (backtick is hard to reach)
vim.keymap.set("n", "'", "`", { desc = "Jump to mark (exact)" })

-- Easier paragraph motion
vim.keymap.set({ "n", "x", "o" }, "Ø", "{", { desc = "Prev paragraph" })
vim.keymap.set({ "n", "x", "o" }, "Æ", "}", { desc = "Next paragraph" })
```

### Why ø and æ?

On Norwegian keyboards, `ø` and `æ` are:

- Located on the home row (right pinky)
- Rarely used in programming
- Single key press vs ++alt+8++ / ++alt+9++
- Natural left/right association (ø is left of æ)

This mapping lets you use all bracket-based navigation naturally.

## General

| Key | Action |
|-----|--------|
| ++space+space++ | Find files |
| ++space+comma++ | Switch buffer |
| ++space+colon++ | Command history |
| ++space+slash++ | Search in project (grep) |
| ++esc++ | Clear search highlight |
| ++ctrl+s++ | Save file |
| ++space+q+q++ | Quit all |

## File Operations

| Key | Action |
|-----|--------|
| ++space+f+f++ | Find files |
| ++space+f+r++ | Recent files |
| ++space+f+n++ | New file |
| ++space+f+t++ | File explorer (focus) |
| ++space+e++ | File explorer (toggle) |

## Buffers

| Key | Action |
|-----|--------|
| ++space+comma++ | Switch buffer |
| ++space+b+d++ | Delete buffer |
| ++space+b+o++ | Delete other buffers |
| ++shift+h++ | Previous buffer |
| ++shift+l++ | Next buffer |
| ++bracket-left+b++ | Previous buffer |
| ++bracket-right+b++ | Next buffer |

## Windows

| Key | Action |
|-----|--------|
| ++ctrl+h++ | Go to left window |
| ++ctrl+j++ | Go to lower window |
| ++ctrl+k++ | Go to upper window |
| ++ctrl+l++ | Go to right window |
| ++space+w+d++ | Delete window |
| ++space+w+minus++ | Split horizontal |
| ++space+w+pipe++ | Split vertical |
| ++space+bar++ | Split vertical (alt) |
| ++space+minus++ | Split horizontal (alt) |

### Window Resizing

| Key | Action |
|-----|--------|
| ++ctrl+up++ | Increase height |
| ++ctrl+down++ | Decrease height |
| ++ctrl+left++ | Decrease width |
| ++ctrl+right++ | Increase width |

## Search

| Key | Action |
|-----|--------|
| ++space+slash++ | Grep (search in files) |
| ++space+s+g++ | Grep (search in files) |
| ++space+s+w++ | Search word under cursor |
| ++space+s+b++ | Search in buffer |
| ++space+s+r++ | Replace in files |
| ++star++ | Search word forward |
| ++pound++ | Search word backward |
| ++n++ | Next search result |
| ++shift+n++ | Previous search result |

## Code Navigation (LSP)

| Key | Action |
|-----|--------|
| ++g+d++ | Go to definition |
| ++g+r++ | Go to references |
| ++g+i++ | Go to implementation |
| ++g+y++ | Go to type definition |
| ++g+shift+d++ | Go to declaration |
| ++shift+k++ | Hover documentation |
| ++space+c+a++ | Code actions |
| ++space+c+r++ | Rename symbol |
| ++space+c+f++ | Format document |
| ++bracket-left+d++ | Previous diagnostic |
| ++bracket-right+d++ | Next diagnostic |

## Code Editing

| Key | Action |
|-----|--------|
| ++g+c+c++ | Toggle line comment |
| ++g+c++ (visual) | Toggle comment selection |
| ++space+c+f++ | Format buffer |
| ++ctrl+space++ | Trigger completion |
| ++enter++ | Accept completion |
| ++ctrl+n++ / ++ctrl+p++ | Navigate completion |

## Git

| Key | Action |
|-----|--------|
| ++space+g+g++ | LazyGit |
| ++space+g+b++ | Git blame |
| ++space+g+d++ | Diff this |
| ++space+g+h++ | Hunk actions |
| ++bracket-left+h++ | Previous hunk |
| ++bracket-right+h++ | Next hunk |
| ++space+g+s++ | Stage hunk |
| ++space+g+r++ | Reset hunk |

## Telescope (Fuzzy Finder)

| Key | Action |
|-----|--------|
| ++space+space++ | Find files |
| ++space+slash++ | Grep |
| ++space+colon++ | Command history |
| ++space+f+f++ | Find files |
| ++space+f+r++ | Recent files |
| ++space+f+g++ | Find git files |
| ++space+s+s++ | Search symbols |
| ++space+s+h++ | Help tags |
| ++space+s+k++ | Keymaps |

### Inside Telescope

| Key | Action |
|-----|--------|
| ++ctrl+j++ / ++ctrl+k++ | Navigate results |
| ++ctrl+n++ / ++ctrl+p++ | Navigate results (alt) |
| ++enter++ | Open file |
| ++ctrl+x++ | Open in horizontal split |
| ++ctrl+v++ | Open in vertical split |
| ++ctrl+t++ | Open in new tab |
| ++esc++ / ++ctrl+c++ | Close |

## Neo-tree (File Explorer)

| Key | Action |
|-----|--------|
| ++space+e++ | Toggle explorer |
| ++space+f+e++ | Focus explorer |
| ++enter++ / ++o++ | Open file |
| ++a++ | Add file/directory |
| ++d++ | Delete |
| ++r++ | Rename |
| ++y++ | Copy to clipboard |
| ++x++ | Cut to clipboard |
| ++p++ | Paste from clipboard |
| ++period++ | Toggle hidden files |
| ++question++ | Help |

## Terminal

| Key | Action |
|-----|--------|
| ++space+f+t++ | Terminal (root dir) |
| ++space+f+shift+t++ | Terminal (cwd) |
| ++ctrl+slash++ | Toggle terminal |
| ++ctrl+backslash++ | Toggle terminal (alt) |

### Inside Terminal

| Key | Action |
|-----|--------|
| ++ctrl+backslash+backslash++ | Exit terminal mode |
| ++esc+esc++ | Exit terminal mode |

## Diagnostics & Quickfix

| Key | Action |
|-----|--------|
| ++space+x+x++ | Trouble diagnostics |
| ++space+x+shift+x++ | Trouble workspace diagnostics |
| ++space+x+l++ | Location list |
| ++space+x+q++ | Quickfix list |
| ++bracket-left+q++ | Previous quickfix |
| ++bracket-right+q++ | Next quickfix |

## Motion & Editing

### Text Objects

| Key | Action |
|-----|--------|
| `iw` / `aw` | Inner/around word |
| `ip` / `ap` | Inner/around paragraph |
| `i"` / `a"` | Inner/around double quotes |
| `i'` / `a'` | Inner/around single quotes |
| `i(` / `a(` | Inner/around parentheses |
| `i{` / `a{` | Inner/around braces |
| `i[` / `a[` | Inner/around brackets |
| `if` / `af` | Inner/around function |
| `ic` / `ac` | Inner/around class |

### Surround (mini.surround)

| Key | Action |
|-----|--------|
| `gza` | Add surrounding |
| `gzd` | Delete surrounding |
| `gzr` | Replace surrounding |
| `gzf` | Find surrounding forward |
| `gzF` | Find surrounding backward |

## UI Toggles

| Key | Action |
|-----|--------|
| ++space+u+c++ | Toggle colorcolumn |
| ++space+u+f++ | Toggle format on save |
| ++space+u+h++ | Toggle inlay hints |
| ++space+u+l++ | Toggle line numbers |
| ++space+u+shift+l++ | Toggle relative numbers |
| ++space+u+s++ | Toggle spell check |
| ++space+u+w++ | Toggle word wrap |
| ++space+u+shift+c++ | Toggle conceal |

## Folding

| Key | Action |
|-----|--------|
| ++z+c++ | Close fold |
| ++z+o++ | Open fold |
| ++z+shift+m++ | Close all folds |
| ++z+shift+r++ | Open all folds |
| ++z+a++ | Toggle fold |

## Marks & Jumps

| Key | Action |
|-----|--------|
| ++m++ + letter | Set mark |
| ++backtick++ + letter | Jump to mark |
| ++ctrl+o++ | Jump back |
| ++ctrl+i++ | Jump forward |
| ++g+semicolon++ | Previous change |
| ++g+comma++ | Next change |

## Macros

| Key | Action |
|-----|--------|
| ++q++ + letter | Start recording macro |
| ++q++ | Stop recording |
| ++at++ + letter | Play macro |
| ++at+at++ | Repeat last macro |

## Discovering Keybindings

Press ++space++ and wait for which-key to show available commands.

Search keybindings:

```vim
:Telescope keymaps
```

Or press ++space+s+k++.
