#!/usr/bin/env bash
# ==============================================================================
# setup-docker.sh - One-time Docker Engine installer for Kali / Debian / Ubuntu
# ==============================================================================
set -euo pipefail

usage() {
    cat << 'EOF'
Usage: ./setup-docker.sh [--help]

Installs Docker Engine (docker.io) on Debian/Ubuntu/Kali Linux systems and starts
the Docker service. Run this script ONCE while connected to the internet before
the Cyberus Linux Quest session.
EOF
}

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

echo "[*] Checking for existing Docker installation..."
if command -v docker >/dev/null 2>&1; then
    echo "[+] Docker CLI is already installed: $(docker --version)"
else
    echo "[*] Installing docker.io via apt..."
    sudo apt-get update
    sudo apt-get install -y docker.io
fi

echo "[*] Ensuring Docker daemon is enabled and running..."
if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    sudo systemctl enable --now docker
else
    sudo service docker start || true
fi

echo ""
echo "[!] SECURITY NOTE:"
echo "    Adding your user to the 'docker' group allows running Docker without sudo,"
echo "    which is equivalent to root access on the host machine."
read -r -p "Add current user ($USER) to the 'docker' group? [y/N]: " ans
if [[ "${ans,,}" == "y" ]] || [[ "${ans,,}" == "yes" ]]; then
    sudo usermod -aG docker "$USER"
    echo "[+] Added '$USER' to the 'docker' group. Log out and back in (or run 'newgrp docker') for it to take effect."
else
    echo "[*] Skipped adding '$USER' to the 'docker' group. './start.sh' will automatically use 'sudo docker' when needed."
fi

echo "[+] Setup complete! Next, run: ./start.sh"
