#!/usr/bin/env bash
set -euo pipefail

chmod u+r ~/doors/door1.txt
CODE="$(awk -F': ' '/^PASSCODE:/ {print $2}' ~/doors/door1.txt)"
chmod 640 ~/doors/door2.key
chmod +x ~/doors/unlock.sh
printf '%s\n' "$CODE" | ~/doors/unlock.sh >/dev/null

OUT="$(sudo cat /opt/vault/flag.txt)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
