# Common Problems

## Quick Solutions Reference

### Docker Ports Accessible Despite UFW

**Problem:** Published Docker ports bypass UFW rules.

**Solution:**

```bash
# Option 1: Bind to localhost
docker run -p 127.0.0.1:8080:80 nginx

# Option 2: Use ufw-docker
sudo ufw-docker install
sudo ufw-docker allow container_name 80

# Option 3: DOCKER-USER rules
iptables -I DOCKER-USER -i eth0 -p tcp --dport 8080 -j DROP
```

---

### VM Can't Reach Internet

**Problem:** VMs on NAT network have no external connectivity.

**Checklist:**

```bash
# 1. IP forwarding enabled?
cat /proc/sys/net/ipv4/ip_forward
# If 0:
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 2. UFW forward policy?
grep DEFAULT_FORWARD /etc/default/ufw
# If DROP, add rules to before.rules

# 3. NAT rule exists?
sudo iptables -t nat -L POSTROUTING -n | grep 192.168.122
# If missing, restart libvirtd

# 4. libvirt network running?
virsh net-list
virsh net-start default
```

---

### Container-to-Container DNS Fails

**Problem:** Containers can't resolve each other by name.

**Solution:**

```bash
# Use custom network (not default bridge)
docker network create mynet
docker run --network mynet --name web nginx
docker run --network mynet alpine ping web  # Works
```

---

### UFW Rules Disappear After Restart

**Problem:** Custom iptables rules lost on UFW reload.

**Solution:** Put rules in UFW's files:

```bash
# For NAT
# Add to /etc/ufw/before.rules in *nat section

# For filter rules
# Add to /etc/ufw/before.rules in *filter section
# Or add as ufw commands for user rules
```

---

### Service Listening But Not Accessible

**Problem:** `ss -tlnp` shows service, but can't connect.

**Checklist:**

```bash
# 1. Binding address?
ss -tlnp | grep :8080
# "127.0.0.1:8080" = localhost only
# "0.0.0.0:8080" or "*:8080" = all interfaces

# 2. Firewall?
sudo ufw status | grep 8080
sudo iptables -L INPUT -n | grep 8080

# 3. If Docker
docker port container
# Check if bound to 127.0.0.1
```

---

### Bridge Traffic Not Filtered

**Problem:** Traffic between VMs/containers bypasses firewall.

**Solution:**

```bash
# Enable bridge filtering
echo 1 | sudo tee /proc/sys/net/bridge/bridge-nf-call-iptables

# Make permanent
echo "net.bridge.bridge-nf-call-iptables = 1" | sudo tee /etc/sysctl.d/99-bridge.conf
```

---

### Docker Compose Networks Isolated

**Problem:** Services in different compose projects can't communicate.

**Solution:**

```yaml
# Use external network
# Create first:
# docker network create shared

# In compose files:
networks:
  shared:
    external: true
    name: shared
```

---

### libvirt and Docker Conflict

**Problem:** After Docker restart, VMs lose network.

**Solution:**

```bash
# Restart libvirtd after Docker
sudo systemctl restart libvirtd

# Or create systemd dependency
sudo mkdir -p /etc/systemd/system/libvirtd.service.d
echo -e "[Unit]\nAfter=docker.service" | sudo tee /etc/systemd/system/libvirtd.service.d/docker.conf
sudo systemctl daemon-reload
```

---

### Cannot SSH to VM After GPU Passthrough

**Problem:** VM has no network after enabling GPU passthrough.

**Checklist:**

```bash
# 1. VM using virtio-net?
virsh dumpxml vmname | grep "model type="

# 2. virtio drivers installed in VM?
# For Windows: Install virtio-win drivers

# 3. Network interface in VM?
# Check Device Manager (Windows) or ip addr (Linux)
```

---

### DHCP Not Working in VM/Container

**Problem:** VM or container not getting IP.

**For VMs:**

```bash
# Check dnsmasq running
ps aux | grep dnsmasq | grep virbr

# Check libvirt network has DHCP
virsh net-dumpxml default | grep dhcp

# Restart network
virsh net-destroy default && virsh net-start default
```

**For Docker:**

```bash
# Check Docker's IPAM
docker network inspect bridge

# Recreate network if corrupted
docker network rm mynet
docker network create mynet
```

---

### Port Forwarding Not Working

**Problem:** External can't reach VM via port forward.

**Checklist:**

```bash
# 1. DNAT rule exists?
sudo iptables -t nat -L PREROUTING -n | grep 2222

# 2. FORWARD rule allows it?
sudo iptables -L FORWARD -n | grep "192.168.122.10.*dpt:22"

# 3. VM service running?
virsh console vmname
# Check: systemctl status sshd

# 4. VM firewall allows it?
# Check: sudo ufw status (in VM)
```

---

### LXD Proxy Device Not Working

**Problem:** Proxy device added but service unreachable.

**Checklist:**

```bash
# 1. Proxy device exists?
lxc config device show container | grep proxy

# 2. Using bind=host?
# Without it, UFW won't apply
lxc config device set container proxy bind=host

# 3. UFW allows port?
sudo ufw allow 8080/tcp

# 4. Service in container running?
lxc exec container -- systemctl status nginx
```

---

### All Container/VM Traffic Blocked After UFW Change

**Problem:** Changed UFW, now nothing works.

**Emergency Fix:**

```bash
# Disable UFW temporarily
sudo ufw disable

# Fix the issue

# Re-enable with defaults
sudo ufw default allow outgoing
sudo ufw default deny incoming
sudo ufw enable
```

**Check forwarding:**

```bash
# /etc/default/ufw
DEFAULT_FORWARD_POLICY="DROP"  # This blocks VMs/containers

# Fix in before.rules or change policy
```

---

### Network Namespace Confusion

**Problem:** Rules apply to wrong namespace.

**Solution:**

```bash
# Check which namespace you're in
ip netns identify $$

# View container's namespace
docker inspect container -f '{{.NetworkSettings.SandboxKey}}'

# Execute in namespace
nsenter -t $(docker inspect -f '{{.State.Pid}}' container) -n iptables -L
```

---

### MTU Issues

**Problem:** Large packets fail, small packets work.

**Symptoms:**

- SSH works, SCP fails
- Small HTTP requests work, large fail
- Ping works, but ping with large packet fails

**Solution:**

```bash
# Check MTU
ip link show docker0
ip link show virbr0

# Set lower MTU
ip link set docker0 mtu 1400

# For Docker
# /etc/docker/daemon.json
{
  "mtu": 1400
}

# For compose
networks:
  default:
    driver_opts:
      com.docker.network.driver.mtu: 1400
```
