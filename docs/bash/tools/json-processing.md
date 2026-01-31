# JSON Processing

Working with JSON data on the command line using `jq`.

## jq - JSON Processor

`jq` is a lightweight command-line JSON processor. It's essential for working with APIs, configuration files, and data processing.

### Installation

```bash
# macOS
brew install jq

# Debian/Ubuntu
apt install jq
```

### Basic Usage

```bash
# Pretty print
echo '{"name":"Alice","age":30}' | jq '.'

# Read from file
jq '.' data.json

# Compact output
jq -c '.' data.json
```

## Selecting Data

### Simple Selection

```bash
echo '{"name":"Alice","age":30}' | jq '.name'
# "Alice"

echo '{"name":"Alice","age":30}' | jq '.age'
# 30
```

### Nested Objects

```bash
echo '{"user":{"name":"Alice","address":{"city":"NYC"}}}' | jq '.user.name'
# "Alice"

echo '{"user":{"name":"Alice","address":{"city":"NYC"}}}' | jq '.user.address.city'
# "NYC"
```

### Array Access

```bash
echo '[1,2,3,4,5]' | jq '.[0]'
# 1

echo '[1,2,3,4,5]' | jq '.[-1]'
# 5

echo '[1,2,3,4,5]' | jq '.[1:3]'
# [2,3]
```

### Array of Objects

```bash
data='[{"name":"Alice"},{"name":"Bob"},{"name":"Charlie"}]'

echo "$data" | jq '.[0].name'
# "Alice"

echo "$data" | jq '.[].name'
# "Alice"
# "Bob"
# "Charlie"

echo "$data" | jq '.[1:].name'
# Error - use map instead
```

## Iterating Arrays

### Get All Elements

```bash
echo '[1,2,3]' | jq '.[]'
# 1
# 2
# 3
```

### Map Over Array

```bash
echo '[{"name":"Alice"},{"name":"Bob"}]' | jq '.[].name'
# "Alice"
# "Bob"

# Or using map
echo '[1,2,3]' | jq 'map(. * 2)'
# [2,4,6]
```

## Filters and Conditions

### Select

Filter array elements:

```bash
echo '[1,2,3,4,5]' | jq '.[] | select(. > 3)'
# 4
# 5

echo '[{"name":"Alice","age":30},{"name":"Bob","age":25}]' | jq '.[] | select(.age > 28)'
# {"name":"Alice","age":30}
```

### Multiple Conditions

```bash
data='[{"name":"Alice","age":30,"active":true},{"name":"Bob","age":25,"active":false}]'

echo "$data" | jq '.[] | select(.age > 20 and .active == true)'
# {"name":"Alice","age":30,"active":true}
```

### Contains

```bash
echo '["apple","banana","cherry"]' | jq '.[] | select(contains("an"))'
# "banana"

echo '{"tags":["linux","bash","shell"]}' | jq '.tags | contains(["bash"])'
# true
```

## Transforming Data

### Create New Objects

```bash
echo '{"first":"Alice","last":"Smith","age":30}' | jq '{name: .first, years: .age}'
# {"name":"Alice","years":30}
```

### Add Fields

```bash
echo '{"name":"Alice"}' | jq '. + {age: 30}'
# {"name":"Alice","age":30}
```

### Modify Fields

```bash
echo '{"name":"Alice","age":30}' | jq '.age = .age + 1'
# {"name":"Alice","age":31}

echo '{"name":"Alice","age":30}' | jq '.age += 1'
# {"name":"Alice","age":31}
```

### Delete Fields

```bash
echo '{"name":"Alice","age":30,"temp":true}' | jq 'del(.temp)'
# {"name":"Alice","age":30}
```

### Rename Fields

```bash
echo '{"name":"Alice"}' | jq '{username: .name}'
# {"username":"Alice"}
```

## String Operations

### Length

```bash
echo '"hello"' | jq 'length'
# 5

echo '[1,2,3]' | jq 'length'
# 3
```

### String Manipulation

```bash
echo '{"name":"alice"}' | jq '.name | ascii_upcase'
# "ALICE"

echo '{"text":"hello world"}' | jq '.text | split(" ")'
# ["hello","world"]

echo '{"words":["hello","world"]}' | jq '.words | join("-")'
# "hello-world"
```

### String Interpolation

```bash
echo '{"name":"Alice","age":30}' | jq '"\(.name) is \(.age) years old"'
# "Alice is 30 years old"
```

## Numbers and Math

```bash
echo '[1,2,3,4,5]' | jq 'add'
# 15

echo '[1,2,3,4,5]' | jq 'add / length'
# 3

echo '{"a":10,"b":3}' | jq '.a / .b'
# 3.3333333333333335

echo '[3,1,4,1,5]' | jq 'min'
# 1

echo '[3,1,4,1,5]' | jq 'max'
# 5

echo '[3,1,4,1,5]' | jq 'sort'
# [1,1,3,4,5]

echo '[3,1,4,1,5]' | jq 'unique'
# [1,3,4,5]
```

## Grouping and Aggregating

### Group By

```bash
data='[{"type":"a","val":1},{"type":"b","val":2},{"type":"a","val":3}]'

echo "$data" | jq 'group_by(.type)'
# [[{"type":"a","val":1},{"type":"a","val":3}],[{"type":"b","val":2}]]
```

### Count By Type

```bash
echo "$data" | jq 'group_by(.type) | map({type: .[0].type, count: length})'
# [{"type":"a","count":2},{"type":"b","count":1}]
```

## Output Formatting

### Raw Output

Remove quotes from strings:

```bash
echo '{"name":"Alice"}' | jq '.name'
# "Alice"

echo '{"name":"Alice"}' | jq -r '.name'
# Alice
```

### Compact Output

```bash
echo '{"name":"Alice","age":30}' | jq -c '.'
# {"name":"Alice","age":30}
```

### Tab-Separated Values

```bash
echo '[{"a":1,"b":2},{"a":3,"b":4}]' | jq -r '.[] | [.a, .b] | @tsv'
# 1	2
# 3	4
```

### CSV Output

```bash
echo '[{"a":1,"b":2},{"a":3,"b":4}]' | jq -r '.[] | [.a, .b] | @csv'
# 1,2
# 3,4
```

## Working with APIs

### curl + jq

```bash
# Get and parse JSON
curl -s https://api.github.com/users/octocat | jq '.name, .company'

# Extract specific fields
curl -s https://api.example.com/data | jq '.results[] | {id, name}'

# Filter results
curl -s https://api.example.com/items | jq '.[] | select(.status == "active")'
```

### Handling Arrays

```bash
# Pretty print API response
curl -s https://api.example.com/users | jq '.'

# Get first item
curl -s https://api.example.com/users | jq '.[0]'

# Count items
curl -s https://api.example.com/users | jq 'length'

# Get all names
curl -s https://api.example.com/users | jq -r '.[].name'
```

## Advanced Patterns

### Recursive Descent

Find all values of a key anywhere in the structure:

```bash
echo '{"a":{"b":{"c":1}},"d":{"c":2}}' | jq '.. | .c? // empty'
# 1
# 2
```

### Conditionals

```bash
echo '{"score":85}' | jq 'if .score >= 90 then "A" elif .score >= 80 then "B" else "C" end'
# "B"
```

### Error Handling

```bash
# Optional object access (no error if missing)
echo '{"name":"Alice"}' | jq '.address.city?'
# null

# Default value
echo '{"name":"Alice"}' | jq '.age // 0'
# 0
```

### Variables

```bash
echo '{"items":[1,2,3]}' | jq --arg n 2 '.items | map(. * ($n | tonumber))'
# [2,4,6]

# Pass JSON as argument
echo '{}' | jq --argjson data '{"key":"value"}' '. + $data'
# {"key":"value"}
```

## Practical Examples

### Parse Docker JSON

```bash
docker inspect container_name | jq '.[0].NetworkSettings.IPAddress'
```

### Parse kubectl Output

```bash
kubectl get pods -o json | jq '.items[] | {name: .metadata.name, status: .status.phase}'
```

### Transform Config File

```bash
# Add new field
jq '.newField = "value"' config.json > config_new.json

# Update nested field
jq '.database.host = "newhost"' config.json
```

### API Response Processing

```bash
# Get paginated results
page=1
while true; do
    result=$(curl -s "https://api.example.com/items?page=$page")
    count=$(echo "$result" | jq '.items | length')
    [[ $count -eq 0 ]] && break
    echo "$result" | jq -r '.items[].name'
    ((page++))
done
```

### Build JSON

```bash
# Create JSON from variables
name="Alice"
age=30
jq -n --arg name "$name" --argjson age "$age" '{name: $name, age: $age}'
# {"name":"Alice","age":30}
```

## Try It

1. Basic selection:
   ```bash
   echo '{"name":"Alice","age":30}' | jq '.name'
   echo '[1,2,3,4,5]' | jq '.[2]'
   ```

2. Filtering:
   ```bash
   echo '[1,2,3,4,5]' | jq '[.[] | select(. > 2)]'
   ```

3. Transformation:
   ```bash
   echo '{"a":1,"b":2}' | jq '{x: .a, y: .b}'
   ```

4. Array operations:
   ```bash
   echo '[5,2,8,1,9]' | jq 'sort | reverse | .[0:3]'
   ```

## Summary

| Operation | Syntax |
|-----------|--------|
| Select field | `.field` |
| Select nested | `.a.b.c` |
| Array element | `.[0]` |
| All elements | `.[]` |
| Filter | `select(condition)` |
| Create object | `{key: .value}` |
| Add field | `. + {key: value}` |
| Delete field | `del(.field)` |
| Raw output | `-r` |
| Length | `length` |
| Map | `map(expr)` |
| Sort | `sort` |
| Unique | `unique` |
| Sum | `add` |

Key flags:

| Flag | Purpose |
|------|---------|
| `-r` | Raw string output |
| `-c` | Compact output |
| `-e` | Exit with error if null |
| `--arg name val` | Pass string variable |
| `--argjson name val` | Pass JSON variable |
