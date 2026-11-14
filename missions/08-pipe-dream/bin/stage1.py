#!/usr/bin/env python3
"""stage1 binary for Mission 08: Pipe Dream."""

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
    if not _is_pipe(1):
        print(
            "[-] /challenge/stage1: My stdout must be piped (`|`) directly into `/challenge/stage2`!\n"
            "    Try: /challenge/stage1 | /challenge/stage2 | /challenge/stage3",
            file=sys.stderr,
        )
        return 1

    tok1 = deterministic_token(ctx["student_id"], "m08_stage1", 10).upper()
    print(f"STAGE1_PAYLOAD:{tok1}")
    return 0
