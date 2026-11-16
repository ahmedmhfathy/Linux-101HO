#!/usr/bin/env bash
# ==============================================================================
# start.sh - Launcher for Cyberus Linux Quest
# ==============================================================================
set -euo pipefail

readonly VERSION="1.0"
readonly IMAGE_NAME="linux-quest:${VERSION}"
readonly CONTAINER_NAME="cyberus-linux-quest"
readonly HOME_VOLUME="cyberus-quest-v1-home"
readonly STATE_VOLUME="cyberus-quest-v1-state"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

usage() {
    cat << EOF
Usage: ./start.sh [--help] [--doctor]

Starts (or attaches to) the Cyberus Linux Quest container (${IMAGE_NAME}).
State is persisted in Docker volumes:
  - ${HOME_VOLUME}
  - ${STATE_VOLUME}
EOF
}

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "[!] Docker is not installed. Run './setup-docker.sh' first." >&2
    exit 1
fi

DOCKER_CMD=("docker")
if ! docker info >/dev/null 2>&1; then
    if sudo docker info >/dev/null 2>&1; then
        DOCKER_CMD=("sudo" "docker")
    else
        echo "[!] Docker daemon does not appear to be running." >&2
        echo "    Start it with: sudo systemctl start docker" >&2
        exit 1
    fi
fi

detect_arch() {
    local machine
    machine="$(uname -m)"
    case "$machine" in
        x86_64|amd64)
            printf 'amd64\n'
            ;;
        aarch64|arm64)
            printf 'arm64\n'
            ;;
        *)
            echo "[!] Unsupported CPU architecture: $machine" >&2
            exit 1
            ;;
    esac
}

ARCH="$(detect_arch)"
TAR_FILE="${SCRIPT_DIR}/linux-quest-v${VERSION}-${ARCH}.tar"

if ! "${DOCKER_CMD[@]}" image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    if [[ -f "$TAR_FILE" ]]; then
        if [[ -f "${SCRIPT_DIR}/SHA256SUMS" ]] && command -v sha256sum >/dev/null 2>&1; then
            echo "[*] Verifying archive checksum..."
            (cd "$SCRIPT_DIR" && sha256sum --ignore-missing -c SHA256SUMS)
        fi
        echo "[*] Loading offline image from ${TAR_FILE}..."
        "${DOCKER_CMD[@]}" load -i "$TAR_FILE"
        if "${DOCKER_CMD[@]}" image inspect "linux-quest:${VERSION}-${ARCH}" >/dev/null 2>&1; then
            "${DOCKER_CMD[@]}" tag "linux-quest:${VERSION}-${ARCH}" "$IMAGE_NAME"
        fi
    elif [[ -f "${SCRIPT_DIR}/Dockerfile" ]]; then
        echo "[*] Offline archive not found; building ${IMAGE_NAME} locally from Dockerfile..."
        "${DOCKER_CMD[@]}" build --target runtime -t "$IMAGE_NAME" "$SCRIPT_DIR"
    else
        echo "[!] Image '${IMAGE_NAME}' not found and '${TAR_FILE}' is missing." >&2
        exit 1
    fi
fi

# If this is a freshly cloned directory (no .quest_initialized marker yet),
# wipe any leftover container and volumes from previous clones so it starts 100% clean.
INIT_MARKER="${SCRIPT_DIR}/.quest_initialized"
if [[ ! -f "$INIT_MARKER" ]]; then
    if "${DOCKER_CMD[@]}" ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
        "${DOCKER_CMD[@]}" rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    "${DOCKER_CMD[@]}" volume rm -f "$HOME_VOLUME" "$STATE_VOLUME" >/dev/null 2>&1 || true
    touch "$INIT_MARKER" 2>/dev/null || true
fi

if [[ "${1:-}" == "--doctor" ]]; then
    exec "${DOCKER_CMD[@]}" run --rm \
        --network none \
        -v "${HOME_VOLUME}:/home/member" \
        -v "${STATE_VOLUME}:/var/lib/quest" \
        "$IMAGE_NAME" /usr/local/bin/quest doctor
fi

# If container is already running, attach a new login shell inside it
if "${DOCKER_CMD[@]}" ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "[*] Attaching to running '${CONTAINER_NAME}' container..."
    exec "${DOCKER_CMD[@]}" exec -it -u member "$CONTAINER_NAME" bash -l
fi

# Remove any stopped leftover container with the same name
if "${DOCKER_CMD[@]}" ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    "${DOCKER_CMD[@]}" rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

exec "${DOCKER_CMD[@]}" run -it --rm \
    --name "$CONTAINER_NAME" \
    --hostname cyberus \
    --network none \
    --pids-limit 256 \
    --memory 512m \
    --cpus 1 \
    -v "${HOME_VOLUME}:/home/member" \
    -v "${STATE_VOLUME}:/var/lib/quest" \
    "$IMAGE_NAME"
