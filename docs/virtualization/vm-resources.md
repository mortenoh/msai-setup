# VM Resource Allocation

!!! note "Background — the concepts apply, the libvirt XML doesn't"
    On this build you allocate VM resources through **[Incus](../incus/index.md)**
    config keys, not libvirt XML or `virsh`. The mapping is direct:

    | This page (libvirt) | Incus equivalent |
    |---|---|
    | `<vcpu>` / `virsh setvcpus` | `incus config set <vm> limits.cpu 8` |
    | `<cputune><vcpupin>` (CCX pinning) | `incus config set <vm> limits.cpu.pin '8-15'` |
    | `<memory>` / `virsh setmem` | `incus config set <vm> limits.memory 16GiB` |
    | `<iotune>` disk limits | `incus config device set <vm> root limits.read/write` |
    | `<numatune>` / hugepages | `limits.memory.hugepages` and instance options |

    See [Incus VMs → resource allocation](../incus/vms.md#resource-allocation)
    for the current commands. The **sizing guidance and the Strix Halo CCX
    reasoning** below are still correct and worth reading — they explain
    *what* to allocate and why; just translate the mechanism to `incus`
    config keys rather than hand-writing XML.

Proper resource allocation for a VM ensures stable performance and prevents
host resource exhaustion. The XML and `virsh` examples below are the
under-the-hood form of what Incus configures for you.

## Memory Allocation

### Static Allocation

Set fixed memory in VM XML:

```xml
<memory unit='GiB'>16</memory>
<currentMemory unit='GiB'>16</currentMemory>
```

Or via virsh:

```bash
# Set maximum memory (requires VM shutdown)
virsh setmaxmem myvm 16G --config

# Set current memory
virsh setmem myvm 16G --config
```

### Memory Ballooning

Ballooning allows dynamic memory adjustment. The guest OS releases unused memory back to the host.

Enable in VM XML:

```xml
<memballoon model='virtio'>
  <stats period='10'/>
</memballoon>
```

Adjust at runtime:

```bash
# Reduce to 8GB (guest releases memory)
virsh setmem myvm 8G --live

# Increase to 12GB
virsh setmem myvm 12G --live
```

!!! note
    Ballooning requires guest cooperation. Windows needs the virtio balloon driver; Linux includes it by default.

### Memory Locking

For latency-sensitive VMs, lock memory to prevent swapping:

```xml
<memoryBacking>
  <locked/>
</memoryBacking>
```

Requires `ulimit -l` adjustment for libvirt.

## Hugepages

Hugepages reduce TLB misses for memory-intensive VMs.

### Configure Host Hugepages

```bash
# Check current hugepages
grep Huge /proc/meminfo

# Reserve 16GB of 2MB hugepages (8192 pages)
echo 8192 | sudo tee /proc/sys/vm/nr_hugepages

# Make persistent
echo "vm.nr_hugepages = 8192" | sudo tee /etc/sysctl.d/hugepages.conf
```

For 1GB hugepages (better for large VMs):

```bash
# Add to kernel cmdline in GRUB
GRUB_CMDLINE_LINUX="hugepagesz=1G hugepages=32"
```

### VM Hugepages Configuration

```xml
<memoryBacking>
  <hugepages>
    <page size='2048' unit='KiB'/>
  </hugepages>
</memoryBacking>
```

Or for 1GB pages:

```xml
<memoryBacking>
  <hugepages>
    <page size='1048576' unit='KiB'/>
  </hugepages>
</memoryBacking>
```

## vCPU Assignment

### Basic vCPU Configuration

```xml
<vcpu placement='static'>8</vcpu>
```

Via virsh:

```bash
# Set vCPU count (requires shutdown for increase)
virsh setvcpus myvm 8 --config --maximum
virsh setvcpus myvm 8 --config
```

### CPU Topology

Define sockets/cores/threads to match guest OS expectations:

```xml
<vcpu placement='static'>8</vcpu>
<cpu mode='host-passthrough'>
  <topology sockets='1' dies='1' cores='4' threads='2'/>
</cpu>
```

### CPU Pinning

Pin vCPUs to specific host cores for consistent performance:

```xml
<vcpu placement='static'>4</vcpu>
<cputune>
  <vcpupin vcpu='0' cpuset='4'/>
  <vcpupin vcpu='1' cpuset='5'/>
  <vcpupin vcpu='2' cpuset='6'/>
  <vcpupin vcpu='3' cpuset='7'/>
</cputune>
```

View host CPU topology:

```bash
lscpu --extended
virsh capabilities | grep -A20 '<topology>'
```

!!! note "Strix Halo CCX pinning"
    The Ryzen AI Max+ 395 has **2 x CCX of 8 Zen 5 cores each**, each CCX with its own L3 cache. Crossing the CCX boundary inside a single VM incurs a noticeable L3-miss penalty. For latency-sensitive guests (Windows VM for interactive use, gaming VM if you ever go that route), **pin all vCPUs of one VM to a single CCX**.

    Check the CCX layout with `lscpu --extended` — look at the `L3` column; cores sharing an L3 cache value are on the same CCX. Typical layout:

    - CCX 0: cores 0-7 (siblings 16-23 with SMT)
    - CCX 1: cores 8-15 (siblings 24-31 with SMT)

    Example: pin an 8-vCPU Windows VM entirely to CCX 1:

    ```xml
    <vcpu placement='static'>8</vcpu>
    <cputune>
      <vcpupin vcpu='0' cpuset='8'/>
      <vcpupin vcpu='1' cpuset='24'/>  <!-- SMT sibling -->
      <vcpupin vcpu='2' cpuset='9'/>
      <vcpupin vcpu='3' cpuset='25'/>
      <vcpupin vcpu='4' cpuset='10'/>
      <vcpupin vcpu='5' cpuset='26'/>
      <vcpupin vcpu='6' cpuset='11'/>
      <vcpupin vcpu='7' cpuset='27'/>
      <emulatorpin cpuset='0-1'/>     <!-- emulator threads on the OTHER CCX -->
    </cputune>
    ```

    This pattern leaves CCX 0 (cores 0-7 + siblings 16-23) for the host, Docker services, and Ollama/llama.cpp — which is roughly the right split given the workload mix.

### Emulator Pinning

Pin QEMU emulator threads separately:

```xml
<cputune>
  <vcpupin vcpu='0' cpuset='4'/>
  <vcpupin vcpu='1' cpuset='5'/>
  <emulatorpin cpuset='0-1'/>
</cputune>
```

## NUMA Configuration

For multi-socket systems or large VMs, NUMA awareness improves performance.

### View Host NUMA

```bash
numactl --hardware
virsh capabilities | grep -A50 '<numa>'
```

### VM NUMA Configuration

```xml
<numatune>
  <memory mode='strict' nodeset='0'/>
</numatune>
<cpu mode='host-passthrough'>
  <numa>
    <cell id='0' cpus='0-7' memory='16' unit='GiB'/>
  </numa>
</cpu>
```

## I/O Resource Control

### Disk I/O Limits

```xml
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2'/>
  <source file='/mnt/tank/vm/myvm/disk.qcow2'/>
  <target dev='vda' bus='virtio'/>
  <iotune>
    <read_bytes_sec>104857600</read_bytes_sec>   <!-- 100 MB/s -->
    <write_bytes_sec>52428800</write_bytes_sec>  <!-- 50 MB/s -->
    <read_iops_sec>1000</read_iops_sec>
    <write_iops_sec>500</write_iops_sec>
  </iotune>
</disk>
```

Set at runtime:

```bash
virsh blkdeviotune myvm vda --read-bytes-sec 104857600 --live
```

### Network Bandwidth

```xml
<interface type='bridge'>
  <source bridge='br0'/>
  <bandwidth>
    <inbound average='125000' peak='250000' burst='256'/>   <!-- KB/s -->
    <outbound average='125000' peak='250000' burst='256'/>
  </bandwidth>
</interface>
```

## Resource Monitoring

### VM Statistics

```bash
# Overview of all VMs
virsh list --all

# CPU and memory for running VMs
virsh domstats

# Specific VM stats
virsh domstats myvm

# CPU usage
virsh cpu-stats myvm

# Memory stats (requires balloon)
virsh dommemstat myvm
```

### Detailed Statistics

```bash
# Block device stats
virsh domblkstat myvm vda

# Network stats
virsh domifstat myvm vnet0

# Complete domain info
virsh dominfo myvm
```

### Real-Time Monitoring

```bash
# Watch VM stats (updates every 2 seconds)
watch -n2 'virsh domstats --cpu-total --balloon --block --interface'

# virt-top for interactive view
sudo apt install virt-top
virt-top
```

## Live Resource Adjustment

### Memory

```bash
# Adjust current memory (within max)
virsh setmem myvm 8G --live

# Check current allocation
virsh dominfo myvm | grep memory
```

### vCPUs

```bash
# Reduce vCPUs (if hotplug enabled)
virsh setvcpus myvm 4 --live

# Check current vCPUs
virsh vcpucount myvm
```

### I/O Limits

```bash
# Adjust disk I/O
virsh blkdeviotune myvm vda \
  --read-bytes-sec 209715200 \
  --write-bytes-sec 104857600 \
  --live

# Adjust network bandwidth
virsh domiftune myvm vnet0 --inbound 250000,500000,512 --live
```

## Best Practices

### Windows VMs

| Setting | Recommendation |
|---------|----------------|
| Memory | Fixed allocation, no ballooning |
| vCPUs | Even number, matching host topology |
| Storage | virtio with latest drivers |
| Network | virtio with latest drivers |

Windows-specific XML:

```xml
<features>
  <hyperv mode='custom'>
    <relaxed state='on'/>
    <vapic state='on'/>
    <spinlocks state='on' retries='8191'/>
    <vpindex state='on'/>
    <synic state='on'/>
    <stimer state='on'/>
  </hyperv>
</features>
<clock offset='localtime'>
  <timer name='hypervclock' present='yes'/>
</clock>
```

### Linux VMs

| Setting | Recommendation |
|---------|----------------|
| Memory | Ballooning enabled for flexibility |
| vCPUs | Match workload, can overcommit |
| Storage | virtio-scsi for multiple disks |
| Network | virtio (default driver) |

### General Guidelines

1. **Don't overcommit memory** for production VMs
2. **Reserve host resources**: Leave 4-8GB RAM and 2-4 cores for host
3. **Use CPU pinning** for latency-sensitive workloads
4. **Enable hugepages** for VMs >8GB
5. **Monitor regularly** with virsh domstats and virt-top

## Resource Budget Example

For a 128GB / 16-core host running mixed workloads:

| Workload | Memory | vCPUs | Notes |
|----------|--------|-------|-------|
| Host reserved | 8GB | 4 | OS, Docker, services |
| Windows VM | 24GB | 6 | Admin/utility, virtio-gpu (no passthrough by default) |
| Linux VM | 16GB | 4 | Development |
| LLM inference | 64GB | 8 | Ollama containers |
| Available | 16GB | - | Headroom |

See [Capacity Planning](../operations/capacity-planning.md) for system-wide resource strategy.

## Next Steps

- [KVM Setup](kvm-setup.md) for installation and configuration
- [GPU Passthrough](gpu-passthrough.md) for dedicated VM graphics
- [Windows 11 VM](windows-vm.md) for gaming VM setup
