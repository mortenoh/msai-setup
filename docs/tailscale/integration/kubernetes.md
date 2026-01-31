# Kubernetes Integration

## Overview

Tailscale integrates with Kubernetes through the Tailscale Operator, enabling:

- Expose Kubernetes services to your tailnet
- Access cluster resources securely
- Use Tailscale as an ingress controller
- Connect pods to your tailnet

## Tailscale Operator

### Installation

```bash
# Add Helm repository
helm repo add tailscale https://pkgs.tailscale.com/helmcharts
helm repo update

# Create OAuth client in Tailscale admin console
# Settings → OAuth clients → Create

# Install operator
helm upgrade --install tailscale-operator tailscale/tailscale-operator \
  --namespace=tailscale \
  --create-namespace \
  --set oauth.clientId="${OAUTH_CLIENT_ID}" \
  --set oauth.clientSecret="${OAUTH_CLIENT_SECRET}"
```

### OAuth Scopes

Create an OAuth client with these scopes:
- `devices:read`
- `devices:write`

### Verify Installation

```bash
kubectl get pods -n tailscale

# Should show:
# tailscale-operator-xxx   Running
```

## Exposing Services

### Via Annotation

Add annotation to expose a service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    tailscale.com/expose: "true"
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

The service becomes accessible at `my-service.tailnet.ts.net`.

### With Custom Hostname

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    tailscale.com/expose: "true"
    tailscale.com/hostname: "custom-name"
spec:
  selector:
    app: my-app
  ports:
    - port: 80
```

Accessible at `custom-name.tailnet.ts.net`.

### LoadBalancer Services

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: LoadBalancer
  loadBalancerClass: tailscale
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

## Ingress Controller

Use Tailscale as an Ingress controller:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: tailscale
  rules:
    - host: my-app.tailnet.ts.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
```

### TLS with Tailscale

Tailscale automatically provisions TLS certificates:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: tailscale
  tls:
    - hosts:
        - my-app.tailnet.ts.net
  rules:
    - host: my-app.tailnet.ts.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
```

## Subnet Router

Run a subnet router to expose cluster network:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: tailscale-router
  namespace: tailscale
spec:
  selector:
    matchLabels:
      app: tailscale-router
  template:
    metadata:
      labels:
        app: tailscale-router
    spec:
      hostNetwork: true
      serviceAccountName: tailscale-operator
      containers:
        - name: tailscale
          image: tailscale/tailscale:latest
          securityContext:
            capabilities:
              add:
                - NET_ADMIN
                - NET_RAW
          env:
            - name: TS_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: tailscale-auth
                  key: authkey
            - name: TS_KUBE_SECRET
              value: "tailscale-router-state"
            - name: TS_EXTRA_ARGS
              value: "--advertise-routes=10.96.0.0/12,10.244.0.0/16"
          volumeMounts:
            - name: tun
              mountPath: /dev/net/tun
      volumes:
        - name: tun
          hostPath:
            path: /dev/net/tun
```

Routes to advertise:
- `10.96.0.0/12` - Service CIDR (typical)
- `10.244.0.0/16` - Pod CIDR (varies by CNI)

## Exit Node in Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tailscale-exit
  namespace: tailscale
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tailscale-exit
  template:
    metadata:
      labels:
        app: tailscale-exit
    spec:
      hostNetwork: true
      containers:
        - name: tailscale
          image: tailscale/tailscale:latest
          securityContext:
            capabilities:
              add:
                - NET_ADMIN
                - NET_RAW
          env:
            - name: TS_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: tailscale-auth
                  key: authkey
            - name: TS_EXTRA_ARGS
              value: "--advertise-exit-node --hostname=k8s-exit"
          volumeMounts:
            - name: tun
              mountPath: /dev/net/tun
      volumes:
        - name: tun
          hostPath:
            path: /dev/net/tun
```

## Sidecar Pattern

Add Tailscale as a sidecar to pods:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: tailscale
          image: tailscale/tailscale:latest
          securityContext:
            capabilities:
              add:
                - NET_ADMIN
                - NET_RAW
          env:
            - name: TS_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: tailscale-auth
                  key: authkey
            - name: TS_KUBE_SECRET
              value: "my-app-ts-state"
            - name: TS_USERSPACE
              value: "true"
            - name: TS_SOCKS5_SERVER
              value: ":1055"
          volumeMounts:
            - name: tun
              mountPath: /dev/net/tun
        - name: app
          image: my-app:latest
          env:
            - name: ALL_PROXY
              value: "socks5://localhost:1055"
      volumes:
        - name: tun
          hostPath:
            path: /dev/net/tun
```

## Secrets Management

### Create Auth Key Secret

```bash
kubectl create secret generic tailscale-auth \
  --namespace=tailscale \
  --from-literal=authkey=tskey-auth-xxxxx
```

### Using External Secrets

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: tailscale-auth
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: tailscale-auth
  data:
    - secretKey: authkey
      remoteRef:
        key: tailscale/authkey
```

## Network Policies

Allow Tailscale traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-tailscale
spec:
  podSelector:
    matchLabels:
      app: tailscale
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - {}
  egress:
    - {}
```

## Operator Configuration

### Custom Resource Definitions

The operator creates custom resources:

```bash
kubectl get tailscaleconfigs
kubectl get tailscaleproxies
```

### Operator Flags

```yaml
# Helm values
operator:
  logging: info
  hostname: ""
  apiServerProxyConfig:
    mode: "true"
```

## Troubleshooting

### Check Operator Logs

```bash
kubectl logs -n tailscale deployment/tailscale-operator
```

### Check Proxy Pods

```bash
# List Tailscale proxy pods
kubectl get pods -n tailscale -l app.kubernetes.io/name=tailscale

# Check specific proxy
kubectl logs -n tailscale <proxy-pod-name>
```

### Service Not Exposed

```bash
# Check annotation
kubectl get svc my-service -o yaml | grep tailscale

# Check operator events
kubectl get events -n tailscale

# Verify OAuth credentials
kubectl get secret -n tailscale
```

### DNS Issues

```bash
# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Test DNS resolution
kubectl run test --rm -it --image=busybox -- nslookup my-service.tailnet.ts.net
```

## Best Practices

1. **Use the operator** for managed deployments
2. **Create dedicated OAuth client** for Kubernetes
3. **Use secrets** for auth keys, never hardcode
4. **Apply network policies** appropriately
5. **Monitor operator logs** for issues
6. **Use tags** for ACL-based access control
7. **Consider namespace isolation** for multi-tenant clusters
