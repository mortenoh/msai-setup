# Testing Guide

Testing best practices for Python, JavaScript, and shell scripts.

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
# Install
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=src
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

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

## See Also

- [Python Testing](python.md)
- [JavaScript Testing](javascript.md)
- [GitHub Actions](../bash/tools/github-actions.md)
