#!/usr/bin/env python3
"""checker binary (/challenge/checker) for Mission 08: Pipe Dream."""

import os
import stat
import sys
from typing import Any, Dict

from engine.core import deterministic_token


def _is_pipe(fd: int) -> bool:
    try:
        if os.readlink(f"/proc/self/fd/{fd}").startswith("pipe:"):
            return True
    except OSError:
        pass
    try:
        return stat.S_ISFIFO(os.fstat(fd).st_mode)
    except OSError:
        return False


def run(ctx: Dict[str, Any]) -> int:
    passphrase = f"CYBERUS-PIPE-PASSPHRASE-{deterministic_token(ctx['student_id'], 'm08_pass', 10).upper()}"

    # Case A: Run interactively (keyboard/TTY input) or via CLI arguments
    if ctx.get("args") or os.isatty(0):
        print("[-] /challenge/checker: Interactive keyboard input is not allowed!")
        print("[*] Send the secret passphrase directly into my standard input instead.")
        return 1

    submitted = sys.stdin.read().strip()
    if passphrase not in submitted:
        print("[-] /challenge/checker: Incorrect passphrase on standard input.")
        print("[*] Complete the stage1, stage2, and stage3 assembly line first to obtain the secret passphrase.")
        return 1

    # Case B: Valid passphrase received via stdin (distinguish pipe vs file redirection)
    if _is_pipe(0):
        print("[+] Passphrase verified!")
    else:
        print("[+] Passphrase verified! (Nice file redirection!)")
    print(f"[+] Flag: {ctx['flag']}")
    print(f"    Submit with: quest submit {ctx['flag']}")
    return 0
