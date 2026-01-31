# Python Testing with pytest

pytest is the standard testing framework for Python projects.

## Installation

```bash
pip install pytest pytest-cov pytest-asyncio
```

## Basic Usage

### Running Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific file
pytest tests/test_user.py

# Run specific test
pytest tests/test_user.py::test_create_user

# Run tests matching pattern
pytest -k "user and not delete"

# Stop on first failure
pytest -x

# Run last failed
pytest --lf
```

### Test Discovery

pytest finds tests automatically:

```
project/
├── src/
│   └── mymodule/
│       └── user.py
└── tests/
    └── test_user.py   # Discovered
```

Naming conventions:
- Files: `test_*.py` or `*_test.py`
- Functions: `test_*`
- Classes: `Test*`

## Writing Tests

### Basic Test

```python
# tests/test_calculator.py
from mymodule.calculator import add, divide

def test_add():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0

def test_divide():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
```

### Test Classes

```python
class TestUser:
    def test_create_user(self):
        user = User("Alice", "alice@example.com")
        assert user.name == "Alice"

    def test_user_email_validation(self):
        with pytest.raises(ValueError):
            User("Alice", "invalid-email")
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert square(input) == expected

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

## Fixtures

### Basic Fixture

```python
import pytest

@pytest.fixture
def sample_user():
    return User(name="Test", email="test@example.com")

def test_user_greeting(sample_user):
    assert sample_user.greet() == "Hello, Test!"

def test_user_email(sample_user):
    assert sample_user.email == "test@example.com"
```

### Fixture Scope

```python
@pytest.fixture(scope="function")  # Default, runs per test
def function_fixture():
    return create_resource()

@pytest.fixture(scope="class")  # Once per test class
def class_fixture():
    return create_resource()

@pytest.fixture(scope="module")  # Once per module
def module_fixture():
    return create_resource()

@pytest.fixture(scope="session")  # Once per test session
def session_fixture():
    return create_resource()
```

### Setup and Teardown

```python
@pytest.fixture
def database():
    # Setup
    db = create_database()
    db.connect()

    yield db  # Test runs here

    # Teardown
    db.disconnect()
    db.cleanup()
```

### Fixture Dependencies

```python
@pytest.fixture
def database():
    return create_database()

@pytest.fixture
def user(database):
    return database.create_user("test")

def test_user_exists(database, user):
    assert database.get_user(user.id) is not None
```

### conftest.py

Shared fixtures across test files:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
```

## Mocking

### Using pytest-mock

```bash
pip install pytest-mock
```

```python
def test_api_call(mocker):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.json.return_value = {"status": "ok"}

    result = fetch_status()

    assert result == {"status": "ok"}
    mock_get.assert_called_once()
```

### Using unittest.mock

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    mock_service = Mock()
    mock_service.get_data.return_value = {"key": "value"}

    result = process_data(mock_service)

    assert result == "value"
    mock_service.get_data.assert_called_once()

def test_with_patch():
    with patch('mymodule.external_api') as mock_api:
        mock_api.return_value = {"data": "test"}
        result = my_function()
        assert result == "test"
```

### Patching Decorators

```python
@patch('mymodule.database.connect')
@patch('mymodule.external.api_call')
def test_with_multiple_patches(mock_api, mock_db):
    mock_db.return_value = Mock()
    mock_api.return_value = {"result": "success"}

    result = process()
    assert result == "success"
```

## Async Testing

```bash
pip install pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_fetch_data()
    assert result == expected_data

@pytest.fixture
async def async_client():
    client = await create_async_client()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_with_async_fixture(async_client):
    result = await async_client.get("/api/data")
    assert result.status == 200
```

## Testing Exceptions

```python
def test_raises_value_error():
    with pytest.raises(ValueError):
        validate_email("invalid")

def test_raises_with_message():
    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("invalid")

def test_raises_with_info():
    with pytest.raises(ValueError) as exc_info:
        validate_email("invalid")
    assert "invalid" in str(exc_info.value)
```

## Markers

### Built-in Markers

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_new_feature():
    pass

@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    assert buggy_function() == expected
```

### Custom Markers

```python
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests

# tests/test_example.py
@pytest.mark.slow
def test_slow_operation():
    ...

@pytest.mark.integration
def test_database_connection():
    ...
```

```bash
# Run only slow tests
pytest -m slow

# Skip integration tests
pytest -m "not integration"
```

## Coverage

### Configuration

```ini
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### Running with Coverage

```bash
# Generate coverage report
pytest --cov=src

# HTML report
pytest --cov=src --cov-report=html

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

## Project Configuration

### pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

## Best Practices

### Test Isolation

```python
# Good - each test is independent
def test_create_user(database):
    user = database.create_user("test")
    assert user.id is not None

def test_delete_user(database):
    user = database.create_user("test")
    database.delete_user(user.id)
    assert database.get_user(user.id) is None
```

### Clear Assertions

```python
# Good - clear what's being tested
def test_user_full_name():
    user = User(first="John", last="Doe")
    assert user.full_name == "John Doe"

# Bad - multiple unrelated assertions
def test_user():
    user = User(first="John", last="Doe")
    assert user.first == "John"
    assert user.last == "Doe"
    assert user.full_name == "John Doe"
    assert user.is_active == True
```

### Descriptive Names

```python
# Good
def test_empty_cart_has_zero_total():
    ...

def test_adding_item_increases_cart_total():
    ...

# Bad
def test_cart():
    ...

def test_cart2():
    ...
```

## See Also

- [Testing Overview](index.md)
- [JavaScript Testing](javascript.md)
- [GitHub Actions](../bash/tools/git/github-actions.md)
