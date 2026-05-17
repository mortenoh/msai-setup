# Docker Services

This section covers Docker setup and containerized services for the MS-S1 MAX.

## Overview

Docker runs services with data stored on ZFS datasets.

## Golden Rule

> **Containers are disposable. Data is not.**

All persistent data lives on ZFS via bind mounts.

## Bind Mounts vs Docker Volumes

| Approach | Use Case |
|----------|----------|
| Bind mounts | All persistent data (default) |
| Docker volumes | Small, disposable state only |

### Why Bind Mounts?

- Transparent paths
- Backed by ZFS datasets
- Easy snapshots and backups
- Human-inspectable

## Sections

- [Docker Setup](setup.md) — Install Docker on Ubuntu 26.04 (with `resolute → noble` fallback) and configure the daemon
- [Docker Compose](compose.md) — Compose Spec, project structure, common patterns
- [Resource Limits](resources.md) — Container memory, CPU, GPU, and device constraints
- [Development Stacks](development-stacks.md) — Postgres, Redis, Elasticsearch, etc. for dev
- [Ollama Stack](ollama-stack.md) — ROCm-backed Ollama + Open WebUI compose
- [Monitoring](monitoring.md) — Prometheus + Grafana + Loki + cAdvisor
- [Nextcloud](nextcloud.md) — Self-hosted cloud storage
- [Plex](plex.md) — Media server (with iGPU transcoding caveat — see notes inside)
