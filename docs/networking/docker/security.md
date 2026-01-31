# Docker Network Security

## Security Principles

### Defense in Depth

Multiple layers of protection:

1. **Host firewall** (UFW/iptables)
2. **Docker network isolation**
3. **Container-level restrictions**
4. **Application-level security**

### Least Privilege

- Only expose necessary ports
- Use internal networks for backend services
- Restrict network access between services

## Hardening Docker Networking

### Disable ICC (Inter-Container Communication)

By default, containers on the same bridge can communicate:

```json
// /etc/docker/daemon.json
{
  "icc": false
}
```

Now containers must use links or user-defined networks to communicate.

### Disable IP Forwarding When Not Needed

```json
// /etc/docker/daemon.json
{
  "ip-forward": false
}
```

Only use when containers don't need internet access.

### Restrict Container Capabilities

```yaml
services:
  web:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only for ports < 1024
```

### Network Options

```yaml
services:
  web:
    sysctls:
      - net.ipv4.ip_unprivileged_port_start=0
    security_opt:
      - no-new-privileges:true
```

## Network Segmentation

### Strict Segmentation

```yaml
services:
  # DMZ - Internet facing
  nginx:
    networks:
      - dmz
    ports:
      - "80:80"

  # Application tier
  app:
    networks:
      - dmz      # Can receive from nginx
      - backend  # Can access backend

  # Data tier - No external access
  db:
    networks:
      - backend

networks:
  dmz:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

### Service Mesh Approach

```yaml
services:
  # Sidecar proxies control all traffic
  app:
    networks:
      - service-mesh
    depends_on:
      - envoy

  envoy:
    image: envoyproxy/envoy
    networks:
      - service-mesh
    # Envoy controls what app can access
```

## Firewall Strategies

### DOCKER-USER Hardening

```bash
#!/bin/bash
# /usr/local/bin/docker-security.sh

# Clear DOCKER-USER
iptables -F DOCKER-USER

# Default deny from external
iptables -A DOCKER-USER -i eth0 -j DROP

# Allow established
iptables -I DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN

# Allow local networks
iptables -I DOCKER-USER -s 10.0.0.0/8 -j RETURN
iptables -I DOCKER-USER -s 172.16.0.0/12 -j RETURN
iptables -I DOCKER-USER -s 192.168.0.0/16 -j RETURN

# Whitelist specific services
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -j RETURN
iptables -I DOCKER-USER -i eth0 -p tcp --dport 443 -j RETURN

# Log denied
iptables -I DOCKER-USER -i eth0 -j LOG --log-prefix "[DOCKER-DENY] "
```

### Rate Limiting

```bash
# Rate limit connections to containers
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -m connlimit --connlimit-above 50 -j DROP
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -m hashlimit --hashlimit-above 100/sec --hashlimit-mode srcip --hashlimit-name http -j DROP
```

### Geo-Blocking

```bash
# With xtables-addons geoip
iptables -I DOCKER-USER -i eth0 -m geoip --src-cc CN,RU,KP -j DROP
```

## Container-to-Container Security

### User-Defined Networks Only

```json
// /etc/docker/daemon.json
{
  "bridge": "none",
  "default-address-pools": []
}
```

Force explicit network creation:

```bash
docker network create mynet
docker run --network mynet myimage
```

### Network Policies (Kubernetes-style)

For Docker, use Calico or Weave with policies:

```yaml
# Calico network policy example
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
spec:
  selector: app == 'api'
  ingress:
    - action: Allow
      source:
        selector: app == 'web'
  egress:
    - action: Deny
```

## Secrets Management

### Don't Expose via Environment

```yaml
# BAD
services:
  db:
    environment:
      - POSTGRES_PASSWORD=secret123  # Visible in docker inspect
```

### Use Docker Secrets

```yaml
# GOOD
services:
  db:
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### External Secret Stores

```yaml
services:
  app:
    environment:
      - VAULT_ADDR=http://vault:8200
    # App retrieves secrets from Vault
```

## TLS Between Containers

### mTLS with Traefik

```yaml
services:
  traefik:
    command:
      - "--providers.docker=true"
      - "--serversTransport.insecureSkipVerify=false"

  app:
    labels:
      - "traefik.http.services.app.loadbalancer.server.scheme=https"
```

### Service Mesh (Linkerd/Istio)

Automatic mTLS between services:

```yaml
services:
  app:
    labels:
      - "linkerd.io/inject=enabled"
```

## Logging and Monitoring

### Log Container Traffic

```bash
# Log all Docker forwarded traffic
iptables -I DOCKER-USER -j LOG --log-prefix "[DOCKER] "
```

### Monitor with Falco

```yaml
services:
  falco:
    image: falcosecurity/falco
    privileged: true
    volumes:
      - /var/run/docker.sock:/host/var/run/docker.sock
      - /dev:/host/dev
      - /proc:/host/proc:ro
```

### Network Traffic Analysis

```yaml
services:
  tcpdump:
    image: nicolaka/netshoot
    network_mode: "container:target-container"
    command: tcpdump -i any -w /data/capture.pcap
    volumes:
      - ./captures:/data
```

## Vulnerability Scanning

### Scan Images

```bash
# Using Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image myimage:latest
```

### Scan Running Containers

```bash
# Network vulnerability scan
docker run --rm -it --network container:target \
    instrumentisto/nmap -sV -p- localhost
```

## Incident Response

### Isolate Compromised Container

```bash
# Disconnect from all networks
docker network disconnect bridge compromised-container
docker network disconnect mynet compromised-container

# Or stop it
docker stop compromised-container
```

### Capture Evidence

```bash
# Save container state
docker export compromised-container > container-export.tar

# Save logs
docker logs compromised-container > container-logs.txt

# Save network connections
docker exec compromised-container netstat -an > connections.txt
```

### Block Attacker IP

```bash
# Immediate block
iptables -I DOCKER-USER 1 -s attacker.ip.address -j DROP
```

## Security Checklist

### Container Configuration

- [ ] Use non-root user in containers
- [ ] Drop all capabilities, add only needed
- [ ] Read-only root filesystem where possible
- [ ] No privileged mode unless absolutely necessary
- [ ] Resource limits set

### Network Configuration

- [ ] Internal networks for backend services
- [ ] Localhost binding for development ports
- [ ] DOCKER-USER rules for external access
- [ ] No unnecessary port publishing
- [ ] TLS for sensitive traffic

### Host Configuration

- [ ] Docker socket not exposed to containers
- [ ] UFW/iptables properly configured
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Network monitoring in place
