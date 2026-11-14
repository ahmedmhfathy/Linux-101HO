#!/usr/bin/env bash
# ==============================================================================
# reset.sh - Safely removes Cyberus Linux Quest volumes after confirmation
# ==============================================================================
set -euo pipefail

readonly CONTAINER_NAME="cyberus-linux-quest"
readonly HOME_VOLUME="cyberus-quest-v1-home"
readonly STATE_VOLUME="cyberus-quest-v1-state"

usage() {
    cat << EOF
Usage: ./reset.sh [--yes] [--help]

Stops '${CONTAINER_NAME}' (if running) and deletes ONLY the two lab volumes:
  - ${HOME_VOLUME}
  - ${STATE_VOLUME}
EOF
}

AUTO_YES=0
for arg in "$@"; do
    case "$arg" in
        -y|--yes)
            AUTO_YES=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            usage >&2
            exit 1
            ;;
    esac
done

DOCKER_CMD=("docker")
if ! docker info >/dev/null 2>&1; then
    if sudo docker info >/dev/null 2>&1; then
        DOCKER_CMD=("sudo" "docker")
    else
        echo "[!] Cannot connect to Docker daemon." >&2
        exit 1
    fi
fi

if [[ "$AUTO_YES" -ne 1 ]]; then
    echo "[!] WARNING: This will permanently wipe your Cyberus Linux Quest progress"
    echo "    and delete volumes '${HOME_VOLUME}' and '${STATE_VOLUME}'."
    read -r -p "Are you sure you want to continue? [y/N]: " ans
    if [[ "${ans,,}" != "y" ]] && [[ "${ans,,}" != "yes" ]]; then
        echo "Aborted."
        exit 0
    fi
fi

if "${DOCKER_CMD[@]}" ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "[*] Stopping container '${CONTAINER_NAME}'..."
    "${DOCKER_CMD[@]}" rm -f "$CONTAINER_NAME" >/dev/null
fi

echo "[*] Removing volumes '${HOME_VOLUME}' and '${STATE_VOLUME}'..."
"${DOCKER_CMD[@]}" volume rm -f "$HOME_VOLUME" "$STATE_VOLUME" >/dev/null

echo "[+] Reset complete. Run './start.sh' to start a fresh lab."
