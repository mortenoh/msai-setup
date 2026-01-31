# Bash Testing

Testing shell scripts with Bats (Bash Automated Testing System).

## Bats Installation

```bash
# npm
npm install -g bats

# Homebrew
brew install bats-core

# From source
git clone https://github.com/bats-core/bats-core.git
cd bats-core
./install.sh /usr/local
```

### Helper Libraries

```bash
# Install helpers
git clone https://github.com/bats-core/bats-support test/test_helper/bats-support
git clone https://github.com/bats-core/bats-assert test/test_helper/bats-assert
git clone https://github.com/bats-core/bats-file test/test_helper/bats-file
```

## Project Structure

```
project/
├── scripts/
│   └── my-script.sh
└── test/
    ├── test_helper/
    │   ├── bats-support/
    │   ├── bats-assert/
    │   └── bats-file/
    └── my-script.bats
```

## Basic Tests

### Simple Test

```bash
#!/usr/bin/env bats

@test "echo outputs text" {
  result="$(echo hello)"
  [ "$result" = "hello" ]
}

@test "exit code is 0 on success" {
  run echo "test"
  [ "$status" -eq 0 ]
}

@test "exit code is non-zero on failure" {
  run false
  [ "$status" -ne 0 ]
}
```

### Run Command

```bash
@test "my script runs successfully" {
  run ./scripts/my-script.sh
  [ "$status" -eq 0 ]
}

@test "my script outputs expected text" {
  run ./scripts/my-script.sh
  [ "$output" = "Expected output" ]
}

@test "my script handles arguments" {
  run ./scripts/my-script.sh --name "test"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "test" ]]
}
```

## Using Bats-Assert

```bash
#!/usr/bin/env bats

load 'test_helper/bats-support/load'
load 'test_helper/bats-assert/load'

@test "assert success" {
  run echo "hello"
  assert_success
}

@test "assert failure" {
  run false
  assert_failure
}

@test "assert output equals" {
  run echo "hello world"
  assert_output "hello world"
}

@test "assert output contains" {
  run echo "hello world"
  assert_output --partial "hello"
}

@test "assert output matches regex" {
  run echo "hello world"
  assert_output --regexp "^hello.*$"
}

@test "assert line" {
  run printf "line1\nline2\nline3"
  assert_line --index 0 "line1"
  assert_line --index 1 "line2"
}

@test "refute output" {
  run echo "hello"
  refute_output --partial "goodbye"
}
```

## Using Bats-File

```bash
#!/usr/bin/env bats

load 'test_helper/bats-support/load'
load 'test_helper/bats-assert/load'
load 'test_helper/bats-file/load'

@test "file exists" {
  touch /tmp/testfile
  assert_file_exists /tmp/testfile
  rm /tmp/testfile
}

@test "directory exists" {
  mkdir -p /tmp/testdir
  assert_dir_exists /tmp/testdir
  rmdir /tmp/testdir
}

@test "file contains text" {
  echo "hello world" > /tmp/testfile
  assert_file_contains /tmp/testfile "hello"
  rm /tmp/testfile
}

@test "file is executable" {
  touch /tmp/testscript
  chmod +x /tmp/testscript
  assert_file_executable /tmp/testscript
  rm /tmp/testscript
}
```

## Setup and Teardown

```bash
#!/usr/bin/env bats

# Run once before all tests
setup_file() {
  export TEST_DIR="$(mktemp -d)"
  export PATH="$BATS_TEST_DIRNAME/../scripts:$PATH"
}

# Run once after all tests
teardown_file() {
  rm -rf "$TEST_DIR"
}

# Run before each test
setup() {
  cd "$TEST_DIR"
}

# Run after each test
teardown() {
  rm -f "$TEST_DIR"/*
}

@test "test in temp directory" {
  touch testfile
  [ -f testfile ]
}
```

## Testing Functions

### Source and Test

```bash
#!/usr/bin/env bats

# Source the script to test
setup() {
  source ./scripts/functions.sh
}

@test "greet function outputs greeting" {
  result="$(greet "World")"
  [ "$result" = "Hello, World!" ]
}

@test "validate_email returns 0 for valid email" {
  run validate_email "test@example.com"
  [ "$status" -eq 0 ]
}

@test "validate_email returns 1 for invalid email" {
  run validate_email "invalid"
  [ "$status" -eq 1 ]
}
```

### Mocking Commands

```bash
@test "script calls curl" {
  # Create mock curl
  function curl() {
    echo '{"status": "ok"}'
  }
  export -f curl

  run ./scripts/fetch-data.sh
  assert_success
  assert_output --partial "ok"
}

@test "script handles curl failure" {
  function curl() {
    return 1
  }
  export -f curl

  run ./scripts/fetch-data.sh
  assert_failure
}
```

## Environment Variables

```bash
@test "script uses environment variable" {
  export MY_VAR="test_value"
  run ./scripts/my-script.sh
  assert_output --partial "test_value"
}

@test "script has default when var not set" {
  unset MY_VAR
  run ./scripts/my-script.sh
  assert_output --partial "default"
}
```

## Testing Exit Codes

```bash
@test "script exits 0 on success" {
  run ./scripts/my-script.sh valid-input
  assert_success
}

@test "script exits 1 on invalid input" {
  run ./scripts/my-script.sh invalid-input
  assert_failure
  [ "$status" -eq 1 ]
}

@test "script exits 2 on missing argument" {
  run ./scripts/my-script.sh
  [ "$status" -eq 2 ]
}
```

## Testing Standard Error

```bash
@test "script outputs error to stderr" {
  run ./scripts/my-script.sh invalid
  assert_failure

  # Check stderr (requires bats 1.5+)
  assert_output --partial "Error:"
}

# Alternative: capture stderr separately
@test "check stderr" {
  run bash -c './scripts/my-script.sh invalid 2>&1'
  [[ "$output" =~ "Error:" ]]
}
```

## Skipping Tests

```bash
@test "skip this test" {
  skip "Not implemented yet"
  # This code won't run
  run false
  assert_success
}

@test "skip on condition" {
  if [[ "$(uname)" != "Linux" ]]; then
    skip "Linux only"
  fi
  # Linux-specific test
}

@test "skip if command missing" {
  if ! command -v docker &> /dev/null; then
    skip "Docker not installed"
  fi
  run docker --version
  assert_success
}
```

## Running Tests

```bash
# Run all tests
bats test/

# Run specific file
bats test/my-script.bats

# Verbose output
bats --verbose-run test/

# TAP output
bats --tap test/

# Pretty output
bats --pretty test/

# Show timing
bats --timing test/

# Run in parallel
bats --jobs 4 test/
```

## CI Integration

### GitHub Actions

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Bats
        run: |
          git clone https://github.com/bats-core/bats-core.git
          cd bats-core && sudo ./install.sh /usr/local

      - name: Install helpers
        run: |
          git clone https://github.com/bats-core/bats-support test/test_helper/bats-support
          git clone https://github.com/bats-core/bats-assert test/test_helper/bats-assert

      - name: Run tests
        run: bats test/
```

## Best Practices

### Use Temporary Directories

```bash
setup() {
  TEST_TEMP_DIR="$(mktemp -d)"
}

teardown() {
  rm -rf "$TEST_TEMP_DIR"
}
```

### Make Tests Independent

```bash
# Good - each test sets up its own state
@test "test 1" {
  echo "data" > "$TEST_TEMP_DIR/file1"
  run cat "$TEST_TEMP_DIR/file1"
  assert_success
}

@test "test 2" {
  echo "other" > "$TEST_TEMP_DIR/file2"
  run cat "$TEST_TEMP_DIR/file2"
  assert_success
}
```

### Descriptive Test Names

```bash
# Good
@test "my-script exits with error when config file is missing" {
}

@test "my-script creates output directory if it does not exist" {
}

# Bad
@test "test 1" {
}

@test "test error" {
}
```

## See Also

- [Testing Overview](index.md)
- [Bash Scripting](../bash/scripting/index.md)
- [GitHub Actions](../bash/tools/git/github-actions.md)
