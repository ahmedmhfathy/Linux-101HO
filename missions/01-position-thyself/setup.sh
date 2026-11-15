#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
CHALLENGE_DIR="${QUEST_CHALLENGE_DIR:-/challenge}"
RUNAS_BIN="${QUEST_RUNAS_BIN:-/usr/local/lib/quest/runas}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p "$CHALLENGE_DIR" /var/log
    if [[ -f "$RUNAS_BIN" ]]; then
        cp -f "$RUNAS_BIN" "$CHALLENGE_DIR/run"
        chown root:root "$CHALLENGE_DIR/run"
        chmod 4755 "$CHALLENGE_DIR/run"
    fi

    # Install decoy `run` inside /var/log to catch students running `./run` from /var/log
    cat << 'EOF' > /var/log/run
#!/usr/bin/env bash
echo "Wrong path yasta I TOLD YOU TO USE ABSOLUTE PATHS YA3AM ENTA" >&2
exit 1
EOF
    chown root:root /var/log/run
    chmod 0755 /var/log/run

    printf '01\n' > "$CHALLENGE_DIR/.mission_run"
    printf '01\n' > "$CHALLENGE_DIR/.active_mission"
    chmod 0644 "$CHALLENGE_DIR/.mission_run" "$CHALLENGE_DIR/.active_mission"
elif [[ "$PHASE" == "home" ]]; then
    exit 0
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
