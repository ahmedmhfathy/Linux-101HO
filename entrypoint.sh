#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/var/lib/quest"
HOME_DIR="/home/member"
CHALLENGE_DIR="/challenge"

# Ensure container hostname resolves in /etc/hosts (prevents sudo warning with --network none)
CURRENT_HOSTNAME="$(hostname 2>/dev/null || echo cyberus)"
for hname in "$CURRENT_HOSTNAME" cyberus lab; do
    if ! grep -qE "(^|[[:space:]])${hname}([[:space:]]|$)" /etc/hosts 2>/dev/null; then
        printf '127.0.1.1\t%s\n' "$hname" >> /etc/hosts 2>/dev/null || true
    fi
done

mkdir -p "$STATE_DIR" "$CHALLENGE_DIR" "$HOME_DIR" /usr/local/bin
ln -sfn "$HOME_DIR" /home/student 2>/dev/null || true
chown root:root "$STATE_DIR" "$CHALLENGE_DIR"
chmod 0700 "$STATE_DIR"
chmod 0755 "$CHALLENGE_DIR"

# Install `killswitch` command shortcut (wipes progress + resets machine; --soft resets machine only)
cat << 'EOF' > /usr/local/bin/killswitch
#!/usr/bin/env bash
exec /usr/local/bin/quest killswitch "$@"
EOF
chown root:root /usr/local/bin/killswitch
chmod 0755 /usr/local/bin/killswitch

# Install `reset-machine` and `softswitch` shortcuts (resets machine state WITHOUT wiping progress)
for cmd_name in reset-machine softswitch; do
    cat << 'EOF' > "/usr/local/bin/${cmd_name}"
#!/usr/bin/env bash
exec /usr/local/bin/quest reset-machine "$@"
EOF
    chown root:root "/usr/local/bin/${cmd_name}"
    chmod 0755 "/usr/local/bin/${cmd_name}"
done

# Install `man` wrapper so `man /challenge/run` (or `man ./run`) opens `man run`
# instead of treating the ELF binary `/challenge/run` as a raw troff file!
cat << 'EOF' > /usr/local/bin/man
#!/usr/bin/env bash
ARGS=()
for arg in "$@"; do
    case "$arg" in
        /challenge/*|./run|*/challenge/run)
            ARGS+=("${arg##*/}")
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done
exec /usr/bin/man "${ARGS[@]}"
EOF
chown root:root /usr/local/bin/man
chmod 0755 /usr/local/bin/man

# Populate /home/member from /etc/skel if empty
if [[ ! -f "$HOME_DIR/.bashrc" ]] && [[ -d /etc/skel ]]; then
    cp -rn /etc/skel/. "$HOME_DIR/" || true
fi

touch "$HOME_DIR/.bashrc"

# Ensure .bashrc has the latest Cyberus Linux Quest block (including history-clearing wrappers)
if grep -q "# >>> CYBERUS-LINUX-QUEST >>>" "$HOME_DIR/.bashrc" 2>/dev/null; then
    sed -i '/# >>> CYBERUS-LINUX-QUEST >>>/,/# <<< CYBERUS-LINUX-QUEST <<</d' "$HOME_DIR/.bashrc" 2>/dev/null || true
fi

cat << 'EOF' >> "$HOME_DIR/.bashrc"

# >>> CYBERUS-LINUX-QUEST >>>
export LANG=C.UTF-8
export TERM="${TERM:-xterm-256color}"
export PS1='\[\033[01;32m\]member@cyberus\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

killswitch() {
    /usr/local/bin/quest killswitch "$@"
    local rc=$?
    rm -f ~/.bash_history ~/.lesshst 2>/dev/null || true
    history -c 2>/dev/null || true
    history -w 2>/dev/null || true
    return $rc
}

reset-machine() {
    /usr/local/bin/quest reset-machine "$@"
    local rc=$?
    rm -f ~/.bash_history ~/.lesshst 2>/dev/null || true
    history -c 2>/dev/null || true
    history -w 2>/dev/null || true
    return $rc
}

softswitch() {
    reset-machine "$@"
}

quest() {
    /usr/local/bin/quest "$@"
    local rc=$?
    if [[ "${1:-}" == "killswitch" ]] || [[ "${1:-}" == "reset-machine" ]] || [[ "${1:-}" == "softswitch" ]] || [[ "${*:-}" == *"--all"* ]] || [[ "${*:-}" == *"--machine"* ]]; then
        rm -f ~/.bash_history ~/.lesshst 2>/dev/null || true
        history -c 2>/dev/null || true
        history -w 2>/dev/null || true
    fi
    return $rc
}

if [[ $- == *i* ]]; then
    echo -e "\033[1;36m============================================================\033[0m"
    echo -e "\033[1;36m   Welcome to CYBERUS LINUX QUEST\033[0m"
    echo -e "\033[0;37m   Type \033[1;33mquest\033[0;37m to view your current mission.\033[0m"
    echo -e "\033[0;37m   Type \033[1;33mquest list\033[0;37m to see all missions, or \033[1;33mquest hint\033[0;37m for help.\033[0m"
    echo -e "\033[1;36m============================================================\033[0m"
fi
# <<< CYBERUS-LINUX-QUEST <<<
EOF

chown member:bug "$HOME_DIR" "$HOME_DIR/.bashrc"
if [[ -f "$HOME_DIR/.profile" ]]; then
    chown member:bug "$HOME_DIR/.profile"
fi

# Initialize quest state & replay system phase for unlocked missions
/usr/bin/python3 -I /opt/quest/engine/cli.py --internal-init

if [[ $# -eq 0 ]] || [[ "${1:-}" == "login-shell" ]]; then
    exec runuser -l member
else
    exec "$@"
fi
