VENV_DIR ?= .venv
UV := uv

.PHONY: help install lint test docs docs-serve docs-build clean

help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies with uv"
	@echo "  lint        - Run ruff, mypy, pyright"
	@echo "  test        - Run pytest"
	@echo "  docs        - Serve docs locally"
	@echo "  docs-build  - Build documentation"
	@echo "  clean       - Remove caches"

install:
	$(UV) sync

lint:
	@echo ">>> Running formatter"
	@$(UV) run ruff format .
	@$(UV) run ruff check . --fix
	@echo ">>> Running type checkers"
	@$(UV) run mypy .
	@$(UV) run pyright

test:
	$(UV) run pytest

docs docs-serve:
	$(UV) run mkdocs serve

docs-build:
	$(UV) run mkdocs build

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .pyright dist build site
