#!/usr/bin/env python3
"""Stage 3 binary (/challenge/run2) for Mission 07: Redirect Trilogy."""

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
    home_dir = os.path.realpath(ctx["home"])
    stderr_target = _fd_target(2)

    # Always emit decoy noise on stdout
    for i in range(1, 6):
        print(f"[STDOUT DECOY #{i}] DECOY_STREAM_NOISE — Do not include stdout in stderr_flag.txt!")

    if not stderr_target.startswith(home_dir + "/"):
        print(
            "[-] /challenge/run2: stderr (stream 2) is not redirected to a file in your home directory!",
            file=sys.stderr,
        )
        return 1

    s3_tok = f"STAGE3-STDERR-{deterministic_token(ctx['student_id'], 'm07_s3', 8).upper()}"
    print(f"CYBERUS_REDIRECT_STAGE3={s3_tok}", file=sys.stderr)
    return 0
