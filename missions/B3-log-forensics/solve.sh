#!/usr/bin/env bash
set -euo pipefail

TOP_IP="$(grep " 401 " ~/forensics/access.log | cut -d' ' -f1 | sort | uniq -c | sort -rn | head -n 1 | awk '{print $2}')"
printf '%s\n' "$TOP_IP" > ~/forensics/attacker_ip.txt

OUT="$(quest check B3)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
