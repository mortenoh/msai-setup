# Styling

Starship provides extensive styling options for customizing colors, text effects, and symbols. This guide covers all aspects of visual customization.

## Style Strings

Style strings define how text appears in your prompt. They consist of space-separated attributes.

### Basic Syntax

```toml
style = "attribute1 attribute2 attribute3"
```

### Attributes

| Type | Examples |
|------|----------|
| Text effects | `bold`, `italic`, `underline`, `dimmed`, `inverted`, `blink` |
| Basic colors | `black`, `red`, `green`, `yellow`, `blue`, `purple`, `cyan`, `white` |
| Bright colors | `bright-black`, `bright-red`, `bright-green`, etc. |
| Foreground | `fg:red`, `fg:#ff5733`, `fg:123` |
| Background | `bg:blue`, `bg:#2e3440`, `bg:234` |

### Examples

```toml
# Bold green text
style = "bold green"

# Italic cyan
style = "italic cyan"

# Red background with white text
style = "fg:white bg:red"

# Dimmed and underlined
style = "dimmed underline"

# Hex color
style = "bold fg:#ff5733"

# 256 color
style = "fg:208"  # Orange
```

## Color Reference

### Basic Colors

| Color | Name | Typical Appearance |
|-------|------|-------------------|
| black | `black` | Black |
| red | `red` | Red |
| green | `green` | Green |
| yellow | `yellow` | Yellow |
| blue | `blue` | Blue |
| purple | `purple` | Purple/Magenta |
| cyan | `cyan` | Cyan |
| white | `white` | White/Light gray |

### Bright Colors

Bright variants are more vivid:

| Color | Name |
|-------|------|
| bright-black | `bright-black` |
| bright-red | `bright-red` |
| bright-green | `bright-green` |
| bright-yellow | `bright-yellow` |
| bright-blue | `bright-blue` |
| bright-purple | `bright-purple` |
| bright-cyan | `bright-cyan` |
| bright-white | `bright-white` |

### Hex Colors

Use any hex color with the `#RRGGBB` format:

```toml
style = "fg:#ff5733"      # Orange
style = "fg:#2ecc71"      # Green
style = "bg:#2e3440"      # Dark background
style = "fg:#e5e5e5 bg:#1e1e1e"  # Light on dark
```

!!! note "Terminal Support"
    Hex colors require a terminal that supports true color (24-bit color). Most modern terminals do, but some older ones may fall back to the nearest 256-color equivalent.

### 256 Colors

Reference colors by their 256-color palette number:

```toml
style = "fg:208"   # Orange
style = "fg:39"    # Blue
style = "fg:156"   # Light green
style = "bg:236"   # Dark gray background
```

See [256 color chart](https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit) for the full palette.

## Text Effects

### Bold

Makes text thicker/heavier:

```toml
[directory]
style = "bold blue"
```

### Italic

Slants text (terminal support varies):

```toml
[git_branch]
style = "italic purple"
```

### Underline

Adds underline:

```toml
[hostname]
style = "underline green"
```

### Dimmed

Reduces brightness:

```toml
[time]
style = "dimmed white"
```

### Inverted

Swaps foreground and background:

```toml
[status]
style = "inverted red"
```

### Blink

Text blinks (terminal support varies, often disabled):

```toml
[battery]
style = "bold red blink"  # Attention-grabbing for low battery
```

### Combining Effects

```toml
style = "bold italic underline bright-red"
```

## Foreground and Background

### Explicit Foreground

Use `fg:` prefix:

```toml
style = "fg:red"
style = "fg:#ff5733"
style = "fg:208"
```

### Explicit Background

Use `bg:` prefix:

```toml
style = "bg:blue"
style = "bg:#2e3440"
style = "fg:white bg:red"  # White text on red
```

### Combined Example

```toml
[kubernetes]
format = '[$symbol$context]($style) '
style = "fg:white bg:blue bold"
# White bold text on blue background
```

## Nerd Fonts

[Nerd Fonts](https://www.nerdfonts.com/) are patched fonts that include icons. They're recommended for the best Starship experience.

### Installation

=== "macOS (Homebrew)"

    ```bash
    brew tap homebrew/cask-fonts
    brew install --cask font-fira-code-nerd-font
    brew install --cask font-jetbrains-mono-nerd-font
    brew install --cask font-hack-nerd-font
    ```

=== "Linux"

    Download from [nerdfonts.com](https://www.nerdfonts.com/font-downloads):

    ```bash
    mkdir -p ~/.local/share/fonts
    cd ~/.local/share/fonts
    # Download and extract your chosen font
    fc-cache -fv
    ```

=== "Windows"

    Download from [nerdfonts.com](https://www.nerdfonts.com/font-downloads) and install via right-click.

### Configure Terminal

After installing, configure your terminal to use the Nerd Font:

- **iTerm2**: Preferences > Profiles > Text > Font
- **Terminal.app**: Preferences > Profiles > Font
- **Windows Terminal**: Settings > Profiles > Appearance > Font face
- **VS Code**: Settings > Terminal > Integrated: Font Family

### Popular Nerd Fonts

| Font | Style |
|------|-------|
| FiraCode Nerd Font | Programming ligatures |
| JetBrainsMono Nerd Font | Clean, modern |
| Hack Nerd Font | Classic monospace |
| MesloLGS Nerd Font | Recommended for Powerlevel10k |
| CaskaydiaCove Nerd Font | Cascadia Code variant |

### Default Symbols

Starship uses Nerd Font symbols by default. Common ones:

| Symbol | Meaning | Unicode |
|--------|---------|---------|
|  | Git branch | `\ue725` |
|  | Folder | `\uf07c` |
|  | Node.js | `\ue718` |
|  | Python | `\ue73c` |
|  | Rust | `\ue7a8` |
|  | Docker | `\uf308` |
|  | Kubernetes | `\u2388` |

## Symbols Without Nerd Fonts

If you can't use Nerd Fonts, configure text-based symbols:

```toml
[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"

[directory]
read_only = " ro"

[git_branch]
symbol = "git:"

[nodejs]
symbol = "node:"

[python]
symbol = "py:"

[rust]
symbol = "rs:"

[docker_context]
symbol = "docker:"

[kubernetes]
symbol = "k8s:"

[aws]
symbol = "aws:"

[package]
symbol = "pkg:"
```

## Color Palettes

Define reusable color palettes:

```toml
palette = "catppuccin_mocha"

[palettes.catppuccin_mocha]
rosewater = "#f5e0dc"
flamingo = "#f2cdcd"
pink = "#f5c2e7"
mauve = "#cba6f7"
red = "#f38ba8"
maroon = "#eba0ac"
peach = "#fab387"
yellow = "#f9e2af"
green = "#a6e3a1"
teal = "#94e2d5"
sky = "#89dceb"
sapphire = "#74c7ec"
blue = "#89b4fa"
lavender = "#b4befe"
text = "#cdd6f4"
subtext1 = "#bac2de"
subtext0 = "#a6adc8"
overlay2 = "#9399b2"
overlay1 = "#7f849c"
overlay0 = "#6c7086"
surface2 = "#585b70"
surface1 = "#45475a"
surface0 = "#313244"
base = "#1e1e2e"
mantle = "#181825"
crust = "#11111b"
```

Use palette colors:

```toml
[directory]
style = "bold sapphire"

[git_branch]
style = "bold mauve"
```

### Popular Palettes

**Nord:**

```toml
[palettes.nord]
polar_night_1 = "#2e3440"
polar_night_2 = "#3b4252"
polar_night_3 = "#434c5e"
polar_night_4 = "#4c566a"
snow_storm_1 = "#d8dee9"
snow_storm_2 = "#e5e9f0"
snow_storm_3 = "#eceff4"
frost_1 = "#8fbcbb"
frost_2 = "#88c0d0"
frost_3 = "#81a1c1"
frost_4 = "#5e81ac"
aurora_red = "#bf616a"
aurora_orange = "#d08770"
aurora_yellow = "#ebcb8b"
aurora_green = "#a3be8c"
aurora_purple = "#b48ead"
```

**Dracula:**

```toml
[palettes.dracula]
background = "#282a36"
current_line = "#44475a"
foreground = "#f8f8f2"
comment = "#6272a4"
cyan = "#8be9fd"
green = "#50fa7b"
orange = "#ffb86c"
pink = "#ff79c6"
purple = "#bd93f9"
red = "#ff5555"
yellow = "#f1fa8c"
```

## Complete Styling Example

A cohesive themed configuration:

```toml
palette = "custom"

[palettes.custom]
primary = "#61afef"
secondary = "#98c379"
warning = "#e5c07b"
error = "#e06c75"
muted = "#5c6370"
text = "#abb2bf"

format = """
$directory\
$git_branch\
$git_status\
$nodejs\
$python\
$rust\
$cmd_duration\
$line_break\
$character"""

[character]
success_symbol = "[->](bold secondary)"
error_symbol = "[->](bold error)"

[directory]
style = "bold primary"
truncation_length = 3

[git_branch]
format = "[$symbol$branch]($style) "
style = "bold secondary"
symbol = " "

[git_status]
format = '([$all_status$ahead_behind]($style) )'
style = "bold error"

[nodejs]
format = "[$symbol$version]($style) "
style = "bold secondary"
symbol = " "

[python]
format = '[$symbol$version(\($virtualenv\))]($style) '
style = "bold warning"
symbol = " "

[rust]
format = "[$symbol$version]($style) "
style = "bold error"
symbol = " "

[cmd_duration]
format = "[$duration]($style) "
style = "muted"
min_time = 2000

[time]
disabled = false
format = "[$time]($style)"
style = "muted"
```

## Terminal Compatibility

### Check True Color Support

Test if your terminal supports 24-bit color:

```bash
awk 'BEGIN{
    s="/\\/\\/\\/\\/\\"; s=s s s s s s s s;
    for (colession=0; colnum<77; colnum++) {
        r = 255-(colnum*255/76);
        g = (colnum*510/76);
        b = (colnum*255/76);
        if (g>255) g = 510-g;
        printf "\033[48;2;%d;%d;%dm", r,g,b;
        printf "\033[38;2;%d;%d;%dm", 255-r,255-g,255-b;
        printf "%s\033[0m", substr(s,colnum+1,1);
    }
    printf "\n";
}'
```

If you see a smooth gradient, true color is supported.

### Fallback for Limited Terminals

For terminals with limited color support:

```toml
# Use only basic 16 colors
[directory]
style = "bold blue"

[git_branch]
style = "bold purple"

[git_status]
style = "bold red"
```

## Tips

1. **Consistency**: Pick a palette and use it throughout
2. **Contrast**: Ensure text is readable against your terminal background
3. **Subtlety**: Use dimmed for less important information
4. **Emphasis**: Use bold and bright colors for important items
5. **Test**: Check how colors look in both light and dark terminal themes
