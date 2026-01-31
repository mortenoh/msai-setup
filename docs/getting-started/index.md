# Getting Started

This section covers the foundational information you need before setting up your MS-S1 MAX server.

## Overview

The MS-S1 MAX project creates a home server that separates concerns cleanly:

- **Host OS** handles hardware, networking, and virtualization
- **ZFS** manages all persistent data
- **KVM/QEMU** runs full operating systems with GPU passthrough
- **Docker** runs services with data stored on ZFS

## Sections

- [Hardware](hardware.md) - MS-S1 MAX specifications and storage layout
- [Architecture](architecture.md) - System design and component relationships
- [Prerequisites](prerequisites.md) - What you need before starting
