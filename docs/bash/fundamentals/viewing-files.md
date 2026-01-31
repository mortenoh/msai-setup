# Viewing Files

Commands for reading and examining file contents without editing.

## cat - Concatenate and Print

The simplest way to view file contents:

```bash
cat file.txt                    # Print entire file
cat file1.txt file2.txt         # Concatenate multiple files
cat -n file.txt                 # Number all lines
cat -b file.txt                 # Number non-empty lines
cat -s file.txt                 # Squeeze blank lines
cat -A file.txt                 # Show all (tabs, line endings)
```

### Showing Special Characters

```bash
cat -A file.txt
```

Shows:

- `^I` for tabs
- `$` at end of lines
- `^M` for Windows carriage returns

Useful for debugging whitespace issues.

### Creating Files with cat

```bash
cat > newfile.txt << 'EOF'
Line 1
Line 2
EOF
```

## less - Pager for Large Files

For files too large to fit on screen:

```bash
less file.txt
```

### Navigation

| Key | Action |
|-----|--------|
| `Space` / `f` | Forward one page |
| `b` | Back one page |
| `d` | Forward half page |
| `u` | Back half page |
| `g` | Go to beginning |
| `G` | Go to end |
| `q` | Quit |

### Searching

| Key | Action |
|-----|--------|
| `/pattern` | Search forward |
| `?pattern` | Search backward |
| `n` | Next match |
| `N` | Previous match |
| `&pattern` | Show only matching lines |

### Useful Options

```bash
less -N file.txt        # Show line numbers
less -S file.txt        # Don't wrap long lines
less -i file.txt        # Case-insensitive search
less +F file.txt        # Follow mode (like tail -f)
less +/pattern file.txt # Start at first match
```

### Less vs More

`more` is older and less capable. Always prefer `less`:

```bash
# less has:
# - Backward navigation
# - Better search
# - No screen clear on exit (with -X)
less -X file.txt
```

## head - View Beginning

```bash
head file.txt           # First 10 lines (default)
head -n 20 file.txt     # First 20 lines
head -n -5 file.txt     # All but last 5 lines
head -c 100 file.txt    # First 100 bytes
```

Multiple files:

```bash
head -n 5 *.txt
```

```
==> file1.txt <==
Line 1
...

==> file2.txt <==
Line 1
...
```

## tail - View End

```bash
tail file.txt           # Last 10 lines (default)
tail -n 20 file.txt     # Last 20 lines
tail -n +5 file.txt     # Starting from line 5
tail -c 100 file.txt    # Last 100 bytes
```

### Follow Mode

Watch a file for changes (essential for logs):

```bash
tail -f /var/log/system.log     # Follow file
tail -F /var/log/system.log     # Follow, handles rotation
tail -f -n 50 logfile           # Last 50 lines, then follow
```

Exit follow mode with `Ctrl+C`.

### Multiple Files

```bash
tail -f log1.txt log2.txt
```

## Combining head and tail

View lines 10-20:

```bash
head -n 20 file.txt | tail -n 11
```

Or with `sed`:

```bash
sed -n '10,20p' file.txt
```

## wc - Word Count

```bash
wc file.txt             # lines, words, bytes
wc -l file.txt          # Lines only
wc -w file.txt          # Words only
wc -c file.txt          # Bytes only
wc -m file.txt          # Characters only
```

Example:

```bash
wc -l *.py
```

```
   45 main.py
   23 utils.py
   68 total
```

## file - Identify File Type

Determine what a file contains:

```bash
file image.png
```

```
image.png: PNG image data, 800 x 600, 8-bit/color RGB, non-interlaced
```

```bash
file mystery_file
```

```
mystery_file: gzip compressed data, was "backup.tar", from Unix
```

```bash
file script.sh
```

```
script.sh: Bourne-Again shell script, ASCII text executable
```

Useful for:

- Files without extensions
- Verifying file types
- Detecting encoding issues

### MIME Type

```bash
file --mime-type document.pdf
```

```
document.pdf: application/pdf
```

## Modern Alternative: bat

`bat` is a `cat` replacement with syntax highlighting:

```bash
brew install bat
```

```bash
bat file.py             # Syntax highlighting
bat -n file.txt         # Line numbers only (no header)
bat -p file.txt         # Plain (no decorations)
bat -A file.txt         # Show non-printable characters
bat --diff file.txt     # Show git changes
```

Features:

- Automatic syntax detection
- Git integration
- Line highlighting
- Paging built-in

See [Modern Replacements](../tools/modern-replacements.md).

## Viewing Specific Parts

### Extract Lines by Number

With `sed`:

```bash
sed -n '5p' file.txt            # Line 5 only
sed -n '5,10p' file.txt         # Lines 5-10
sed -n '5p;10p;15p' file.txt    # Lines 5, 10, and 15
```

With `awk`:

```bash
awk 'NR==5' file.txt            # Line 5
awk 'NR>=5 && NR<=10' file.txt  # Lines 5-10
```

### Extract Columns

```bash
cut -d',' -f1,3 data.csv        # Fields 1 and 3
cut -c1-10 file.txt             # Characters 1-10
```

## Viewing Binary Files

### hexdump / xxd

```bash
hexdump -C file.bin | head      # Hex + ASCII
xxd file.bin | head             # Alternative format
xxd -b file.bin | head          # Binary format
```

### strings

Extract readable text from binary:

```bash
strings binary_file
strings -n 10 binary_file       # Minimum 10 characters
```

## Comparing Files

### diff

```bash
diff file1.txt file2.txt        # Show differences
diff -u file1.txt file2.txt     # Unified format (patch style)
diff -y file1.txt file2.txt     # Side by side
diff -q file1.txt file2.txt     # Just report if different
```

### comm

Compare sorted files:

```bash
comm file1.txt file2.txt
```

Output columns:

1. Lines only in file1
2. Lines only in file2
3. Lines in both

## Practical Examples

### Check Log Errors

```bash
tail -f /var/log/app.log | grep -i error
```

### Quick File Preview

```bash
head -n 50 file.txt
```

### Count Lines of Code

```bash
wc -l src/*.py
```

### View CSV Header

```bash
head -n 1 data.csv
```

### Check File Encoding

```bash
file -i document.txt
```

```
document.txt: text/plain; charset=utf-8
```

## Try It

1. Create a test file:
   ```bash
   seq 1 100 > /tmp/numbers.txt
   ```

2. Practice viewing:
   ```bash
   cat /tmp/numbers.txt
   head -n 5 /tmp/numbers.txt
   tail -n 5 /tmp/numbers.txt
   head -n 20 /tmp/numbers.txt | tail -n 10
   ```

3. Use less:
   ```bash
   less /tmp/numbers.txt
   # Try: /50, n, g, G, q
   ```

4. Count and identify:
   ```bash
   wc -l /tmp/numbers.txt
   file /tmp/numbers.txt
   ```

5. Clean up:
   ```bash
   rm /tmp/numbers.txt
   ```

## Summary

| Command | Purpose |
|---------|---------|
| `cat` | Print entire file |
| `less` | Page through file |
| `head` | View beginning |
| `tail` | View end |
| `tail -f` | Follow file updates |
| `wc` | Count lines/words/bytes |
| `file` | Identify file type |
| `diff` | Compare files |
| `bat` | Syntax-highlighted viewing |
