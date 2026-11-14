#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
FLAG="${QUEST_FLAG:-CYBERUS{B2_placeholder}}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p /var/log /root /etc/sudoers.d
    cat << 'EOF' > /var/log/quest-demo.log
==========================================================
Cyberus System Audit Daemon Log (/var/log/quest-demo.log)
==========================================================
[INFO] Audit service started.
[INFO] Note to admins: Do NOT grant sudo access to interactive pagers like less!
[INFO] Tip for Mission B2: Inside less, typing !sh spawns a shell as the effective user (root).
[INFO] Target file: /root/b2_flag.txt
EOF
    for i in $(seq 1 40); do
        echo "[AUDIT $i] Routine integrity check passed." >> /var/log/quest-demo.log
    done
    chown root:root /var/log/quest-demo.log
    chmod 0644 /var/log/quest-demo.log

    cat << EOF > /root/b2_flag.txt
Congratulations on escaping less via GTFOBins!
Flag: ${FLAG}
EOF
    chown root:root /root/b2_flag.txt
    chmod 0600 /root/b2_flag.txt

    TMP_SUDO="$(mktemp)"
    cat << 'EOF' > "$TMP_SUDO"
student ALL=(root) NOPASSWD: /usr/bin/less /var/log/quest-demo.log
EOF
    chmod 0440 "$TMP_SUDO"
    if command -v visudo >/dev/null 2>&1; then
        visudo -cf "$TMP_SUDO" >/dev/null
    fi
    mv -f "$TMP_SUDO" /etc/sudoers.d/quest-b2-gtfo
    chown root:root /etc/sudoers.d/quest-b2-gtfo
    chmod 0440 /etc/sudoers.d/quest-b2-gtfo

elif [[ "$PHASE" == "home" ]]; then
    exit 0
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
