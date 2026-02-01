# JavaScript Testing

Modern JavaScript testing with Vitest, Jest, and Testing Library.

## Vitest (Recommended)

### Installation

```bash
npm install -D vitest
```

### Configuration

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node', // or 'jsdom' for browser
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
})
```

### Running Tests

```bash
# Run tests
npx vitest

# Watch mode
npx vitest --watch

# Run once
npx vitest run

# With coverage
npx vitest --coverage

# Specific file
npx vitest src/utils.test.js
```

### Basic Tests

```javascript
// math.test.js
import { describe, it, expect } from 'vitest'
import { add, multiply } from './math'

describe('math functions', () => {
  it('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })

  it('multiplies two numbers', () => {
    expect(multiply(2, 3)).toBe(6)
  })
})
```

### Async Tests

```javascript
import { describe, it, expect } from 'vitest'

describe('async operations', () => {
  it('fetches data', async () => {
    const data = await fetchData()
    expect(data).toHaveProperty('id')
  })

  it('handles promise rejection', async () => {
    await expect(failingOperation()).rejects.toThrow('Error')
  })
})
```

### Mocking

```javascript
import { describe, it, expect, vi } from 'vitest'

// Mock a module
vi.mock('./api', () => ({
  fetchUser: vi.fn(() => Promise.resolve({ id: 1, name: 'Test' }))
}))

describe('user service', () => {
  it('fetches user', async () => {
    const user = await getUser(1)
    expect(user.name).toBe('Test')
  })
})

// Mock functions
describe('callbacks', () => {
  it('calls callback with result', () => {
    const callback = vi.fn()
    processData('input', callback)
    expect(callback).toHaveBeenCalledWith('processed')
  })
})

// Spy on methods
describe('spy', () => {
  it('tracks method calls', () => {
    const obj = { method: () => 'original' }
    const spy = vi.spyOn(obj, 'method')

    obj.method()

    expect(spy).toHaveBeenCalled()
  })
})
```

### Timers

```javascript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('timers', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('delays execution', () => {
    const callback = vi.fn()
    setTimeout(callback, 1000)

    expect(callback).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1000)

    expect(callback).toHaveBeenCalled()
  })
})
```

## Jest

### Installation

```bash
npm install -D jest
```

### Configuration

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  collectCoverageFrom: ['src/**/*.js'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
    },
  },
}
```

### Basic Tests

```javascript
// math.test.js
const { add, multiply } = require('./math')

describe('math functions', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })

  test('multiplies two numbers', () => {
    expect(multiply(2, 3)).toBe(6)
  })
})
```

### Jest Mocking

```javascript
// Mock entire module
jest.mock('./api')

// Mock implementation
const api = require('./api')
api.fetchData.mockResolvedValue({ data: 'test' })

// Mock return value
jest.fn().mockReturnValue('mocked')
jest.fn().mockResolvedValue('async mocked')
```

## Testing Library

For testing React, Vue, and DOM interactions.

### Installation

```bash
# React
npm install -D @testing-library/react @testing-library/jest-dom

# Vue
npm install -D @testing-library/vue

# DOM
npm install -D @testing-library/dom
```

### React Testing

```javascript
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    await userEvent.click(screen.getByText('Click me'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<Button loading>Submit</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
})
```

### Queries

```javascript
// By role (preferred)
screen.getByRole('button')
screen.getByRole('heading', { level: 1 })
screen.getByRole('textbox', { name: 'Email' })

// By text
screen.getByText('Hello')
screen.getByText(/hello/i)

// By label
screen.getByLabelText('Email')

// By placeholder
screen.getByPlaceholderText('Enter email')

// By test id
screen.getByTestId('submit-button')

// Query variants
screen.queryByText('Optional')  // Returns null if not found
screen.findByText('Async')      // Returns promise, waits for element
screen.getAllByRole('listitem') // Returns array
```

### Async Testing

```javascript
import { render, screen, waitFor } from '@testing-library/react'

describe('async component', () => {
  it('loads data', async () => {
    render(<UserProfile userId={1} />)

    // Wait for element to appear
    expect(await screen.findByText('John Doe')).toBeInTheDocument()
  })

  it('shows loading then content', async () => {
    render(<DataFetcher />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Data loaded')).toBeInTheDocument()
  })
})
```

## Matchers

### Common Matchers

```javascript
// Equality
expect(value).toBe(expected)
expect(value).toEqual(expected)
expect(value).toStrictEqual(expected)

// Truthiness
expect(value).toBeTruthy()
expect(value).toBeFalsy()
expect(value).toBeNull()
expect(value).toBeUndefined()
expect(value).toBeDefined()

// Numbers
expect(value).toBeGreaterThan(3)
expect(value).toBeLessThanOrEqual(10)
expect(value).toBeCloseTo(0.3, 5)

// Strings
expect(value).toMatch(/pattern/)
expect(value).toContain('substring')

// Arrays
expect(array).toContain(item)
expect(array).toHaveLength(3)

// Objects
expect(obj).toHaveProperty('key')
expect(obj).toMatchObject({ key: 'value' })

// Errors
expect(() => fn()).toThrow()
expect(() => fn()).toThrow('error message')
expect(() => fn()).toThrow(ErrorClass)
```

### Jest DOM Matchers

```javascript
import '@testing-library/jest-dom'

expect(element).toBeInTheDocument()
expect(element).toBeVisible()
expect(element).toBeEnabled()
expect(element).toBeDisabled()
expect(element).toHaveClass('active')
expect(element).toHaveAttribute('href', '/path')
expect(element).toHaveTextContent('Hello')
expect(element).toHaveValue('input value')
expect(element).toBeChecked()
expect(element).toHaveFocus()
```

## Test Organization

### Describe Blocks

```javascript
describe('Calculator', () => {
  describe('addition', () => {
    it('adds positive numbers', () => {})
    it('adds negative numbers', () => {})
  })

  describe('subtraction', () => {
    it('subtracts numbers', () => {})
  })
})
```

### Setup and Teardown

```javascript
describe('database tests', () => {
  beforeAll(async () => {
    await db.connect()
  })

  afterAll(async () => {
    await db.disconnect()
  })

  beforeEach(async () => {
    await db.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('creates record', async () => {})
})
```

## Snapshot Testing

```javascript
describe('Component', () => {
  it('matches snapshot', () => {
    const { container } = render(<MyComponent />)
    expect(container).toMatchSnapshot()
  })

  it('matches inline snapshot', () => {
    expect(formatDate(new Date('2024-01-01'))).toMatchInlineSnapshot(`"January 1, 2024"`)
  })
})
```

Update snapshots:
```bash
npx vitest -u
```

## Coverage Configuration

```javascript
// vitest.config.js
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
      thresholds: {
        lines: 80,
        branches: 80,
        functions: 80,
        statements: 80,
      },
    },
  },
})
```

## Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui"
  }
}
```

## See Also

- [Testing Overview](index.md)
- [Python Testing](python.md)
- [GitHub Actions](../bash/tools/github-actions.md)
