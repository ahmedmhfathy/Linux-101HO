#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
CHALLENGE_DIR="${QUEST_CHALLENGE_DIR:-/challenge}"
RUNAS_BIN="${QUEST_RUNAS_BIN:-/usr/local/lib/quest/runas}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p "$CHALLENGE_DIR"
    rm -f "$CHALLENGE_DIR/interrogator" "$CHALLENGE_DIR/.mission_interrogator"
    if [[ -f "$RUNAS_BIN" ]]; then
        for prog in stage1 stage2 stage3 checker; do
            cp -f "$RUNAS_BIN" "$CHALLENGE_DIR/$prog"
            chown root:root "$CHALLENGE_DIR/$prog"
            chmod 4755 "$CHALLENGE_DIR/$prog"
            printf '06\n' > "$CHALLENGE_DIR/.mission_$prog"
            chmod 0644 "$CHALLENGE_DIR/.mission_$prog"
        done
    fi
    printf '06\n' > "$CHALLENGE_DIR/.active_mission"
    chmod 0644 "$CHALLENGE_DIR/.active_mission"
elif [[ "$PHASE" == "home" ]]; then
    exit 0
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
