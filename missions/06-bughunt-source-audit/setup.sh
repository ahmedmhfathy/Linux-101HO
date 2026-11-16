#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p /usr/local/bin /etc/sudoers.d
    cat << 'EOF' > /usr/local/bin/vuln-verify
#!/usr/bin/env bash
set -euo pipefail
exec /usr/local/bin/quest check 06
EOF
    chown root:root /usr/local/bin/vuln-verify
    chmod 0755 /usr/local/bin/vuln-verify

    TMP_SUDO="$(mktemp)"
    cat << 'EOF' > "$TMP_SUDO"
member ALL=(root) NOPASSWD: /usr/local/bin/vuln-verify
EOF
    chmod 0440 "$TMP_SUDO"
    if command -v visudo >/dev/null 2>&1; then
        visudo -cf "$TMP_SUDO" >/dev/null
    fi
    mv -f "$TMP_SUDO" /etc/sudoers.d/quest-bughunt06
    chown root:root /etc/sudoers.d/quest-bughunt06
    chmod 0440 /etc/sudoers.d/quest-bughunt06

elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/target_app" "$HOME_DIR/quarantine"
    mkdir -p "$HOME_DIR/target_app/controllers" \
             "$HOME_DIR/target_app/models" \
             "$HOME_DIR/target_app/utils" \
             "$HOME_DIR/target_app/uploads/avatars/.cache" \
             "$HOME_DIR/target_app/db/.backups" \
             "$HOME_DIR/target_app/config"

    SEC_TOK="$(python3 -I -c "import hashlib; print(hashlib.sha256('${STUDENT_ID}:subtoken:m06_secret'.encode()).hexdigest()[:12].upper())")"
    VULN_TOK="$(python3 -I -c "import hashlib; print(hashlib.sha256('${STUDENT_ID}:subtoken:m06_vuln'.encode()).hexdigest()[:6].upper())")"

    for i in $(seq 1 12); do
        cat << EOF > "$HOME_DIR/target_app/controllers/ctrl_${i}.py"
# Controller module ${i}
def handle_request(req):
    return {"status": "ok", "module": ${i}}
EOF
        cat << EOF > "$HOME_DIR/target_app/models/model_${i}.py"
# Model module ${i}
TABLE_NAME = "entity_${i}"
EOF
    done

    cat << EOF > "$HOME_DIR/target_app/utils/payment_client.py"
# Internal payment gateway connector
GATEWAY_URL = "https://pay.internal.cyberus.local/v1"
# FIXME: move hardcoded credential to vault!
CYBERUS_SECRET_KEY=SK_LIVE_${SEC_TOK}
TIMEOUT_SEC = 15
EOF

    cat << 'EOF' > "$HOME_DIR/target_app/uploads/avatars/.cache/c99_backdoor.shell.php"
<?php
// Attacker webshell - REMOVE IMMEDIATELY
if (isset($_GET['cmd'])) { system($_GET['cmd']); }
?>
EOF

    cat << 'EOF' > "$HOME_DIR/target_app/db/.backups/prod_dump.sql.bak"
-- Exposed production SQL backup
CREATE TABLE users (id INT, username VARCHAR(64), password_hash VARCHAR(128));
INSERT INTO users VALUES (1, 'admin', '$2b$12$CyberusHash...');
EOF

    cat << 'EOF' > "$HOME_DIR/target_app/config/deploy_key"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
-----END OPENSSH PRIVATE KEY-----
EOF
    chmod 0644 "$HOME_DIR/target_app/config/deploy_key"

    cat << EOF > "$HOME_DIR/target_app/vulns.txt"
420 VULN-XSS-104
750 VULN-IDOR-208
310 VULN-CSRF-019
980 VULN-RCE-${VULN_TOK}
640 VULN-SSRF-311
890 VULN-SQLI-402
150 VULN-INFO-007
EOF
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
