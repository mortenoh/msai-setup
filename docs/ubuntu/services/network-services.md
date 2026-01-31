# Network Services Hardening

Network-facing services require special attention as they're directly exposed to potential attackers. This page covers hardening common network services on Ubuntu.

## General Principles

### Network Service Security

| Principle | Implementation |
|-----------|----------------|
| Minimize exposure | Bind to specific IPs, not 0.0.0.0 |
| Least privilege | Run as non-root user |
| Strong authentication | Require auth, use strong creds |
| Encryption | TLS for all sensitive data |
| Rate limiting | Prevent abuse and DoS |
| Logging | Comprehensive audit trail |

### Common Checklist

- [ ] Runs as non-root user
- [ ] Binds to specific interfaces only
- [ ] Uses TLS/encryption
- [ ] Has rate limiting
- [ ] Logs access and errors
- [ ] Has firewall rules
- [ ] Has fail2ban protection

## SSH (Covered Separately)

SSH hardening is covered in detail in [SSH Hardening](../security/ssh-hardening.md).

Key points:

- Key-only authentication
- Disable root login
- Use strong ciphers
- Enable fail2ban

## Web Servers

### Nginx Hardening

Create `/etc/nginx/conf.d/security.conf`:

```nginx
# Hide version
server_tokens off;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;

# SSL settings
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# Limit request size
client_max_body_size 10m;
client_body_buffer_size 128k;

# Timeouts
client_body_timeout 10;
client_header_timeout 10;
keepalive_timeout 65;
send_timeout 10;

# Rate limiting
limit_req_zone $binary_remote_addr zone=perip:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=perip_conn:10m;
```

Apply rate limiting per location:

```nginx
server {
    location /login {
        limit_req zone=perip burst=5 nodelay;
        limit_conn perip_conn 10;
        # ... rest of config
    }
}
```

### systemd Hardening for Nginx

```bash
sudo systemctl edit nginx.service
```

```ini
[Service]
ProtectSystem=full
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
NoNewPrivileges=yes
ProtectKernelModules=yes
ProtectKernelTunables=yes
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_DAC_OVERRIDE
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

### Apache Hardening

Edit `/etc/apache2/conf-enabled/security.conf`:

```apache
# Hide version
ServerTokens Prod
ServerSignature Off

# Disable directory listing
<Directory />
    Options -Indexes
    AllowOverride None
    Require all denied
</Directory>

# Limit request body
LimitRequestBody 10485760

# Disable unnecessary modules
# Run: a2dismod status autoindex
```

Enable required modules:

```bash
sudo a2enmod headers ssl rewrite
sudo a2dismod status autoindex
```

Security headers:

```apache
<IfModule mod_headers.c>
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
```

## Database Servers

### MySQL/MariaDB Hardening

Run the security script:

```bash
sudo mysql_secure_installation
```

Manual hardening in `/etc/mysql/mysql.conf.d/mysqld.cnf`:

```ini
[mysqld]
# Bind to localhost only (unless remote needed)
bind-address = 127.0.0.1

# Disable local infile (file read vulnerability)
local_infile = 0

# Disable symbolic links
symbolic-links = 0

# Log queries for audit
general_log = 1
general_log_file = /var/log/mysql/mysql.log

# Slow query log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
```

User management:

```sql
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Remove remote root
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- Require SSL for remote connections
ALTER USER 'appuser'@'%' REQUIRE SSL;

-- Grant minimum privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON appdb.* TO 'appuser'@'localhost';
```

### PostgreSQL Hardening

Edit `/etc/postgresql/16/main/postgresql.conf`:

```ini
# Listen only on localhost (or specific IPs)
listen_addresses = 'localhost'

# Log connections
log_connections = on
log_disconnections = on
log_statement = 'ddl'

# SSL
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

Edit `/etc/postgresql/16/main/pg_hba.conf`:

```
# TYPE  DATABASE  USER  ADDRESS       METHOD
local   all       all                 peer
host    all       all   127.0.0.1/32  scram-sha-256
host    all       all   ::1/128       scram-sha-256

# Require SSL for remote connections
hostssl appdb     appuser 192.168.1.0/24 scram-sha-256
```

## Mail Servers

### Postfix Hardening

Edit `/etc/postfix/main.cf`:

```ini
# Restrict to localhost (for app mail only)
inet_interfaces = loopback-only

# Or specific interface for receiving
inet_interfaces = 192.168.1.100

# Disable VRFY
disable_vrfy_command = yes

# HELO restrictions
smtpd_helo_required = yes
smtpd_helo_restrictions =
    permit_mynetworks,
    reject_invalid_helo_hostname,
    reject_non_fqdn_helo_hostname

# Recipient restrictions
smtpd_recipient_restrictions =
    permit_mynetworks,
    reject_unauth_destination,
    reject_unknown_recipient_domain

# TLS
smtpd_tls_security_level = may
smtpd_tls_cert_file = /etc/ssl/certs/postfix.pem
smtpd_tls_key_file = /etc/ssl/private/postfix.key
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1

# Rate limiting
smtpd_client_connection_rate_limit = 10
smtpd_client_message_rate_limit = 100
```

## DNS Servers

### BIND Hardening

Edit `/etc/bind/named.conf.options`:

```
options {
    directory "/var/cache/bind";

    // Disable zone transfers except to secondaries
    allow-transfer { none; };

    // Limit recursion
    recursion yes;
    allow-recursion { localhost; 192.168.1.0/24; };

    // Disable version exposure
    version "not disclosed";

    // Enable response rate limiting (against DNS amplification)
    rate-limit {
        responses-per-second 5;
        window 5;
    };

    // DNSSEC validation
    dnssec-validation auto;

    // Minimize queries
    minimal-responses yes;

    // Listen on specific interface
    listen-on { 127.0.0.1; 192.168.1.100; };
    listen-on-v6 { none; };
};
```

## Redis

### Redis Hardening

Edit `/etc/redis/redis.conf`:

```ini
# Bind to localhost only
bind 127.0.0.1 ::1

# Set password
requirepass YOUR_STRONG_PASSWORD

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""
rename-command SHUTDOWN SHUTDOWN_SECURE

# Protected mode
protected-mode yes

# Limit clients
maxclients 100

# TLS (Redis 6+)
tls-port 6379
port 0
tls-cert-file /etc/redis/redis.crt
tls-key-file /etc/redis/redis.key
tls-ca-cert-file /etc/redis/ca.crt
```

## Docker Daemon

### Docker Socket Security

```bash
# Don't expose Docker socket to network
# Remove any DOCKER_HOST TCP settings

# Limit socket access to docker group
sudo chmod 660 /var/run/docker.sock
sudo chown root:docker /var/run/docker.sock
```

### Enable TLS for Remote

If remote Docker access needed, use TLS:

```bash
# Create daemon.json
sudo nano /etc/docker/daemon.json
```

```json
{
    "tls": true,
    "tlsverify": true,
    "tlscacert": "/etc/docker/ca.pem",
    "tlscert": "/etc/docker/server-cert.pem",
    "tlskey": "/etc/docker/server-key.pem",
    "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"]
}
```

## Firewall Rules

### Per-Service UFW Rules

```bash
# SSH (from specific network)
sudo ufw allow from 192.168.1.0/24 to any port 22

# Web (public)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Database (internal only)
sudo ufw allow from 192.168.1.0/24 to any port 5432

# Redis (localhost only - usually no rule needed)
# Default deny handles this
```

## Fail2ban Rules

### Multiple Services

```ini
# /etc/fail2ban/jail.local

[sshd]
enabled = true
maxretry = 3
bantime = 1h

[nginx-http-auth]
enabled = true
maxretry = 3
bantime = 1h

[nginx-botsearch]
enabled = true
maxretry = 2
bantime = 1d

[postfix]
enabled = true
maxretry = 3
bantime = 1h

[mysqld-auth]
enabled = true
maxretry = 3
bantime = 1h
```

## Monitoring Network Services

### Check Listening Services

```bash
# Regular monitoring script
#!/bin/bash
echo "=== Listening Services ==="
sudo ss -tlnp | grep LISTEN

echo -e "\n=== Unexpected Listeners ==="
# Alert if unexpected ports
sudo ss -tlnp | grep -vE ":(22|80|443|5432) " | grep LISTEN
```

### Log Analysis

```bash
# Watch for auth failures
sudo tail -f /var/log/auth.log | grep -i failed

# Web server errors
sudo tail -f /var/log/nginx/error.log

# Database connections
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

## Quick Reference

### Security Headers

| Header | Purpose |
|--------|---------|
| X-Frame-Options | Prevent clickjacking |
| X-Content-Type-Options | Prevent MIME sniffing |
| X-XSS-Protection | XSS filter (legacy) |
| Content-Security-Policy | Resource loading policy |
| Strict-Transport-Security | Force HTTPS |

### TLS Best Practices

| Setting | Recommendation |
|---------|----------------|
| Protocols | TLSv1.2, TLSv1.3 only |
| Ciphers | AEAD ciphers (GCM, ChaCha20) |
| Key size | RSA 2048+, ECDSA 256+ |
| HSTS | Enable with long max-age |

### Binding Best Practices

| Scenario | Bind To |
|----------|---------|
| Public web server | 0.0.0.0:80, 0.0.0.0:443 |
| Internal database | 127.0.0.1 or internal IP |
| Local-only service | 127.0.0.1 |
| Docker internal | Docker network IP |

## Next Steps

With services hardened, proceed to [Troubleshooting](../troubleshooting/index.md) for problem resolution guidance.
