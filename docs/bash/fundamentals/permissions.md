# Permissions

Understanding Unix permissions is essential for security and proper system administration.

## The Permission Model

Every file and directory has:

- An **owner** (user)
- A **group**
- **Permissions** for owner, group, and others

```bash
ls -l file.txt
```

```
-rw-r--r--  1 alice  staff  1234 Jan 15 10:30 file.txt
```

Breaking down `-rw-r--r--`:

| Position | Meaning |
|----------|---------|
| `-` | File type (`-` file, `d` directory, `l` link) |
| `rw-` | Owner permissions |
| `r--` | Group permissions |
| `---` | Other permissions |

## Permission Types

| Symbol | Meaning | File | Directory |
|--------|---------|------|-----------|
| `r` | Read | View contents | List contents |
| `w` | Write | Modify contents | Create/delete files |
| `x` | Execute | Run as program | Enter directory |
| `-` | None | Permission denied | Permission denied |

### Directory Permissions Explained

For directories, permissions work differently:

- **Read (r)**: Can list files with `ls`
- **Write (w)**: Can create, delete, rename files inside
- **Execute (x)**: Can `cd` into directory, access files

!!! warning "Common Gotcha"
    A directory needs `x` permission to access anything inside, even with `r`:
    ```bash
    chmod 644 mydir   # Can't cd into it!
    chmod 755 mydir   # Now accessible
    ```

## Numeric (Octal) Notation

Permissions can be expressed as numbers:

| Permission | Value |
|------------|-------|
| Read (r) | 4 |
| Write (w) | 2 |
| Execute (x) | 1 |
| None (-) | 0 |

Add values for each category:

| Octal | Permissions | Meaning |
|-------|-------------|---------|
| `7` | `rwx` | Full access |
| `6` | `rw-` | Read and write |
| `5` | `r-x` | Read and execute |
| `4` | `r--` | Read only |
| `3` | `-wx` | Write and execute |
| `2` | `-w-` | Write only |
| `1` | `--x` | Execute only |
| `0` | `---` | No access |

Common permission sets:

| Octal | Symbolic | Typical Use |
|-------|----------|-------------|
| `755` | `rwxr-xr-x` | Executables, directories |
| `644` | `rw-r--r--` | Regular files |
| `700` | `rwx------` | Private directories |
| `600` | `rw-------` | Private files |
| `777` | `rwxrwxrwx` | Full access (avoid!) |

## chmod - Change Mode

### Symbolic Mode

```bash
chmod u+x script.sh         # Add execute for user
chmod g-w file.txt          # Remove write for group
chmod o=r file.txt          # Set others to read only
chmod a+r file.txt          # Add read for all
chmod u+x,g-w file.txt      # Multiple changes
```

Symbols:

| Symbol | Meaning |
|--------|---------|
| `u` | User (owner) |
| `g` | Group |
| `o` | Others |
| `a` | All (u+g+o) |
| `+` | Add permission |
| `-` | Remove permission |
| `=` | Set exactly |

### Numeric Mode

```bash
chmod 755 script.sh         # rwxr-xr-x
chmod 644 file.txt          # rw-r--r--
chmod 600 secret.txt        # rw-------
chmod 700 private_dir       # rwx------
```

### Recursive Changes

```bash
chmod -R 755 directory/     # Apply to all contents
chmod -R u+w directory/     # Add write recursively
```

### Reference Another File

```bash
chmod --reference=good.txt bad.txt
```

## chown - Change Owner

Change file ownership:

```bash
chown alice file.txt            # Change owner
chown alice:staff file.txt      # Change owner and group
chown :staff file.txt           # Change group only
chown -R alice:staff directory/ # Recursive
```

!!! note "Root Required"
    Only root (sudo) can change file ownership:
    ```bash
    sudo chown alice file.txt
    ```

## chgrp - Change Group

```bash
chgrp staff file.txt            # Change group
chgrp -R staff directory/       # Recursive
```

## umask - Default Permissions

`umask` sets default permissions for new files:

```bash
umask               # Show current mask
```

```
0022
```

The umask is **subtracted** from maximum permissions:

- Files max: `666` (no execute by default)
- Directories max: `777`

| umask | File Result | Directory Result |
|-------|-------------|------------------|
| `022` | `644` | `755` |
| `077` | `600` | `700` |
| `002` | `664` | `775` |

Set umask:

```bash
umask 022           # Common default
umask 077           # Private files
```

Add to `.bashrc` for persistence.

## Special Permissions

### Setuid (Set User ID)

When executed, runs as the file owner:

```bash
ls -l /usr/bin/passwd
```

```
-rwsr-xr-x 1 root root 68208 Jan 1 00:00 /usr/bin/passwd
```

The `s` in owner execute position indicates setuid.

```bash
chmod u+s executable        # Set setuid
chmod 4755 executable       # Numeric (4 = setuid)
```

### Setgid (Set Group ID)

For files: runs as file's group
For directories: new files inherit directory's group

```bash
chmod g+s directory/        # Set setgid
chmod 2755 directory/       # Numeric (2 = setgid)
```

### Sticky Bit

Only owner (or root) can delete files in directory:

```bash
ls -ld /tmp
```

```
drwxrwxrwt 10 root root 4096 Jan 15 10:30 /tmp
```

The `t` indicates sticky bit.

```bash
chmod +t directory/         # Set sticky bit
chmod 1777 directory/       # Numeric (1 = sticky)
```

### Combined Special Permissions

```bash
chmod 4755 file     # setuid + rwxr-xr-x
chmod 2755 dir      # setgid + rwxr-xr-x
chmod 1777 dir      # sticky + rwxrwxrwx
```

## Users and Groups

### View Current User

```bash
whoami              # Current username
id                  # User and group IDs
id username         # Info about another user
```

```
uid=501(alice) gid=20(staff) groups=20(staff),80(admin)
```

### List Groups

```bash
groups              # Your groups
groups username     # Another user's groups
```

### Managing Groups (Linux)

```bash
sudo groupadd developers
sudo usermod -aG developers alice   # Add user to group
newgrp developers                    # Switch primary group
```

## Common Permission Scenarios

### Make Script Executable

```bash
chmod +x script.sh
# or
chmod 755 script.sh
```

### Secure SSH Keys

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 600 ~/.ssh/config
```

### Web Server Files

```bash
chmod 644 public_html/*.html
chmod 755 public_html/
chmod 755 public_html/cgi-bin/*.cgi
```

### Shared Directory

```bash
mkdir /shared
chmod 2775 /shared          # setgid for group inheritance
chgrp staff /shared
```

### Private Directory

```bash
chmod 700 ~/private
```

## Checking Effective Permissions

### test Command

```bash
[[ -r file.txt ]] && echo "Readable"
[[ -w file.txt ]] && echo "Writable"
[[ -x file.txt ]] && echo "Executable"
```

### stat Command

```bash
stat -c "%a %U %G %n" file.txt      # Linux
stat -f "%Lp %Su %Sg %N" file.txt   # macOS
```

## ACLs (Access Control Lists)

For more granular control beyond owner/group/other:

### macOS

```bash
ls -le file.txt             # View ACLs
chmod +a "alice allow read" file.txt
chmod -a "alice allow read" file.txt   # Remove
```

### Linux

```bash
getfacl file.txt            # View ACLs
setfacl -m u:alice:rw file.txt
setfacl -x u:alice file.txt # Remove
```

## Try It

1. Create test files:
   ```bash
   mkdir ~/perm-test && cd ~/perm-test
   touch file.txt
   mkdir subdir
   ```

2. Examine permissions:
   ```bash
   ls -la
   stat file.txt
   ```

3. Modify permissions:
   ```bash
   chmod 600 file.txt
   ls -l file.txt
   chmod u+x file.txt
   ls -l file.txt
   ```

4. Test access:
   ```bash
   chmod 000 file.txt
   cat file.txt           # Permission denied
   chmod 644 file.txt
   cat file.txt           # Works
   ```

5. Clean up:
   ```bash
   cd && rm -rf ~/perm-test
   ```

## Summary

| Command | Purpose |
|---------|---------|
| `chmod` | Change permissions |
| `chown` | Change owner |
| `chgrp` | Change group |
| `umask` | Set default permissions |
| `ls -l` | View permissions |
| `stat` | Detailed file info |
| `id` | User and group info |

| Octal | Symbolic | Meaning |
|-------|----------|---------|
| `755` | `rwxr-xr-x` | Standard executable/directory |
| `644` | `rw-r--r--` | Standard file |
| `700` | `rwx------` | Private directory |
| `600` | `rw-------` | Private file |
