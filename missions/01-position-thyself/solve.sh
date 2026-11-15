#!/usr/bin/env bash
set -euo pipefail

cd /var/log
OUT="$(/challenge/run)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
