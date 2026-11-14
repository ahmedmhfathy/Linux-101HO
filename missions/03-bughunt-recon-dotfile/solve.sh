#!/usr/bin/env bash
set -euo pipefail

ENDPOINT_LINE="$(grep 'INTERNAL_ENDPOINT=' ~/webapp_recon/api/v2/.env.bak)"
STAGING_LINE="$(grep -oE 'STAGING_TOKEN=STG-[A-F0-9]+' ~/webapp_recon/logs/http_response.txt)"

sed -i 's/DEBUG=true/DEBUG=false/' ~/webapp_recon/config.ini

mkdir -p ~/bounty_report
cat << EOF > ~/bounty_report/finding.txt
$ENDPOINT_LINE
$STAGING_LINE
EOF

OUT="$(quest check 03)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
