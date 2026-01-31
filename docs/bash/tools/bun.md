# Bun

Bun is an all-in-one JavaScript runtime, bundler, transpiler, and package manager. Built in Zig with JavaScriptCore (Safari's engine), it's designed for speed and offers significant performance improvements over Node.js for many workloads.

## Installation

### macOS (Homebrew)

```bash
brew install oven-sh/bun/bun
```

### Linux/macOS (Shell)

```bash
curl -fsSL https://bun.sh/install | bash
```

### Upgrade

```bash
bun upgrade
bun upgrade --canary                 # Canary version
```

## Quick Start

```bash
# Run a script
bun run script.ts
bun script.ts                        # Shorthand

# Run package.json script
bun run dev
bun dev                              # Shorthand

# Install packages
bun install
bun add express
bun add -d typescript                # Dev dependency

# Start REPL
bun repl
```

## Package Management

Bun is a drop-in replacement for npm/yarn/pnpm with dramatic speed improvements.

### Install Packages

```bash
# Install all dependencies
bun install
bun i                                # Shorthand

# Add dependencies
bun add express zod
bun add -d typescript vitest         # Dev dependencies
bun add -g typescript                # Global

# Add specific version
bun add react@18.2.0
bun add 'react@^18.0.0'

# Add from git
bun add github:user/repo
bun add github:user/repo#branch

# Install without running postinstall scripts
bun install --ignore-scripts
```

### Remove Packages

```bash
bun remove express
bun rm express                       # Shorthand
```

### Update Packages

```bash
bun update                           # Update all
bun update express                   # Update specific
```

### List Packages

```bash
bun pm ls                            # List dependencies
bun pm ls --all                      # Include transitive
```

### Cache Management

```bash
bun pm cache                         # Cache location
bun pm cache rm                      # Clear cache
```

### Lockfile

Bun uses `bun.lockb` (binary lockfile) for fast parsing:

```bash
# Generate text version for debugging
bun install --yarn                   # Creates yarn.lock too
```

## Running Code

### Run Files

```bash
bun run index.ts                     # TypeScript
bun run index.js                     # JavaScript
bun run index.jsx                    # JSX
bun index.ts                         # Shorthand

# With arguments
bun run script.ts -- --port 3000
```

### Run package.json Scripts

```bash
bun run dev                          # Run "dev" script
bun dev                              # Shorthand (if no file named "dev")
bun run build
bun run test
```

### Execute Packages

```bash
# Run package binary (like npx)
bunx cowsay "Hello"
bunx create-react-app my-app
bunx vitest run

# Without bunx (if globally installed)
bun x cowsay "Hello"
```

## Project Setup

### Initialize Project

```bash
bun init                             # Interactive
bun init -y                          # Accept defaults
```

### package.json

```json
{
  "name": "my-bun-project",
  "version": "1.0.0",
  "module": "src/index.ts",
  "type": "module",
  "scripts": {
    "dev": "bun --watch src/index.ts",
    "start": "bun src/index.ts",
    "build": "bun build src/index.ts --outdir dist",
    "test": "bun test"
  },
  "dependencies": {
    "hono": "^4.0.0"
  },
  "devDependencies": {
    "@types/bun": "latest",
    "typescript": "^5.3.0"
  }
}
```

### bunfig.toml

Optional configuration file:

```toml
# bunfig.toml

# Package management
[install]
# Where to install packages
optional = true
dev = true
peer = false

# Scoped registry
[install.scopes]
"@myorg" = "https://npm.myorg.com/"

# Environment variables for scripts
[run]
shell = "/bin/bash"

# Development server
[serve]
port = 3000

# Test configuration
[test]
coverage = true
coverageDir = "coverage"

# Bundler configuration
[build]
target = "browser"
minify = true
```

## HTTP Server

### Using Bun.serve()

```typescript
// src/server.ts
const server = Bun.serve({
  port: 3000,
  fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      return new Response("Hello, World!");
    }

    if (url.pathname === "/api/data") {
      return Response.json({ message: "Hello", timestamp: Date.now() });
    }

    if (url.pathname === "/api/echo" && request.method === "POST") {
      return request.json().then(body =>
        Response.json({ received: body })
      );
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`Server running at http://localhost:${server.port}`);
```

### Using Hono Framework

```typescript
// src/server.ts
import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

const app = new Hono();

// Middleware
app.use("*", logger());
app.use("/api/*", cors());

// Routes
app.get("/", (c) => c.text("Hello, World!"));

app.get("/api/users/:id", (c) => {
  const id = c.req.param("id");
  return c.json({ id, name: `User ${id}` });
});

app.post("/api/users", async (c) => {
  const body = await c.req.json();
  return c.json({ created: true, ...body });
});

// Error handling
app.onError((err, c) => {
  console.error(err);
  return c.json({ error: "Internal Server Error" }, 500);
});

export default app;
```

### WebSocket

```typescript
const server = Bun.serve({
  port: 3000,
  fetch(req, server) {
    // Upgrade to WebSocket
    if (server.upgrade(req)) {
      return; // Upgraded
    }
    return new Response("Not a WebSocket request", { status: 400 });
  },
  websocket: {
    open(ws) {
      console.log("Client connected");
      ws.send("Welcome!");
    },
    message(ws, message) {
      console.log("Received:", message);
      ws.send(`Echo: ${message}`);
    },
    close(ws) {
      console.log("Client disconnected");
    },
  },
});
```

## File I/O

### Read Files

```typescript
// Read as text
const text = await Bun.file("file.txt").text();

// Read as JSON
const data = await Bun.file("data.json").json();

// Read as ArrayBuffer
const buffer = await Bun.file("image.png").arrayBuffer();

// Read as stream
const stream = Bun.file("large.txt").stream();

// File info
const file = Bun.file("file.txt");
console.log(file.size);           // Size in bytes
console.log(file.type);           // MIME type
```

### Write Files

```typescript
// Write text
await Bun.write("output.txt", "Hello, World!");

// Write JSON
await Bun.write("data.json", JSON.stringify({ key: "value" }));

// Write from Response
const response = await fetch("https://example.com/data.json");
await Bun.write("downloaded.json", response);

// Write from another file
await Bun.write("copy.txt", Bun.file("original.txt"));
```

### File Watching

```typescript
const watcher = Bun.spawn({
  cmd: ["bun", "--watch", "src/index.ts"],
});

// Or programmatically
import { watch } from "fs";

watch("./src", { recursive: true }, (event, filename) => {
  console.log(`${event}: ${filename}`);
});
```

## Bundler

### Bundle for Browser

```bash
# CLI
bun build src/index.ts --outdir dist --target browser --minify

# With source maps
bun build src/index.ts --outdir dist --sourcemap
```

### Bundle API

```typescript
const result = await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  target: "browser",
  minify: true,
  sourcemap: "external",
  splitting: true,        // Code splitting
  format: "esm",          // or "cjs"
  naming: "[name].[hash].[ext]",
  external: ["react", "react-dom"],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
});

if (!result.success) {
  for (const message of result.logs) {
    console.error(message);
  }
}
```

### Compile to Executable

```bash
bun build src/index.ts --compile --outfile app
./app                                # Run standalone executable
```

## Testing

### Write Tests

```typescript
// src/math.test.ts
import { describe, expect, test, beforeEach, mock } from "bun:test";
import { add, divide } from "./math";

test("add function", () => {
  expect(add(2, 3)).toBe(5);
  expect(add(-1, 1)).toBe(0);
});

describe("divide", () => {
  test("divides two numbers", () => {
    expect(divide(10, 2)).toBe(5);
  });

  test("throws on division by zero", () => {
    expect(() => divide(10, 0)).toThrow("Cannot divide by zero");
  });
});

// Async tests
test("async operation", async () => {
  const result = await fetchData();
  expect(result.status).toBe("ok");
});

// Mocking
const mockFn = mock(() => "mocked");
test("mock function", () => {
  mockFn();
  expect(mockFn).toHaveBeenCalled();
  expect(mockFn.mock.calls.length).toBe(1);
});

// Snapshot testing
test("snapshot", () => {
  const obj = { name: "test", items: [1, 2, 3] };
  expect(obj).toMatchSnapshot();
});
```

### Run Tests

```bash
bun test                             # Run all tests
bun test src/math.test.ts            # Specific file
bun test --watch                     # Watch mode
bun test --coverage                  # With coverage
bun test --timeout 10000             # Custom timeout
bun test --bail                      # Stop on first failure
```

### Test Configuration

In `bunfig.toml`:

```toml
[test]
preload = ["./src/test-setup.ts"]
coverage = true
coverageDir = "coverage"
coverageReporters = ["text", "lcov"]
coverageThreshold = { line = 80, function = 80, branch = 80 }
```

## Environment Variables

```typescript
// Read environment variables
const apiKey = Bun.env.API_KEY;
const port = Bun.env.PORT ?? "3000";

// Or using process.env (Node.js compatible)
const dbUrl = process.env.DATABASE_URL;
```

### .env Files

Bun automatically loads `.env` files:

```bash
# .env
DATABASE_URL=postgres://localhost/mydb
API_KEY=secret123
```

```bash
# Priority (highest to lowest):
# .env.local
# .env.development / .env.production
# .env
```

## SQLite (Built-in)

```typescript
import { Database } from "bun:sqlite";

// Open database
const db = new Database("mydb.sqlite");
const db = new Database(":memory:");    // In-memory

// Execute queries
db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)");
db.run("INSERT INTO users (name) VALUES (?)", ["Alice"]);

// Query data
const users = db.query("SELECT * FROM users").all();
const user = db.query("SELECT * FROM users WHERE id = ?").get(1);

// Prepared statements
const stmt = db.prepare("INSERT INTO users (name) VALUES (?)");
stmt.run("Bob");
stmt.run("Charlie");

// Transactions
const insertMany = db.transaction((users: string[]) => {
  for (const name of users) {
    db.run("INSERT INTO users (name) VALUES (?)", [name]);
  }
});
insertMany(["Dave", "Eve"]);

// Close
db.close();
```

## Shell Commands

```typescript
import { $ } from "bun";

// Run command
const result = await $`ls -la`.text();

// With variables (escaped automatically)
const filename = "my file.txt";
await $`cat ${filename}`;

// Get output
const output = await $`echo "Hello"`.text();
const lines = await $`ls`.lines();
const buffer = await $`cat file.bin`.arrayBuffer();

// Check exit code
const { exitCode } = await $`test -f file.txt`.nothrow();

// Pipe commands
await $`cat file.txt | grep "pattern" | wc -l`;

// Environment variables
await $`echo $HOME`.env({ HOME: "/custom/home" });
```

## Node.js Compatibility

Bun aims for Node.js compatibility:

```typescript
// Node.js built-in modules work
import fs from "node:fs";
import path from "node:path";
import { EventEmitter } from "node:events";

// npm packages work
import express from "express";
import lodash from "lodash";

// process global
console.log(process.version);
console.log(process.platform);
console.log(process.cwd());
```

### Compatibility Notes

Most npm packages work, but some Node.js APIs are not yet implemented:

- `vm` module (partial)
- `worker_threads` (partial)
- `cluster` (partial)
- Some `crypto` functions

Check compatibility: https://bun.sh/docs/runtime/nodejs-apis

## Performance Comparison

| Operation | Bun | Node.js |
|-----------|-----|---------|
| Install packages | ~25x faster | Baseline |
| Start time | ~4x faster | Baseline |
| TypeScript | Built-in | Requires setup |
| Bundling | Built-in | Requires esbuild/webpack |
| SQLite | Built-in | Requires better-sqlite3 |
| Hot reload | `--watch` | Requires nodemon |

## Bun vs Node.js vs Deno

| Feature | Bun | Node.js | Deno |
|---------|-----|---------|------|
| Engine | JavaScriptCore | V8 | V8 |
| TypeScript | Built-in | External | Built-in |
| Package manager | Built-in | npm/yarn | Import maps |
| Bundler | Built-in | External | Built-in |
| Test runner | Built-in | External | Built-in |
| SQLite | Built-in | External | External |
| Security model | None | None | Permissions |
| npm compatibility | High | Native | High |
| Speed | Very fast | Fast | Fast |

## Common Workflows

### Development

```bash
# Start with hot reload
bun --watch src/index.ts

# Or in package.json
{
  "scripts": {
    "dev": "bun --watch src/index.ts"
  }
}
```

### Production Build

```bash
# Bundle and minify
bun build src/index.ts --outdir dist --minify --target bun

# Or compile to standalone
bun build src/index.ts --compile --outfile dist/server
```

### Docker

```dockerfile
FROM oven/bun:1

WORKDIR /app

COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

COPY . .

CMD ["bun", "src/index.ts"]
```

## Related Tools

- [Node.js](nodejs.md) - Traditional JavaScript runtime
- [Deno](deno.md) - Secure TypeScript runtime
- [TypeScript](https://www.typescriptlang.org/) - Typed JavaScript
