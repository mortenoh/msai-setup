# Text Processing

The Unix text processing toolkit for searching, transforming, and analyzing text data.

## grep - Search Text

Search for patterns in files:

```bash
grep "pattern" file.txt           # Basic search
grep -i "pattern" file.txt        # Case insensitive
grep -r "pattern" dir/            # Recursive
grep -n "pattern" file.txt        # Show line numbers
grep -c "pattern" file.txt        # Count matches
grep -l "pattern" *.txt           # List matching files
grep -L "pattern" *.txt           # List non-matching files
grep -v "pattern" file.txt        # Invert match (exclude)
grep -w "word" file.txt           # Whole word only
grep -A 2 "pattern" file.txt      # 2 lines after
grep -B 2 "pattern" file.txt      # 2 lines before
grep -C 2 "pattern" file.txt      # 2 lines context
```

### Regular Expressions

```bash
grep "^start" file.txt            # Lines starting with
grep "end$" file.txt              # Lines ending with
grep "a.b" file.txt               # Any char between a and b
grep "a.*b" file.txt              # Any chars between a and b
grep "[0-9]" file.txt             # Contains digit
grep -E "(cat|dog)" file.txt      # Extended regex (OR)
grep -E "[0-9]{3}" file.txt       # Three digits
```

### Practical Examples

```bash
# Find TODOs in code
grep -rn "TODO" --include="*.py"

# Count error lines in log
grep -c "ERROR" app.log

# Find IP addresses
grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" file.txt

# Exclude binary files
grep -rI "pattern" .

# Multiple patterns
grep -E "error|warning|critical" log.txt
```

## sed - Stream Editor

Transform text with patterns:

```bash
sed 's/old/new/' file.txt         # Replace first occurrence
sed 's/old/new/g' file.txt        # Replace all occurrences
sed -i 's/old/new/g' file.txt     # Edit in place
sed -i.bak 's/old/new/g' file.txt # Edit with backup
sed 's/old/new/gi' file.txt       # Case insensitive
```

### Common Operations

```bash
# Delete lines
sed '/pattern/d' file.txt         # Delete matching lines
sed '5d' file.txt                 # Delete line 5
sed '5,10d' file.txt              # Delete lines 5-10
sed '/^$/d' file.txt              # Delete empty lines

# Print specific lines
sed -n '5p' file.txt              # Print line 5
sed -n '5,10p' file.txt           # Print lines 5-10
sed -n '/pattern/p' file.txt     # Print matching lines

# Insert/append
sed '3i\New line' file.txt        # Insert before line 3
sed '3a\New line' file.txt        # Append after line 3
sed '$a\Last line' file.txt       # Append at end
```

### Capture Groups

```bash
# Rearrange date format
echo "2024-01-15" | sed 's/\([0-9]*\)-\([0-9]*\)-\([0-9]*\)/\3\/\2\/\1/'
# 15/01/2024

# Extract with backreference
echo "name: John" | sed 's/name: \(.*\)/Hello, \1!/'
# Hello, John!
```

### Practical Examples

```bash
# Remove trailing whitespace
sed 's/[[:space:]]*$//' file.txt

# Convert Windows to Unix line endings
sed 's/\r$//' file.txt

# Add prefix to lines
sed 's/^/PREFIX: /' file.txt

# Change file extension in paths
sed 's/\.txt$/.md/' paths.txt

# Extract between markers
sed -n '/START/,/END/p' file.txt
```

## awk - Pattern Processing

Powerful text processing with fields:

```bash
awk '{print $1}' file.txt         # Print first field
awk '{print $1, $3}' file.txt     # Print fields 1 and 3
awk '{print $NF}' file.txt        # Print last field
awk '{print NR, $0}' file.txt     # Print with line numbers
awk -F',' '{print $1}' file.csv   # Custom delimiter
```

### Patterns and Conditions

```bash
awk '/pattern/' file.txt          # Print matching lines
awk '!/pattern/' file.txt         # Print non-matching
awk 'NR==5' file.txt              # Print line 5
awk 'NR>=5 && NR<=10' file.txt    # Print lines 5-10
awk '$3 > 100' file.txt           # Field 3 greater than 100
awk 'length > 80' file.txt        # Lines longer than 80 chars
```

### Built-in Variables

| Variable | Meaning |
|----------|---------|
| `$0` | Entire line |
| `$1, $2, ...` | Fields |
| `NF` | Number of fields |
| `NR` | Current line number |
| `FS` | Field separator |
| `OFS` | Output field separator |
| `RS` | Record separator |

### Arithmetic

```bash
# Sum a column
awk '{sum += $1} END {print sum}' numbers.txt

# Average
awk '{sum += $1; count++} END {print sum/count}' numbers.txt

# Max value
awk 'BEGIN {max=0} $1 > max {max=$1} END {print max}' numbers.txt
```

### Practical Examples

```bash
# Print CSV column
awk -F',' '{print $2}' data.csv

# Filter and format
awk -F':' '$3 >= 1000 {print $1, $3}' /etc/passwd

# Count unique values
awk '{count[$1]++} END {for (word in count) print count[word], word}' file.txt

# Calculate disk usage
df -h | awk 'NR>1 {print $5, $6}'

# Process log file
awk '/ERROR/ {count++} END {print "Errors:", count}' app.log
```

## cut - Extract Columns

Extract sections from lines:

```bash
cut -c1-10 file.txt               # Characters 1-10
cut -c5- file.txt                 # From character 5 to end
cut -d',' -f1 file.csv            # First field (comma delimiter)
cut -d',' -f1,3 file.csv          # Fields 1 and 3
cut -d',' -f1-3 file.csv          # Fields 1 through 3
cut -d':' -f1 /etc/passwd         # Usernames
```

## sort - Sort Lines

```bash
sort file.txt                     # Alphabetical sort
sort -r file.txt                  # Reverse
sort -n file.txt                  # Numeric sort
sort -h file.txt                  # Human-readable (1K, 2M)
sort -k2 file.txt                 # Sort by field 2
sort -k2,2n file.txt              # Numeric sort by field 2
sort -t',' -k2 file.csv           # Custom delimiter
sort -u file.txt                  # Unique only
sort -f file.txt                  # Case insensitive
```

### Practical Examples

```bash
# Sort by size (human readable)
ls -lh | sort -k5 -h

# Sort IP addresses
sort -t. -k1,1n -k2,2n -k3,3n -k4,4n ips.txt

# Find largest files
du -h * | sort -rh | head -10
```

## uniq - Filter Duplicates

Works on **sorted** input:

```bash
sort file.txt | uniq              # Remove duplicates
sort file.txt | uniq -c           # Count occurrences
sort file.txt | uniq -d           # Show only duplicates
sort file.txt | uniq -u           # Show only unique
```

### Common Pattern

```bash
# Count and sort by frequency
sort file.txt | uniq -c | sort -rn

# Top 10 most common
sort file.txt | uniq -c | sort -rn | head -10
```

## tr - Translate Characters

Character-by-character translation:

```bash
tr 'a-z' 'A-Z' < file.txt         # Lowercase to uppercase
tr 'A-Z' 'a-z' < file.txt         # Uppercase to lowercase
tr -d '0-9' < file.txt            # Delete digits
tr -s ' ' < file.txt              # Squeeze repeated spaces
tr '\n' ' ' < file.txt            # Newlines to spaces
tr -cd 'a-zA-Z\n' < file.txt      # Keep only letters
```

### Practical Examples

```bash
# Remove non-printable characters
tr -cd '[:print:]\n' < file.txt

# Convert Windows line endings
tr -d '\r' < windows.txt > unix.txt

# Create comma-separated list
ls | tr '\n' ','
```

## wc - Word Count

```bash
wc file.txt                       # Lines, words, bytes
wc -l file.txt                    # Lines only
wc -w file.txt                    # Words only
wc -c file.txt                    # Bytes only
wc -m file.txt                    # Characters only
wc -l *.txt                       # Multiple files with total
```

## Combining Tools

### Classic Pipelines

```bash
# Word frequency
cat file.txt | tr ' ' '\n' | sort | uniq -c | sort -rn | head -10

# Log analysis
cat access.log | grep "404" | awk '{print $7}' | sort | uniq -c | sort -rn

# Find large directories
du -h /home | sort -rh | head -20

# Extract emails
grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' file.txt | sort -u

# CSV processing
cut -d',' -f2,4 data.csv | sort -t',' -k1 | uniq
```

### Data Transformation

```bash
# JSON to CSV (simple)
cat data.json | grep -oE '"name":"[^"]*"' | cut -d'"' -f4

# Log timestamps
grep "ERROR" app.log | awk '{print $1, $2}' | sort | uniq -c

# Summarize by hour
awk '{print substr($4, 14, 2)}' access.log | sort | uniq -c
```

## Try It

1. grep practice:
   ```bash
   echo -e "apple\nbanana\napricot\ncherry" | grep "^a"
   echo -e "one\ntwo\nthree" | grep -n "t"
   ```

2. sed practice:
   ```bash
   echo "hello world" | sed 's/world/bash/'
   echo -e "line1\nline2\nline3" | sed -n '2p'
   ```

3. awk practice:
   ```bash
   echo -e "Alice 25\nBob 30\nCharlie 35" | awk '$2 > 28 {print $1}'
   echo -e "1\n2\n3\n4\n5" | awk '{sum+=$1} END {print "Sum:", sum}'
   ```

4. Pipeline:
   ```bash
   echo -e "banana\napple\napple\ncherry\nbanana\napple" | sort | uniq -c | sort -rn
   ```

## Summary

| Tool | Purpose |
|------|---------|
| `grep` | Search for patterns |
| `sed` | Stream editing/replacement |
| `awk` | Field-based processing |
| `cut` | Extract columns |
| `sort` | Sort lines |
| `uniq` | Filter duplicates |
| `tr` | Character translation |
| `wc` | Count lines/words/chars |

Key patterns:

- `grep pattern | wc -l` - Count matches
- `sort | uniq -c | sort -rn` - Frequency count
- `awk '{print $N}'` - Extract field N
- `sed 's/old/new/g'` - Replace all
- `cut -d',' -f1` - Extract CSV column
