#!/usr/bin/env bash
# ==============================================================================
# build-release.sh - Build amd64 & arm64 offline tarballs + SHA256SUMS
# ==============================================================================
set -euo pipefail

readonly VERSION="1.0"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DIST_DIR="${SCRIPT_DIR}/dist/linux-quest-v${VERSION}"

usage() {
    cat << EOF
Usage: ./build-release.sh [--arch amd64|arm64|all]

Builds Cyberus Linux Quest image(s), runs the automated test harness, and packages
offline release archives into dist/linux-quest-v${VERSION}/.
EOF
}

TARGET_ARCH="all"
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
elif [[ "${1:-}" == "--arch" ]] && [[ -n "${2:-}" ]]; then
    TARGET_ARCH="$2"
fi

mkdir -p "$DIST_DIR"

build_one() {
    local arch="$1"
    local tag="linux-quest:${VERSION}-${arch}"
    local tar_out="${DIST_DIR}/linux-quest-v${VERSION}-${arch}.tar"

    echo "[*] Building ${tag} for linux/${arch}..."
    docker buildx build \
        --platform "linux/${arch}" \
        --target runtime \
        --load \
        -t "$tag" \
        -t "linux-quest:${VERSION}" \
        "$SCRIPT_DIR"

    echo "[*] Running automated test harness inside ${tag}..."
    docker run --rm --network none "$tag" /opt/quest/tests/run_all.sh

    echo "[*] Saving offline image archive ${tar_out}..."
    docker save -o "$tar_out" "$tag" "linux-quest:${VERSION}"
}

case "$TARGET_ARCH" in
    amd64)
        build_one "amd64"
        ;;
    arm64)
        build_one "arm64"
        ;;
    all)
        build_one "amd64"
        build_one "arm64"
        ;;
    *)
        echo "Invalid --arch: $TARGET_ARCH" >&2
        exit 1
        ;;
esac

cp -f "${SCRIPT_DIR}/setup-docker.sh" \
      "${SCRIPT_DIR}/start.sh" \
      "${SCRIPT_DIR}/reset.sh" \
      "${SCRIPT_DIR}/docker-compose.yml" \
      "${SCRIPT_DIR}/README_STUDENTS.md" \
      "$DIST_DIR/"

chmod +x "${DIST_DIR}/setup-docker.sh" "${DIST_DIR}/start.sh" "${DIST_DIR}/reset.sh"

(
    cd "$DIST_DIR"
    sha256sum ./*.tar setup-docker.sh start.sh reset.sh > SHA256SUMS
)

echo "[+] Release package ready at: ${DIST_DIR}"
