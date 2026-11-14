#!/usr/bin/env bash
set -euo pipefail

/challenge/run ~/stage_a.txt
PHRASE="$(grep -oE 'CYBERUS-NOTE-[A-F0-9]+' ~/stage_a.txt | head -n 1)"
mkdir -p ~/notes
printf '%s\n' "$PHRASE" > ~/notes/plan.txt
OUT="$(quest check 02)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
