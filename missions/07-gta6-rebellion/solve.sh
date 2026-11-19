#!/usr/bin/env bash
set -euo pipefail

chmod u+rwx ~/gta6_leak/digital_only_edition
mv ~/gta6_leak/digital_only_edition ~/gta6_leak/physical_disc_edition
echo "a3da2_sherket_nvidia_microntech_sony_rockstar" >> ~/gta6_leak/physical_disc_edition/enemies.txt
TOFO_FILE="$(find ~/gta6_leak/physical_disc_edition -name "*.tofo" | head -n 1)"
cat "$TOFO_FILE" >/dev/null

OUT="$(/challenge/gta6_patcher --burn-disc 2>&1 | /challenge/disc_burner)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
