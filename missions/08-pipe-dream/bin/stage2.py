#!/usr/bin/env python3
"""stage2 binary for Mission 08: Pipe Dream."""

import os
import sys
from typing import Any, Dict

from engine.core import deterministic_token


def _is_pipe(fd: int) -> bool:
    try:
        return os.readlink(f"/proc/self/fd/{fd}").startswith("pipe:")
    except OSError:
        return False


def run(ctx: Dict[str, Any]) -> int:
    if os.isatty(0) or not _is_pipe(0):
        print(
            "[-] /challenge/stage2: Waiting for input from /challenge/stage1 on standard input!",
            file=sys.stderr,
        )
        return 1

    if not _is_pipe(1):
        print(
            "[-] /challenge/stage2: Output must be sent directly into /challenge/stage3!",
            file=sys.stderr,
        )
        return 1

    expected_in = f"STAGE1_PAYLOAD:{deterministic_token(ctx['student_id'], 'm08_stage1', 10).upper()}"
    data = sys.stdin.read().strip()
    if data != expected_in:
        print(
            "[-] /challenge/stage2: Invalid input payload. Did it come from /challenge/stage1?",
            file=sys.stderr,
        )
        return 1

    tok2 = deterministic_token(ctx["student_id"], "m08_stage2", 10).upper()
    print(f"STAGE2_TRANSFORMED:{tok2}")
    return 0
