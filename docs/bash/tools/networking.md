# Networking

Command-line tools for HTTP requests, downloads, SSH, and network diagnostics.

## curl - HTTP Client

The Swiss Army knife for HTTP requests.

### Basic Requests

```bash
curl https://example.com          # GET request
curl -o file.html https://example.com  # Save to file
curl -O https://example.com/file.zip   # Save with original name
curl -L https://example.com       # Follow redirects
curl -I https://example.com       # Headers only (HEAD)
curl -v https://example.com       # Verbose (debug)
curl -s https://example.com       # Silent (no progress)
```

### HTTP Methods

```bash
# GET (default)
curl https://api.example.com/users

# POST
curl -X POST https://api.example.com/users

# PUT
curl -X PUT https://api.example.com/users/1

# DELETE
curl -X DELETE https://api.example.com/users/1

# PATCH
curl -X PATCH https://api.example.com/users/1
```

### Sending Data

```bash
# POST form data
curl -d "name=Alice&age=30" https://api.example.com/users

# POST JSON
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","age":30}' \
  https://api.example.com/users

# POST from file
curl -d @data.json https://api.example.com/users

# POST file upload
curl -F "file=@photo.jpg" https://api.example.com/upload
```

### Headers

```bash
# Add header
curl -H "Authorization: Bearer TOKEN" https://api.example.com

# Multiple headers
curl -H "Accept: application/json" \
     -H "Authorization: Bearer TOKEN" \
     https://api.example.com

# User agent
curl -A "MyApp/1.0" https://example.com
```

### Authentication

```bash
# Basic auth
curl -u username:password https://api.example.com

# Bearer token
curl -H "Authorization: Bearer TOKEN" https://api.example.com

# API key in header
curl -H "X-API-Key: APIKEY" https://api.example.com
```

### Useful Options

```bash
curl -w "%{http_code}" -o /dev/null -s URL  # Just status code
curl -w "%{time_total}s\n" -o /dev/null -s URL  # Response time
curl --retry 3 URL                 # Retry on failure
curl --connect-timeout 10 URL      # Connection timeout
curl --max-time 30 URL             # Total timeout
curl -k URL                        # Ignore SSL errors (insecure!)
curl --compressed URL              # Request compression
```

### Download Examples

```bash
# Resume download
curl -C - -O https://example.com/large-file.zip

# Download multiple
curl -O https://example.com/file1.txt -O https://example.com/file2.txt

# Show progress bar
curl -# -O https://example.com/file.zip

# Rate limit
curl --limit-rate 1M -O URL        # Max 1 MB/s
```

### API Examples

```bash
# GET with jq
curl -s https://api.github.com/users/octocat | jq '.name'

# POST and parse response
response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}' \
  https://api.example.com/items)
echo "$response" | jq '.id'

# Check API health
curl -sf https://api.example.com/health || echo "API is down"
```

## wget - Download Tool

Simpler tool focused on downloading.

### Basic Usage

```bash
wget https://example.com/file.zip         # Download file
wget -O name.zip URL                      # Custom filename
wget -c URL                               # Resume download
wget -q URL                               # Quiet mode
wget -b URL                               # Background
```

### Recursive Download

```bash
wget -r URL                               # Recursive
wget -r -l 2 URL                          # Depth limit 2
wget -r -np URL                           # No parent directories
wget -m URL                               # Mirror website
wget -p URL                               # Get page with assets
```

### Options

```bash
wget --no-check-certificate URL           # Skip SSL (insecure!)
wget --limit-rate=1m URL                  # Rate limit
wget --tries=3 URL                        # Retry count
wget --timeout=30 URL                     # Timeout
wget -i urls.txt                          # Download list of URLs
```

## SSH - Secure Shell

See the [SSH section](../../ssh/index.md) for comprehensive coverage.

### Quick Reference

```bash
# Basic connection
ssh user@host

# With port
ssh -p 2222 user@host

# Run command
ssh user@host 'ls -la'

# Forward local port
ssh -L 8080:localhost:80 user@host

# Copy files
scp file.txt user@host:/path/
scp user@host:/path/file.txt ./

# Sync directories
rsync -avz dir/ user@host:/path/
```

## nc (netcat) - Network Swiss Army Knife

Low-level TCP/UDP tool.

### Port Scanning

```bash
nc -zv host 80                    # Check if port 80 is open
nc -zv host 20-30                 # Scan port range
```

### Simple Client/Server

```bash
# Server (listen)
nc -l 1234

# Client (connect)
nc localhost 1234

# Then type messages back and forth
```

### File Transfer

```bash
# Receiver
nc -l 1234 > received_file

# Sender
nc host 1234 < file_to_send
```

### HTTP Request

```bash
echo -e "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n" | nc example.com 80
```

## Network Diagnostics

### ping

Test connectivity:

```bash
ping google.com                   # Continuous ping
ping -c 4 google.com              # 4 pings only
ping -i 0.5 google.com            # 0.5s interval
```

### traceroute / tracepath

Show route to host:

```bash
traceroute google.com             # macOS/BSD
tracepath google.com              # Linux
mtr google.com                    # Combined ping + traceroute
```

### dig / nslookup

DNS lookups:

```bash
dig example.com                   # DNS query
dig +short example.com            # IP only
dig MX example.com                # Mail records
dig @8.8.8.8 example.com          # Use specific DNS server
nslookup example.com              # Alternative tool
host example.com                  # Simple lookup
```

### Network Statistics

```bash
# Open connections
netstat -an                       # All connections
netstat -tuln                     # Listening ports (Linux)
lsof -i :80                       # Who's using port 80
ss -tuln                          # Linux socket stats (faster)

# Interface info
ifconfig                          # macOS/BSD
ip addr                           # Linux
```

### Check External IP

```bash
curl -s ifconfig.me
curl -s icanhazip.com
curl -s ipinfo.io/ip
```

### Local IP

```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'
```

## Practical Examples

### API Health Check Script

```bash
#!/usr/bin/env bash
check_api() {
    local url="$1"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [[ "$status" == "200" ]]; then
        echo "OK: $url"
        return 0
    else
        echo "FAIL: $url (status: $status)"
        return 1
    fi
}

check_api "https://api.example.com/health"
```

### Download with Progress

```bash
curl -L -# -o file.zip "https://example.com/file.zip"
```

### Parallel Downloads

```bash
urls=(
    "https://example.com/file1.zip"
    "https://example.com/file2.zip"
    "https://example.com/file3.zip"
)

for url in "${urls[@]}"; do
    curl -LO "$url" &
done
wait
```

### Test Port Connectivity

```bash
test_port() {
    local host="$1"
    local port="$2"
    nc -zv -w 5 "$host" "$port" 2>&1 | grep -q succeeded
}

if test_port google.com 443; then
    echo "Port is open"
else
    echo "Port is closed"
fi
```

### Wait for Service

```bash
wait_for_service() {
    local host="$1"
    local port="$2"
    local max_attempts="${3:-30}"

    echo "Waiting for $host:$port..."
    for ((i=1; i<=max_attempts; i++)); do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "Service is up!"
            return 0
        fi
        sleep 1
    done
    echo "Timeout waiting for service"
    return 1
}

wait_for_service localhost 8080
```

### Webhook Trigger

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"event":"deploy","version":"1.0.0"}' \
  https://hooks.example.com/trigger
```

## Try It

1. Basic curl:
   ```bash
   curl -s https://httpbin.org/get | jq '.headers'
   ```

2. POST request:
   ```bash
   curl -s -X POST -d "name=test" https://httpbin.org/post | jq '.form'
   ```

3. Check port:
   ```bash
   nc -zv google.com 443
   ```

4. DNS lookup:
   ```bash
   dig +short google.com
   ```

## Summary

| Task | Command |
|------|---------|
| HTTP GET | `curl URL` |
| HTTP POST | `curl -X POST -d "data" URL` |
| POST JSON | `curl -H "Content-Type: application/json" -d '{}' URL` |
| Download file | `curl -O URL` or `wget URL` |
| Follow redirects | `curl -L URL` |
| Headers only | `curl -I URL` |
| SSH connect | `ssh user@host` |
| Copy file | `scp file user@host:/path/` |
| Check port | `nc -zv host port` |
| DNS lookup | `dig domain` |
| Ping | `ping -c 4 host` |
| Route trace | `traceroute host` |
| Local ports | `netstat -tuln` or `ss -tuln` |

Key curl flags:

| Flag | Purpose |
|------|---------|
| `-o` | Output to file |
| `-O` | Save with original name |
| `-L` | Follow redirects |
| `-s` | Silent |
| `-v` | Verbose |
| `-I` | Headers only |
| `-X` | HTTP method |
| `-H` | Add header |
| `-d` | POST data |
| `-u` | Basic auth |
| `-k` | Ignore SSL (insecure) |
