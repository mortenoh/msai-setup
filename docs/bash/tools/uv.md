# uv

uv is an extremely fast Python package installer and resolver, written in Rust. Created by Astral (the makers of Ruff), it's designed as a drop-in replacement for pip and pip-tools, with speeds 10-100x faster than traditional tools.

## Installation

### macOS (Homebrew)

```bash
brew install uv
```

### Linux/macOS (Standalone)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### pipx

```bash
pipx install uv
```

## Quick Start

```bash
# Install a package
uv pip install requests

# Install from requirements file
uv pip install -r requirements.txt

# Create virtual environment
uv venv

# Sync project dependencies
uv sync
```

## Core Concepts

uv provides several commands:

| Command | Purpose |
|---------|---------|
| `uv pip` | pip-compatible interface |
| `uv venv` | Create virtual environments |
| `uv sync` | Sync project dependencies from pyproject.toml |
| `uv lock` | Generate/update lock file |
| `uv run` | Run commands in project environment |
| `uv add` | Add dependencies to project |
| `uv remove` | Remove dependencies from project |

## Virtual Environments

### Create Virtual Environment

```bash
# Create .venv in current directory
uv venv

# Create with specific name
uv venv myenv

# Create with specific Python version
uv venv --python 3.12
uv venv --python python3.11
uv venv --python /usr/bin/python3.10

# Create in specific location
uv venv /path/to/venv
```

### Activate Virtual Environment

```bash
# bash/zsh
source .venv/bin/activate

# fish
source .venv/bin/activate.fish

# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### Deactivate

```bash
deactivate
```

## pip-Compatible Interface

### Install Packages

```bash
# Install package
uv pip install requests

# Install specific version
uv pip install 'requests==2.31.0'
uv pip install 'requests>=2.28,<3.0'

# Install multiple packages
uv pip install requests flask pytest

# Install from requirements file
uv pip install -r requirements.txt

# Install with extras
uv pip install 'fastapi[all]'
uv pip install 'package[extra1,extra2]'

# Install editable (development mode)
uv pip install -e .
uv pip install -e '.[dev]'

# Install from git
uv pip install 'git+https://github.com/user/repo.git'
uv pip install 'git+https://github.com/user/repo.git@v1.0.0'
```

### Uninstall Packages

```bash
uv pip uninstall requests
uv pip uninstall requests flask pytest
```

### List Installed Packages

```bash
uv pip list
uv pip list --outdated
```

### Freeze Requirements

```bash
uv pip freeze > requirements.txt
```

### Show Package Info

```bash
uv pip show requests
```

## Project Management

### Initialize Project

Create a `pyproject.toml`:

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My awesome project"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.28",
    "click>=8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "ruff>=0.1",
]
```

### Sync Dependencies

```bash
# Create venv and install dependencies
uv sync

# Include optional/dev dependencies
uv sync --all-extras
uv sync --extra dev

# Update to latest compatible versions
uv sync --upgrade
```

### Add Dependencies

```bash
# Add runtime dependency
uv add requests
uv add 'requests>=2.28'

# Add development dependency
uv add --dev pytest ruff

# Add optional dependency
uv add --optional test pytest
```

### Remove Dependencies

```bash
uv remove requests
uv remove --dev pytest
```

### Lock Dependencies

```bash
# Generate/update uv.lock
uv lock

# Upgrade all dependencies in lock file
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package requests
```

## Running Commands

### uv run

Run commands in the project environment without manual activation:

```bash
# Run Python script
uv run python script.py

# Run module
uv run python -m pytest

# Run any command
uv run ruff check .
uv run mypy src/

# Run with additional packages (not in project)
uv run --with httpx python -c "import httpx; print(httpx.__version__)"
```

## uv-shell Helper Function

For interactive shell work, you can use a helper function that activates the project's virtual environment in your current shell:

```bash
# Add to ~/.bashrc or ~/.zshrc

uv-shell() {
  local want_sync=1
  local stay=0
  local print_only=0
  local proj=""

  # Parse arguments
  for arg in "$@"; do
    case "$arg" in
      --project=*) proj="${arg#*=}" ;;
      --no-sync) want_sync=0 ;;
      --stay) stay=1 ;;
      --print) print_only=1 ;;
      -h|--help)
        cat <<'EOF'
uv-shell - activate a uv-managed virtualenv in the current shell

Usage:
  uv-shell [--project DIR] [--no-sync] [--stay] [--print] [--help]

Options:
  --project DIR  Use this directory as the starting point
  --no-sync      Do not create the venv automatically (skip uv sync)
  --stay         Do not cd into the project root
  --print        Print the resolved project root and venv path, then exit
  -h, --help     Show this help
EOF
        return 0
        ;;
    esac
  done

  # Check uv is installed
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv-shell: 'uv' not found. Install: https://docs.astral.sh/uv/" >&2
    return 127
  fi

  # Find project root
  local start_dir="${proj:-$(pwd)}"
  local dir="$start_dir"
  while :; do
    if [[ -f "$dir/pyproject.toml" || -d "$dir/.venv" ]]; then
      break
    fi
    if [[ "$dir" == "/" ]]; then
      echo "uv-shell: no project found from '$start_dir'" >&2
      return 2
    fi
    dir="$(dirname "$dir")"
  done

  local proj_root="$dir"
  local venv_dir="$proj_root/.venv"

  if (( print_only )); then
    printf "project_root=%s\nvenv=%s\n" "$proj_root" "$venv_dir"
    return 0
  fi

  # Create venv if missing
  if [[ ! -d "$venv_dir" ]]; then
    if (( want_sync )); then
      echo "uv-shell: creating venv with 'uv sync' in $proj_root ..."
      ( cd "$proj_root" && uv sync ) || return 1
    else
      echo "uv-shell: venv missing and --no-sync specified" >&2
      return 1
    fi
  fi

  # Change to project directory
  if (( ! stay )); then
    cd "$proj_root" || return 1
  fi

  # Activate
  source "$venv_dir/bin/activate"
  echo "Activated: $(python -V) at $(which python)"
}

# Convenience function to deactivate
uv-deactivate() {
  if type deactivate >/dev/null 2>&1; then
    deactivate
  else
    echo "No active venv"
  fi
}
```

### Usage

```bash
# From anywhere in a project
uv-shell

# Stay in current directory
uv-shell --stay

# Start from specific path
uv-shell --project ~/dev/my-app

# Just show what it would do
uv-shell --print

# Skip auto-sync
uv-shell --no-sync
```

## pyproject.toml Examples

### Minimal Project

```toml
[project]
name = "my-app"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "requests",
]
```

### Full-Featured Project

```toml
[project]
name = "my-app"
version = "0.1.0"
description = "A sample Python project"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"},
]
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.100",
    "uvicorn[standard]>=0.23",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "httpx>=0.24",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.1",
    "ruff>=0.1",
    "mypy>=1.5",
    "pre-commit>=3.4",
]
docs = [
    "mkdocs-material>=9.0",
    "mkdocstrings[python]>=0.23",
]

[project.scripts]
my-app = "my_app.cli:main"

[project.urls]
Homepage = "https://github.com/user/my-app"
Documentation = "https://user.github.io/my-app"
Repository = "https://github.com/user/my-app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4",
    "ruff>=0.1",
]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Library Project

```toml
[project]
name = "my-library"
version = "0.1.0"
description = "A reusable Python library"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "typing-extensions>=4.0; python_version<'3.11'",
]

[project.optional-dependencies]
all = [
    "pandas>=2.0",
    "numpy>=1.24",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_library"]
```

## Common Workflows

### New Project

```bash
# Create project directory
mkdir my-project && cd my-project

# Create pyproject.toml (manually or use a template)

# Initialize environment
uv sync

# Start development
uv run python -m my_project
```

### Install Existing Project

```bash
git clone https://github.com/user/project.git
cd project
uv sync                    # Install dependencies
uv run pytest              # Run tests
```

### Upgrade Dependencies

```bash
# Upgrade all
uv lock --upgrade
uv sync

# Upgrade specific package
uv lock --upgrade-package requests
uv sync
```

### Development Workflow

```bash
# Start shell in project
uv-shell

# Or use uv run for one-off commands
uv run pytest
uv run ruff check .
uv run mypy src/
uv run python -m my_app
```

### Build and Publish

```bash
# Build distribution
uv pip install build
uv run python -m build

# Publish to PyPI
uv pip install twine
uv run twine upload dist/*
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `UV_CACHE_DIR` | Cache directory location |
| `UV_NO_CACHE` | Disable cache |
| `UV_PYTHON` | Default Python interpreter |
| `UV_SYSTEM_PYTHON` | Allow using system Python |
| `UV_LINK_MODE` | Linking mode (copy, hardlink, symlink) |
| `UV_CONCURRENT_DOWNLOADS` | Max concurrent downloads |
| `UV_PUBLISH_TOKEN` | PyPI token for publishing |

## Configuration

### Global Config

Create `~/.config/uv/uv.toml`:

```toml
[pip]
index-url = "https://pypi.org/simple"
extra-index-url = ["https://download.pytorch.org/whl/cu118"]

[cache]
dir = "~/.cache/uv"
```

### Per-Project Config

In `pyproject.toml`:

```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
]
```

## Performance Tips

1. **Use uv sync instead of pip install**: Faster resolution and installation
2. **Lock files**: Use `uv.lock` for reproducible builds
3. **Cache**: uv caches aggressively by default
4. **Parallel downloads**: uv downloads packages in parallel

## Comparison: uv vs pip

```bash
# pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt     # Slow

# uv
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt  # 10-100x faster

# Or better
uv sync                             # All in one
```

## Troubleshooting

### Python Version Not Found

```bash
# List available Python versions
uv python list

# Install specific version (if using uv python)
uv python install 3.12
```

### Cache Issues

```bash
# Clear cache
uv cache clean

# Or specific package
uv cache clean requests
```

### Resolution Conflicts

```bash
# Show resolution details
uv pip install requests --verbose

# Force reinstall
uv pip install --reinstall requests
```

## Related Tools

- [Python](https://www.python.org/) - Python programming language
- [Ruff](https://docs.astral.sh/ruff/) - Fast Python linter (also by Astral)
- [pyproject.toml](https://packaging.python.org/en/latest/specifications/pyproject-toml/) - Python project configuration
