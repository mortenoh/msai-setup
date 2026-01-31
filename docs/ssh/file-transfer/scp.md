# SCP - Secure Copy

## Overview

SCP (Secure Copy Protocol) copies files between hosts over SSH. Simple, secure, and available wherever SSH is.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           SCP Transfer                                    │
│                                                                           │
│   Local Machine                              Remote Server                │
│   ┌─────────────────┐                       ┌─────────────────┐          │
│   │                 │      SSH Tunnel       │                 │          │
│   │   file.txt     ─┼──────────────────────▶│    file.txt     │          │
│   │                 │      Encrypted        │                 │          │
│   └─────────────────┘                       └─────────────────┘          │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Basic Syntax

```bash
scp [options] source destination
```

Locations can be:
- Local: `/path/to/file`
- Remote: `user@host:/path/to/file`

## Copy To Remote

### Single File

```bash
scp file.txt user@host:/home/user/
scp file.txt user@host:~/
scp file.txt user@host:~/newname.txt
```

### Multiple Files

```bash
scp file1.txt file2.txt user@host:~/
scp *.txt user@host:~/documents/
```

### Directory

```bash
scp -r directory/ user@host:~/
scp -r directory/ user@host:~/newdirname/
```

## Copy From Remote

### Single File

```bash
scp user@host:/path/to/file.txt ./
scp user@host:~/file.txt ./local_name.txt
```

### Multiple Files

```bash
scp user@host:~/file1.txt user@host:~/file2.txt ./
scp "user@host:~/*.txt" ./
```

### Directory

```bash
scp -r user@host:~/directory/ ./
```

## Copy Between Remote Hosts

```bash
scp user1@host1:/path/file.txt user2@host2:/path/
```

!!! note "Routing"
    By default, traffic goes through your local machine. Use `-3` to force this, or configure ProxyJump for direct transfer.

## Common Options

### Port

```bash
scp -P 2222 file.txt user@host:~/
```

### Identity File

```bash
scp -i ~/.ssh/mykey file.txt user@host:~/
```

### Recursive (Directories)

```bash
scp -r directory/ user@host:~/
```

### Preserve Attributes

```bash
scp -p file.txt user@host:~/
# Preserves modification times, access times, modes
```

### Compression

```bash
scp -C largefile.tar.gz user@host:~/
```

### Bandwidth Limit

```bash
scp -l 1000 file.txt user@host:~/
# Limit in Kbit/s (1000 Kbit/s = ~125 KB/s)
```

### Quiet Mode

```bash
scp -q file.txt user@host:~/
```

### Verbose

```bash
scp -v file.txt user@host:~/
```

## Using SSH Config

SCP uses `~/.ssh/config`:

```bash
# ~/.ssh/config
Host myserver
    HostName server.example.com
    User admin
    IdentityFile ~/.ssh/server_key
    Port 2222
```

Then simply:

```bash
scp file.txt myserver:~/
scp myserver:~/file.txt ./
```

## Through Jump Host

### With ProxyJump

```bash
scp -o ProxyJump=bastion file.txt internal:~/
```

### Using Config

```bash
# ~/.ssh/config
Host internal
    HostName 10.0.0.10
    User admin
    ProxyJump bastion
```

```bash
scp file.txt internal:~/
```

## Progress and Statistics

### Show Progress (Default)

```bash
scp file.txt user@host:~/
# Shows: file.txt    100%  1234KB  10.5MB/s   00:00
```

### Hide Progress

```bash
scp -q file.txt user@host:~/
```

## Handling Special Characters

### Spaces in Paths

```bash
# Quote the entire remote path
scp "user@host:~/path with spaces/file.txt" ./

# Or escape
scp user@host:~/path\ with\ spaces/file.txt ./
```

### Special Characters

```bash
scp "user@host:~/file[1].txt" ./
scp user@host:"~/file[1].txt" ./
```

## Large File Transfers

### With Compression

```bash
scp -C largefile.iso user@host:~/
```

### Resumable (Not Native)

SCP doesn't support resume. For large files, use rsync instead:

```bash
rsync -avP --partial largefile.iso user@host:~/
```

### Monitor Progress with pv

```bash
# Alternative approach
cat largefile.iso | pv | ssh user@host "cat > largefile.iso"
```

## Batch Operations

### Multiple Hosts

```bash
for host in server1 server2 server3; do
    scp file.txt user@$host:~/
done
```

### Multiple Files with Wildcards

```bash
scp user@host:"/var/log/*.log" ./logs/
```

### From File List

```bash
while read file; do
    scp "$file" user@host:~/backup/
done < filelist.txt
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Connection error |
| 65 | Host not allowed |
| 66 | Protocol error |

## Comparison with Alternatives

| Feature | SCP | SFTP | rsync |
|---------|-----|------|-------|
| Simple copies | ✅ | ✅ | ✅ |
| Interactive | ❌ | ✅ | ❌ |
| Resume transfers | ❌ | ✅ | ✅ |
| Delta sync | ❌ | ❌ | ✅ |
| Preserve permissions | ✅ | ✅ | ✅ |
| Bandwidth limit | ✅ | ✅ | ✅ |
| Available everywhere | ✅ | ✅ | ⚠️ |

## When to Use SCP

**Use SCP for:**
- Quick, simple file copies
- Small to medium files
- One-off transfers
- Scripts needing simple syntax

**Use SFTP for:**
- Interactive file management
- Browsing remote directories
- Resume support

**Use rsync for:**
- Large files (resume support)
- Directory synchronization
- Incremental backups
- Bandwidth optimization

## Troubleshooting

### Permission Denied

```bash
# Check remote permissions
ssh user@host "ls -la ~/target/"

# Check you're using correct user
scp file.txt correctuser@host:~/
```

### Connection Refused

```bash
# Test SSH connection first
ssh user@host

# Check port
scp -P 2222 file.txt user@host:~/
```

### Slow Transfers

```bash
# Enable compression
scp -C file.txt user@host:~/

# Check network
ssh user@host "speedtest-cli"
```

### Path Issues

```bash
# Use absolute paths
scp file.txt user@host:/home/user/

# Quote paths with spaces
scp file.txt "user@host:/path with spaces/"
```

## Security Considerations

1. **Uses SSH encryption** - Traffic is secure
2. **Respects SSH config** - Same security as SSH
3. **Key-based auth** - Use keys, not passwords
4. **Verify host keys** - Don't skip host key verification

```bash
# Bad (skips verification)
scp -o StrictHostKeyChecking=no file.txt user@host:~/

# Good (uses verification)
scp file.txt user@host:~/
```
