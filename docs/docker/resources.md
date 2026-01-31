# Container Resource Limits

Docker containers run without resource limits by default, meaning they can consume all available CPU, memory, and I/O. For a multi-workload server, proper resource constraints prevent any single container from starving others.

## Memory Limits

### Compose Configuration

```yaml
services:
  myapp:
    image: myapp:latest
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

For Compose V2 (non-swarm mode), use the top-level `mem_limit`:

```yaml
services:
  myapp:
    image: myapp:latest
    mem_limit: 2g
    memswap_limit: 2g    # Same as mem_limit = no swap
```

### Memory Settings

| Setting | Purpose |
|---------|---------|
| `mem_limit` | Hard memory limit (container killed if exceeded) |
| `memswap_limit` | Memory + swap limit combined |
| `mem_reservation` | Soft limit (guaranteed minimum) |
| `oom_kill_disable` | Prevent OOM killer (use with caution) |

### Swap Behavior

| mem_limit | memswap_limit | Behavior |
|-----------|---------------|----------|
| 2G | unset | Unlimited swap |
| 2G | 2G | No swap allowed |
| 2G | 4G | 2G memory + 2G swap |
| 2G | -1 | Unlimited swap |

### Memory Examples

```yaml
# Database: fixed memory, no swap
services:
  postgres:
    image: postgres:16
    mem_limit: 4g
    memswap_limit: 4g
    environment:
      - POSTGRES_SHARED_BUFFERS=1GB

# Cache: allow some swap for eviction buffer
  redis:
    image: redis:7
    mem_limit: 1g
    memswap_limit: 1536m    # 512MB swap headroom
```

## CPU Limits

### CPU Settings

| Setting | Purpose |
|---------|---------|
| `cpus` | Number of CPUs (e.g., 2.5 = 2.5 cores) |
| `cpu_shares` | Relative weight (default 1024) |
| `cpuset` | Pin to specific cores |

### Compose Configuration

```yaml
services:
  worker:
    image: worker:latest
    cpus: 2.0              # Max 2 cores
    cpu_shares: 512        # Half priority vs default

  critical:
    image: critical:latest
    cpus: 4.0
    cpu_shares: 2048       # Double priority
    cpuset: "0,1,2,3"      # Pin to cores 0-3
```

### CPU Pinning for Isolation

For latency-sensitive workloads, pin containers to specific cores:

```yaml
services:
  llm-inference:
    image: ollama/ollama
    cpuset: "8-15"         # Cores 8-15 for inference

  background-jobs:
    image: worker:latest
    cpuset: "0-7"          # Cores 0-7 for background work
```

## GPU Access

### Expose GPU to Container

```yaml
services:
  ollama:
    image: ollama/ollama
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
```

For NVIDIA GPUs with nvidia-container-toolkit:

```yaml
services:
  llm:
    image: nvidia/cuda:12.0-base
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Complete Service Examples

### Database Stack

```yaml
services:
  postgres:
    image: postgres:16
    mem_limit: 4g
    memswap_limit: 4g
    cpus: 2.0
    shm_size: 256m
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - /tank/docker/postgres/data:/var/lib/postgresql/data
    secrets:
      - db_password

  redis:
    image: redis:7-alpine
    mem_limit: 512m
    memswap_limit: 512m
    cpus: 0.5
    command: redis-server --maxmemory 400mb --maxmemory-policy allkeys-lru
```

### Web Application

```yaml
services:
  nginx:
    image: nginx:alpine
    mem_limit: 128m
    memswap_limit: 128m
    cpus: 0.5

  app:
    image: myapp:latest
    mem_limit: 1g
    memswap_limit: 1g
    cpus: 2.0
    deploy:
      replicas: 2
```

### LLM Inference

```yaml
services:
  ollama:
    image: ollama/ollama
    mem_limit: 96g          # Reserve for large models
    cpus: 12.0
    cpuset: "4-15"
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
      - render
    volumes:
      - /tank/ai/ollama:/root/.ollama
    environment:
      - OLLAMA_NUM_PARALLEL=2
```

## Daemon-Level Defaults

Set default limits for all containers in `/etc/docker/daemon.json`:

```json
{
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Reload after changes:

```bash
sudo systemctl reload docker
```

## Monitoring Container Resources

### Live Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats mycontainer

# No-stream (snapshot)
docker stats --no-stream
```

Output:

```
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O           BLOCK I/O
a1b2c3d4e5f6   postgres  2.50%     1.2GiB / 4GiB       30.00%    1.2MB / 800KB     50MB / 100MB
```

### Inspect Container Limits

```bash
# View configured limits
docker inspect mycontainer --format '{{.HostConfig.Memory}}'
docker inspect mycontainer --format '{{.HostConfig.NanoCpus}}'

# Detailed resource config
docker inspect mycontainer | jq '.[0].HostConfig | {Memory, MemorySwap, NanoCpus, CpuShares}'
```

### Using ctop

Install for a better interactive view:

```bash
sudo apt install ctop
ctop
```

## Troubleshooting OOM Kills

### Detect OOM Events

```bash
# Check container status
docker inspect mycontainer --format '{{.State.OOMKilled}}'

# System logs
sudo dmesg | grep -i "killed process"
sudo journalctl -k | grep -i oom
```

### Container Exits with Code 137

Exit code 137 = SIGKILL (128 + 9), typically from OOM:

```bash
# Check last exit
docker inspect mycontainer --format '{{.State.ExitCode}}'

# View events
docker events --filter container=mycontainer --since 1h
```

### Prevention

1. **Set appropriate limits**: Monitor actual usage, then set limits 20-30% above typical
2. **Use memory reservations**: Guarantee minimum memory for critical services
3. **Configure application memory**: Tell applications their memory budget (e.g., Java heap, Postgres shared_buffers)
4. **Consider swap**: Allow some swap for non-latency-sensitive workloads

### Application-Level Configuration

Ensure applications respect container limits:

```yaml
services:
  java-app:
    image: openjdk:17
    mem_limit: 2g
    environment:
      # Let JVM auto-detect container limits
      - JAVA_OPTS=-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0

  postgres:
    image: postgres:16
    mem_limit: 4g
    environment:
      # Set shared_buffers to ~25% of limit
      - POSTGRES_SHARED_BUFFERS=1GB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=3GB
```

## Integration with systemd

Docker containers inherit cgroup limits from Docker's slice. To set overall Docker limits:

```bash
# Create override
sudo systemctl edit docker.service
```

```ini
[Service]
MemoryMax=100G
CPUQuota=1200%    # 12 cores
```

See [systemd Resource Management](../ubuntu/system/systemd.md#resource-management) for details on cgroup configuration.

## Next Steps

- [Capacity Planning](../operations/capacity-planning.md) for overall resource strategy
- [Docker Setup](setup.md) for installation and configuration
- [GPU Containers](../ai/containers/gpu-containers.md) for LLM workloads
