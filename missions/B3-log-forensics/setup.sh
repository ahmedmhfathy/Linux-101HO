#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

if [[ "$PHASE" == "system" ]]; then
    exit 0
elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/forensics"
    mkdir -p "$HOME_DIR/forensics"

    # Generate a deterministic 10,000-line access.log in Python
    python3 -I - "$HOME_DIR/forensics/access.log" "$STUDENT_ID" << 'PYEOF'
import hashlib
import pathlib
import random
import sys

log_path = pathlib.Path(sys.argv[1])
student_id = sys.argv[2]

h = hashlib.sha256(f"{student_id}:subtoken:mB3_ip".encode()).hexdigest()
octet3 = (int(h[:4], 16) % 200) + 10
octet4 = (int(h[4:8], 16) % 200) + 20
attacker_ip = f"198.51.{octet3}.{octet4}"

rng = random.Random(int(h[:16], 16))
benign_ips = [
    "203.0.113.12",
    "203.0.113.45",
    "192.0.2.88",
    "192.0.2.104",
    "198.51.100.7",
    "198.51.100.23",
    "10.20.30.40",
    "172.16.0.19",
]
paths = ["/login", "/api/v1/token", "/index.html", "/static/app.js", "/profile", "/robots.txt"]

lines = []
# 450 failed logins (401) from attacker_ip
for i in range(450):
    lines.append(
        f'{attacker_ip} - - [14/Nov/2026:10:{i % 60:02d}:{i % 59:02d} +0000] "POST /login HTTP/1.1" 401 312'
    )

# 9,550 mixed lines from other IPs (at most ~80 401s per benign IP)
for i in range(9550):
    ip = rng.choice(benign_ips)
    path = rng.choice(paths)
    status = 401 if (i % 25 == 0) else rng.choice([200, 200, 200, 302, 404])
    method = "POST" if path == "/login" else "GET"
    lines.append(
        f'{ip} - - [14/Nov/2026:11:{i % 60:02d}:{(i * 7) % 60:02d} +0000] "{method} {path} HTTP/1.1" {status} 512'
    )

rng.shuffle(lines)
log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PYEOF
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
