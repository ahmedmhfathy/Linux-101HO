#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/student}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

if [[ "$PHASE" == "system" ]]; then
    exit 0
elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/webapp_recon" "$HOME_DIR/bounty_report"
    mkdir -p "$HOME_DIR/webapp_recon/public/assets" \
             "$HOME_DIR/webapp_recon/api/v1" \
             "$HOME_DIR/webapp_recon/api/v2" \
             "$HOME_DIR/webapp_recon/logs"

    # Generate deterministic tokens matching engine.core.deterministic_token
    ENDP_TOK="$(python3 -I -c "import hashlib; print(hashlib.sha256('${STUDENT_ID}:subtoken:m03_endpoint'.encode()).hexdigest()[:10])")"
    STG_TOK="$(python3 -I -c "import hashlib; print(hashlib.sha256('${STUDENT_ID}:subtoken:m03_staging'.encode()).hexdigest()[:10].upper())")"

    cat << 'EOF' > "$HOME_DIR/webapp_recon/README.txt"
Cyberus Target WebApp Snapshot
==============================
Directories:
  public/   - static web assets
  api/      - backend REST API modules
  logs/     - captured HTTP response traffic
  config.ini - deployment settings
EOF

    cat << 'EOF' > "$HOME_DIR/webapp_recon/config.ini"
[server]
HOST=0.0.0.0
PORT=8080
DEBUG=true
ENVIRONMENT=production
EOF

    cat << 'EOF' > "$HOME_DIR/webapp_recon/public/index.html"
<!DOCTYPE html>
<html>
<head><title>Cyberus Portal</title></head>
<body><h1>Welcome to the Cyberus Portal</h1></body>
</html>
EOF

    cat << 'EOF' > "$HOME_DIR/webapp_recon/api/v1/status.txt"
API v1 deprecated. Check v2 directory.
EOF

    cat << EOF > "$HOME_DIR/webapp_recon/api/v2/.env.bak"
# Backup environment configuration - DO NOT COMMIT TO GIT
DB_HOST=10.10.20.15
INTERNAL_ENDPOINT=/api/v2/debug-console-${ENDP_TOK}
CACHE_TTL=300
EOF

    # Build a 600-line HTTP response capture with the staging token on line 342
    {
        echo "HTTP/1.1 200 OK"
        echo "Server: nginx/1.24.0"
        echo "Content-Type: text/html; charset=UTF-8"
        echo "X-Frame-Options: DENY"
        echo ""
        echo "<!DOCTYPE html>"
        echo "<html lang=\"en\">"
        echo "<head><title>Cyberus Dashboard</title></head>"
        echo "<body>"
        for i in $(seq 10 341); do
            echo "  <div class=\"row\" data-line=\"$i\"><span>Telemetry record #$i: status=nominal</span></div>"
        done
        echo "  <!-- TODO(dev): remove before prod! STAGING_TOKEN=STG-${STG_TOK} -->"
        for i in $(seq 343 598); do
            echo "  <div class=\"row\" data-line=\"$i\"><span>Telemetry record #$i: status=nominal</span></div>"
        done
        echo "</body>"
        echo "</html>"
    } > "$HOME_DIR/webapp_recon/logs/http_response.txt"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
