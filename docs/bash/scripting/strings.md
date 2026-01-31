# String Manipulation

Bash has powerful built-in string manipulation through parameter expansion. Understanding these techniques reduces the need for external tools like `sed` and `awk`.

## String Length

```bash
str="Hello, World!"
echo "${#str}"    # 13
```

## Substring Extraction

```bash
str="Hello, World!"

echo "${str:0:5}"     # Hello (from 0, length 5)
echo "${str:7}"       # World! (from 7 to end)
echo "${str:7:5}"     # World (from 7, length 5)
echo "${str: -6}"     # World! (last 6, note space)
echo "${str: -6:5}"   # World (last 6, then length 5)
```

!!! note "Negative Offset"
    Space before negative number is required to distinguish from `:-` default value syntax:
    ```bash
    ${str: -6}    # Substring from end
    ${str:-6}     # Default value if unset
    ```

## Pattern Removal

### Remove from Beginning

```bash
file="/path/to/file.txt"

echo "${file#*/}"      # path/to/file.txt (shortest match)
echo "${file##*/}"     # file.txt (longest match - basename)
```

### Remove from End

```bash
file="/path/to/file.txt"

echo "${file%/*}"      # /path/to (shortest match - dirname)
echo "${file%%/*}"     # (empty - longest match)
echo "${file%.txt}"    # /path/to/file (remove extension)
echo "${file%.*}"      # /path/to/file (remove any extension)
```

### Summary

| Syntax | Direction | Match |
|--------|-----------|-------|
| `${var#pattern}` | From start | Shortest |
| `${var##pattern}` | From start | Longest |
| `${var%pattern}` | From end | Shortest |
| `${var%%pattern}` | From end | Longest |

## Pattern Substitution

### Replace First Match

```bash
str="hello hello hello"
echo "${str/hello/hi}"    # hi hello hello
```

### Replace All Matches

```bash
str="hello hello hello"
echo "${str//hello/hi}"   # hi hi hi
```

### Replace at Beginning

```bash
str="hello world"
echo "${str/#hello/hi}"   # hi world
echo "${str/#world/hi}"   # hello world (no match at start)
```

### Replace at End

```bash
str="hello world"
echo "${str/%world/earth}"  # hello earth
echo "${str/%hello/hi}"     # hello world (no match at end)
```

### Delete Pattern

```bash
str="hello world"
echo "${str/o/}"      # hell world (delete first o)
echo "${str//o/}"     # hell wrld (delete all o)
```

## Case Conversion

**Requires Bash 4.0+**

```bash
str="Hello World"

echo "${str,,}"       # hello world (all lowercase)
echo "${str^^}"       # HELLO WORLD (all uppercase)
echo "${str,}"        # hello World (first char lowercase)
echo "${str^}"        # Hello World (first char uppercase)
```

With pattern:

```bash
str="Hello World"
echo "${str,,[AEIOU]}"    # hEllO wOrld (lowercase vowels only)
```

## Default Values

```bash
unset var
echo "${var:-default}"     # default (use if unset/empty)
echo "${var-default}"      # default (use if unset only)

var=""
echo "${var:-default}"     # default (empty counts as unset)
echo "${var-default}"      # (empty - var is set)
```

### Set and Use Default

```bash
unset var
echo "${var:=default}"     # default (and sets var)
echo "$var"                # default
```

### Error if Unset

```bash
unset var
echo "${var:?Variable not set}"
# bash: var: Variable not set
```

### Use Alternative Value

```bash
var="hello"
echo "${var:+alternative}"  # alternative (var is set)

unset var
echo "${var:+alternative}"  # (empty - var is unset)
```

## String Splitting

### Using IFS

```bash
str="one,two,three"
IFS=',' read -ra arr <<< "$str"
echo "${arr[1]}"    # two
```

### Using Parameter Expansion

```bash
path="/usr/local/bin"

# Split on /
IFS='/' read -ra parts <<< "$path"
for part in "${parts[@]}"; do
    [[ -n "$part" ]] && echo "$part"
done
```

## String Joining

```bash
arr=("one" "two" "three")

# Join with delimiter
IFS=','
echo "${arr[*]}"    # one,two,three
IFS=' '

# Using printf
printf -v joined '%s,' "${arr[@]}"
echo "${joined%,}"  # one,two,three
```

## Pattern Matching

### Glob Patterns in [[ ]]

```bash
str="hello.txt"

[[ "$str" == *.txt ]] && echo "Text file"
[[ "$str" == h* ]] && echo "Starts with h"
[[ "$str" == *ll* ]] && echo "Contains ll"
```

### Regex Matching

```bash
str="user@example.com"

if [[ "$str" =~ ^([^@]+)@(.+)$ ]]; then
    echo "User: ${BASH_REMATCH[1]}"    # user
    echo "Domain: ${BASH_REMATCH[2]}"  # example.com
fi
```

## Practical Examples

### Get File Extension

```bash
file="document.backup.txt"

# Last extension
ext="${file##*.}"
echo "$ext"    # txt

# Without extension
base="${file%.*}"
echo "$base"   # document.backup
```

### Get Filename from Path

```bash
path="/home/user/documents/file.txt"

# Basename
filename="${path##*/}"
echo "$filename"    # file.txt

# Directory
dirname="${path%/*}"
echo "$dirname"     # /home/user/documents
```

### Change File Extension

```bash
file="document.txt"
newfile="${file%.txt}.md"
echo "$newfile"    # document.md
```

### Trim Whitespace

```bash
str="   hello world   "

# Trim leading
trimmed="${str#"${str%%[![:space:]]*}"}"
echo "[$trimmed]"    # [hello world   ]

# Trim trailing
trimmed="${str%"${str##*[![:space:]]}"}"
echo "[$trimmed]"    # [   hello world]

# Trim both (function)
trim() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    echo "$s"
}
echo "[$(trim "$str")]"    # [hello world]
```

### Check String Contains Substring

```bash
str="hello world"

# Using pattern matching
[[ "$str" == *world* ]] && echo "Contains 'world'"

# Using =~
[[ "$str" =~ world ]] && echo "Contains 'world'"
```

### Check String Starts/Ends With

```bash
str="hello world"

# Starts with
[[ "$str" == hello* ]] && echo "Starts with 'hello'"

# Ends with
[[ "$str" == *world ]] && echo "Ends with 'world'"
```

### Repeat String

```bash
repeat() {
    local str="$1"
    local n="$2"
    local result=""
    for ((i=0; i<n; i++)); do
        result+="$str"
    done
    echo "$result"
}

echo "$(repeat "ab" 3)"    # ababab
```

Using printf:

```bash
printf '=%.0s' {1..20}    # ====================
echo
```

### Pad String

```bash
# Left pad with zeros
num="42"
printf "%05d\n" "$num"    # 00042

# Right pad with spaces
str="hello"
printf "%-10s|\n" "$str"  # hello     |
```

### Split Path Components

```bash
path="/home/user/documents/file.txt"

dir="${path%/*}"
base="${path##*/}"
name="${base%.*}"
ext="${base##*.}"

echo "Dir: $dir"      # /home/user/documents
echo "Base: $base"    # file.txt
echo "Name: $name"    # file
echo "Ext: $ext"      # txt
```

### URL Parsing

```bash
url="https://user:pass@example.com:8080/path?query=1"

protocol="${url%%://*}"           # https
without_proto="${url#*://}"       # user:pass@example.com:8080/path?query=1
user_pass="${without_proto%%@*}"  # user:pass
host_path="${without_proto#*@}"   # example.com:8080/path?query=1
host_port="${host_path%%/*}"      # example.com:8080
path_query="${host_path#*/}"      # path?query=1

echo "Protocol: $protocol"
echo "User:Pass: $user_pass"
echo "Host:Port: $host_port"
echo "Path: $path_query"
```

## Try It

1. Substring operations:
   ```bash
   str="Hello, World!"
   echo "Length: ${#str}"
   echo "First 5: ${str:0:5}"
   echo "Last 6: ${str: -6}"
   ```

2. Pattern removal:
   ```bash
   path="/home/user/file.txt"
   echo "Basename: ${path##*/}"
   echo "Dirname: ${path%/*}"
   echo "No ext: ${path%.txt}"
   ```

3. Substitution:
   ```bash
   str="one two one three one"
   echo "First: ${str/one/1}"
   echo "All: ${str//one/1}"
   ```

4. Case conversion:
   ```bash
   str="Hello World"
   echo "Lower: ${str,,}"
   echo "Upper: ${str^^}"
   ```

## Summary

| Operation | Syntax |
|-----------|--------|
| Length | `${#var}` |
| Substring | `${var:offset:length}` |
| Remove prefix (shortest) | `${var#pattern}` |
| Remove prefix (longest) | `${var##pattern}` |
| Remove suffix (shortest) | `${var%pattern}` |
| Remove suffix (longest) | `${var%%pattern}` |
| Replace first | `${var/old/new}` |
| Replace all | `${var//old/new}` |
| Replace start | `${var/#old/new}` |
| Replace end | `${var/%old/new}` |
| Lowercase all | `${var,,}` |
| Uppercase all | `${var^^}` |
| Default if unset | `${var:-default}` |
| Set default | `${var:=default}` |
| Error if unset | `${var:?message}` |
