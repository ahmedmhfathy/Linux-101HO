#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
CHALLENGE_DIR="${QUEST_CHALLENGE_DIR:-/challenge}"
RUNAS_BIN="${QUEST_RUNAS_BIN:-/usr/local/lib/quest/runas}"
MISSION_DIR="${QUEST_MISSION_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p "$CHALLENGE_DIR" /usr/local/share/man/man1
    if [[ -f "$RUNAS_BIN" ]]; then
        cp -f "$RUNAS_BIN" "$CHALLENGE_DIR/run"
        chown root:root "$CHALLENGE_DIR/run"
        chmod 4755 "$CHALLENGE_DIR/run"
    fi
    if [[ -f "$MISSION_DIR/man/run.1" ]]; then
        cp -f "$MISSION_DIR/man/run.1" /usr/local/share/man/man1/run.1
        chmod 0644 /usr/local/share/man/man1/run.1
        mandb -q /usr/local/share/man 2>/dev/null || true
    fi
    printf '02\n' > "$CHALLENGE_DIR/.mission_run"
    printf '02\n' > "$CHALLENGE_DIR/.active_mission"
    chmod 0644 "$CHALLENGE_DIR/.mission_run" "$CHALLENGE_DIR/.active_mission"
elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/notes" "$HOME_DIR/.stage02_a_done" "$HOME_DIR/stage_a.txt"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
