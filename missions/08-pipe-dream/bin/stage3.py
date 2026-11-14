#!/usr/bin/env python3
"""stage3 binary for Mission 08: Pipe Dream."""

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
            "[-] /challenge/stage3: My input must arrive through a pipe (`|`) from `/challenge/stage2`!\n"
            "    Try: /challenge/stage1 | /challenge/stage2 | /challenge/stage3",
            file=sys.stderr,
        )
        return 1

    expected_in = f"STAGE2_TRANSFORMED:{deterministic_token(ctx['student_id'], 'm08_stage2', 10).upper()}"
    data = sys.stdin.read().strip()
    if data != expected_in:
        print(
            "[-] /challenge/stage3: Input was not transformed by stage1 -> stage2!\n"
            "    Run: /challenge/stage1 | /challenge/stage2 | /challenge/stage3",
            file=sys.stderr,
        )
        return 1

    passphrase = f"CYBERUS-PIPE-PASSPHRASE-{deterministic_token(ctx['student_id'], 'm08_pass', 10).upper()}"
    print("[+] Assembly line complete!")
    print(f"[+] Secret Passphrase: {passphrase}")
    print("    Now feed that passphrase into /challenge/interrogator using `|` or `<`!")
    return 0
