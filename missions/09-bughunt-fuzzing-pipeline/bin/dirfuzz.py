#!/usr/bin/env python3
"""/challenge/dirfuzz binary for Mission 09: Bug Hunt: Fuzzing & Exploit Pipeline."""

import sys
from typing import Any, Dict

from engine.core import deterministic_token


def run(ctx: Dict[str, Any]) -> int:
    tok = deterministic_token(ctx["student_id"], "m09_fuzz", 6)

    # Emit noisy timeout errors on stderr and mixed HTTP results on stdout
    paths = [
        ("404 NOT FOUND", "/admin.bak"),
        ("403 FORBIDDEN", "/.htaccess"),
        ("200 OK", f"/api/v2/auth/login-{tok}"),
        ("404 NOT FOUND", "/wp-login.php"),
        ("200 OK", f"/api/v1/debug/vars-{tok}"),
        ("502 BAD GATEWAY", "/legacy/soap"),
        ("200 OK", f"/api/v0/internal/health-{tok}"),
        ("404 NOT FOUND", "/phpmyadmin"),
    ]

    for idx, (status, endpoint) in enumerate(paths, start=1):
        print(
            f"[ERROR] Worker #{idx}: TLS handshake timeout on proxy node {idx}.cyberus.local",
            file=sys.stderr,
        )
        print(f"[{status}] {endpoint}")

    return 0
