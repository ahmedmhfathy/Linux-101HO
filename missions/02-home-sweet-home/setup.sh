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
        mkdir -p /usr/share/man/man1 /usr/local/share/man/man1
        cp -f "$MISSION_DIR/man/run.1" /usr/share/man/man1/run.1
        cp -f "$MISSION_DIR/man/run.1" /usr/local/share/man/man1/run.1
        chmod 0644 /usr/share/man/man1/run.1 /usr/local/share/man/man1/run.1
        mandb -q >/dev/null 2>&1 || true
    fi
    printf '02\n' > "$CHALLENGE_DIR/.mission_run"
    printf '02\n' > "$CHALLENGE_DIR/.active_mission"
    chmod 0644 "$CHALLENGE_DIR/.mission_run" "$CHALLENGE_DIR/.active_mission"
elif [[ "$PHASE" == "home" ]]; then
    find "$HOME_DIR" -mindepth 2 -maxdepth 3 -name ".code.txt" -exec rm -f {} + 2>/dev/null || true
    rm -f -- "$HOME_DIR/.code.txt"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
