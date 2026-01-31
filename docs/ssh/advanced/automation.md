# SSH Automation

## Non-Interactive SSH

### BatchMode

Disable all prompts for scripting:

```bash
ssh -o BatchMode=yes user@host command
```

Fails immediately if:
- Password required
- Host key verification needed
- Any prompt required

### StrictHostKeyChecking Options

```bash
# Prompt (default)
StrictHostKeyChecking ask

# Accept new, reject changed
StrictHostKeyChecking accept-new

# Skip verification (dangerous)
StrictHostKeyChecking no
```

### Recommended for Scripts

```bash
ssh -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=accept-new \
    user@host command
```

## SSH Config for Automation

```bash
# ~/.ssh/config
Host auto-*
    BatchMode yes
    StrictHostKeyChecking accept-new
    ConnectTimeout 10
    ServerAliveInterval 60
    IdentitiesOnly yes

Host auto-web
    HostName web.example.com
    User deploy
    IdentityFile ~/.ssh/deploy_key

Host auto-db
    HostName db.example.com
    User backup
    IdentityFile ~/.ssh/backup_key
```

## Running Remote Commands

### Single Command

```bash
ssh user@host "ls -la /var/log"
```

### Multiple Commands

```bash
ssh user@host "cd /var/log && tail -100 syslog && df -h"
```

### Here Document

```bash
ssh user@host << 'EOF'
cd /var/log
tail -100 syslog
df -h
free -m
EOF
```

### Script File

```bash
ssh user@host "bash -s" < local_script.sh
```

### With Arguments

```bash
ssh user@host "bash -s" < script.sh arg1 arg2
# or
ssh user@host "bash -s -- arg1 arg2" < script.sh
```

## Exit Codes

SSH returns the remote command's exit code:

```bash
ssh user@host "grep pattern /var/log/syslog"
if [ $? -eq 0 ]; then
    echo "Pattern found"
else
    echo "Pattern not found"
fi
```

### Common Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 255 | SSH error (connection failed) |

## Handling Output

### Capture Output

```bash
output=$(ssh user@host "cat /etc/hostname")
echo "Hostname: $output"
```

### Separate stdout and stderr

```bash
ssh user@host "command" > stdout.txt 2> stderr.txt
```

### Streaming

```bash
ssh user@host "tail -f /var/log/syslog" | grep --line-buffered "error"
```

## Parallel Execution

### GNU Parallel

```bash
parallel ssh {} "uptime" ::: server1 server2 server3
```

### Background Jobs

```bash
for host in server1 server2 server3; do
    ssh $host "apt update && apt upgrade -y" &
done
wait
echo "All updates complete"
```

### xargs

```bash
echo "server1 server2 server3" | xargs -n1 -P3 -I{} ssh {} "uptime"
```

## Key-Based Automation

### Dedicated Automation Key

```bash
# Generate key (no passphrase for automation)
ssh-keygen -t ed25519 -f ~/.ssh/automation_key -N ""

# Or with comment
ssh-keygen -t ed25519 -f ~/.ssh/automation_key -N "" -C "automation@hostname"
```

### Restricted Authorized Keys

On the server, restrict what the key can do:

```bash
# ~/.ssh/authorized_keys
command="/usr/local/bin/backup.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAAC3... automation-backup

restrict,command="/usr/local/bin/deploy.sh" ssh-ed25519 AAAAC3... automation-deploy
```

### Restrict by Source IP

```bash
from="192.168.1.100",command="/usr/local/bin/backup.sh" ssh-ed25519 AAAAC3... automation-backup
```

## Scripting Patterns

### Health Check

```bash
#!/bin/bash
HOSTS="server1 server2 server3"

for host in $HOSTS; do
    if ssh -o BatchMode=yes -o ConnectTimeout=5 $host "true" 2>/dev/null; then
        echo "$host: OK"
    else
        echo "$host: FAILED"
    fi
done
```

### Collect Information

```bash
#!/bin/bash
for host in server1 server2 server3; do
    echo "=== $host ==="
    ssh $host "hostname; uptime; df -h /"
done
```

### Deploy Script

```bash
#!/bin/bash
set -e

SERVERS="web1 web2 web3"
DEPLOY_DIR="/var/www/app"

for server in $SERVERS; do
    echo "Deploying to $server..."
    rsync -avz --delete ./dist/ $server:$DEPLOY_DIR/
    ssh $server "systemctl restart app"
done

echo "Deployment complete"
```

### Parallel with Feedback

```bash
#!/bin/bash
SERVERS="server1 server2 server3"

for server in $SERVERS; do
    (
        echo "Starting $server..."
        ssh $server "apt update && apt upgrade -y"
        echo "Finished $server"
    ) &
done

wait
echo "All servers updated"
```

## Error Handling

### Trap Errors

```bash
#!/bin/bash
set -e
trap 'echo "Error on line $LINENO"' ERR

ssh server1 "command1"
ssh server2 "command2"
ssh server3 "command3"
```

### Check Each Command

```bash
#!/bin/bash
ssh server1 "command1" || { echo "Failed on server1"; exit 1; }
ssh server2 "command2" || { echo "Failed on server2"; exit 1; }
```

### Continue on Error

```bash
#!/bin/bash
for host in server1 server2 server3; do
    if ! ssh $host "command"; then
        echo "Warning: $host failed" >&2
    fi
done
```

## Ansible Alternative

For complex automation, consider Ansible:

```yaml
# playbook.yml
- hosts: webservers
  tasks:
    - name: Update packages
      apt:
        update_cache: yes
        upgrade: yes

    - name: Restart service
      service:
        name: nginx
        state: restarted
```

```bash
ansible-playbook -i inventory playbook.yml
```

## Cron Jobs

### Simple Backup

```bash
# /etc/cron.d/backup
0 2 * * * backupuser ssh -i /home/backupuser/.ssh/backup_key -o BatchMode=yes backup@remote "pg_dump mydb" > /backups/db.sql
```

### With Logging

```bash
#!/bin/bash
# /usr/local/bin/daily-backup.sh
LOG="/var/log/backup.log"
exec >> $LOG 2>&1

echo "=== Backup started $(date) ==="
ssh backup@server "tar czf - /data" > /backups/data-$(date +%Y%m%d).tar.gz
echo "=== Backup finished $(date) ==="
```

```bash
# crontab
0 3 * * * /usr/local/bin/daily-backup.sh
```

## SSH in CI/CD

### GitHub Actions

```yaml
- name: Deploy
  env:
    SSH_PRIVATE_KEY: ${{ secrets.SSH_KEY }}
  run: |
    mkdir -p ~/.ssh
    echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_ed25519
    chmod 600 ~/.ssh/id_ed25519
    ssh-keyscan server.example.com >> ~/.ssh/known_hosts
    rsync -avz ./dist/ deploy@server.example.com:/var/www/app/
```

### GitLab CI

```yaml
deploy:
  script:
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | ssh-add -
    - mkdir -p ~/.ssh
    - ssh-keyscan server.example.com >> ~/.ssh/known_hosts
    - rsync -avz ./dist/ deploy@server.example.com:/var/www/app/
```

## Security Best Practices

1. **Use dedicated keys** for automation
2. **Restrict keys** with command= and from=
3. **No passphrase** only when necessary, protect key file
4. **Minimal permissions** for automation users
5. **Audit logs** review automated access
6. **Rotate keys** periodically
7. **Use secrets management** in CI/CD
