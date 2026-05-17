#!/usr/bin/env bash
#
# zfs-lab-vm.sh — VirtualBox lab VM for practising ZFS before the real install.
#
# What this script does:
#   create        Download Ubuntu 26.04 LTS server ISO (with sha256 verify),
#                 build an EFI VM named ms-s1-max-lab with 6 extra virtual
#                 disks for ZFS exercises, kick off an unattended install,
#                 and boot it headless.
#   wait-ssh      Poll until the VM accepts SSH on the forwarded port.
#   post-install  Detach the install ISO so the VM boots from disk going forward.
#   snapshot      Snapshot the VM's current state (great between lab exercises).
#   reset         Restore from the most recent snapshot.
#   destroy       Power off, unregister, and delete all VM files (including the disks).
#
# Idempotent: re-running create on an existing VM does nothing destructive.
# Run from a Mac/Linux host with VirtualBox installed.
#
# Mirrors the MS-S1 MAX install path:
#   - EFI boot, UEFI firmware
#   - Primary disk for the host OS + future ZFS pool member
#   - 6 extra disks for the ZFS lab (single, mirror, raidz1, replace, scrub,
#     send/receive — see docs/zfs/virtualbox-lab.md)
#
# This is for practising ZFS, not for benchmarking. VirtualBox disks share
# host I/O — numbers are not representative of NVMe-backed reality.

set -euo pipefail

# --- Configuration -----------------------------------------------------------

VM_NAME=${VM_NAME:-ms-s1-max-lab}
VM_USER=${VM_USER:-morten}
VM_PASSWORD=${VM_PASSWORD:-changeme}        # change before sharing the lab
VM_HOSTNAME=${VM_HOSTNAME:-${VM_NAME}.local}
VM_FULLNAME=${VM_FULLNAME:-Morten Hansen}

VM_MEMORY_MB=${VM_MEMORY_MB:-8192}          # 8 GiB; raise to 16384 for headroom
VM_CPUS=${VM_CPUS:-4}
VM_VRAM_MB=${VM_VRAM_MB:-32}

SSH_FORWARD_PORT=${SSH_FORWARD_PORT:-2222}   # host port -> guest 22

# Storage layout
TARGET_DIR=${TARGET_DIR:-./target}
PRIMARY_DISK_SIZE_MB=${PRIMARY_DISK_SIZE_MB:-80000}   # 80 GiB
LAB_DISK_COUNT=${LAB_DISK_COUNT:-6}
LAB_DISK_SIZE_MB=${LAB_DISK_SIZE_MB:-8000}            # 8 GiB each

# Ubuntu ISO. SHA256 is from releases.ubuntu.com after 26.04 GA — verify on a
# fresh download against https://releases.ubuntu.com/26.04/SHA256SUMS .
UBUNTU_RELEASE=${UBUNTU_RELEASE:-26.04}
ISO_FILENAME="ubuntu-${UBUNTU_RELEASE}-live-server-amd64.iso"
ISO_URL="https://releases.ubuntu.com/${UBUNTU_RELEASE}/${ISO_FILENAME}"
ISO_SHA256_URL="https://releases.ubuntu.com/${UBUNTU_RELEASE}/SHA256SUMS"
ISO_PATH=${ISO_PATH:-${TARGET_DIR}/${ISO_FILENAME}}

# --- Helpers -----------------------------------------------------------------

log() { printf '[zfs-lab-vm] %s\n' "$*"; }
die() { printf '[zfs-lab-vm] error: %s\n' "$*" >&2; exit 1; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

require_vbox() {
    require_cmd VBoxManage
    VBoxManage --version >/dev/null 2>&1 || die "VBoxManage is installed but doesn't run"
}

vm_exists() {
    VBoxManage list vms | grep -q "\"${VM_NAME}\""
}

vm_running() {
    VBoxManage list runningvms | grep -q "\"${VM_NAME}\""
}

vm_dir() {
    VBoxManage list systemproperties \
        | awk -F': *' '/Default machine folder/{print $2}' \
        | sed -e "s|$|/${VM_NAME}|"
}

# --- ISO download + verify ---------------------------------------------------

download_iso() {
    mkdir -p "${TARGET_DIR}"

    if [[ -f "${ISO_PATH}" ]]; then
        log "ISO already present: ${ISO_PATH}"
    else
        log "Downloading Ubuntu ${UBUNTU_RELEASE} ISO to ${ISO_PATH}"
        curl -L --fail --progress-bar -o "${ISO_PATH}.partial" "${ISO_URL}"
        mv "${ISO_PATH}.partial" "${ISO_PATH}"
    fi

    log "Verifying SHA256 against ${ISO_SHA256_URL}"
    local expected
    expected=$(curl -fsSL "${ISO_SHA256_URL}" \
        | awk -v f="*${ISO_FILENAME}" '$2==f {print $1}')
    [[ -n "${expected}" ]] || die "couldn't find SHA256 for ${ISO_FILENAME} on the release server"

    local actual
    actual=$(shasum -a 256 "${ISO_PATH}" | awk '{print $1}')
    if [[ "${expected}" != "${actual}" ]]; then
        die "ISO checksum mismatch! expected=${expected} actual=${actual}"
    fi
    log "ISO checksum OK"
}

# --- VM lifecycle ------------------------------------------------------------

create_vm() {
    if vm_exists; then
        log "VM ${VM_NAME} already exists; skipping createvm"
    else
        log "Creating VM ${VM_NAME}"
        VBoxManage createvm \
            --name "${VM_NAME}" \
            --ostype Ubuntu_64 \
            --register

        # EFI + sane defaults; matches the real install (UEFI on MS-S1 MAX)
        VBoxManage modifyvm "${VM_NAME}" \
            --memory "${VM_MEMORY_MB}" \
            --cpus "${VM_CPUS}" \
            --vram "${VM_VRAM_MB}" \
            --firmware efi64 \
            --nic1 nat \
            --boot1 disk --boot2 dvd --boot3 none --boot4 none \
            --rtcuseutc on \
            --audio-driver none \
            --usbohci off --usbehci off --usbxhci off

        # Forward host port to guest SSH for headless management
        VBoxManage modifyvm "${VM_NAME}" \
            --natpf1 "ssh,tcp,127.0.0.1,${SSH_FORWARD_PORT},,22"
    fi
}

create_disks() {
    mkdir -p "${TARGET_DIR}"

    local primary_disk="${TARGET_DIR}/${VM_NAME}-primary.vdi"
    if [[ ! -f "${primary_disk}" ]]; then
        log "Creating primary disk (${PRIMARY_DISK_SIZE_MB} MiB) -> ${primary_disk}"
        VBoxManage createmedium disk \
            --filename "${primary_disk}" \
            --size "${PRIMARY_DISK_SIZE_MB}" \
            --format VDI
    else
        log "Primary disk already exists: ${primary_disk}"
    fi

    for ((i=1; i<=LAB_DISK_COUNT; i++)); do
        local lab_disk
        lab_disk=$(printf "%s/%s-lab-%02d.vdi" "${TARGET_DIR}" "${VM_NAME}" "$i")
        if [[ ! -f "${lab_disk}" ]]; then
            log "Creating lab disk ${i}/${LAB_DISK_COUNT} (${LAB_DISK_SIZE_MB} MiB) -> ${lab_disk}"
            VBoxManage createmedium disk \
                --filename "${lab_disk}" \
                --size "${LAB_DISK_SIZE_MB}" \
                --format VDI
        else
            log "Lab disk ${i} already exists: ${lab_disk}"
        fi
    done
}

attach_storage() {
    # SATA controller for primary + lab disks (30 ports — plenty).
    if ! VBoxManage showvminfo "${VM_NAME}" --machinereadable | grep -q '^storagecontrollername0='; then
        log "Adding SATA controller"
        VBoxManage storagectl "${VM_NAME}" \
            --name SATA \
            --add sata \
            --controller IntelAhci \
            --portcount 30 \
            --bootable on
    fi

    # IDE controller exclusively for the install ISO (some EFI installers prefer it on IDE)
    if ! VBoxManage showvminfo "${VM_NAME}" --machinereadable | grep -q '^storagecontrollername1='; then
        log "Adding IDE controller for the install ISO"
        VBoxManage storagectl "${VM_NAME}" \
            --name IDE \
            --add ide
    fi

    # Attach primary disk on SATA port 0
    local primary_disk="${TARGET_DIR}/${VM_NAME}-primary.vdi"
    VBoxManage storageattach "${VM_NAME}" \
        --storagectl SATA --port 0 --device 0 \
        --type hdd --medium "${primary_disk}" \
        --nonrotational on --discard on

    # Attach lab disks on SATA ports 1..N
    for ((i=1; i<=LAB_DISK_COUNT; i++)); do
        local lab_disk
        lab_disk=$(printf "%s/%s-lab-%02d.vdi" "${TARGET_DIR}" "${VM_NAME}" "$i")
        VBoxManage storageattach "${VM_NAME}" \
            --storagectl SATA --port "$i" --device 0 \
            --type hdd --medium "${lab_disk}" \
            --nonrotational on --discard on
    done

    # Attach install ISO on IDE port 0
    if [[ -f "${ISO_PATH}" ]]; then
        VBoxManage storageattach "${VM_NAME}" \
            --storagectl IDE --port 0 --device 0 \
            --type dvddrive --medium "${ISO_PATH}"
    fi
}

configure_unattended() {
    log "Configuring unattended install (user=${VM_USER}, host=${VM_HOSTNAME})"
    VBoxManage unattended install "${VM_NAME}" \
        --iso "${ISO_PATH}" \
        --user "${VM_USER}" \
        --password "${VM_PASSWORD}" \
        --full-user-name "${VM_FULLNAME}" \
        --hostname "${VM_HOSTNAME}" \
        --install-additions \
        --time-zone Europe/Oslo \
        --locale en_US.UTF-8
}

start_vm() {
    if vm_running; then
        log "VM ${VM_NAME} is already running"
        return
    fi
    log "Starting VM ${VM_NAME} (headless)"
    VBoxManage startvm "${VM_NAME}" --type headless
}

# --- Post-install helpers ----------------------------------------------------

detach_iso() {
    log "Detaching install ISO from VM"
    VBoxManage storageattach "${VM_NAME}" \
        --storagectl IDE --port 0 --device 0 \
        --medium none || true
}

wait_ssh() {
    log "Waiting for SSH on 127.0.0.1:${SSH_FORWARD_PORT} (Ctrl-C to give up)"
    until nc -z 127.0.0.1 "${SSH_FORWARD_PORT}" 2>/dev/null; do
        sleep 5
    done
    log "SSH is up. Connect with: ssh -p ${SSH_FORWARD_PORT} ${VM_USER}@127.0.0.1"
}

snapshot_vm() {
    local name=${1:-snap-$(date +%Y%m%d-%H%M%S)}
    log "Snapshotting VM as '${name}'"
    VBoxManage snapshot "${VM_NAME}" take "${name}" --pause
}

reset_vm() {
    if vm_running; then
        log "Powering off VM before restore"
        VBoxManage controlvm "${VM_NAME}" poweroff || true
        sleep 2
    fi
    log "Restoring most recent snapshot"
    VBoxManage snapshot "${VM_NAME}" restorecurrent
    start_vm
}

destroy_vm() {
    if vm_running; then
        log "Powering off VM"
        VBoxManage controlvm "${VM_NAME}" poweroff || true
        sleep 2
    fi
    if vm_exists; then
        log "Unregistering VM and deleting all files"
        VBoxManage unregistervm "${VM_NAME}" --delete
    fi
    # Belt-and-braces: remove any leftover lab disks if the unregister didn't
    rm -f \
        "${TARGET_DIR}/${VM_NAME}-primary.vdi" \
        "${TARGET_DIR}/${VM_NAME}-lab-"*.vdi
    log "Done. (ISO at ${ISO_PATH} preserved.)"
}

# --- Dispatch ----------------------------------------------------------------

usage() {
    cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  create        Download ISO (verify SHA256), create VM, disks, attach storage, unattended install, start headless.
  wait-ssh      Poll until SSH on host port ${SSH_FORWARD_PORT} is reachable.
  post-install  Detach the install ISO (run after install completes).
  snapshot [name]  Take a snapshot of the VM (default: snap-YYYYMMDD-HHMMSS).
  reset         Power off and restore from the most recent snapshot.
  destroy       Power off, unregister VM, delete all VM files.

Env vars (defaults):
  VM_NAME=${VM_NAME}
  VM_USER=${VM_USER}
  VM_PASSWORD=${VM_PASSWORD}
  VM_HOSTNAME=${VM_HOSTNAME}
  VM_MEMORY_MB=${VM_MEMORY_MB}
  VM_CPUS=${VM_CPUS}
  SSH_FORWARD_PORT=${SSH_FORWARD_PORT}
  TARGET_DIR=${TARGET_DIR}
  PRIMARY_DISK_SIZE_MB=${PRIMARY_DISK_SIZE_MB}
  LAB_DISK_COUNT=${LAB_DISK_COUNT}
  LAB_DISK_SIZE_MB=${LAB_DISK_SIZE_MB}
  UBUNTU_RELEASE=${UBUNTU_RELEASE}
  ISO_PATH=${ISO_PATH}

Examples:
  # Full create flow:
  ./$(basename "$0") create
  ./$(basename "$0") wait-ssh
  ssh -p ${SSH_FORWARD_PORT} ${VM_USER}@127.0.0.1
  # After install reboots and you can SSH:
  ./$(basename "$0") post-install
  ./$(basename "$0") snapshot fresh-install

  # Between lab exercises:
  ./$(basename "$0") reset

  # When done:
  ./$(basename "$0") destroy
EOF
}

main() {
    [[ $# -ge 1 ]] || { usage; exit 1; }
    require_vbox
    case "$1" in
        create)
            require_cmd curl
            require_cmd shasum
            download_iso
            create_vm
            create_disks
            attach_storage
            configure_unattended
            start_vm
            log "Install is running. Run: $(basename "$0") wait-ssh"
            ;;
        wait-ssh)
            require_cmd nc
            wait_ssh
            ;;
        post-install)
            detach_iso
            ;;
        snapshot)
            shift
            snapshot_vm "${1:-}"
            ;;
        reset)
            reset_vm
            ;;
        destroy)
            destroy_vm
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
