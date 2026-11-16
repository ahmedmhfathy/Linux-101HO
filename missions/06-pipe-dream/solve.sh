#!/usr/bin/env bash
set -euo pipefail

PIPE_OUT="$(/challenge/stage1 | /challenge/stage2 | /challenge/stage3)"
PASSPHRASE="$(printf '%s\n' "$PIPE_OUT" | grep -oE 'CYBERUS-PIPE-PASSPHRASE-[A-F0-9]+' | head -n 1)"
FINAL_OUT="$(printf '%s\n' "$PASSPHRASE" | /challenge/checker)"
FLAG="$(printf '%s\n' "$FINAL_OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
