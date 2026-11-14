#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
case "$PHASE" in
    system|home)
        exit 0
        ;;
    *)
        echo "Usage: $0 {system|home}" >&2
        exit 1
        ;;
esac
