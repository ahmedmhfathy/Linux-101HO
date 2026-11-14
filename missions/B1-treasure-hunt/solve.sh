#!/usr/bin/env bash
set -euo pipefail

FLAG="$(grep -oE 'CYBERUS\{[^}]+\}' ~/treasure/north/cavern/.secret_chamber/vault/.ancient.log | head -n 1)"
quest submit "$FLAG"
