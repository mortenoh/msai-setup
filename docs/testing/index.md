# Testing Guide

Testing best practices for Python, JavaScript, and shell scripts.

!!! note "Status in this repo: no test suite yet"
    This repository does **not** currently have a `tests/` directory or a
    `[tool.pytest.ini_options]` block in `pyproject.toml`. pytest is already
    listed in the `[dependency-groups] dev` group, but no tests have been
    written. The pages in this section are forward-looking guidance for **when**
    tests are added — they do not describe existing practice.

    When tests are added, use this project's real toolchain:

    - **`uv` for everything** — `uv sync` to install, `uv run pytest` to run.
      Do not use bare `pip install` (this project has no `[project.optional-dependencies]`
      extra; the dev tools live in a PEP 735 `[dependency-groups] dev` group).
    - **Python `>=3.14`** — matches `requires-python` and the mypy/pyright
      `python_version = "3.14"` settings in `pyproject.toml`.
    - **The linters that are already configured** — `ruff`, plus `mypy` and
      `pyright` in **strict** mode (`typeCheckingMode = "strict"`,
      `disallow_untyped_defs = true`) — run alongside pytest, not instead of it.
      The repo's `Makefile` already wires this up: `make lint` runs
      `uv run ruff` / `mypy` / `pyright`, and `make test` runs `uv run pytest`.

## In This Section

| Document | Description |
|----------|-------------|
| [Python Testing](python.md) | pytest and testing Python code |
| [JavaScript Testing](javascript.md) | Vitest, Jest, and frontend testing |
| [Bash Testing](bash.md) | Testing shell scripts |

## Testing Philosophy

### The Testing Pyramid

```
        /\
       /  \
      / E2E\        Few, slow, expensive
     /──────\
    / Integr-\      Some, medium speed
   /  ation   \
  /────────────\
 /    Unit      \   Many, fast, cheap
/________________\
```

### When to Write Tests

- **Unit tests**: Pure functions, business logic
- **Integration tests**: API endpoints, database operations
- **E2E tests**: Critical user flows

### What Not to Test

- Third-party libraries
- Trivial code (getters, setters)
- Private implementation details
- Generated code

## Quick Start

### Python (pytest)

```bash
# Install the dev toolchain (pytest is in the [dependency-groups] dev group)
uv sync

# Run tests
uv run pytest

# With coverage (add pytest-cov to the dev group first)
uv run pytest --cov=src
```

```python
# test_example.py
def test_addition():
    assert 1 + 1 == 2
```

### JavaScript (Vitest)

```bash
# Install
npm install -D vitest

# Run tests
npx vitest
```

```javascript
// example.test.js
import { describe, it, expect } from 'vitest'

describe('math', () => {
  it('adds numbers', () => {
    expect(1 + 1).toBe(2)
  })
})
```

### Bash (Bats)

```bash
# Install
npm install -g bats

# Run tests
bats tests/
```

```bash
# test_example.bats
@test "echo works" {
  result="$(echo hello)"
  [ "$result" = "hello" ]
}
```

## Test Structure

### Arrange-Act-Assert

```python
def test_user_creation():
    # Arrange
    name = "Alice"
    email = "alice@example.com"

    # Act
    user = create_user(name, email)

    # Assert
    assert user.name == name
    assert user.email == email
```

### Given-When-Then (BDD)

```python
def test_user_login():
    # Given a registered user
    user = create_user("alice", "password123")

    # When they attempt to login with correct credentials
    result = login("alice", "password123")

    # Then they should be authenticated
    assert result.authenticated is True
```

## Naming Conventions

### Test Files

```
Python:  test_module.py or module_test.py
JS:      module.test.js or module.spec.js
Bash:    test_script.bats
```

### Test Functions

```python
# Good - descriptive
def test_user_with_invalid_email_raises_error():
    ...

def test_calculate_discount_with_coupon_code():
    ...

# Bad - vague
def test_user():
    ...

def test_calculate():
    ...
```

## Fixtures and Mocking

### Python Fixtures

```python
import pytest

@pytest.fixture
def sample_user():
    return User(name="Test", email="test@example.com")

def test_user_greeting(sample_user):
    assert sample_user.greet() == "Hello, Test!"
```

### JavaScript Mocks

```javascript
import { vi, describe, it, expect } from 'vitest'

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API', () => {
  it('fetches data', async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ data: 'test' })
    })

    const result = await fetchData()
    expect(result.data).toBe('test')
  })
})
```

## CI Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          # Match requires-python >=3.14 and the mypy/pyright python_version
          python-version: '3.14'

      - name: Install dependencies
        run: uv sync

      - name: Lint and type-check (strict)
        run: |
          uv run ruff check .
          uv run mypy .
          uv run pyright

      - name: Run tests
        run: uv run pytest
```

## See Also

- [Python Testing](python.md)
- [JavaScript Testing](javascript.md)
- [GitHub Actions](../bash/tools/github-actions.md)
