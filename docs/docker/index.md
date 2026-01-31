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

- [Docker Setup](setup.md) - Install and configure Docker
- [Resource Limits](resources.md) - Container memory, CPU, and device constraints
- [Nextcloud](nextcloud.md) - Self-hosted cloud storage
- [Plex](plex.md) - Media server
