#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

VAULT_TOK="$(python3 -I -c "import hashlib; print(hashlib.sha256('${STUDENT_ID}:subtoken:m05_vault'.encode()).hexdigest()[:12].upper())")"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p /opt/vault /etc/sudoers.d
    chown root:root /opt/vault
    chmod 0755 /opt/vault

    cat << EOF > /opt/vault/flag.txt
=== ROOT VAULT ===
VAULT_SECRET=VAULT-${VAULT_TOK}
Copy the VAULT_SECRET line above into ~/doors/vault.txt and run: quest check 05
EOF
    chown root:root /opt/vault/flag.txt
    chmod 0600 /opt/vault/flag.txt

    TMP_SUDO="$(mktemp)"
    cat << 'EOF' > "$TMP_SUDO"
student ALL=(root) NOPASSWD: /usr/bin/cat /opt/vault/flag.txt
EOF
    chmod 0440 "$TMP_SUDO"
    if command -v visudo >/dev/null 2>&1; then
        visudo -cf "$TMP_SUDO" >/dev/null
    fi
    mv -f "$TMP_SUDO" /etc/sudoers.d/quest-vault
    chown root:root /etc/sudoers.d/quest-vault
    chmod 0440 /etc/sudoers.d/quest-vault

elif [[ "$PHASE" == "home" ]]; then
    if [[ -d "$HOME_DIR/doors" ]]; then
        chmod -R u+rwX "$HOME_DIR/doors" 2>/dev/null || true
    fi
    rm -rf -- "$HOME_DIR/doors"
    mkdir -p "$HOME_DIR/doors"

    cat << 'EOF' > "$HOME_DIR/doors/door1.txt"
Door 1 opened! Keep this file readable (u+r) and move to Door 2 (unlock.sh).
EOF
    chmod 0000 "$HOME_DIR/doors/door1.txt"

    cat << 'EOF' > "$HOME_DIR/doors/unlock.sh"
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
echo "DOOR2_UNLOCKED" > "$DIR/.door2_unlocked"
echo "[+] Door 2 unlocked! Now set door3.key to mode 640 and check sudo -l for the vault."
EOF
    chmod 0644 "$HOME_DIR/doors/unlock.sh"

    cat << 'EOF' > "$HOME_DIR/doors/door3.key"
PRIVATE_DOOR3_KEY_MATERIAL
EOF
    chmod 0777 "$HOME_DIR/doors/door3.key"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
