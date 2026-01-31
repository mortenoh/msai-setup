# Deno

Deno is a secure runtime for JavaScript and TypeScript, created by Ryan Dahl (the original creator of Node.js). It features built-in TypeScript support, a secure-by-default permission system, and modern web APIs.

## Installation

### macOS (Homebrew)

```bash
brew install deno
```

### Linux/macOS (Shell)

```bash
curl -fsSL https://deno.land/install.sh | sh

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export DENO_INSTALL="$HOME/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"
```

### Update

```bash
deno upgrade
deno upgrade --version 1.40.0    # Specific version
```

## Quick Start

```bash
# Run a script
deno run script.ts

# Run with permissions
deno run --allow-net server.ts
deno run --allow-read --allow-write file-processor.ts

# Run from URL
deno run https://deno.land/std/examples/welcome.ts

# REPL
deno
```

## Permissions

Deno is secure by default. Scripts need explicit permissions:

| Permission | Flag | Description |
|------------|------|-------------|
| Network | `--allow-net` | Network access |
| Read | `--allow-read` | File system read |
| Write | `--allow-write` | File system write |
| Environment | `--allow-env` | Environment variables |
| Run | `--allow-run` | Subprocess execution |
| FFI | `--allow-ffi` | Foreign function interface |
| All | `--allow-all` or `-A` | All permissions |

### Fine-Grained Permissions

```bash
# Specific hosts
deno run --allow-net=api.example.com,localhost:8080 script.ts

# Specific paths
deno run --allow-read=/etc,/tmp --allow-write=/tmp script.ts

# Specific environment variables
deno run --allow-env=HOME,PATH script.ts

# Specific commands
deno run --allow-run=git,npm script.ts
```

### Permission Prompts

```bash
# Interactive permission prompts
deno run --prompt script.ts
```

## Project Configuration

### deno.json (or deno.jsonc)

```json
{
  "name": "@myorg/my-project",
  "version": "1.0.0",
  "exports": "./mod.ts",

  "tasks": {
    "dev": "deno run --watch --allow-net --allow-read src/main.ts",
    "start": "deno run --allow-net --allow-read src/main.ts",
    "test": "deno test --allow-read",
    "lint": "deno lint",
    "fmt": "deno fmt",
    "check": "deno check src/**/*.ts"
  },

  "imports": {
    "@std/": "jsr:@std/",
    "oak": "jsr:@oak/oak@^14",
    "zod": "npm:zod@^3.22",
    "@/": "./src/"
  },

  "compilerOptions": {
    "strict": true,
    "lib": ["deno.window"]
  },

  "lint": {
    "include": ["src/"],
    "exclude": ["src/generated/"],
    "rules": {
      "tags": ["recommended"],
      "include": ["ban-untagged-todo"],
      "exclude": ["no-unused-vars"]
    }
  },

  "fmt": {
    "useTabs": false,
    "lineWidth": 100,
    "indentWidth": 2,
    "singleQuote": true,
    "proseWrap": "preserve",
    "include": ["src/"],
    "exclude": ["src/generated/"]
  },

  "test": {
    "include": ["src/"],
    "exclude": ["src/fixtures/"]
  },

  "publish": {
    "include": ["src/", "mod.ts", "README.md"],
    "exclude": ["src/tests/"]
  },

  "lock": true,
  "nodeModulesDir": false
}
```

### Import Maps

Map module specifiers to URLs or paths:

```json
{
  "imports": {
    "@std/assert": "jsr:@std/assert@^0.220",
    "@std/path": "jsr:@std/path@^0.220",
    "oak": "jsr:@oak/oak@^14",
    "lodash": "npm:lodash@^4.17",
    "@/": "./src/",
    "~/": "./",
    "utils/": "./src/utils/"
  }
}
```

Usage in code:

```typescript
import { assertEquals } from "@std/assert";
import { Application } from "oak";
import { helper } from "@/utils/helper.ts";
```

## Tasks

Define and run tasks in `deno.json`:

```json
{
  "tasks": {
    "dev": "deno run --watch --allow-all src/main.ts",
    "start": "deno run --allow-all src/main.ts",
    "build": "deno compile --allow-all --output=dist/app src/main.ts",
    "test": "deno test --allow-read --coverage=coverage/",
    "test:watch": "deno test --watch",
    "coverage": "deno coverage coverage/ --lcov > coverage/lcov.info",
    "lint": "deno lint",
    "fmt": "deno fmt",
    "fmt:check": "deno fmt --check",
    "check": "deno check src/**/*.ts",
    "cache": "deno cache --reload src/deps.ts",
    "clean": "rm -rf dist/ coverage/"
  }
}
```

Run tasks:

```bash
deno task dev
deno task test
deno task lint
```

## Dependencies

### Import from JSR (JavaScript Registry)

```typescript
// Recommended: Use JSR for Deno-first packages
import { Application } from "jsr:@oak/oak@^14";
import { assertEquals } from "jsr:@std/assert@^0.220";
```

### Import from npm

```typescript
// npm packages work directly
import express from "npm:express@^4";
import { z } from "npm:zod@^3.22";
import _ from "npm:lodash@^4.17";
```

### Import from URL

```typescript
// Direct URL imports (less common now)
import { serve } from "https://deno.land/std@0.220.0/http/server.ts";
```

### Lock Files

```bash
# Generate/update lock file
deno cache --lock=deno.lock --lock-write src/main.ts

# Use lock file
deno run --lock=deno.lock src/main.ts
```

## Built-in Tools

### Format Code

```bash
deno fmt                         # Format all files
deno fmt src/                    # Format directory
deno fmt --check                 # Check formatting
deno fmt --ignore=dist/          # Ignore paths
```

### Lint Code

```bash
deno lint                        # Lint all files
deno lint src/                   # Lint directory
deno lint --rules                # List available rules
```

### Type Check

```bash
deno check src/main.ts
deno check src/**/*.ts
```

### Test

```bash
deno test                        # Run all tests
deno test --allow-read           # With permissions
deno test --filter "user"        # Filter by name
deno test --watch                # Watch mode
deno test --coverage=cov/        # Generate coverage
deno coverage cov/               # View coverage report
```

### Compile

```bash
# Compile to single executable
deno compile --allow-all --output=app src/main.ts

# Cross-compile
deno compile --target x86_64-unknown-linux-gnu src/main.ts
deno compile --target x86_64-apple-darwin src/main.ts
deno compile --target x86_64-pc-windows-msvc src/main.ts
```

### Documentation

```bash
deno doc                         # Generate docs
deno doc --html --output=docs/   # HTML docs
deno doc mod.ts                  # Document specific file
```

### REPL

```bash
deno                             # Start REPL
deno repl --eval "const x = 5"   # With initial code
```

## Standard Library

Import from `@std/`:

```typescript
// Assertions
import { assertEquals, assertThrows } from "@std/assert";

// Path manipulation
import { join, resolve, basename } from "@std/path";

// File system
import { ensureDir, copy, walk } from "@std/fs";

// Async utilities
import { delay, deadline } from "@std/async";

// UUID
import { v4 as uuid } from "@std/uuid";

// Encoding
import { encodeBase64, decodeBase64 } from "@std/encoding/base64";

// HTTP
import { serve } from "@std/http/server";

// Streams
import { toText, toJson } from "@std/streams";

// Testing
import { describe, it, beforeEach } from "@std/testing/bdd";
```

## Example: HTTP Server

### Using std/http

```typescript
// src/main.ts
import { serve } from "@std/http/server";

const handler = (request: Request): Response => {
  const url = new URL(request.url);

  if (url.pathname === "/") {
    return new Response("Hello, World!");
  }

  if (url.pathname === "/api/data") {
    return Response.json({ message: "Hello", timestamp: Date.now() });
  }

  return new Response("Not Found", { status: 404 });
};

console.log("Server running on http://localhost:8000");
await serve(handler, { port: 8000 });
```

### Using Oak Framework

```typescript
// src/main.ts
import { Application, Router } from "oak";

const router = new Router();

router.get("/", (ctx) => {
  ctx.response.body = "Hello, World!";
});

router.get("/api/users/:id", (ctx) => {
  const id = ctx.params.id;
  ctx.response.body = { id, name: `User ${id}` };
});

router.post("/api/users", async (ctx) => {
  const body = await ctx.request.body.json();
  ctx.response.body = { created: true, ...body };
});

const app = new Application();

// Middleware
app.use(async (ctx, next) => {
  const start = Date.now();
  await next();
  const ms = Date.now() - start;
  console.log(`${ctx.request.method} ${ctx.request.url} - ${ms}ms`);
});

app.use(router.routes());
app.use(router.allowedMethods());

console.log("Server running on http://localhost:8000");
await app.listen({ port: 8000 });
```

## Testing

```typescript
// src/math_test.ts
import { assertEquals, assertThrows } from "@std/assert";
import { describe, it, beforeEach } from "@std/testing/bdd";
import { add, divide } from "./math.ts";

// Simple tests
Deno.test("add function", () => {
  assertEquals(add(2, 3), 5);
  assertEquals(add(-1, 1), 0);
});

// Async tests
Deno.test("async operation", async () => {
  const result = await fetchData();
  assertEquals(result.status, "ok");
});

// BDD-style tests
describe("Calculator", () => {
  describe("divide", () => {
    it("divides two numbers", () => {
      assertEquals(divide(10, 2), 5);
    });

    it("throws on division by zero", () => {
      assertThrows(
        () => divide(10, 0),
        Error,
        "Cannot divide by zero"
      );
    });
  });
});

// Test with permissions
Deno.test({
  name: "reads file",
  permissions: { read: true },
  fn: async () => {
    const content = await Deno.readTextFile("test.txt");
    assertEquals(content.length > 0, true);
  },
});

// Sanitizers
Deno.test({
  name: "test with custom sanitizers",
  sanitizeOps: false,    // Don't check for leaking ops
  sanitizeResources: false,  // Don't check for leaking resources
  fn: () => {
    // Test code
  },
});
```

Run tests:

```bash
deno test
deno test --allow-read
deno test --filter "Calculator"
deno test --coverage=coverage/
```

## Environment Variables

```typescript
// Read environment variables
const apiKey = Deno.env.get("API_KEY");
const homeDir = Deno.env.get("HOME");

// Set environment variable
Deno.env.set("MY_VAR", "value");

// All environment variables
const allEnv = Deno.env.toObject();

// Load .env file
import { load } from "@std/dotenv";
const env = await load();
console.log(env.DATABASE_URL);
```

```bash
# Run with environment
deno run --allow-env=API_KEY src/main.ts
API_KEY=secret deno run --allow-env src/main.ts
```

## File System

```typescript
// Read file
const text = await Deno.readTextFile("file.txt");
const bytes = await Deno.readFile("image.png");

// Write file
await Deno.writeTextFile("output.txt", "Hello");
await Deno.writeFile("data.bin", new Uint8Array([1, 2, 3]));

// File info
const info = await Deno.stat("file.txt");
console.log(info.size, info.isFile, info.mtime);

// Directory operations
await Deno.mkdir("new-dir", { recursive: true });
await Deno.remove("old-file.txt");
await Deno.rename("old.txt", "new.txt");
await Deno.copyFile("src.txt", "dst.txt");

// Read directory
for await (const entry of Deno.readDir("./src")) {
  console.log(entry.name, entry.isFile);
}

// Walk directory (std)
import { walk } from "@std/fs";
for await (const entry of walk("./src", { exts: [".ts"] })) {
  console.log(entry.path);
}
```

## Web APIs

Deno implements standard Web APIs:

```typescript
// Fetch
const response = await fetch("https://api.example.com/data");
const data = await response.json();

// URL
const url = new URL("/path", "https://example.com");
url.searchParams.set("q", "search");

// WebSocket
const ws = new WebSocket("wss://example.com/ws");
ws.onopen = () => ws.send("Hello");
ws.onmessage = (e) => console.log(e.data);

// FormData
const form = new FormData();
form.append("file", new Blob(["content"]), "file.txt");

// Streams
const stream = new ReadableStream({
  start(controller) {
    controller.enqueue("Hello");
    controller.close();
  },
});

// Crypto
const uuid = crypto.randomUUID();
const hash = await crypto.subtle.digest(
  "SHA-256",
  new TextEncoder().encode("message")
);
```

## Deno vs Node.js

| Feature | Deno | Node.js |
|---------|------|---------|
| TypeScript | Built-in | Requires setup |
| Permissions | Secure by default | No restrictions |
| Package manager | Import maps, JSR | npm, package.json |
| Module system | ES Modules | CommonJS + ESM |
| Standard library | Built-in | Third-party |
| Tooling | Built-in (fmt, lint, test) | Third-party |
| Single executable | `deno compile` | Third-party |
| Top-level await | Yes | Yes (ESM) |
| Web APIs | Yes (fetch, etc.) | Partial |

## Migrating from Node.js

### Compatibility Mode

```typescript
// Use Node.js built-in modules with node: prefix
import { readFileSync } from "node:fs";
import { join } from "node:path";
import process from "node:process";
```

### Enable Node.js Modules Directory

```json
{
  "nodeModulesDir": true
}
```

## Related Tools

- [Node.js](nodejs.md) - Traditional JavaScript runtime
- [Bun](bun.md) - Fast JavaScript runtime
- [TypeScript](https://www.typescriptlang.org/) - Typed JavaScript
