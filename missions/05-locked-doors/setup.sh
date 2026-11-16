#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/member}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

DOOR1_CODE="$(python3 -I -c "import hashlib; print(hashlib.sha256('${STUDENT_ID}:subtoken:m05_door1_code'.encode()).hexdigest()[:8].upper())")"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p /opt/vault /etc/sudoers.d /usr/local/bin
    chown root:root /opt/vault
    chmod 0755 /opt/vault

    # Only overwrite /opt/vault/flag.txt with sealed message if vault is not currently unsealed
    UNSEALED="$(python3 -I -c "import json, pathlib; p=pathlib.Path('/var/lib/quest/state.json'); print('1' if p.is_file() and json.loads(p.read_text()).get('m05_vault_unsealed') else '0')" 2>/dev/null || echo 0)"
    if [[ "$UNSEALED" != "1" ]]; then
        for vfile in /opt/vault/flag.txt /opt/vault/vault.txt; do
            cat << 'EOF' > "$vfile"
[-] ACCESS DENIED: The vault is still sealed!
[*] Unlock Door 1 and Door 2 using ~/doors/unlock.sh first.
EOF
            chown root:root "$vfile"
            chmod 0600 "$vfile"
        done
    fi

    # Install /usr/local/bin/cat wrapper to enforce the vault seal check when invoked via sudo
    cat << 'EOF' > /usr/local/bin/cat
#!/usr/bin/env bash
set -euo pipefail

IS_VAULT_TARGET=0
for arg in "$@"; do
    if [[ "$arg" == -* ]]; then
        continue
    fi
    REAL_P="$(realpath -m -- "$arg" 2>/dev/null || printf '%s' "$arg")"
    if [[ "$REAL_P" == "/opt/vault/flag.txt" ]] || [[ "$REAL_P" == "/opt/vault/vault.txt" ]]; then
        IS_VAULT_TARGET=1
    elif [[ "$(id -u)" -eq 0 ]]; then
        echo "cat: $arg: Permission denied" >&2
        exit 1
    fi
done

if [[ "$IS_VAULT_TARGET" -eq 1 ]] && [[ "$(id -u)" -eq 0 ]]; then
    exec /usr/local/bin/quest --internal-check-vault
fi

exec /usr/bin/cat "$@"
EOF
    chown root:root /usr/local/bin/cat
    chmod 0755 /usr/local/bin/cat

    TMP_SUDO="$(mktemp)"
    cat << 'EOF' > "$TMP_SUDO"
member ALL=(root) NOPASSWD: /usr/local/bin/cat /opt/vault/flag.txt, /usr/local/bin/cat /opt/vault/vault.txt, /usr/local/bin/cat flag.txt, /usr/local/bin/cat vault.txt, /usr/local/bin/cat ./flag.txt, /usr/local/bin/cat ./vault.txt, /usr/bin/cat /opt/vault/flag.txt, /usr/bin/cat /opt/vault/vault.txt
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

    cat << EOF > "$HOME_DIR/doors/door1.txt"
[+] Door 1 unlocked!
PASSCODE: ${DOOR1_CODE}
EOF
    chmod 0000 "$HOME_DIR/doors/door1.txt"

    cat << 'EOF' > "$HOME_DIR/doors/door2.key"
PRIVATE_DOOR2_KEY_MATERIAL
EOF
    chmod 0777 "$HOME_DIR/doors/door2.key"

    cat << 'EOF' > "$HOME_DIR/doors/unlock.sh"
#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if [[ ! -r "$DIR/door1.txt" ]]; then
    echo "[-] Door 1 (~/doors/door1.txt) is still unreadable! Make it readable first." >&2
    exit 1
fi

MODE2="$(stat -c '%a' "$DIR/door2.key" 2>/dev/null || echo 000)"
if [[ "$MODE2" != "640" ]]; then
    echo "[-] Door 2 (~/doors/door2.key) is still too open (mode: $MODE2)! Change its permissions so they read exactly rw-r----- (640)." >&2
    exit 1
fi

if [[ $# -ge 1 ]]; then
    USER_CODE="$*"
else
    read -r -p "[?] Enter Door 1 PASSCODE: " USER_CODE
fi

exec /usr/local/bin/quest --internal-unseal-vault "$USER_CODE"
EOF
    chmod 0644 "$HOME_DIR/doors/unlock.sh"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
