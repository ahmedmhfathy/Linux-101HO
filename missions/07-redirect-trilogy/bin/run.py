#!/usr/bin/env python3
"""Stage 1 & Stage 2 binary (/challenge/run) for Mission 07: Redirect Trilogy."""

import os
import sys
from typing import Any, Dict

from engine.core import deterministic_token


def _fd_target(fd: int) -> str:
    try:
        return os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        return ""


def run(ctx: Dict[str, Any]) -> int:
    args = ctx["args"]
    home_dir = os.path.realpath(ctx["home"])
    stdout_target = _fd_target(1)

    if not stdout_target.startswith(home_dir + "/"):
        print(
            "[-] /challenge/run: stdout (stream 1) is currently pointing to your terminal (or outside ~).\n"
            "    Redirect stdout to a file in your home directory!",
            file=sys.stderr,
        )
        return 1

    s1_tok = f"STAGE1-OK-{deterministic_token(ctx['student_id'], 'm07_s1', 8).upper()}"
    p1_tok = f"PART1-{deterministic_token(ctx['student_id'], 'm07_p1', 6).upper()}"
    p2_tok = f"PART2-{deterministic_token(ctx['student_id'], 'm07_p2', 6).upper()}"

    if not args:
        print("[stderr] Stage 1 stdout successfully redirected to file!", file=sys.stderr)
        print(f"CYBERUS_REDIRECT_STAGE1={s1_tok}")
        return 0

    if args[0] == "--part1":
        print("[stderr] Wrote Part 1 to file.", file=sys.stderr)
        print(f"HALF1:{p1_tok}")
        return 0

    if args[0] == "--part2":
        print("[stderr] Wrote Part 2!", file=sys.stderr)
        print(f"HALF2:{p2_tok}")
        return 0

    print("Usage: /challenge/run [--part1 | --part2]", file=sys.stderr)
    return 1
