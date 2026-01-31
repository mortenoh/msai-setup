# ZFS Storage

This section covers ZFS setup and management for the MS-S1 MAX.

## Overview

ZFS provides:

- Copy-on-write filesystem
- Built-in compression
- Snapshots and clones
- Data integrity verification

## Why ZFS?

- **Snapshots** - Point-in-time recovery without backup restore
- **Compression** - Save space transparently with lz4
- **Datasets** - Separate policies per data type
- **Simplicity** - One tool for volumes and filesystems

## Sections

- [Concepts](concepts.md) - ZFS fundamentals
- [Pool Creation](pool-creation.md) - Create the tank pool
- [Datasets](datasets.md) - Dataset hierarchy and properties
- [Snapshots](snapshots.md) - Snapshot policies and management
