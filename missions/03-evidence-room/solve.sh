#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/evidence
EVD_FILE="$(grep -rnwl --include="*.evd" "a3da2_sherket_nvidia_microntech" ~/archive | head -n 1)"
mv "$EVD_FILE" ~/evidence/
rm -rf ~/archive/decoy_trap
sort -n ~/archive/scores.txt | tail -n 1 | awk '{print $2}' > ~/evidence/top_researcher.txt

OUT="$(quest check 03)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
