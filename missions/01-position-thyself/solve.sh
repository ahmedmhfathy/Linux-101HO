#!/usr/bin/env bash
set -euo pipefail

# Discover required directory from error message, cd there, and run /challenge/run
ERR_OUT="$(/challenge/run 2>&1 || true)"
REQ_DIR="$(printf '%s\n' "$ERR_OUT" | grep -oE '(/var/log|/etc|/usr/share/doc|/usr/include|/var/backups)' | head -n 1)"
cd "$REQ_DIR"
OUT="$(/challenge/run)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
