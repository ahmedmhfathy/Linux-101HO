#!/usr/bin/env bash
set -euo pipefail

/challenge/dirfuzz 2>/dev/null | grep "200 OK" | sort > ~/recon/live_endpoints.txt
/challenge/sqli_runner < ~/recon/payloads.txt 2> ~/recon/db_error.log > /dev/null

FLAG="$(grep -oE 'CYBERUS\{[^}]+\}' ~/recon/db_error.log | head -n 1)"
quest submit "$FLAG"
