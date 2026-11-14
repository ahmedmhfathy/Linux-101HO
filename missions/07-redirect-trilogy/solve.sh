#!/usr/bin/env bash
set -euo pipefail

/challenge/run > ~/myflag 2>/dev/null
/challenge/run --part1 > ~/twopart.txt 2>/dev/null
/challenge/run --part2 >> ~/twopart.txt 2>/dev/null
/challenge/run2 2> ~/stderr_flag.txt > /dev/null

OUT="$(quest check 07)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
