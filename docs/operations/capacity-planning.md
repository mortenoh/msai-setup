# Capacity Planning

This guide covers system-wide resource allocation strategy for a multi-workload server running Docker containers, KVM VMs, and LLM inference.

## Resource Budget Overview

### MS-S1 MAX Resources

| Resource | Total | Notes |
|----------|-------|-------|
| CPU | 16 cores / 32 threads | Zen 5 architecture |
| Memory | 128GB DDR5 | Unified CPU/GPU |
| GPU CUs | 40 | RDNA 3.5, shared memory |

### Allocation Strategy

| Workload | Memory | CPU Cores | Priority |
|----------|--------|-----------|----------|
| Host OS & Services | 4-8GB | 2 | High |
| Docker containers | 8-16GB | 4-6 | Medium |
| KVM VMs | 16-32GB | 4-8 | Medium |
| LLM inference | 64-96GB | 8-12 | Low (batch) |
| Headroom | 8-16GB | 2-4 | - |

!!! warning
    Memory totals should not exceed physical RAM. Overcommit leads to swapping and severe performance degradation, especially for LLM workloads.

## Monitoring Current Usage

### System-Wide View

```bash
# Real-time resource usage by cgroup
systemd-cgtop

# Memory breakdown
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree"

# CPU usage
htop
# or
mpstat -P ALL 1
```

### Docker Resources

```bash
# Container resource usage
docker stats --no-stream

# Total Docker memory
docker stats --no-stream --format "{{.MemUsage}}" | \
  awk -F'/' '{sum += $1} END {print sum " total"}'
```

### VM Resources

```bash
# All VM stats
virsh domstats

# Memory usage per VM
virsh list --all | tail -n +3 | awk '{print $2}' | \
  xargs -I{} sh -c 'echo -n "{}: "; virsh dominfo {} 2>/dev/null | grep "Used memory"'

# Interactive monitoring
virt-top
```

### LLM/GPU Resources

```bash
# GPU memory and utilization (ROCm)
rocm-smi

# Ollama model memory
curl -s http://localhost:11434/api/ps | jq '.models[] | {name, size}'

# Check unified memory pressure
cat /sys/class/drm/card0/device/mem_info_vram_used
```

## Warning Thresholds

### Memory Thresholds

| Level | Available Memory | Action |
|-------|------------------|--------|
| Normal | >20% | No action |
| Warning | 10-20% | Review allocations |
| Critical | <10% | Reduce workloads immediately |

### Monitoring Script

```bash
#!/bin/bash
# /usr/local/bin/check-resources.sh

MEM_WARN=20
MEM_CRIT=10

available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
total=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
pct=$((available * 100 / total))

if [ $pct -lt $MEM_CRIT ]; then
    echo "CRITICAL: Only ${pct}% memory available"
    # Add alerting here
elif [ $pct -lt $MEM_WARN ]; then
    echo "WARNING: ${pct}% memory available"
fi
```

### Systemd Timer for Monitoring

```ini
# /etc/systemd/system/resource-check.timer
[Unit]
Description=Check system resources

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
```

## When to Scale

### Add Resources When

- Memory consistently >80% used
- CPU regularly sustained >70%
- Swap usage >0 during normal operations
- LLM inference becomes unusably slow
- VM or container OOM kills occurring

### Optimize First

Before adding resources, check for:

1. **Unused containers/VMs**: Stop what you don't need
2. **Oversized allocations**: Right-size based on actual usage
3. **Memory leaks**: Applications growing unbounded
4. **Duplicate services**: Consolidate where possible

### Optimization Checklist

```bash
# Find idle containers
docker ps --filter "status=running" -q | xargs docker stats --no-stream | \
  awk '$3 < 1 {print $2 " is idle"}'

# VMs not using allocated memory
virsh list --name | while read vm; do
  [ -z "$vm" ] && continue
  alloc=$(virsh dominfo "$vm" | awk '/Max memory/ {print $3}')
  used=$(virsh dommemstat "$vm" 2>/dev/null | awk '/actual/ {print $2}')
  [ -n "$used" ] && echo "$vm: ${used}KB used of ${alloc}KB allocated"
done
```

## Workload-Specific Guidelines

### Docker Containers

See [Docker Resource Limits](../docker/resources.md) for detailed configuration.

Key points:

- Always set `mem_limit` for production containers
- Use `memswap_limit` = `mem_limit` to prevent swap
- Set CPU limits to prevent runaway containers
- Monitor with `docker stats`

### KVM VMs

See [VM Resource Allocation](../virtualization/vm-resources.md) for detailed configuration.

Key points:

- Don't overcommit memory for production VMs
- Use hugepages for VMs >8GB
- Pin CPUs for latency-sensitive workloads
- Use ballooning for flexible Linux VMs

### LLM Inference

See [Memory Management](../ai/performance/memory-management.md) for detailed configuration.

Key points:

- Model size determines minimum memory requirement
- GPU CUs share system memory (no separate VRAM budget)
- Context length affects memory usage significantly
- Quantization trades quality for memory savings

## Resource Contention

### Priority Using Cgroups

Use systemd slices to prioritize workloads:

```bash
# Check current slice hierarchy
systemd-cgls

# Set CPU weight (higher = more priority)
sudo systemctl set-property docker.service CPUWeight=100
sudo systemctl set-property libvirtd.service CPUWeight=200

# Set memory limits on slices
sudo systemctl set-property user.slice MemoryMax=16G
```

### Example Slice Configuration

```ini
# /etc/systemd/system/llm.slice
[Unit]
Description=LLM Inference Slice

[Slice]
CPUWeight=50
MemoryMax=96G
IOWeight=50
```

Assign services to slice:

```ini
# In service unit
[Service]
Slice=llm.slice
```

## Capacity Planning Example

### Scenario: Mixed Workload Server

Running:

- 2 Docker services (Nextcloud, Plex)
- 1 Windows VM (gaming)
- Ollama with 70B model

| Component | Memory | CPU | Notes |
|-----------|--------|-----|-------|
| Host OS | 4GB | 2 | systemd, SSH, monitoring |
| Nextcloud | 2GB | 1 | Docker container |
| Plex | 4GB | 2 | Docker container, transcoding |
| Windows VM | 24GB | 6 | When running |
| Ollama 70B | 80GB | 8 | Q4 quantization |
| **Total** | **114GB** | **19** | OK if not simultaneous |

**Constraint**: Windows VM and 70B model can't run simultaneously.

**Solution**: Use smaller model (32B) when VM is active:

| Scenario | Windows | LLM | Memory Used |
|----------|---------|-----|-------------|
| Gaming | 24GB | 32B (20GB) | 54GB |
| AI Work | Off | 70B (80GB) | 90GB |

## Quick Reference

### Essential Commands

```bash
# System overview
systemd-cgtop
htop
free -h

# Docker
docker stats
docker system df

# VMs
virsh domstats
virt-top

# GPU/LLM
rocm-smi
ollama list
```

### Key Files

| Resource | Configuration |
|----------|---------------|
| systemd limits | `/etc/systemd/system/*.service.d/` |
| Docker limits | `docker-compose.yml` or `/etc/docker/daemon.json` |
| VM limits | `/etc/libvirt/qemu/*.xml` |
| Kernel tuning | `/etc/sysctl.d/` |

## Related Documentation

- [systemd Resource Management](../ubuntu/system/systemd.md#resource-management)
- [Docker Resource Limits](../docker/resources.md)
- [VM Resource Allocation](../virtualization/vm-resources.md)
- [LLM Memory Management](../ai/performance/memory-management.md)
- [GPU Memory Configuration](../ai/gpu/memory-configuration.md)
