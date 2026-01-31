# Files & Directories

Essential commands for working with files and directories: listing, creating, copying, moving, and removing.

## Listing Files (ls)

### Basic Usage

```bash
ls                  # List current directory
ls /etc             # List specific directory
ls file.txt         # Check if file exists
```

### Common Options

```bash
ls -l               # Long format (details)
ls -a               # Show hidden files (starting with .)
ls -la              # Both: long format + hidden
ls -lh              # Human-readable sizes (K, M, G)
ls -lt              # Sort by modification time
ls -lS              # Sort by size
ls -lR              # Recursive listing
ls -1               # One file per line
```

### Long Format Explained

```bash
ls -l
```

```
-rw-r--r--  1 user  staff   1234 Jan 15 10:30 file.txt
drwxr-xr-x  3 user  staff     96 Jan 14 09:00 mydir/
```

| Field | Meaning |
|-------|---------|
| `-rw-r--r--` | Permissions (see [Permissions](permissions.md)) |
| `1` | Number of hard links |
| `user` | Owner |
| `staff` | Group |
| `1234` | Size in bytes |
| `Jan 15 10:30` | Last modified |
| `file.txt` | Name |

### Filtering with Wildcards

```bash
ls *.txt            # All .txt files
ls file?.txt        # file1.txt, file2.txt, etc.
ls [abc]*           # Files starting with a, b, or c
ls **/*.md          # All .md files recursively (bash 4+)
```

Enable recursive globbing:

```bash
shopt -s globstar   # Enables **
```

## Modern Alternative: eza

`eza` (formerly `exa`) provides better output:

```bash
brew install eza
```

```bash
eza                 # Colorized output
eza -l              # Long format with icons
eza -la             # Include hidden files
eza --tree          # Tree view
eza --git           # Show git status
eza -l --header     # Show column headers
```

See [Modern Replacements](../tools/modern-replacements.md) for more.

## Creating Directories (mkdir)

```bash
mkdir mydir                     # Create directory
mkdir -p path/to/nested/dir     # Create nested (parents too)
mkdir dir1 dir2 dir3            # Multiple directories
mkdir -m 755 secure             # Create with specific permissions
```

The `-p` flag is essential - it:

- Creates parent directories as needed
- Doesn't error if directory exists

```bash
mkdir -p projects/{frontend,backend}/{src,tests}
```

Creates:

```
projects/
├── frontend/
│   ├── src/
│   └── tests/
└── backend/
    ├── src/
    └── tests/
```

## Creating Files (touch)

```bash
touch file.txt              # Create empty file
touch file1.txt file2.txt   # Multiple files
touch existing.txt          # Update modification time
```

Touch is often used to:

1. Create empty placeholder files
2. Update timestamps for make/build tools

For creating files with content, use redirection:

```bash
echo "content" > file.txt
```

## Copying (cp)

```bash
cp source.txt dest.txt          # Copy file
cp file.txt /path/to/dir/       # Copy to directory
cp -r mydir/ newdir/            # Copy directory recursively
cp -i source.txt dest.txt       # Prompt before overwrite
cp -n source.txt dest.txt       # Never overwrite
cp -v source.txt dest.txt       # Verbose output
cp -p source.txt dest.txt       # Preserve permissions/timestamps
```

### Copy Multiple Files

```bash
cp file1.txt file2.txt /dest/   # Multiple files to directory
cp *.txt /dest/                 # Using wildcards
```

### Recursive Copy

The `-r` flag is required for directories:

```bash
cp -r source_dir/ dest_dir/     # Copy directory and contents
```

!!! warning "Trailing Slashes"
    Behavior can differ:
    ```bash
    cp -r dir1 dir2      # Creates dir2/dir1 if dir2 exists
    cp -r dir1/ dir2/    # Copies contents of dir1 into dir2
    ```

## Moving & Renaming (mv)

Moving and renaming use the same command:

```bash
mv old.txt new.txt              # Rename
mv file.txt /path/to/dir/       # Move
mv old_dir/ new_dir/            # Rename directory
mv file.txt /path/to/newname    # Move and rename
mv -i source dest               # Prompt before overwrite
mv -n source dest               # Never overwrite
mv -v source dest               # Verbose
```

### Move Multiple Files

```bash
mv file1.txt file2.txt /dest/
mv *.txt /dest/
```

Unlike `cp`, no `-r` flag is needed for directories.

## Removing (rm)

```bash
rm file.txt                     # Remove file
rm file1.txt file2.txt          # Remove multiple files
rm -r mydir/                    # Remove directory and contents
rm -rf mydir/                   # Force remove (no prompts)
rm -i file.txt                  # Prompt for confirmation
rm -v file.txt                  # Verbose
```

!!! danger "rm -rf"
    `rm -rf` is dangerous. It removes files recursively without confirmation.

    - **Never** run `rm -rf /` or `rm -rf *` without extreme care
    - **Never** use variables without checking: `rm -rf $DIR` where DIR might be empty
    - Consider using trash utilities instead (see below)

### Safe Practices

Always verify before removing:

```bash
# List first
ls *.log
# Then remove
rm *.log
```

Or use interactive mode:

```bash
rm -i *.log
```

### Safer Alternative: trash

Install a trash utility:

```bash
brew install trash              # macOS
```

```bash
trash file.txt                  # Moves to Trash
```

## Removing Directories (rmdir)

```bash
rmdir empty_dir                 # Remove empty directory only
rmdir -p path/to/empty          # Remove empty parents too
```

`rmdir` only works on empty directories - use `rm -r` for directories with contents.

## Viewing File Information

### file Command

Determine file type:

```bash
file document.pdf
```

```
document.pdf: PDF document, version 1.4
```

```bash
file script.sh
```

```
script.sh: Bourne-Again shell script, ASCII text executable
```

### stat Command

Detailed file information:

```bash
stat file.txt
```

macOS format:

```
16777220 8726849 -rw-r--r-- 1 user staff 0 1234 "Jan 15 10:30:00 2024" ...
```

Linux format:

```
  File: file.txt
  Size: 1234            Blocks: 8          IO Block: 4096   regular file
Device: 801h/2049d      Inode: 1234567     Links: 1
Access: (0644/-rw-r--r--)  Uid: ( 1000/    user)   Gid: ( 1000/   staff)
...
```

## File Existence Tests

Check if files/directories exist in scripts:

```bash
[[ -f file.txt ]] && echo "File exists"
[[ -d mydir ]] && echo "Directory exists"
[[ -e anything ]] && echo "Exists (file or dir)"
[[ -r file.txt ]] && echo "Readable"
[[ -w file.txt ]] && echo "Writable"
[[ -x script.sh ]] && echo "Executable"
```

## Working with Hidden Files

Files starting with `.` are hidden:

```bash
touch .hidden           # Create hidden file
ls -a                   # Show hidden files
ls -A                   # Show hidden except . and ..
```

Common hidden files:

```
.bashrc                 # Bash configuration
.gitignore              # Git ignore patterns
.env                    # Environment variables
.ssh/                   # SSH configuration
```

## Brace Expansion

Efficiently create multiple files/directories:

```bash
# Create multiple files
touch file{1,2,3}.txt   # file1.txt, file2.txt, file3.txt
touch file{1..5}.txt    # file1.txt through file5.txt
touch {a,b,c}{1,2}.txt  # a1.txt, a2.txt, b1.txt, b2.txt, c1.txt, c2.txt

# Create directory structure
mkdir -p project/{src,tests,docs}

# Copy with rename
cp file.txt{,.bak}      # Creates file.txt.bak
```

## Common Patterns

### Backup Before Editing

```bash
cp config.yml{,.bak}    # Creates config.yml.bak
```

### Move All Except One

```bash
shopt -s extglob
mv !(keep.txt) /dest/
```

### Count Files in Directory

```bash
ls -1 | wc -l           # Count visible files
ls -1A | wc -l          # Count including hidden
```

### Find Large Files

```bash
ls -lhS | head -10      # 10 largest files
```

## Try It

1. Create a test directory structure:
   ```bash
   mkdir -p ~/test-files/{docs,src,tests}
   touch ~/test-files/docs/{readme,changelog}.md
   touch ~/test-files/src/{main,utils}.py
   ls -laR ~/test-files
   ```

2. Practice copying and moving:
   ```bash
   cp ~/test-files/docs/readme.md ~/test-files/docs/readme.bak
   mv ~/test-files/docs/changelog.md ~/test-files/
   ls ~/test-files/docs/
   ```

3. Clean up:
   ```bash
   rm -rf ~/test-files
   ```

## Summary

| Command | Purpose |
|---------|---------|
| `ls` | List files |
| `mkdir` | Create directory |
| `mkdir -p` | Create nested directories |
| `touch` | Create file / update timestamp |
| `cp` | Copy files |
| `cp -r` | Copy directories |
| `mv` | Move / rename |
| `rm` | Remove files |
| `rm -r` | Remove directories |
| `rmdir` | Remove empty directories |
| `file` | Identify file type |
| `stat` | Detailed file info |
