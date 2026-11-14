#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/quarantine
SEC_LINE="$(grep -rh "CYBERUS_SECRET_KEY=" ~/target_app | head -n 1)"
WEBSHELL="$(find ~/target_app -name "*.shell.php" | head -n 1)"
rm -f "$WEBSHELL"

SQL_BAK="$(find ~/target_app -name "*.sql.bak" | head -n 1)"
mv "$SQL_BAK" ~/quarantine/

chmod 600 ~/target_app/config/deploy_key

TOP_VULN="$(sort -n ~/target_app/vulns.txt | tail -n 1)"
cat << EOF > ~/quarantine/triage_report.txt
$SEC_LINE
$TOP_VULN
EOF

OUT="$(sudo /usr/local/bin/vuln-verify)"
FLAG="$(printf '%s\n' "$OUT" | grep -oE 'CYBERUS\{[^}]+\}' | head -n 1)"
quest submit "$FLAG"
