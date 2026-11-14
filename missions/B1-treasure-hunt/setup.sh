#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"
FLAG="${QUEST_FLAG:-CYBERUS{B1_placeholder}}"

if [[ "$PHASE" == "system" ]]; then
    exit 0
elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/treasure"
    mkdir -p "$HOME_DIR/treasure/north/cavern/.secret_chamber/vault" \
             "$HOME_DIR/treasure/south/ruins/.forgotten" \
             "$HOME_DIR/treasure/east/docks"

    echo "Nothing here but old maps." > "$HOME_DIR/treasure/north/map.txt"
    echo "Keep digging deeper! Try ls -a or tree -a." > "$HOME_DIR/treasure/south/ruins/.clue"

    {
        for i in $(seq 1 641); do
            echo "[SCROLL Line $i] The ancient guardians patrolled the gate without incident."
        done
        echo "[SCROLL Line 642] TREASURE UNLOCKED: ${FLAG} (Submit with: quest submit ${FLAG})"
        for i in $(seq 643 1000); do
            echo "[SCROLL Line $i] The ancient guardians patrolled the gate without incident."
        done
    } > "$HOME_DIR/treasure/north/cavern/.secret_chamber/vault/.ancient.log"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
