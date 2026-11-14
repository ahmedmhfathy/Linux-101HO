#!/usr/bin/env python3
"""/challenge/sqli_runner binary for Mission 09: Bug Hunt: Fuzzing & Exploit Pipeline."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from engine.core import deterministic_token


def _fd_target(fd: int) -> str:
    try:
        return os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        return ""


def run(ctx: Dict[str, Any]) -> int:
    home_dir = Path(ctx["home"]).resolve()
    tok = deterministic_token(ctx["student_id"], "m09_fuzz", 6)

    expected_endpoints = sorted(
        [
            f"[200 OK] /api/v0/internal/health-{tok}",
            f"[200 OK] /api/v1/debug/vars-{tok}",
            f"[200 OK] /api/v2/auth/login-{tok}",
        ]
    )

    live_file = home_dir / "recon" / "live_endpoints.txt"
    if not live_file.is_file() or live_file.is_symlink():
        print(
            "[-] Stage 1 missing: `~/recon/live_endpoints.txt` does not exist yet.\n"
            "    Run `/challenge/dirfuzz`, silence stderr (`2>/dev/null`), pipe through `grep \"200 OK\"` and `sort`,\n"
            "    and redirect stdout to `~/recon/live_endpoints.txt`!",
            file=sys.stderr,
        )
        return 1

    lines = [line.strip() for line in live_file.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    if lines != expected_endpoints:
        print(
            "[-] Stage 1 incomplete: `~/recon/live_endpoints.txt` does not contain the exact sorted `[200 OK]` lines.\n"
            "    Make sure you silenced stderr (`2>/dev/null`), filtered with `grep \"200 OK\"`, and sorted with `sort`!",
            file=sys.stderr,
        )
        return 1

    if os.isatty(0):
        print(
            "[-] /challenge/sqli_runner: Waiting for SQLi payloads on stdin!\n"
            "    Redirect `~/recon/payloads.txt` into stdin (`< ~/recon/payloads.txt`) and redirect stderr (`2> ~/recon/db_error.log`).",
            file=sys.stderr,
        )
        return 1

    stdin_data = sys.stdin.read()
    if "CYBERUS_SQLI_TRIGGER" not in stdin_data:
        print(
            "[-] /challenge/sqli_runner: Expected SQLi payloads from `~/recon/payloads.txt` on stdin.",
            file=sys.stderr,
        )
        return 1

    stderr_target = _fd_target(2)
    if not stderr_target.startswith(str(home_dir) + "/"):
        print(
            "[-] /challenge/sqli_runner: Redirect stderr (stream 2) to `~/recon/db_error.log` using `2> ~/recon/db_error.log`!",
            file=sys.stderr,
        )
        return 1

    print("[INFO] Replaying payloads against /api/v2/auth/login-" + tok + " ...")
    print("[INFO] HTTP 500 Internal Server Error triggered! Dumping database error to stderr.")

    print(
        f"[DB_ERROR] Unhandled SQL syntax exception near ''' OR ''1''=''1'''\n"
        f"[DB_ERROR] Leaked row (users.admin_secret): {ctx['flag']}\n"
        f"[DB_ERROR] Submit flag with: quest submit {ctx['flag']}",
        file=sys.stderr,
    )
    return 0
