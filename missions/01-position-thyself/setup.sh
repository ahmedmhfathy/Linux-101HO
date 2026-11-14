#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
CHALLENGE_DIR="${QUEST_CHALLENGE_DIR:-/challenge}"
RUNAS_BIN="${QUEST_RUNAS_BIN:-/usr/local/lib/quest/runas}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p "$CHALLENGE_DIR" /var/log /etc /usr/share/doc /usr/include /var/backups
    if [[ -f "$RUNAS_BIN" ]]; then
        cp -f "$RUNAS_BIN" "$CHALLENGE_DIR/run"
        chown root:root "$CHALLENGE_DIR/run"
        chmod 4755 "$CHALLENGE_DIR/run"
    fi
    printf '01\n' > "$CHALLENGE_DIR/.mission_run"
    printf '01\n' > "$CHALLENGE_DIR/.active_mission"
    chmod 0644 "$CHALLENGE_DIR/.mission_run" "$CHALLENGE_DIR/.active_mission"
elif [[ "$PHASE" == "home" ]]; then
    exit 0
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
