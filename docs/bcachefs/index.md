# Bcachefs

Bcachefs is a next-generation copy-on-write filesystem for Linux, created by Kent Overstreet (developer of bcache). It aims to provide features comparable to ZFS and Btrfs with a cleaner, more maintainable codebase.

## Current Status

!!! warning "Experimental Filesystem"
    Bcachefs is still experimental. Always maintain backups of important data.

!!! info "Kernel Status (2025)"
    Bcachefs was merged into the Linux kernel in version 6.7 (January 2024) but was **removed in Linux 6.18** (September 2025). It is now maintained as an external DKMS module.

### The Kernel Removal

In September 2025, Linus Torvalds removed bcachefs from the Linux kernel tree (~117,000 lines of code). The removal occurred because:

1. The developer repeatedly submitted major patches late in merge windows, violating kernel development norms
2. After warnings during the 6.17 cycle, Torvalds followed through on consequences
3. The project had already shifted to DKMS distribution, making in-kernel code stale

Quote from the removal commit:
> "It's now a DKMS module, making the in-kernel code stale, so remove it to avoid any version confusion"

Bcachefs continues development outside the kernel tree and remains usable via DKMS.

## Key Features

| Feature | Description |
|---------|-------------|
| Copy-on-write | Never overwrites data in place |
| Checksums | Full data and metadata checksums |
| Compression | LZ4, gzip, zstd support |
| Encryption | ChaCha20/Poly1305 whole-filesystem encryption |
| Multi-device | Striping, mirroring, RAID1, SSD caching |
| Snapshots | Efficient point-in-time copies |
| Subvolumes | Independent filesystem namespaces |

## Why Consider Bcachefs?

**Potential advantages over ZFS:**

- Native Linux filesystem (no licensing concerns)
- Smaller, more maintainable codebase
- Designed with modern storage in mind
- Built-in encryption without LUKS

**Potential advantages over Btrfs:**

- Cleaner implementation
- Better RAID handling (eventually)
- More consistent performance

## When to Use Bcachefs

**Consider bcachefs for:**

- Non-critical data storage
- Experimentation and learning
- Systems where you control kernel/module versions
- Users comfortable with DKMS and kernel compilation

**Avoid bcachefs for:**

- Production servers
- Critical data without redundant backups
- Systems requiring stability guarantees
- Environments where DKMS compilation is problematic

## Sections

- [Concepts](concepts.md) - Bcachefs fundamentals and architecture
- [Installation](installation.md) - DKMS setup on Ubuntu
- [Usage](usage.md) - Creating and managing filesystems
- [Features](features.md) - Encryption, compression, caching
- [Limitations](limitations.md) - Known issues and what to avoid
