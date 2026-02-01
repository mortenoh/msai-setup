# SSL/TLS Certificates

Understanding and managing HTTPS certificates for your homelab services.

## Certificate Types Overview

| Type | Use Case | Validity | Effort |
|------|----------|----------|--------|
| **Let's Encrypt** | Public services | 90 days (auto-renew) | Low |
| **Self-Signed** | Internal/testing | Custom | Low |
| **Internal CA** | Multiple internal services | Custom | Medium |
| **Purchased** | Commercial/compliance | 1-2 years | Low |

## Let's Encrypt (Recommended)

Free, automated certificates for public-facing services.

### How It Works

```
Your Server              Let's Encrypt
    │                         │
    │  1. Request cert for    │
    │     example.com         │
    │ ─────────────────────>  │
    │                         │
    │  2. Prove domain        │
    │     ownership           │
    │  <─────────────────────>│
    │                         │
    │  3. Receive signed      │
    │     certificate         │
    │ <─────────────────────  │
```

### Challenge Types

| Challenge | Requirements | Best For |
|-----------|--------------|----------|
| HTTP-01 | Port 80 accessible | Single server, public IP |
| DNS-01 | DNS API access | Wildcards, internal servers |
| TLS-ALPN-01 | Port 443 accessible | Port 80 blocked |

### Traefik (Automatic)

Traefik handles Let's Encrypt automatically.

```yaml
# traefik.yml
certificatesResolvers:
  letsencrypt:
    acme:
      email: you@example.com
      storage: acme.json
      httpChallenge:
        entryPoint: http
```

```yaml
# Service labels
labels:
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

### Caddy (Automatic)

Caddy handles HTTPS by default.

```
# Caddyfile
example.com {
    reverse_proxy localhost:8080
}
```

Caddy automatically:
- Obtains Let's Encrypt certificate
- Redirects HTTP to HTTPS
- Renews before expiration

### Certbot (Manual/Standalone)

For services not behind Traefik/Caddy.

```bash
# Install
sudo apt install certbot

# HTTP challenge (port 80 must be free)
sudo certbot certonly --standalone -d example.com

# Webroot (existing web server)
sudo certbot certonly --webroot -w /var/www/html -d example.com

# DNS challenge (for wildcards)
sudo certbot certonly --manual --preferred-challenges dns -d "*.example.com"
```

Certificates are stored in:
```
/etc/letsencrypt/live/example.com/
  ├── fullchain.pem   # Certificate + intermediates
  ├── privkey.pem     # Private key
  ├── cert.pem        # Certificate only
  └── chain.pem       # Intermediate certificates
```

### Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Renewal runs automatically via systemd timer
systemctl list-timers | grep certbot
```

### DNS Challenge with Cloudflare

For wildcards or servers without public access.

```bash
# Install Cloudflare plugin
sudo apt install python3-certbot-dns-cloudflare

# Create credentials file
cat > ~/.secrets/cloudflare.ini << EOF
dns_cloudflare_api_token = your-api-token
EOF
chmod 600 ~/.secrets/cloudflare.ini

# Get wildcard certificate
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d "*.example.com" \
  -d "example.com"
```

## Self-Signed Certificates

For internal services, testing, or when Let's Encrypt isn't viable.

### Quick Self-Signed Cert

```bash
# Generate in one command
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key \
  -out server.crt \
  -subj "/CN=myservice.local"

# With SANs (Subject Alternative Names)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key \
  -out server.crt \
  -subj "/CN=myservice.local" \
  -addext "subjectAltName=DNS:myservice.local,DNS:localhost,IP:192.168.1.100"
```

### Using Self-Signed Certs

```yaml
# Traefik with self-signed cert
# config/certs.yml
tls:
  certificates:
    - certFile: /certs/server.crt
      keyFile: /certs/server.key
```

```yaml
# docker-compose.yml
services:
  myapp:
    labels:
      - "traefik.http.routers.myapp.tls=true"
    # No certresolver = uses default certificate
```

### Trusting Self-Signed Certs

Clients must trust the certificate to avoid warnings.

**Linux:**
```bash
# Copy cert
sudo cp server.crt /usr/local/share/ca-certificates/myservice.crt

# Update trust store
sudo update-ca-certificates
```

**macOS:**
```bash
# Add to keychain
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain server.crt
```

**Windows:**
```powershell
# Import as admin
Import-Certificate -FilePath server.crt -CertStoreLocation Cert:\LocalMachine\Root
```

**Browser-specific:**
Most browsers have their own trust stores. You may need to add the certificate manually in browser settings.

## Internal Certificate Authority

For multiple internal services, create your own CA.

### Create Root CA

```bash
# Create directory structure
mkdir -p ~/ca/{certs,private,newcerts}
cd ~/ca
touch index.txt
echo 1000 > serial

# Generate CA private key
openssl genrsa -aes256 -out private/ca.key 4096
chmod 400 private/ca.key

# Generate CA certificate (10 years)
openssl req -new -x509 -days 3650 \
  -key private/ca.key \
  -out certs/ca.crt \
  -subj "/CN=Homelab CA/O=Homelab/C=NO"
```

### Sign Server Certificates

```bash
# Generate server key
openssl genrsa -out server.key 2048

# Create CSR (Certificate Signing Request)
openssl req -new -key server.key -out server.csr \
  -subj "/CN=myservice.local"

# Create extensions file for SANs
cat > server.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = myservice.local
DNS.2 = myservice
IP.1 = 192.168.1.100
EOF

# Sign with CA
openssl x509 -req -days 365 \
  -in server.csr \
  -CA ~/ca/certs/ca.crt \
  -CAkey ~/ca/private/ca.key \
  -CAcreateserial \
  -out server.crt \
  -extfile server.ext
```

### Deploy CA Certificate

Install the CA certificate (not individual certs) on all clients:

```bash
# On each client
sudo cp ca.crt /usr/local/share/ca-certificates/homelab-ca.crt
sudo update-ca-certificates
```

Now all certificates signed by your CA are trusted.

## Certificate Formats

### Common Formats

| Format | Extension | Contains | Use |
|--------|-----------|----------|-----|
| PEM | .pem, .crt | Base64 text | Most Linux/Apache |
| DER | .der, .cer | Binary | Windows/Java |
| PKCS#12 | .p12, .pfx | Cert + key | Windows/browsers |

### Converting Formats

```bash
# PEM to DER
openssl x509 -outform der -in cert.pem -out cert.der

# DER to PEM
openssl x509 -inform der -in cert.der -out cert.pem

# PEM to PKCS#12
openssl pkcs12 -export -out cert.pfx -inkey key.pem -in cert.pem

# PKCS#12 to PEM
openssl pkcs12 -in cert.pfx -out cert.pem -nodes
```

## Troubleshooting

### Certificate Not Trusted

```bash
# View certificate details
openssl x509 -in cert.crt -text -noout

# Check certificate chain
openssl s_client -connect example.com:443 -showcerts

# Verify against CA
openssl verify -CAfile ca.crt server.crt
```

### Let's Encrypt Failures

```bash
# Check renewal status
sudo certbot certificates

# Debug HTTP challenge
curl http://example.com/.well-known/acme-challenge/test

# Check rate limits
# https://letsencrypt.org/docs/rate-limits/
```

**Common issues:**

1. **Port 80 blocked** - Firewall or ISP blocking
2. **DNS not resolving** - Check A record
3. **Rate limited** - Wait 1 hour, use staging for testing
4. **CAA record** - Ensure CAA allows letsencrypt.org

### Certificate Expired

```bash
# Check expiration
openssl x509 -enddate -noout -in cert.crt

# Check remote certificate expiration
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -enddate

# Force renewal
sudo certbot renew --force-renewal
```

### Browser Still Shows Warning

1. Clear browser cache
2. Check certificate includes correct SANs
3. Verify full chain is served (not just leaf cert)
4. Ensure system time is correct

```bash
# Check what certificate is served
openssl s_client -connect localhost:443 -servername example.com
```

## Certificate Monitoring

### Check Expiration with Script

```bash
#!/bin/bash
# check-certs.sh
DOMAINS="example.com api.example.com"
DAYS_WARNING=30

for domain in $DOMAINS; do
    expiry=$(echo | openssl s_client -connect ${domain}:443 2>/dev/null | \
             openssl x509 -noout -enddate | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry" +%s)
    now_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

    if [ $days_left -lt $DAYS_WARNING ]; then
        echo "WARNING: $domain expires in $days_left days"
    fi
done
```

### Uptime Kuma

Configure certificate monitoring in Uptime Kuma:

1. Add new monitor
2. Type: TCP/Keyword
3. Enable certificate expiry check
4. Set warning threshold (e.g., 14 days)

## Best Practices

### Security

- Use 2048-bit RSA minimum (4096 for CA)
- Protect private keys (chmod 600)
- Use strong key passphrases for CA
- Rotate certificates before expiration
- Keep separate keys for different services

### Automation

- Use Traefik/Caddy for automatic cert management
- Set up monitoring for expiration
- Test renewal regularly
- Have fallback plan for outages

### Organization

```
/etc/ssl/homelab/
  ├── ca/
  │   ├── ca.crt
  │   └── ca.key (600)
  ├── services/
  │   ├── traefik/
  │   │   ├── cert.crt
  │   │   └── cert.key
  │   └── nginx/
  │       ├── cert.crt
  │       └── cert.key
  └── README.md
```

## See Also

- [Traefik Setup](../reverse-proxy/traefik.md)
- [Caddy Setup](../reverse-proxy/caddy.md)
- [External Access](../../networking/external-access/index.md)
- [Tailscale Funnel](../../tailscale/features/funnel-serve.md)
