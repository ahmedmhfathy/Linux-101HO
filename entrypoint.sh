#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/var/lib/quest"
HOME_DIR="/home/student"
CHALLENGE_DIR="/challenge"

# Ensure container hostname resolves in /etc/hosts (prevents sudo warning with --network none)
CURRENT_HOSTNAME="$(hostname 2>/dev/null || echo lab)"
if ! grep -qE "(^|[[:space:]])${CURRENT_HOSTNAME}([[:space:]]|$)" /etc/hosts 2>/dev/null; then
    printf '127.0.1.1\t%s\n' "$CURRENT_HOSTNAME" >> /etc/hosts 2>/dev/null || true
fi

mkdir -p "$STATE_DIR" "$CHALLENGE_DIR" "$HOME_DIR" /usr/local/bin
chown root:root "$STATE_DIR" "$CHALLENGE_DIR"
chmod 0700 "$STATE_DIR"
chmod 0755 "$CHALLENGE_DIR"

# Install `killswitch` command shortcut
cat << 'EOF' > /usr/local/bin/killswitch
#!/usr/bin/env bash
exec /usr/local/bin/quest killswitch "$@"
EOF
chown root:root /usr/local/bin/killswitch
chmod 0755 /usr/local/bin/killswitch

# Populate /home/student from /etc/skel if empty
if [[ ! -f "$HOME_DIR/.bashrc" ]] && [[ -d /etc/skel ]]; then
    cp -rn /etc/skel/. "$HOME_DIR/" || true
fi

touch "$HOME_DIR/.bashrc"

# Add managed Cyberus Linux Quest block to .bashrc idempotently
if ! grep -q "# >>> CYBERUS-LINUX-QUEST >>>" "$HOME_DIR/.bashrc" 2>/dev/null; then
    cat << 'EOF' >> "$HOME_DIR/.bashrc"

# >>> CYBERUS-LINUX-QUEST >>>
export LANG=C.UTF-8
export TERM="${TERM:-xterm-256color}"
export PS1='\[\033[01;32m\]student@lab\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
if [[ $- == *i* ]]; then
    echo -e "\033[1;36m============================================================\033[0m"
    echo -e "\033[1;36m   Welcome to CYBERUS LINUX QUEST (Bug Hunting Activity)\033[0m"
    echo -e "\033[0;37m   Type \033[1;33mquest\033[0;37m to view your current mission.\033[0m"
    echo -e "\033[0;37m   Type \033[1;33mquest list\033[0;37m to see all missions, or \033[1;33mquest hint\033[0;37m for help.\033[0m"
    echo -e "\033[1;36m============================================================\033[0m"
fi
# <<< CYBERUS-LINUX-QUEST <<<
EOF
fi

chown student:student "$HOME_DIR" "$HOME_DIR/.bashrc"
if [[ -f "$HOME_DIR/.profile" ]]; then
    chown student:student "$HOME_DIR/.profile"
fi

# Initialize quest state & replay system phase for unlocked missions
/usr/bin/python3 -I /opt/quest/engine/cli.py --internal-init

if [[ $# -eq 0 ]] || [[ "${1:-}" == "login-shell" ]]; then
    exec runuser -l student
else
    exec "$@"
fi
