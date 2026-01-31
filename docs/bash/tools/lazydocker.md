# lazydocker

lazydocker is a terminal UI for Docker, providing a visual interface for managing containers, images, volumes, and networks.

## Installation

### macOS (Homebrew)

```bash
brew install lazydocker
```

### Linux

```bash
# Download binary
curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash

# Or via package managers
# Arch Linux
pacman -S lazydocker

# Via Go
go install github.com/jesseduffield/lazydocker@latest
```

### Verify Installation

```bash
lazydocker --version
```

## Basic Usage

### Launch

```bash
lazydocker

# Short alias
lzd
```

### Interface Layout

```
+------------------+----------------------------------+
|    Containers    |           Main Panel             |
|       (1)        |    (Logs/Stats/Config/Top)       |
+------------------+                                  |
|     Images       |                                  |
|       (2)        |                                  |
+------------------+                                  |
|     Volumes      |                                  |
|       (3)        |                                  |
+------------------+                                  |
|    Networks      |                                  |
|       (4)        |                                  |
+------------------+----------------------------------+
```

### Navigation

| Key | Action |
|-----|--------|
| ++h++ / ++l++ | Switch panels |
| ++j++ / ++k++ | Move up/down |
| ++enter++ | Focus main panel |
| ++escape++ | Return to list |
| ++bracket-left++ / ++bracket-right++ | Scroll main panel |
| ++question++ | Show keybindings |

## Containers

### Container List

The containers panel shows all containers with status indicators:

- Green: Running
- Yellow: Paused
- Red: Stopped/Exited
- Gray: Created

### Container Actions

| Key | Action |
|-----|--------|
| ++d++ | Stop container |
| ++s++ | Start/stop toggle |
| ++r++ | Restart |
| ++a++ | Attach to container |
| ++shift+d++ | Remove container |
| ++e++ | Exec shell in container |
| ++shift+e++ | Exec custom command |
| ++l++ | View logs |
| ++c++ | Run docker-compose |
| ++enter++ | View details |

### View Logs

1. Select container
2. Press ++l++ or view in main panel
3. Use ++bracket-left++ / ++bracket-right++ to scroll

Log options in main panel:

| Key | Action |
|-----|--------|
| ++ctrl+f++ | Follow logs |
| ++ctrl+s++ | Search logs |
| ++t++ | Toggle timestamps |
| ++w++ | Wrap lines |

### Container Shell

1. Select container
2. Press ++e++ for shell access
3. Press ++ctrl+d++ or ++exit++ to return

### Container Stats

Select container and view in main panel:

- CPU usage
- Memory usage
- Network I/O
- Block I/O

Toggle views with ++1++ - ++4++ when container selected.

## Images

### Image Actions

| Key | Action |
|-----|--------|
| ++d++ | Delete image |
| ++shift+d++ | Force delete |
| ++enter++ | View layers |
| ++b++ | Build from Dockerfile |
| ++p++ | Push to registry |
| ++f++ | Filter images |

### Prune Images

Press ++p++ in images panel for prune options:

- Prune dangling images
- Prune all unused images

## Volumes

### Volume Actions

| Key | Action |
|-----|--------|
| ++d++ | Delete volume |
| ++enter++ | View details |
| ++p++ | Prune unused volumes |

### Volume Info

View in main panel:

- Mount point
- Size
- Created date
- Associated containers

## Networks

### Network Actions

| Key | Action |
|-----|--------|
| ++d++ | Delete network |
| ++enter++ | View details |
| ++p++ | Prune unused networks |

### Network Info

- Subnet/Gateway
- Connected containers
- Driver type

## Docker Compose

### Running Compose Commands

1. Press ++m++ for menu
2. Select compose action

Or use direct keys:

| Key | Action |
|-----|--------|
| ++u++ | Compose up |
| ++shift+u++ | Compose up --build |
| ++shift+d++ | Compose down |
| ++r++ | Compose restart |

### Project View

lazydocker automatically detects docker-compose projects and groups containers.

## Main Panel Views

Toggle with number keys when container selected:

| Key | View |
|-----|------|
| ++1++ | Logs |
| ++2++ | Stats |
| ++3++ | Config (inspect) |
| ++4++ | Top (processes) |

## Configuration

### Config File Location

```
~/.config/lazydocker/config.yml
```

### Example Configuration

```yaml
gui:
  scrollHeight: 2
  theme:
    activeBorderColor:
      - green
      - bold
    inactiveBorderColor:
      - white
  returnImmediately: false
  showAllContainers: true

logs:
  timestamps: false
  since: '60m'
  tail: 200

commandTemplates:
  dockerCompose: docker compose
  restartService: '{{ .DockerCompose }} restart {{ .Service.Name }}'

oS:
  openCommand: open {{filename}}
  openLinkCommand: open {{link}}

stats:
  graphs:
    - caption: CPU (%)
      statPath: DerivedStats.CPUPercentage
      color: cyan
    - caption: Memory (%)
      statPath: DerivedStats.MemoryPercentage
      color: green
```

### Custom Commands

```yaml
customCommands:
  containers:
    - name: "View container IP"
      attach: false
      command: "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' {{ .Container.ID }}"

    - name: "Export logs"
      attach: false
      command: "docker logs {{ .Container.ID }} > /tmp/{{ .Container.Name }}.log 2>&1"

  images:
    - name: "Scan for vulnerabilities"
      command: "docker scout cves {{ .Image.ID }}"
```

## Bulk Operations

### Select Multiple Items

| Key | Action |
|-----|--------|
| ++space++ | Toggle selection |
| ++ctrl+a++ | Select all |
| ++d++ | Delete selected |

### Prune All

Press ++shift+p++ for system prune options.

## Search and Filter

| Key | Action |
|-----|--------|
| ++slash++ | Start filter |
| ++escape++ | Clear filter |

Filter syntax:

```
# Filter by name
nginx

# Filter by status
status:running
status:exited

# Filter by label
label:env=prod
```

## Keybinding Reference

### Global

| Key | Action |
|-----|--------|
| ++question++ | Help |
| ++x++ | Menu |
| ++m++ | Docker menu |
| ++q++ | Quit |
| ++escape++ | Cancel/back |

### Containers

| Key | Action |
|-----|--------|
| ++s++ | Stop/start |
| ++d++ | Stop |
| ++r++ | Restart |
| ++e++ | Exec shell |
| ++a++ | Attach |
| ++l++ | Logs |
| ++shift+d++ | Remove |
| ++b++ | Bulk actions |

### All Panels

| Key | Action |
|-----|--------|
| ++d++ | Delete |
| ++p++ | Prune |
| ++f++ | Filter |
| ++enter++ | Details |

## Common Workflows

### Quick Container Management

1. Launch: `lazydocker`
2. Navigate to container: ++j++ / ++k++
3. View logs: ++1++ or ++l++
4. Shell access: ++e++

### Clean Up Resources

1. Press ++m++ for menu
2. Select "Prune containers"
3. Or use ++p++ in volumes/images for specific cleanup

### Monitor Container

1. Select container
2. Press ++2++ for stats
3. Watch CPU/memory in real-time

### Troubleshoot Container

1. Select container
2. View logs: ++1++
3. Search logs: ++ctrl+s++
4. Check config: ++3++
5. Shell in: ++e++

## Editor Integration

### Neovim

```lua
-- Custom keymap for lazydocker
vim.keymap.set("n", "<leader>D", function()
  require("toggleterm").exec("lazydocker")
end, { desc = "lazydocker" })
```

### VS Code Task

```json
{
  "label": "lazydocker",
  "type": "shell",
  "command": "lazydocker",
  "presentation": {
    "reveal": "always",
    "panel": "dedicated"
  }
}
```

## Recommended Aliases

```bash
alias lzd='lazydocker'
alias ld='lazydocker'
```

## Troubleshooting

### Permission Denied

Ensure user is in docker group:

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Docker Socket

If using custom socket:

```bash
DOCKER_HOST=unix:///var/run/docker.sock lazydocker
```

### Reset Config

```bash
rm ~/.config/lazydocker/config.yml
```

### Update

```bash
brew upgrade lazydocker
```
