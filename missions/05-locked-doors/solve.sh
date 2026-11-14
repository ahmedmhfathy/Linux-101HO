#!/usr/bin/env bash
set -euo pipefail

chmod u+r ~/doors/door1.txt
chmod +x ~/doors/unlock.sh
~/doors/unlock.sh
chmod 640 ~/doors/door3.key
sudo /usr/bin/cat /opt/vault/flag.txt > ~/doors/vault.txt

OUT="$(quest check 05)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
