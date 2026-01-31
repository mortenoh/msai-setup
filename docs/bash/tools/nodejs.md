# Node.js

Node.js is a JavaScript runtime built on Chrome's V8 engine, enabling server-side JavaScript development. This guide covers Node.js installation via nvm, package management with npm/pnpm, and project configuration.

## Installation with nvm

nvm (Node Version Manager) allows installing and switching between multiple Node.js versions.

### Install nvm

**macOS (Homebrew):**

```bash
brew install nvm

# Add to ~/.bashrc or ~/.zshrc
export NVM_DIR="$HOME/.nvm"
[ -s "$HOMEBREW_PREFIX/opt/nvm/nvm.sh" ] && source "$HOMEBREW_PREFIX/opt/nvm/nvm.sh"
[ -s "$HOMEBREW_PREFIX/opt/nvm/etc/bash_completion.d/nvm" ] && source "$HOMEBREW_PREFIX/opt/nvm/etc/bash_completion.d/nvm"
```

**Linux/macOS (Install Script):**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Add to shell config
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"
```

### nvm Commands

```bash
# List available versions
nvm ls-remote
nvm ls-remote --lts              # Only LTS versions

# Install Node.js
nvm install node                 # Latest version
nvm install --lts                # Latest LTS
nvm install 20                   # Latest v20.x
nvm install 20.10.0              # Specific version

# List installed versions
nvm ls

# Use a version
nvm use 20
nvm use --lts
nvm use node                     # Latest installed

# Set default version
nvm alias default 20
nvm alias default lts/*

# Uninstall version
nvm uninstall 18.0.0

# Show current version
nvm current
node --version

# Run command with specific version
nvm exec 18 node --version
nvm run 18 script.js
```

### .nvmrc File

Specify Node.js version per project:

```bash
# .nvmrc
20
```

```bash
# Use version from .nvmrc
nvm use

# Install version from .nvmrc
nvm install
```

### Auto-switch on cd

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Auto-switch Node version when entering directory with .nvmrc
autoload -U add-zsh-hook

load-nvmrc() {
  local nvmrc_path
  nvmrc_path="$(nvm_find_nvmrc)"

  if [ -n "$nvmrc_path" ]; then
    local nvmrc_node_version
    nvmrc_node_version=$(nvm version "$(cat "${nvmrc_path}")")

    if [ "$nvmrc_node_version" = "N/A" ]; then
      nvm install
    elif [ "$nvmrc_node_version" != "$(nvm version)" ]; then
      nvm use
    fi
  elif [ -n "$(PWD=$OLDPWD nvm_find_nvmrc)" ] && [ "$(nvm version)" != "$(nvm version default)" ]; then
    nvm use default
  fi
}

add-zsh-hook chpwd load-nvmrc
load-nvmrc
```

## Package Managers

### npm (Bundled with Node.js)

```bash
# Install packages
npm install                      # Install from package.json
npm install express              # Add dependency
npm install -D jest              # Add dev dependency
npm install -g typescript        # Global install

# Remove packages
npm uninstall express
npm uninstall -g typescript

# Update packages
npm update                       # Update all
npm update express               # Update specific

# Run scripts
npm run build
npm run test
npm start                        # Shorthand for npm run start

# View info
npm list                         # Installed packages
npm list -g --depth=0           # Global packages
npm outdated                     # Outdated packages
npm info express                 # Package info

# Cache
npm cache clean --force
npm cache verify
```

### pnpm (Faster, Efficient)

pnpm uses a content-addressable store, saving disk space and installation time.

```bash
# Install pnpm
npm install -g pnpm

# Or via corepack (Node.js 16.9+)
corepack enable
corepack prepare pnpm@latest --activate
```

```bash
# pnpm commands (similar to npm)
pnpm install
pnpm add express
pnpm add -D jest
pnpm add -g typescript
pnpm remove express
pnpm update
pnpm run build
pnpm start

# pnpm-specific
pnpm store status               # Store info
pnpm store prune                # Clean unused packages
pnpm why express                # Why is package installed
```

### Comparison

| Feature | npm | pnpm | Yarn |
|---------|-----|------|------|
| Speed | Moderate | Fast | Fast |
| Disk usage | High | Low (shared store) | Moderate |
| Workspaces | Yes | Yes | Yes |
| Lock file | package-lock.json | pnpm-lock.yaml | yarn.lock |
| Strictness | Loose | Strict | Moderate |

## package.json

### Basic Structure

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "description": "A sample project",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src/",
    "format": "prettier --write ."
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.20",
    "@types/node": "^20.10.0",
    "typescript": "^5.3.2"
  }
}
```

### Full-Featured package.json

```json
{
  "name": "@myorg/my-package",
  "version": "1.0.0",
  "description": "A full-featured package",
  "author": "Your Name <you@example.com>",
  "license": "MIT",
  "keywords": ["node", "typescript", "api"],
  "homepage": "https://github.com/user/repo#readme",
  "repository": {
    "type": "git",
    "url": "git+https://github.com/user/repo.git"
  },
  "bugs": {
    "url": "https://github.com/user/repo/issues"
  },

  "main": "dist/index.js",
  "module": "dist/index.mjs",
  "types": "dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.js"
    },
    "./utils": {
      "types": "./dist/utils/index.d.ts",
      "import": "./dist/utils/index.mjs",
      "require": "./dist/utils/index.js"
    }
  },
  "files": [
    "dist",
    "README.md"
  ],
  "bin": {
    "my-cli": "./dist/cli.js"
  },

  "scripts": {
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts",
    "build": "tsup src/index.ts --format cjs,esm --dts",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint src/ --ext .ts,.tsx",
    "lint:fix": "eslint src/ --ext .ts,.tsx --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "prepare": "husky install",
    "prepublishOnly": "npm run build"
  },

  "dependencies": {
    "express": "^4.18.2",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/express": "^4.17.20",
    "@types/node": "^20.10.0",
    "@typescript-eslint/eslint-plugin": "^6.13.0",
    "@typescript-eslint/parser": "^6.13.0",
    "eslint": "^8.54.0",
    "husky": "^8.0.3",
    "lint-staged": "^15.1.0",
    "prettier": "^3.1.0",
    "tsup": "^8.0.1",
    "tsx": "^4.6.0",
    "typescript": "^5.3.2",
    "vitest": "^1.0.0"
  },
  "peerDependencies": {
    "react": ">=18.0.0"
  },
  "peerDependenciesMeta": {
    "react": {
      "optional": true
    }
  },
  "optionalDependencies": {
    "fsevents": "^2.3.3"
  },

  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },

  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  },

  "publishConfig": {
    "access": "public",
    "registry": "https://registry.npmjs.org"
  }
}
```

### Scripts

```json
{
  "scripts": {
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "build:watch": "tsc --watch",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "format": "prettier --write .",
    "typecheck": "tsc --noEmit",
    "clean": "rm -rf dist node_modules",
    "prepare": "husky install",
    "preinstall": "npx only-allow pnpm"
  }
}
```

Run scripts:

```bash
npm run build
npm test                         # Shorthand for npm run test
npm start                        # Shorthand for npm run start
npm run lint -- --fix           # Pass arguments
```

### Version Ranges

```json
{
  "dependencies": {
    "exact": "1.2.3",
    "patch": "~1.2.3",
    "minor": "^1.2.3",
    "range": ">=1.0.0 <2.0.0",
    "any": "*",
    "latest": "latest",
    "git": "git+https://github.com/user/repo.git",
    "github": "user/repo#branch",
    "local": "file:../local-package"
  }
}
```

| Symbol | Meaning | Example |
|--------|---------|---------|
| `1.2.3` | Exact version | Only 1.2.3 |
| `~1.2.3` | Patch updates | 1.2.x (>=1.2.3 <1.3.0) |
| `^1.2.3` | Minor updates | 1.x.x (>=1.2.3 <2.0.0) |
| `*` | Any version | Latest |
| `>=1.0.0` | Range | 1.0.0 or higher |

## TypeScript Configuration

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": false,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "allowSyntheticDefaultImports": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Common Workflows

### Start New Project

```bash
# Create directory and initialize
mkdir my-project && cd my-project
npm init -y

# Or with specific options
npm init

# TypeScript project
npm init -y
npm install -D typescript @types/node tsx
npx tsc --init
```

### Install Project

```bash
git clone https://github.com/user/project.git
cd project
npm install                      # or pnpm install
npm run build
npm start
```

### Update Dependencies

```bash
# Check outdated
npm outdated

# Update to latest in range
npm update

# Update to latest (may break)
npx npm-check-updates -u
npm install

# Interactive update
npx npm-check --update
```

### Workspaces (Monorepo)

**package.json (root):**

```json
{
  "name": "my-monorepo",
  "private": true,
  "workspaces": [
    "packages/*",
    "apps/*"
  ]
}
```

**With pnpm (pnpm-workspace.yaml):**

```yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

```bash
# Install all workspace dependencies
npm install

# Run script in specific workspace
npm run build -w packages/ui
pnpm --filter @myorg/ui build

# Run script in all workspaces
npm run build --workspaces
pnpm -r build

# Add dependency to workspace
npm install lodash -w packages/utils
pnpm --filter @myorg/utils add lodash
```

## Environment Variables

```bash
# .env file (use dotenv package)
DATABASE_URL=postgres://localhost/mydb
API_KEY=secret123
NODE_ENV=development
```

```javascript
// Load with dotenv
import 'dotenv/config';
// or
import dotenv from 'dotenv';
dotenv.config();

console.log(process.env.DATABASE_URL);
```

## Debugging

### Node.js Inspector

```bash
# Start with inspector
node --inspect dist/index.js
node --inspect-brk dist/index.js  # Break on first line

# Debug in VS Code
# launch.json
{
  "type": "node",
  "request": "launch",
  "name": "Debug",
  "program": "${workspaceFolder}/src/index.ts",
  "runtimeExecutable": "tsx"
}
```

### Console Methods

```javascript
console.log('Basic log');
console.error('Error');
console.warn('Warning');
console.table([{ a: 1 }, { a: 2 }]);
console.time('operation');
// ... code
console.timeEnd('operation');
console.trace('Stack trace');
```

## Performance

### Profiling

```bash
# CPU profiling
node --prof dist/index.js
node --prof-process isolate-*.log > profile.txt

# Heap snapshot
node --heapsnapshot-signal=SIGUSR2 dist/index.js
kill -USR2 <pid>
```

### Memory

```javascript
// Check memory usage
const used = process.memoryUsage();
console.log({
  rss: `${Math.round(used.rss / 1024 / 1024)} MB`,
  heapTotal: `${Math.round(used.heapTotal / 1024 / 1024)} MB`,
  heapUsed: `${Math.round(used.heapUsed / 1024 / 1024)} MB`,
});
```

## Security

### Audit Dependencies

```bash
npm audit
npm audit fix
npm audit fix --force           # May update major versions
```

### Best Practices

1. Keep dependencies updated
2. Use exact versions in production
3. Audit regularly
4. Use `.npmrc` for registry config
5. Don't commit `.env` files

### .npmrc

```ini
# .npmrc
registry=https://registry.npmjs.org/
save-exact=true
engine-strict=true
```

## Related Tools

- [Deno](deno.md) - Alternative JavaScript runtime
- [Bun](bun.md) - Fast JavaScript runtime
- [TypeScript](https://www.typescriptlang.org/) - Typed JavaScript
