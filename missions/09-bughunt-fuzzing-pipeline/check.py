"""State checker for Mission 09: Bug Hunt: Fuzzing & Exploit Pipeline."""

from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    tok = deterministic_token(ctx.student_id, "m09_fuzz", 6)
    expected_endpoints = sorted(
        [
            f"[200 OK] /api/v0/internal/health-{tok}",
            f"[200 OK] /api/v1/debug/vars-{tok}",
            f"[200 OK] /api/v2/auth/login-{tok}",
        ]
    )

    if not ctx.exists("recon/live_endpoints.txt"):
        return (
            False,
            "Stage 1: `~/recon/live_endpoints.txt` does not exist. Run `/challenge/dirfuzz 2>/dev/null | grep \"200 OK\" | sort > ~/recon/live_endpoints.txt`.",
        )

    lines = [line.strip() for line in ctx.read("recon/live_endpoints.txt").splitlines() if line.strip()]
    if lines != expected_endpoints:
        return (
            False,
            "Stage 1: `~/recon/live_endpoints.txt` must contain only the sorted `[200 OK]` lines from `/challenge/dirfuzz`.",
        )

    if not ctx.exists("recon/db_error.log"):
        return (
            False,
            "Stage 2: `~/recon/db_error.log` does not exist. Run `/challenge/sqli_runner < ~/recon/payloads.txt 2> ~/recon/db_error.log`.",
        )

    err_log = ctx.read("recon/db_error.log")
    if ctx.flag not in err_log:
        return (
            False,
            "Stage 2: `~/recon/db_error.log` does not contain the leaked database flag yet. Re-run `/challenge/sqli_runner < ~/recon/payloads.txt 2> ~/recon/db_error.log`.",
        )

    return True, "Fuzzer triage pipeline and SQLi stderr error extraction verified!"
