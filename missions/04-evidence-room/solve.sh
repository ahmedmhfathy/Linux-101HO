#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/evidence
EVD_FILE="$(find ~/archive -type f -name "*.evd" -exec grep -l "SIGNATURE:" {} + | head -n 1)"
cp "$EVD_FILE" ~/evidence/case.txt
rm -rf ~/archive/decoy_trap
sort -n ~/archive/scores.txt | tail -n 1 | awk '{print $2}' > ~/evidence/top.txt

OUT="$(quest check 04)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
