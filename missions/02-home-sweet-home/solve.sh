#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/myroom
cd ~/myroom
/challenge/run --please
sed -i 's/CYBERUS-NOTE-/Tofa7aElSafa7a-NOTE-/I' ~/myroom/.code.txt
OUT="$(quest check 02)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
