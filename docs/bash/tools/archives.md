# Archives

Working with compressed files and archives: tar, gzip, zip, and more.

## tar - Tape Archive

The standard Unix archiving tool.

### Create Archives

```bash
# Create tar archive
tar -cvf archive.tar dir/
tar -cvf archive.tar file1 file2 dir/

# Create compressed archives
tar -czvf archive.tar.gz dir/         # gzip (most common)
tar -cjvf archive.tar.bz2 dir/        # bzip2 (better compression)
tar -cJvf archive.tar.xz dir/         # xz (best compression)
```

### Extract Archives

```bash
# Extract tar
tar -xvf archive.tar
tar -xvf archive.tar -C /destination/

# Extract compressed
tar -xzvf archive.tar.gz              # gzip
tar -xjvf archive.tar.bz2             # bzip2
tar -xJvf archive.tar.xz              # xz

# Auto-detect compression
tar -xvf archive.tar.gz               # Often works without z/j/J
```

### List Contents

```bash
tar -tvf archive.tar                  # List contents
tar -tzvf archive.tar.gz              # List compressed
```

### Common Options

| Option | Meaning |
|--------|---------|
| `-c` | Create archive |
| `-x` | Extract archive |
| `-t` | List contents |
| `-v` | Verbose |
| `-f` | Specify filename |
| `-z` | gzip compression |
| `-j` | bzip2 compression |
| `-J` | xz compression |
| `-C` | Change directory |
| `-p` | Preserve permissions |
| `--exclude` | Exclude pattern |

### Selective Operations

```bash
# Extract specific files
tar -xvf archive.tar path/to/file

# Extract with pattern
tar -xvf archive.tar --wildcards '*.txt'

# Exclude files
tar -czvf archive.tar.gz --exclude='*.log' --exclude='node_modules' dir/

# Exclude patterns from file
tar -czvf archive.tar.gz -X exclude.txt dir/
```

### Practical Examples

```bash
# Backup with date
tar -czvf "backup-$(date +%Y%m%d).tar.gz" /data/

# Archive preserving permissions
tar -cpzvf archive.tar.gz dir/

# Extract without top directory
tar -xzvf archive.tar.gz --strip-components=1

# Create from list of files
tar -czvf archive.tar.gz -T files.txt

# View without extracting
tar -tzvf archive.tar.gz | grep "pattern"

# Add to existing archive (uncompressed only)
tar -rvf archive.tar newfile
```

## gzip / gunzip

Compress single files:

```bash
gzip file.txt                         # Creates file.txt.gz
gzip -k file.txt                      # Keep original
gzip -d file.txt.gz                   # Decompress
gunzip file.txt.gz                    # Same as gzip -d
gzip -l file.txt.gz                   # Show compression stats
```

### Options

```bash
gzip -1 file.txt                      # Fastest compression
gzip -9 file.txt                      # Best compression
gzip -c file.txt > file.txt.gz        # Output to stdout
gzip -r dir/                          # Recursive
```

### zcat / zless / zgrep

Work with gzipped files without extracting:

```bash
zcat file.txt.gz                      # View contents
zless file.txt.gz                     # Page through
zgrep "pattern" file.txt.gz           # Search in compressed
```

## bzip2 / bunzip2

Better compression than gzip:

```bash
bzip2 file.txt                        # Creates file.txt.bz2
bzip2 -k file.txt                     # Keep original
bzip2 -d file.txt.bz2                 # Decompress
bunzip2 file.txt.bz2                  # Same as bzip2 -d
```

Related tools: `bzcat`, `bzless`, `bzgrep`

## xz / unxz

Best compression ratio:

```bash
xz file.txt                           # Creates file.txt.xz
xz -k file.txt                        # Keep original
xz -d file.txt.xz                     # Decompress
unxz file.txt.xz                      # Same as xz -d
xz -l file.txt.xz                     # Show info
```

Options:

```bash
xz -0 file.txt                        # Fastest
xz -9 file.txt                        # Best compression (slow)
xz -T 4 file.txt                      # Use 4 threads
```

Related tools: `xzcat`, `xzless`, `xzgrep`

## zip / unzip

Cross-platform archive format:

### Creating Archives

```bash
zip archive.zip file1 file2           # Add files
zip -r archive.zip dir/               # Recursive (directory)
zip -j archive.zip dir/*              # No directory structure
zip -e archive.zip file               # Encrypted (prompts for password)
zip -9 archive.zip file               # Best compression
```

### Extracting

```bash
unzip archive.zip                     # Extract all
unzip archive.zip -d /destination/    # Extract to directory
unzip archive.zip file.txt            # Extract specific file
unzip -l archive.zip                  # List contents
unzip -t archive.zip                  # Test integrity
unzip -o archive.zip                  # Overwrite without prompting
```

### Managing Archives

```bash
zip -u archive.zip newfile            # Update/add file
zip -d archive.zip file               # Delete from archive
zip -sf archive.zip                   # Show files (like -l)
```

## 7z (p7zip)

High compression, many formats:

### Installation

```bash
# macOS
brew install p7zip

# Debian/Ubuntu
apt install p7zip-full
```

### Usage

```bash
7z a archive.7z dir/                  # Create archive
7z x archive.7z                       # Extract
7z l archive.7z                       # List contents
7z t archive.7z                       # Test integrity
7z e archive.7z                       # Extract (flat)
```

### Options

```bash
7z a -p archive.7z dir/               # Password protected
7z a -mx=9 archive.7z dir/            # Maximum compression
7z a -v100m archive.7z dir/           # Split into 100MB volumes
```

## Compression Comparison

| Format | Extension | Compression | Speed | Compatibility |
|--------|-----------|-------------|-------|---------------|
| gzip | .gz | Good | Fast | Universal |
| bzip2 | .bz2 | Better | Slower | Common |
| xz | .xz | Best | Slowest | Modern systems |
| zip | .zip | Good | Fast | Universal (Windows) |
| 7z | .7z | Best | Slow | Needs 7zip |

### When to Use What

- **tar.gz**: Default choice for Unix backups and transfers
- **tar.xz**: When size matters more than time
- **zip**: Sharing with Windows users
- **7z**: Maximum compression needed

## Practical Patterns

### Backup Script

```bash
#!/usr/bin/env bash
backup_dir="/backup"
source_dir="/data"
date_stamp=$(date +%Y%m%d_%H%M%S)
archive="${backup_dir}/backup_${date_stamp}.tar.gz"

tar -czvf "$archive" \
    --exclude='*.log' \
    --exclude='tmp/*' \
    "$source_dir"

echo "Backup created: $archive"
```

### Extract Based on Extension

```bash
extract() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "Error: '$file' not found"
        return 1
    fi

    case "$file" in
        *.tar.bz2)  tar -xjvf "$file" ;;
        *.tar.gz)   tar -xzvf "$file" ;;
        *.tar.xz)   tar -xJvf "$file" ;;
        *.tar)      tar -xvf "$file" ;;
        *.bz2)      bunzip2 "$file" ;;
        *.gz)       gunzip "$file" ;;
        *.xz)       unxz "$file" ;;
        *.zip)      unzip "$file" ;;
        *.7z)       7z x "$file" ;;
        *.rar)      unrar x "$file" ;;
        *)          echo "Unknown format: $file" && return 1 ;;
    esac
}
```

### Compress with Progress

```bash
# Using pv for progress
tar -cf - dir/ | pv -s $(du -sb dir/ | awk '{print $1}') | gzip > archive.tar.gz
```

### Split Large Archives

```bash
# Create split archive
tar -czvf - largedir/ | split -b 100M - archive.tar.gz.

# Rejoin and extract
cat archive.tar.gz.* | tar -xzvf -
```

### Transfer with Compression

```bash
# Compress and transfer
tar -czvf - dir/ | ssh user@host 'cat > /path/archive.tar.gz'

# Transfer and extract
tar -czvf - dir/ | ssh user@host 'tar -xzvf - -C /destination/'

# Using rsync with compression
rsync -avz dir/ user@host:/path/
```

### Compare Archive Contents

```bash
# List files in both
diff <(tar -tzf archive1.tar.gz | sort) <(tar -tzf archive2.tar.gz | sort)
```

## Try It

1. Create tar.gz:
   ```bash
   mkdir -p /tmp/test_archive
   echo "test" > /tmp/test_archive/file.txt
   tar -czvf /tmp/test.tar.gz /tmp/test_archive
   tar -tzvf /tmp/test.tar.gz
   rm -rf /tmp/test_archive /tmp/test.tar.gz
   ```

2. Compress single file:
   ```bash
   echo "test content" > /tmp/test.txt
   gzip -k /tmp/test.txt
   ls -la /tmp/test.txt*
   zcat /tmp/test.txt.gz
   rm /tmp/test.txt*
   ```

3. Create zip:
   ```bash
   echo "test" > /tmp/test.txt
   zip /tmp/test.zip /tmp/test.txt
   unzip -l /tmp/test.zip
   rm /tmp/test.txt /tmp/test.zip
   ```

## Summary

| Task | Command |
|------|---------|
| Create tar.gz | `tar -czvf archive.tar.gz dir/` |
| Extract tar.gz | `tar -xzvf archive.tar.gz` |
| List tar contents | `tar -tzvf archive.tar.gz` |
| Create zip | `zip -r archive.zip dir/` |
| Extract zip | `unzip archive.zip` |
| Compress file | `gzip file` |
| Decompress file | `gunzip file.gz` |
| View compressed | `zcat file.gz` |

Compression flags for tar:

| Flag | Format | Extension |
|------|--------|-----------|
| `-z` | gzip | .tar.gz, .tgz |
| `-j` | bzip2 | .tar.bz2 |
| `-J` | xz | .tar.xz |
