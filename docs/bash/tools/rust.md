# Rust

Rust is a systems programming language focused on safety, speed, and concurrency. It provides memory safety without garbage collection and is ideal for performance-critical applications, CLI tools, and WebAssembly.

## Installation

### Install rustup

rustup is the official Rust toolchain installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Add to your shell config (`~/.bashrc` or `~/.zshrc`):

```bash
# Load Rust environment
if [ -f "$HOME/.cargo/env" ]; then
  source "$HOME/.cargo/env"
fi
```

### Verify Installation

```bash
rustc --version
cargo --version
rustup --version
```

## rustup - Toolchain Manager

### Manage Toolchains

```bash
# Update Rust
rustup update
rustup update stable
rustup update nightly

# Install specific toolchain
rustup install stable
rustup install nightly
rustup install 1.75.0

# Set default toolchain
rustup default stable
rustup default nightly

# List installed toolchains
rustup toolchain list

# Remove toolchain
rustup toolchain uninstall nightly
```

### Components

```bash
# Add components
rustup component add rustfmt           # Code formatter
rustup component add clippy            # Linter
rustup component add rust-analyzer     # LSP server
rustup component add rust-src          # Source code

# List available components
rustup component list

# Add to specific toolchain
rustup component add clippy --toolchain nightly
```

### Cross-Compilation Targets

```bash
# List available targets
rustup target list

# Add target
rustup target add x86_64-unknown-linux-gnu
rustup target add x86_64-pc-windows-gnu
rustup target add wasm32-unknown-unknown
rustup target add aarch64-apple-darwin

# List installed targets
rustup target list --installed
```

### Override Toolchain

```bash
# Set toolchain for current directory
rustup override set nightly

# Remove override
rustup override unset
```

Or use `rust-toolchain.toml`:

```toml
[toolchain]
channel = "1.75.0"
components = ["rustfmt", "clippy"]
targets = ["x86_64-unknown-linux-gnu"]
```

## Cargo - Build System & Package Manager

### Create Projects

```bash
# New binary project
cargo new my-app
cargo new my-app --bin           # Explicit

# New library project
cargo new my-lib --lib

# Initialize in existing directory
cargo init
cargo init --lib
```

### Build & Run

```bash
# Build debug
cargo build

# Build release (optimized)
cargo build --release

# Build specific target
cargo build --target x86_64-unknown-linux-gnu

# Run
cargo run
cargo run --release
cargo run -- arg1 arg2           # Pass arguments

# Check (faster than build, no output)
cargo check
```

### Testing

```bash
# Run tests
cargo test

# Run specific test
cargo test test_name
cargo test module::test_name

# Run tests matching pattern
cargo test integration

# Run with output (println! visible)
cargo test -- --nocapture

# Run ignored tests
cargo test -- --ignored

# Run single-threaded
cargo test -- --test-threads=1

# Run doc tests only
cargo test --doc
```

### Documentation

```bash
# Build documentation
cargo doc

# Build and open in browser
cargo doc --open

# Include private items
cargo doc --document-private-items
```

### Dependencies

```bash
# Add dependency
cargo add serde
cargo add serde --features derive
cargo add tokio --features full
cargo add clap@4.4

# Add dev dependency
cargo add --dev mockall

# Add build dependency
cargo add --build cc

# Remove dependency
cargo remove serde

# Update dependencies
cargo update
cargo update -p serde            # Update specific package
```

### Other Commands

```bash
# Format code
cargo fmt

# Lint code
cargo clippy
cargo clippy --fix               # Auto-fix warnings

# Clean build artifacts
cargo clean

# Show dependency tree
cargo tree
cargo tree --duplicates          # Show duplicate dependencies

# Search crates.io
cargo search http

# Publish to crates.io
cargo publish

# Install binary
cargo install ripgrep
cargo install --path .           # Install from local project
```

## Cargo.toml

### Basic Structure

```toml
[package]
name = "my-project"
version = "0.1.0"
edition = "2021"
authors = ["Your Name <you@example.com>"]
description = "A sample Rust project"
license = "MIT"
repository = "https://github.com/user/repo"
readme = "README.md"
keywords = ["cli", "tool"]
categories = ["command-line-utilities"]

# Binary name (if different from package)
[[bin]]
name = "my-cli"
path = "src/main.rs"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
clap = { version = "4.4", features = ["derive"] }
anyhow = "1.0"
thiserror = "1.0"

[dev-dependencies]
mockall = "0.12"
criterion = "0.5"

[build-dependencies]
cc = "1.0"

[features]
default = ["json"]
json = ["serde_json"]
full = ["json", "yaml"]

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

### Dependency Specifications

```toml
[dependencies]
# From crates.io
serde = "1.0"                    # ^1.0.0
serde = "=1.0.190"               # Exact version
serde = ">=1.0, <2.0"            # Range

# With features
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", default-features = false, features = ["derive"] }

# From git
my-crate = { git = "https://github.com/user/repo" }
my-crate = { git = "https://github.com/user/repo", branch = "main" }
my-crate = { git = "https://github.com/user/repo", tag = "v1.0.0" }
my-crate = { git = "https://github.com/user/repo", rev = "abc123" }

# From path (local development)
my-crate = { path = "../my-crate" }

# Optional dependency
my-optional = { version = "1.0", optional = true }

# Platform-specific
[target.'cfg(windows)'.dependencies]
winapi = "0.3"

[target.'cfg(unix)'.dependencies]
nix = "0.27"
```

### Features

```toml
[features]
# Default features
default = ["std", "json"]

# Feature definitions
std = []
json = ["serde_json"]
yaml = ["serde_yaml"]
full = ["json", "yaml", "toml"]

# Enable optional dependency
http = ["dep:reqwest"]

[dependencies]
serde_json = { version = "1.0", optional = true }
serde_yaml = { version = "0.9", optional = true }
reqwest = { version = "0.11", optional = true }
```

Use features:

```bash
cargo build --features "json yaml"
cargo build --all-features
cargo build --no-default-features
cargo build --no-default-features --features "json"
```

### Profiles

```toml
[profile.dev]
opt-level = 0
debug = true
overflow-checks = true

[profile.release]
opt-level = 3
debug = false
lto = true                       # Link-time optimization
codegen-units = 1                # Better optimization
strip = true                     # Strip symbols
panic = "abort"                  # Smaller binary

[profile.test]
opt-level = 0
debug = true

[profile.bench]
opt-level = 3
debug = false

# Custom profile
[profile.release-with-debug]
inherits = "release"
debug = true
```

## Clippy - Linter

### Run Clippy

```bash
# Basic run
cargo clippy

# Treat warnings as errors
cargo clippy -- -D warnings

# Fix issues automatically
cargo clippy --fix

# Check specific categories
cargo clippy -- -W clippy::pedantic
cargo clippy -- -W clippy::nursery
```

### Configuration

Create `clippy.toml` or `.clippy.toml`:

```toml
# Cognitive complexity threshold
cognitive-complexity-threshold = 30

# Max function arguments
too-many-arguments-threshold = 10

# Max struct fields
too-many-lines-threshold = 200
```

Or in `Cargo.toml`:

```toml
[lints.clippy]
pedantic = "warn"
nursery = "warn"
unwrap_used = "deny"
expect_used = "warn"
```

### Attributes

```rust
// Allow specific lint
#[allow(clippy::too_many_arguments)]
fn my_function(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32) {}

// Deny specific lint
#![deny(clippy::unwrap_used)]

// Module level
#![warn(clippy::pedantic)]
```

## rustfmt - Code Formatter

### Run rustfmt

```bash
cargo fmt
cargo fmt --check                # Check without modifying
cargo fmt -- --emit files        # Show changed files
```

### Configuration

Create `rustfmt.toml` or `.rustfmt.toml`:

```toml
# Maximum line width
max_width = 100

# Use spaces, not tabs
hard_tabs = false
tab_spaces = 4

# Imports
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
reorder_imports = true

# Edition
edition = "2021"

# Newline style
newline_style = "Unix"

# Struct/enum formatting
struct_lit_width = 60
enum_discrim_align_threshold = 20

# Match arms
match_arm_blocks = true
match_block_trailing_comma = true

# Functions
fn_single_line = false
fn_params_layout = "Tall"

# Comments
wrap_comments = true
comment_width = 80
normalize_comments = true

# Use field init shorthand
use_field_init_shorthand = true

# Chains
chain_width = 60
```

## Cross-Compilation

### Setup Target

```bash
# Add target
rustup target add x86_64-unknown-linux-musl
rustup target add aarch64-apple-darwin

# Build for target
cargo build --target x86_64-unknown-linux-musl --release
```

### Linux on macOS

```bash
# Install musl toolchain
brew install filosottile/musl-cross/musl-cross

# Build
cargo build --target x86_64-unknown-linux-musl --release
```

### Cross Tool

```bash
# Install cross
cargo install cross

# Build for different platforms
cross build --target x86_64-unknown-linux-gnu
cross build --target aarch64-unknown-linux-gnu
```

### .cargo/config.toml

```toml
[build]
target = "x86_64-unknown-linux-gnu"

[target.x86_64-unknown-linux-musl]
linker = "x86_64-linux-musl-gcc"

[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"
```

## Common CLI Tools Written in Rust

```bash
# Install useful CLI tools
cargo install ripgrep            # rg - Fast grep
cargo install fd-find            # fd - Fast find
cargo install bat                # cat with syntax highlighting
cargo install eza                # Modern ls
cargo install tokei              # Code statistics
cargo install hyperfine          # Benchmarking
cargo install bottom             # System monitor (btm)
cargo install git-delta          # Git diff viewer
cargo install starship           # Cross-shell prompt
```

## Workspace

For monorepo with multiple packages:

```toml
# Cargo.toml (root)
[workspace]
resolver = "2"
members = [
    "crates/*",
    "apps/*",
]

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT"
authors = ["Your Name <you@example.com>"]

[workspace.dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
anyhow = "1.0"

[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
pedantic = "warn"
```

In member packages:

```toml
# crates/my-lib/Cargo.toml
[package]
name = "my-lib"
version.workspace = true
edition.workspace = true

[dependencies]
serde.workspace = true

[lints]
workspace = true
```

## Environment Variables

```bash
# Build-related
CARGO_HOME          # Cargo home directory (~/.cargo)
CARGO_TARGET_DIR    # Build output directory
RUSTFLAGS           # Compiler flags
RUSTDOCFLAGS        # Doc generation flags

# Runtime
RUST_LOG            # Logging level (with env_logger)
RUST_BACKTRACE      # Enable backtraces (1 or full)

# Example usage
RUST_LOG=debug cargo run
RUST_BACKTRACE=1 cargo run
RUSTFLAGS="-C target-cpu=native" cargo build --release
```

## Performance Optimization

### Cargo.toml Settings

```toml
[profile.release]
opt-level = 3                    # Max optimization
lto = "fat"                      # Full LTO
codegen-units = 1                # Better optimization
panic = "abort"                  # Smaller binary
strip = true                     # Strip symbols
```

### Build Flags

```bash
# Native CPU optimizations
RUSTFLAGS="-C target-cpu=native" cargo build --release

# Enable specific CPU features
RUSTFLAGS="-C target-feature=+avx2" cargo build --release
```

## Shell Completions

```bash
# Generate completions
rustup completions bash > ~/.local/share/bash-completion/completions/rustup
rustup completions zsh > ~/.zfunc/_rustup

# For cargo (if using cargo-completions)
cargo completions bash > ~/.local/share/bash-completion/completions/cargo
```

## Troubleshooting

### Slow Builds

```bash
# Use sccache
cargo install sccache
export RUSTC_WRAPPER=sccache

# Faster linker (mold on Linux, lld elsewhere)
# In .cargo/config.toml
[target.x86_64-unknown-linux-gnu]
linker = "clang"
rustflags = ["-C", "link-arg=-fuse-ld=mold"]
```

### Clean Build

```bash
cargo clean
cargo build
```

### Update Lock File

```bash
cargo update
```

## Related Tools

- [Git](git.md) - Version control
- [GitHub Actions](github-actions.md) - CI/CD for Rust
- [uv](uv.md) - Rust-based Python package manager
