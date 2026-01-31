# SSH Connection Options

## Command Line Reference

### Basic Syntax

```bash
ssh [options] [user@]hostname [command]
```

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `-p port` | Connect to port | `ssh -p 2222 host` |
| `-l user` | Login as user | `ssh -l admin host` |
| `-i key` | Use identity file | `ssh -i ~/.ssh/mykey host` |
| `-v` | Verbose (debug) | `ssh -vvv host` |
| `-q` | Quiet mode | `ssh -q host` |
| `-N` | No command (for tunnels) | `ssh -N -L 8080:localhost:80 host` |
| `-f` | Background after auth | `ssh -f -N -L 8080:localhost:80 host` |
| `-T` | Disable pseudo-terminal | `ssh -T host command` |
| `-t` | Force pseudo-terminal | `ssh -t host sudo command` |

## Identity and Authentication

### Specify Key File

```bash
ssh -i ~/.ssh/specific_key user@host
```

### Multiple Keys

```bash
ssh -i ~/.ssh/key1 -i ~/.ssh/key2 user@host
```

### Only Use Specified Keys

```bash
ssh -o IdentitiesOnly=yes -i ~/.ssh/mykey user@host
```

### Force Password

```bash
ssh -o PreferredAuthentications=password user@host
```

### Force Key

```bash
ssh -o PreferredAuthentications=publickey user@host
```

## Port and Network

### Custom Port

```bash
ssh -p 2222 user@host
```

### IPv4 Only

```bash
ssh -4 user@host
```

### IPv6 Only

```bash
ssh -6 user@host
```

### Bind to Source Address

```bash
ssh -b 192.168.1.50 user@host
```

## Terminal Options

### Force TTY Allocation

Needed for interactive commands like `sudo`:

```bash
ssh -t user@host sudo apt update
```

### Force TTY (Double)

For commands that check TTY:

```bash
ssh -tt user@host
```

### No TTY

For non-interactive commands:

```bash
ssh -T user@host command
```

## Tunneling Options

### Local Port Forward

```bash
ssh -L local_port:remote_host:remote_port user@host
ssh -L 8080:localhost:80 user@host
ssh -L 5432:database.internal:5432 user@host
```

### Remote Port Forward

```bash
ssh -R remote_port:local_host:local_port user@host
ssh -R 8080:localhost:3000 user@host
```

### Dynamic (SOCKS) Proxy

```bash
ssh -D local_port user@host
ssh -D 1080 user@host
```

### Tunnel Only (No Shell)

```bash
ssh -N -L 8080:localhost:80 user@host
```

### Background Tunnel

```bash
ssh -f -N -L 8080:localhost:80 user@host
```

## Jump Hosts

### ProxyJump (Recommended)

```bash
ssh -J jump_host user@destination
ssh -J bastion.example.com internal-server
```

### Multiple Jumps

```bash
ssh -J jump1,jump2,jump3 user@destination
```

### ProxyCommand (Legacy)

```bash
ssh -o ProxyCommand="ssh -W %h:%p jump_host" destination
```

## Execution Options

### Run Single Command

```bash
ssh user@host "ls -la"
```

### Run Command with Arguments

```bash
ssh user@host "grep -r 'pattern' /var/log/"
```

### Run Local Script Remotely

```bash
ssh user@host "bash -s" < local_script.sh
```

### Run with Environment

```bash
ssh user@host "export VAR=value; command"
```

### Background Execution

```bash
ssh user@host "nohup ./long_running.sh &"
```

## Host Key Options

### Skip Host Key Check (Dangerous)

```bash
ssh -o StrictHostKeyChecking=no user@host
```

### Accept New Keys Automatically

```bash
ssh -o StrictHostKeyChecking=accept-new user@host
```

### Different Known Hosts File

```bash
ssh -o UserKnownHostsFile=/dev/null user@host
```

### Combine (For Disposable Hosts)

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@host
```

## Cipher and Algorithm Options

### Specify Cipher

```bash
ssh -c chacha20-poly1305@openssh.com user@host
```

### Specify Key Exchange

```bash
ssh -o KexAlgorithms=curve25519-sha256 user@host
```

### Specify MAC

```bash
ssh -o MACs=hmac-sha2-256-etm@openssh.com user@host
```

### Specify Host Key Algorithm

```bash
ssh -o HostKeyAlgorithms=ssh-ed25519 user@host
```

## Compression

### Enable Compression

```bash
ssh -C user@host
```

### Compression Level

```bash
ssh -o Compression=yes -o CompressionLevel=9 user@host
```

## Keep-Alive

### Send Keep-Alive Packets

```bash
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 user@host
```

## Logging and Debugging

### Verbose Levels

```bash
ssh -v user@host     # Basic
ssh -vv user@host    # More
ssh -vvv user@host   # Maximum
```

### Quiet Mode

```bash
ssh -q user@host
```

### Log to File

```bash
ssh -E /tmp/ssh.log user@host
```

## Multiplexing

### Master Connection

```bash
ssh -M -S /tmp/ssh-socket user@host
```

### Use Existing Connection

```bash
ssh -S /tmp/ssh-socket user@host
```

### Check Connection Status

```bash
ssh -S /tmp/ssh-socket -O check user@host
```

### Close Master Connection

```bash
ssh -S /tmp/ssh-socket -O exit user@host
```

## X11 Forwarding

### Enable X11 Forwarding

```bash
ssh -X user@host
```

### Trusted X11 Forwarding

```bash
ssh -Y user@host
```

## Environment

### Send Environment Variable

```bash
ssh -o SendEnv=MY_VAR user@host
```

### Set Remote Environment

```bash
ssh -o SetEnv="FOO=bar" user@host
```

## Batch Mode

### Non-Interactive (Scripts)

```bash
ssh -o BatchMode=yes user@host command
```

Fails immediately if interaction required.

## Configuration Override

### Override Config File

```bash
ssh -F /path/to/custom_config user@host
```

### No Config File

```bash
ssh -F /dev/null user@host
```

### Set Any Option

```bash
ssh -o "Option=value" user@host
```

Multiple options:

```bash
ssh -o "Option1=value1" -o "Option2=value2" user@host
```

## Practical Examples

### Debug Connection Issues

```bash
ssh -vvv user@host 2>&1 | tee ssh_debug.log
```

### Test Key Without Login

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 user@host echo ok
```

### Port Forward in Background

```bash
ssh -f -N -L 5432:localhost:5432 db.example.com
```

### SOCKS Proxy for Browser

```bash
ssh -D 1080 -C -q -N proxy.example.com
```

### Execute Multiple Commands

```bash
ssh user@host << 'EOF'
cd /var/log
ls -la
tail -n 100 syslog
EOF
```

### Copy with Progress

```bash
ssh user@host "cat file.tar.gz" | pv > file.tar.gz
```

### Parallel SSH (with GNU Parallel)

```bash
parallel ssh {} "uptime" ::: host1 host2 host3
```
