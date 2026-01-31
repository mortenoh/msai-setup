# Arrays

Arrays let you store and manipulate collections of values. Bash supports indexed (numeric) and associative (key-value) arrays.

## Indexed Arrays

### Creating Arrays

```bash
# Direct assignment
fruits=("apple" "banana" "cherry")

# Index assignment
colors[0]="red"
colors[1]="green"
colors[2]="blue"

# From command output
files=($(ls *.txt))

# Empty array
empty=()
```

### Accessing Elements

```bash
fruits=("apple" "banana" "cherry")

echo "${fruits[0]}"      # apple (first element)
echo "${fruits[1]}"      # banana
echo "${fruits[-1]}"     # cherry (last element, bash 4.3+)
echo "${fruits[@]}"      # All elements: apple banana cherry
echo "${fruits[*]}"      # All as single string
```

!!! warning "Braces Required"
    Always use braces for array access:
    ```bash
    echo $fruits[0]      # Wrong - prints "apple[0]"
    echo ${fruits[0]}    # Correct - prints "apple"
    ```

### Array Length

```bash
fruits=("apple" "banana" "cherry")
echo "${#fruits[@]}"     # 3 (number of elements)
echo "${#fruits[0]}"     # 5 (length of first element)
```

### Array Indices

```bash
fruits=("apple" "banana" "cherry")
echo "${!fruits[@]}"     # 0 1 2 (all indices)
```

### Iterating

```bash
fruits=("apple" "banana" "cherry")

# Iterate over values
for fruit in "${fruits[@]}"; do
    echo "$fruit"
done

# Iterate with indices
for i in "${!fruits[@]}"; do
    echo "$i: ${fruits[$i]}"
done
```

Output:

```
apple
banana
cherry
0: apple
1: banana
2: cherry
```

## Modifying Arrays

### Adding Elements

```bash
fruits=("apple" "banana")

# Append
fruits+=("cherry")

# Append multiple
fruits+=("date" "elderberry")

# Insert at index
fruits[5]="fig"    # Sparse array - index 3,4 are unset

echo "${fruits[@]}"
# apple banana cherry date elderberry fig
```

### Removing Elements

```bash
fruits=("apple" "banana" "cherry")

# Remove by index
unset fruits[1]
echo "${fruits[@]}"    # apple cherry

# Note: doesn't reindex - index 1 is now empty
echo "${!fruits[@]}"   # 0 2
```

### Replacing Elements

```bash
fruits=("apple" "banana" "cherry")
fruits[1]="blueberry"
echo "${fruits[@]}"    # apple blueberry cherry
```

### Array Slice

```bash
arr=(a b c d e f)
echo "${arr[@]:2:3}"   # c d e (from index 2, length 3)
echo "${arr[@]:2}"     # c d e f (from index 2 to end)
echo "${arr[@]::3}"    # a b c (first 3 elements)
```

### Copying Arrays

```bash
original=("a" "b" "c")
copy=("${original[@]}")
```

## Associative Arrays

Associative arrays use strings as keys. **Requires Bash 4.0+**.

### Creating

```bash
# Must declare first
declare -A user

user[name]="Alice"
user[age]=30
user[email]="alice@example.com"

# Or inline
declare -A person=(
    [name]="Bob"
    [age]=25
    [city]="NYC"
)
```

### Accessing

```bash
declare -A user=([name]="Alice" [age]=30)

echo "${user[name]}"      # Alice
echo "${user[@]}"         # All values
echo "${!user[@]}"        # All keys: name age
echo "${#user[@]}"        # Number of elements: 2
```

### Iterating

```bash
declare -A user=([name]="Alice" [age]=30 [city]="NYC")

# Iterate over keys
for key in "${!user[@]}"; do
    echo "$key: ${user[$key]}"
done
```

### Checking Key Exists

```bash
declare -A user=([name]="Alice")

if [[ -v user[name] ]]; then
    echo "Name is set"
fi

if [[ -v user[age] ]]; then
    echo "Age is set"
else
    echo "Age is not set"
fi
```

## Common Patterns

### Array from String

```bash
str="one two three"
read -ra arr <<< "$str"
echo "${arr[1]}"    # two
```

With custom delimiter:

```bash
str="one,two,three"
IFS=',' read -ra arr <<< "$str"
echo "${arr[1]}"    # two
```

### Array to String

```bash
arr=("one" "two" "three")
str="${arr[*]}"
echo "$str"    # one two three
```

With custom delimiter:

```bash
arr=("one" "two" "three")
IFS=','
str="${arr[*]}"
IFS=' '
echo "$str"    # one,two,three
```

Or use printf:

```bash
arr=("one" "two" "three")
printf -v str '%s,' "${arr[@]}"
str="${str%,}"    # Remove trailing comma
echo "$str"       # one,two,three
```

### Check if Array Contains Value

```bash
arr=("apple" "banana" "cherry")

contains() {
    local item="$1"
    shift
    local arr=("$@")
    for elem in "${arr[@]}"; do
        [[ "$elem" == "$item" ]] && return 0
    done
    return 1
}

if contains "banana" "${arr[@]}"; then
    echo "Found banana"
fi
```

Using pattern matching:

```bash
arr=("apple" "banana" "cherry")
[[ " ${arr[*]} " =~ " banana " ]] && echo "Found"
```

### Remove Duplicates

```bash
arr=("a" "b" "a" "c" "b")

declare -A seen
unique=()
for item in "${arr[@]}"; do
    if [[ ! -v seen[$item] ]]; then
        seen[$item]=1
        unique+=("$item")
    fi
done

echo "${unique[@]}"    # a b c
```

### Sort Array

```bash
arr=("banana" "apple" "cherry")

# Using printf and sort
IFS=$'\n' sorted=($(printf '%s\n' "${arr[@]}" | sort))
echo "${sorted[@]}"    # apple banana cherry

# Numeric sort
nums=(10 2 30 1)
IFS=$'\n' sorted=($(printf '%s\n' "${nums[@]}" | sort -n))
echo "${sorted[@]}"    # 1 2 10 30
```

### Reverse Array

```bash
arr=("a" "b" "c" "d")
reversed=()
for ((i=${#arr[@]}-1; i>=0; i--)); do
    reversed+=("${arr[$i]}")
done
echo "${reversed[@]}"    # d c b a
```

### Filter Array

```bash
arr=(1 2 3 4 5 6 7 8 9 10)
evens=()
for num in "${arr[@]}"; do
    ((num % 2 == 0)) && evens+=("$num")
done
echo "${evens[@]}"    # 2 4 6 8 10
```

### Map Function Over Array

```bash
arr=(1 2 3 4 5)
doubled=()
for num in "${arr[@]}"; do
    doubled+=($((num * 2)))
done
echo "${doubled[@]}"    # 2 4 6 8 10
```

## Reading File into Array

### Using mapfile (Bash 4+)

```bash
mapfile -t lines < file.txt
echo "Lines: ${#lines[@]}"
echo "First: ${lines[0]}"
```

Options:

- `-t` - Remove trailing newlines
- `-n count` - Read at most count lines
- `-s skip` - Skip first skip lines

### Using While Loop

```bash
lines=()
while IFS= read -r line; do
    lines+=("$line")
done < file.txt
```

## Passing Arrays to Functions

### By Value (Copy)

```bash
process_array() {
    local arr=("$@")
    for item in "${arr[@]}"; do
        echo "Item: $item"
    done
}

fruits=("apple" "banana" "cherry")
process_array "${fruits[@]}"
```

### By Reference (Bash 4.3+)

```bash
process_array() {
    local -n arr=$1    # nameref
    for item in "${arr[@]}"; do
        echo "Item: $item"
    done
}

fruits=("apple" "banana" "cherry")
process_array fruits    # Pass array name, not contents
```

## Stack and Queue

### Stack (LIFO)

```bash
stack=()

push() { stack+=("$1"); }
pop() {
    local top="${stack[-1]}"
    unset 'stack[-1]'
    echo "$top"
}

push "a"
push "b"
push "c"
echo $(pop)    # c
echo $(pop)    # b
```

### Queue (FIFO)

```bash
queue=()

enqueue() { queue+=("$1"); }
dequeue() {
    local front="${queue[0]}"
    queue=("${queue[@]:1}")
    echo "$front"
}

enqueue "a"
enqueue "b"
enqueue "c"
echo $(dequeue)    # a
echo $(dequeue)    # b
```

## Try It

1. Basic array operations:
   ```bash
   fruits=("apple" "banana" "cherry")
   echo "Count: ${#fruits[@]}"
   echo "First: ${fruits[0]}"
   echo "All: ${fruits[@]}"
   ```

2. Iterate with index:
   ```bash
   colors=("red" "green" "blue")
   for i in "${!colors[@]}"; do
       echo "$i: ${colors[$i]}"
   done
   ```

3. Associative array:
   ```bash
   declare -A user=([name]="Alice" [city]="NYC")
   echo "Name: ${user[name]}"
   for key in "${!user[@]}"; do
       echo "$key = ${user[$key]}"
   done
   ```

4. Array from command:
   ```bash
   mapfile -t lines < <(echo -e "one\ntwo\nthree")
   echo "${lines[@]}"
   ```

## Summary

| Operation | Indexed Array | Associative Array |
|-----------|--------------|-------------------|
| Declare | `arr=()` | `declare -A arr` |
| Assign | `arr[0]="val"` | `arr[key]="val"` |
| Access | `${arr[0]}` | `${arr[key]}` |
| All values | `${arr[@]}` | `${arr[@]}` |
| All keys | `${!arr[@]}` | `${!arr[@]}` |
| Length | `${#arr[@]}` | `${#arr[@]}` |
| Append | `arr+=("val")` | `arr[key]="val"` |
| Delete | `unset arr[0]` | `unset arr[key]` |

Best practices:

- Always quote: `"${arr[@]}"`
- Use `declare -A` for associative arrays
- Check existence with `[[ -v arr[key] ]]`
- Use `mapfile -t` to read files
- Associative arrays require Bash 4.0+
