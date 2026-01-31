# Architecture Decisions

Choose the right deployment approach for your local LLM infrastructure.

## Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                 Where to run LLM inference?                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │  Native │     │Container│     │   VM    │
        └────┬────┘     └────┬────┘     └────┬────┘
             │               │               │
             ▼               ▼               ▼
    ┌────────────────┐ ┌────────────┐ ┌────────────────┐
    │ Best for:      │ │ Best for:  │ │ Best for:      │
    │ - macOS/MLX    │ │ - Linux    │ │ - Windows apps │
    │ - Max perf     │ │ - Services │ │ - GPU passthru │
    │ - GUI tools    │ │ - Multi-   │ │ - Isolation    │
    │                │ │   instance │ │                │
    └────────────────┘ └────────────┘ └────────────────┘
```

## Comparison Matrix

| Factor | Native | Container | VM |
|--------|--------|-----------|-----|
| **Performance** | Best | Good (-5-10%) | Good (with passthrough) |
| **Isolation** | None | Process-level | Full |
| **GPU Access** | Direct | Varies by platform | Passthrough required |
| **Setup complexity** | Low | Medium | High |
| **Portability** | Low | High | Medium |
| **macOS support** | Excellent | Limited GPU | No GPU passthrough |
| **Linux support** | Good | Excellent | Good |

## Native Installation

Run inference engines directly on the host OS.

### When to Choose Native

- **macOS with Apple Silicon** - MLX and Metal require native access
- **Maximum performance** - No virtualization overhead
- **GUI applications** - LM Studio, Jan.ai
- **Development/testing** - Quick iteration

### Engines for Native

| Engine | macOS | Linux | Notes |
|--------|-------|-------|-------|
| MLX | Excellent | N/A | Apple Silicon only |
| llama.cpp | Good (Metal) | Good (CUDA) | Cross-platform |
| Ollama | Good | Good | Docker-like UX |
| LM Studio | Excellent | Good | GUI |
| Jan.ai | Good | Good | GUI, offline-first |

### Native Example (macOS)

```bash
# Install MLX
pip install mlx-lm

# Or install Ollama natively
brew install ollama
ollama serve
ollama pull llama3.3:70b-instruct-q4_K_M
```

## Container Deployment

Run inference engines in Docker/Podman containers.

### When to Choose Containers

- **Linux servers** - NVIDIA Container Toolkit for GPU
- **Service isolation** - Separate models/configs
- **Reproducibility** - Consistent deployments
- **Multi-tenant** - Different users/applications
- **Orchestration** - Compose, Kubernetes

### Container GPU Access

| Platform | GPU Access | Setup |
|----------|------------|-------|
| Linux + NVIDIA | Excellent | nvidia-container-toolkit |
| Linux + AMD | Good | ROCm containers |
| macOS | Limited | No Metal passthrough |
| Windows + WSL2 | Good | CUDA support in WSL |

### Container Example (Linux)

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - /tank/ai/models/ollama:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### macOS Container Limitations

Containers on macOS cannot access Metal GPU:

```
┌──────────────────────────────────────────────┐
│                macOS Host                     │
│  ┌────────────────┐  ┌────────────────────┐  │
│  │  Native Apps   │  │  Docker Desktop    │  │
│  │  (Metal GPU)   │  │  (CPU only)        │  │
│  │  ┌──────────┐  │  │  ┌──────────────┐  │  │
│  │  │ LM Studio│  │  │  │   Ollama     │  │  │
│  │  │ MLX      │  │  │  │ (no Metal)   │  │  │
│  │  └──────────┘  │  │  └──────────────┘  │  │
│  └────────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────┘
```

For macOS: Use native Ollama or LM Studio, not containerized versions.

## Virtual Machine

Run LLMs inside a full virtual machine.

### When to Choose VMs

- **Windows-only tools** - LM Studio has good Windows support
- **GPU passthrough** - Dedicate GPU to VM
- **Strong isolation** - Security boundaries
- **Testing different OSes** - Linux distros, Windows

### VM GPU Passthrough

See [GPU Passthrough](../../virtualization/gpu-passthrough.md) for detailed setup.

```
┌───────────────────────────────────────────────────────┐
│                     Host OS (Linux)                    │
│  ┌─────────────────────────────────────────────────┐  │
│  │                QEMU/KVM                          │  │
│  │  ┌───────────────────────────────────────────┐  │  │
│  │  │           Windows 11 VM                    │  │  │
│  │  │  ┌─────────────────────────────────────┐  │  │  │
│  │  │  │       LM Studio + GPU               │  │  │  │
│  │  │  │    (OpenAI-compatible API)          │  │  │  │
│  │  │  └─────────────────────────────────────┘  │  │  │
│  │  └───────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────┘  │
│                          │                             │
│                   API accessible                       │
│              (host, containers, network)               │
└───────────────────────────────────────────────────────┘
```

### VM Example

```bash
# Expose LM Studio API from Windows VM
# In VM: LM Studio → Local Server → Start
# API available at http://vm-ip:1234/v1/

# From host or container:
curl http://192.168.122.10:1234/v1/models
```

## Hybrid Approaches

Combine approaches for flexibility:

### Development Setup

```
Native (daily use):
├── LM Studio (GUI, model testing)
└── Ollama (CLI, API)

Container (services):
├── Open WebUI (web interface)
└── LocalAI (API gateway)
```

### Production Setup

```
Container (primary):
├── Ollama (main inference)
├── llama.cpp (specific models)
└── Traefik (load balancing)

Native (fallback):
└── MLX (macOS-specific workloads)
```

## Recommendations by Use Case

### AI-Assisted Coding

| Scenario | Recommendation |
|----------|----------------|
| macOS daily driver | Native Ollama + LM Studio |
| Linux server | Containerized Ollama |
| Mixed fleet | Container API + native clients |

### Multi-User Service

| Requirement | Solution |
|-------------|----------|
| Web interface | Open WebUI container |
| API access | Ollama/llama.cpp container |
| Authentication | Open WebUI or reverse proxy |

### Maximum Performance

| Platform | Solution |
|----------|----------|
| Apple Silicon | Native MLX |
| NVIDIA GPU | Native or container llama.cpp |
| Multi-GPU | vLLM container |

## Migration Paths

### Native to Container

```bash
# Export Ollama models
ollama list  # Note model names

# In container
docker exec ollama ollama pull <model>
```

### Container to Container

```bash
# Models stored on ZFS volume are portable
# Just mount the same volume in new container
volumes:
  - /tank/ai/models/ollama:/root/.ollama
```

## See Also

- [Container Deployment](../containers/index.md) - Docker/Podman setup
- [VM Integration](../vm-integration/index.md) - GPU passthrough VMs
- [Inference Engines](../inference-engines/index.md) - Engine comparison
- [GPU Passthrough](../../virtualization/gpu-passthrough.md) - VM GPU setup
