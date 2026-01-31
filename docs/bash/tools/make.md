# Make

Make is a build automation tool that automatically builds executable programs and libraries from source code. While originally designed for C programs, Makefiles are widely used as task runners for any project.

## Basics

### Anatomy of a Makefile

```makefile
# Makefile

# Variables
CC = gcc
CFLAGS = -Wall -g

# Target: dependencies
#     recipe (must be TAB-indented!)
target: dependency1 dependency2
	command1
	command2

# Phony targets (not files)
.PHONY: clean test
```

### First Makefile

```makefile
# Makefile

.PHONY: all build test clean

all: build test

build:
	npm run build

test:
	npm test

clean:
	rm -rf dist node_modules
```

Run:

```bash
make              # Runs first target (all)
make build        # Runs build target
make clean        # Runs clean target
```

## Variables

### Defining Variables

```makefile
# Simple assignment (evaluated when used)
CC = gcc

# Immediate assignment (evaluated when defined)
CC := gcc

# Conditional assignment (only if not set)
CC ?= gcc

# Append
CFLAGS += -Wall

# Shell command
DATE := $(shell date +%Y-%m-%d)
GIT_SHA := $(shell git rev-parse --short HEAD)
```

### Using Variables

```makefile
CC = gcc
CFLAGS = -Wall -O2
SRC = main.c utils.c
OBJ = $(SRC:.c=.o)

build:
	$(CC) $(CFLAGS) -o app $(SRC)
```

### Automatic Variables

| Variable | Meaning |
|----------|---------|
| `$@` | Target name |
| `$<` | First dependency |
| `$^` | All dependencies |
| `$?` | Dependencies newer than target |
| `$*` | Stem (pattern match) |
| `$(@D)` | Directory of target |
| `$(@F)` | File name of target |

```makefile
%.o: %.c
	$(CC) -c $< -o $@
	# $< is the .c file, $@ is the .o file

app: main.o utils.o
	$(CC) $^ -o $@
	# $^ is "main.o utils.o", $@ is "app"
```

### Environment Variables

```makefile
# Use environment variable with default
PORT ?= 3000
NODE_ENV ?= development

dev:
	NODE_ENV=$(NODE_ENV) PORT=$(PORT) npm start
```

Override from command line:

```bash
make dev PORT=8080 NODE_ENV=production
```

## Targets

### Phony Targets

Targets that don't create files:

```makefile
.PHONY: all build test clean install

all: build test

build:
	npm run build

test:
	npm test

clean:
	rm -rf dist

install:
	npm install
```

### Default Target

The first target is the default:

```makefile
.DEFAULT_GOAL := all

all: build test
```

### Multiple Targets

```makefile
# Multiple targets with same recipe
clean mrproper:
	rm -rf dist

# Same as:
clean:
	rm -rf dist

mrproper:
	rm -rf dist
```

## Dependencies

### File Dependencies

```makefile
# Rebuild app if any source changes
app: main.c utils.c config.h
	$(CC) -o $@ main.c utils.c

# Rebuild dist if sources change
dist: $(wildcard src/*.ts)
	npm run build
```

### Order-Only Dependencies

Dependencies that must exist but don't trigger rebuild:

```makefile
# Create dist directory if needed, but don't rebuild if only dir changed
output: src/main.ts | dist
	npm run build

dist:
	mkdir -p dist
```

### Target Dependencies

```makefile
deploy: build test
	./deploy.sh

build:
	npm run build

test: build
	npm test
```

## Pattern Rules

### Implicit Rules

```makefile
# Any .o from .c
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Any .js from .ts
%.js: %.ts
	npx tsc $<

# Any file from template
%: %.template
	envsubst < $< > $@
```

### Static Pattern Rules

```makefile
OBJECTS = main.o utils.o parser.o

$(OBJECTS): %.o: %.c
	$(CC) -c $< -o $@
```

## Functions

### Text Functions

```makefile
SRC = src/main.c src/utils.c

# Substitution
OBJ = $(SRC:.c=.o)              # src/main.o src/utils.o
OBJ = $(patsubst %.c,%.o,$(SRC))  # Same result

# Directory and file
DIRS = $(dir $(SRC))            # src/ src/
FILES = $(notdir $(SRC))        # main.c utils.c
BASE = $(basename $(SRC))       # src/main src/utils
EXT = $(suffix $(SRC))          # .c .c

# Add prefix/suffix
OBJECTS = $(addprefix obj/,$(notdir $(SRC:.c=.o)))  # obj/main.o obj/utils.o

# Wildcard
SOURCES = $(wildcard src/*.c)

# Filter
C_FILES = $(filter %.c,$(FILES))
NOT_TESTS = $(filter-out %_test.c,$(FILES))

# Sort and unique
SORTED = $(sort z a m a)        # a m z
```

### Conditional Functions

```makefile
DEBUG ?= 0

CFLAGS = -Wall
ifeq ($(DEBUG), 1)
    CFLAGS += -g -DDEBUG
else
    CFLAGS += -O2
endif

# One-liner
CFLAGS += $(if $(DEBUG),-g,-O2)
```

### Shell Function

```makefile
DATE := $(shell date +%Y-%m-%d)
GIT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION := $(shell cat VERSION)
PWD := $(shell pwd)
```

## Conditionals

```makefile
# ifeq / ifneq
ifeq ($(OS),Windows_NT)
    RM = del /Q
else
    RM = rm -f
endif

# ifdef / ifndef
ifdef DEBUG
    CFLAGS += -g
endif

ifndef CC
    CC = gcc
endif

# Nested
ifeq ($(TARGET),linux)
    ifeq ($(ARCH),x86_64)
        CFLAGS += -m64
    endif
endif
```

## Include

```makefile
# Include other makefiles
include common.mk
include config.mk

# Optional include (no error if missing)
-include .env.mk
-include $(wildcard *.d)
```

## Complete Examples

### Node.js Project

```makefile
# Makefile for Node.js project

.PHONY: all build dev test lint format clean install deploy

# Variables
NODE_ENV ?= development
PORT ?= 3000

# Default target
all: install build test

# Install dependencies
install:
	npm ci

# Development server with watch
dev:
	NODE_ENV=development npm run dev

# Production build
build:
	NODE_ENV=production npm run build

# Run tests
test:
	npm test

test-watch:
	npm run test:watch

test-coverage:
	npm run test:coverage

# Linting
lint:
	npm run lint

lint-fix:
	npm run lint:fix

# Formatting
format:
	npm run format

format-check:
	npm run format:check

# Type checking
typecheck:
	npm run typecheck

# All checks
check: lint typecheck test

# Clean build artifacts
clean:
	rm -rf dist node_modules coverage .cache

# Docker
docker-build:
	docker build -t myapp:latest .

docker-run:
	docker run -p $(PORT):$(PORT) myapp:latest

# Deploy
deploy: check build
	./scripts/deploy.sh $(NODE_ENV)

# Help
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Start development server"
	@echo "  build       - Production build"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linter"
	@echo "  format      - Format code"
	@echo "  check       - Run all checks"
	@echo "  clean       - Remove build artifacts"
	@echo "  deploy      - Deploy to environment"
```

### Python Project

```makefile
# Makefile for Python project with uv

.PHONY: all install dev test lint format clean build publish

# Variables
PYTHON_VERSION ?= 3.12
VENV = .venv
BIN = $(VENV)/bin

# Default
all: install lint test

# Setup virtual environment
$(VENV):
	uv venv --python $(PYTHON_VERSION)

# Install dependencies
install: $(VENV)
	uv sync

# Install with dev dependencies
install-dev: $(VENV)
	uv sync --all-extras

# Development mode
dev: install-dev
	$(BIN)/python -m my_package

# Run tests
test: install-dev
	uv run pytest

test-coverage:
	uv run pytest --cov=src --cov-report=html

# Linting
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

# Type checking
typecheck:
	uv run mypy src/

# Formatting
format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# All checks
check: lint typecheck test

# Clean
clean:
	rm -rf $(VENV) dist build *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

# Build package
build: clean
	uv build

# Publish to PyPI
publish: build
	uv publish

# Docker
docker-build:
	docker build -t myapp:latest .

# Help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install dependencies"
	@echo "  dev          Run in development mode"
	@echo "  test         Run tests"
	@echo "  lint         Run linter"
	@echo "  format       Format code"
	@echo "  check        Run all checks"
	@echo "  build        Build package"
	@echo "  publish      Publish to PyPI"
	@echo "  clean        Clean build artifacts"
```

### Rust Project

```makefile
# Makefile for Rust project

.PHONY: all build release test lint format clean install

# Variables
CARGO = cargo
TARGET = target/release/myapp
INSTALL_DIR = /usr/local/bin

# Default
all: build

# Debug build
build:
	$(CARGO) build

# Release build
release:
	$(CARGO) build --release

# Run
run:
	$(CARGO) run

run-release:
	$(CARGO) run --release

# Test
test:
	$(CARGO) test

test-verbose:
	$(CARGO) test -- --nocapture

# Lint
lint:
	$(CARGO) clippy --all-targets --all-features -- -D warnings

# Format
format:
	$(CARGO) fmt

format-check:
	$(CARGO) fmt -- --check

# Check (fast compile check)
check:
	$(CARGO) check

# All checks
verify: format-check lint test

# Clean
clean:
	$(CARGO) clean

# Install locally
install: release
	install -m 755 $(TARGET) $(INSTALL_DIR)/

# Documentation
doc:
	$(CARGO) doc --open

# Benchmark
bench:
	$(CARGO) bench

# Update dependencies
update:
	$(CARGO) update

# Help
help:
	@echo "Targets:"
	@echo "  build    - Debug build"
	@echo "  release  - Release build"
	@echo "  test     - Run tests"
	@echo "  lint     - Run clippy"
	@echo "  format   - Format code"
	@echo "  verify   - All checks"
	@echo "  clean    - Clean artifacts"
	@echo "  install  - Install binary"
```

### Multi-Language Monorepo

```makefile
# Makefile for monorepo

.PHONY: all build test clean help

# Directories
BACKEND_DIR = backend
FRONTEND_DIR = frontend
SHARED_DIR = packages/shared

# Default
all: build

# Build all
build: build-shared build-backend build-frontend

build-shared:
	$(MAKE) -C $(SHARED_DIR) build

build-backend: build-shared
	$(MAKE) -C $(BACKEND_DIR) build

build-frontend: build-shared
	$(MAKE) -C $(FRONTEND_DIR) build

# Test all
test: test-shared test-backend test-frontend

test-shared:
	$(MAKE) -C $(SHARED_DIR) test

test-backend:
	$(MAKE) -C $(BACKEND_DIR) test

test-frontend:
	$(MAKE) -C $(FRONTEND_DIR) test

# Lint all
lint:
	$(MAKE) -C $(SHARED_DIR) lint
	$(MAKE) -C $(BACKEND_DIR) lint
	$(MAKE) -C $(FRONTEND_DIR) lint

# Clean all
clean:
	$(MAKE) -C $(SHARED_DIR) clean
	$(MAKE) -C $(BACKEND_DIR) clean
	$(MAKE) -C $(FRONTEND_DIR) clean

# Development
dev-backend:
	$(MAKE) -C $(BACKEND_DIR) dev

dev-frontend:
	$(MAKE) -C $(FRONTEND_DIR) dev

# Parallel dev (requires terminal multiplexer)
dev:
	@echo "Run in separate terminals:"
	@echo "  make dev-backend"
	@echo "  make dev-frontend"

# Docker
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Help
help:
	@echo "Monorepo Makefile"
	@echo ""
	@echo "Build targets:"
	@echo "  build           - Build all packages"
	@echo "  build-backend   - Build backend"
	@echo "  build-frontend  - Build frontend"
	@echo ""
	@echo "Test targets:"
	@echo "  test            - Test all packages"
	@echo ""
	@echo "Development:"
	@echo "  dev-backend     - Run backend dev server"
	@echo "  dev-frontend    - Run frontend dev server"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    - Build Docker images"
	@echo "  docker-up       - Start containers"
	@echo "  docker-down     - Stop containers"
```

## Tips and Tricks

### Self-Documenting Makefile

```makefile
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the project
	npm run build

test: ## Run tests
	npm test

deploy: ## Deploy to production
	./deploy.sh
```

### Verbose Mode

```makefile
V ?= 0
ifeq ($(V), 1)
    Q =
else
    Q = @
endif

build:
	$(Q)npm run build
```

```bash
make build      # Quiet
make build V=1  # Verbose
```

### Confirmation Prompt

```makefile
confirm:
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]

deploy-prod: confirm
	./deploy.sh production
```

### Timestamp Marker Files

```makefile
.PHONY: install
install: .installed

.installed: package.json package-lock.json
	npm ci
	touch .installed

clean:
	rm -f .installed
```

## Common Issues

### Tabs vs Spaces

Recipes MUST use tabs, not spaces:

```makefile
target:
	command   # This is a TAB
```

### .PHONY

Always declare phony targets to avoid conflicts with files:

```makefile
.PHONY: clean test build
```

### Shell Escaping

Use `$$` for shell variables:

```makefile
list:
	for f in *.txt; do echo $$f; done
```

## Related Tools

- [GitHub Actions](github-actions.md) - CI/CD automation
- [Git](git.md) - Version control
