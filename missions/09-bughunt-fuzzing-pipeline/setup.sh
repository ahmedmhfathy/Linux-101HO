#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
CHALLENGE_DIR="${QUEST_CHALLENGE_DIR:-/challenge}"
RUNAS_BIN="${QUEST_RUNAS_BIN:-/usr/local/lib/quest/runas}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p "$CHALLENGE_DIR"
    if [[ -f "$RUNAS_BIN" ]]; then
        for prog in dirfuzz sqli_runner; do
            cp -f "$RUNAS_BIN" "$CHALLENGE_DIR/$prog"
            chown root:root "$CHALLENGE_DIR/$prog"
            chmod 4755 "$CHALLENGE_DIR/$prog"
            printf '09\n' > "$CHALLENGE_DIR/.mission_$prog"
            chmod 0644 "$CHALLENGE_DIR/.mission_$prog"
        done
    fi
    printf '09\n' > "$CHALLENGE_DIR/.active_mission"
    chmod 0644 "$CHALLENGE_DIR/.active_mission"
elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/recon"
    mkdir -p "$HOME_DIR/recon"

    cat << 'EOF' > "$HOME_DIR/recon/payloads.txt"
admin
guest' AND 1=2 --
' OR '1'='1' -- CYBERUS_SQLI_TRIGGER
" OR ""="
1; SELECT pg_sleep(0)--
EOF
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
