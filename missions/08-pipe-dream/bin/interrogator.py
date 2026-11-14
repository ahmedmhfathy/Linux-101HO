#!/usr/bin/env python3
"""interrogator binary for Mission 08: Pipe Dream."""

import os
import sys
from typing import Any, Dict

from engine.core import deterministic_token


def run(ctx: Dict[str, Any]) -> int:
    passphrase = f"CYBERUS-PIPE-PASSPHRASE-{deterministic_token(ctx['student_id'], 'm08_pass', 10).upper()}"

    if os.isatty(0):
        print(
            "[-] /challenge/interrogator: I do not accept interactive keyboard input!\n"
            "    Feed me the secret passphrase from stage3 using a pipe (`|`) or file redirection (`<`):\n"
            "      echo \"<PASSPHRASE>\" | /challenge/interrogator\n"
            "    or:\n"
            "      /challenge/interrogator < ~/phrase.txt",
            file=sys.stderr,
        )
        return 1

    submitted = sys.stdin.read().strip()
    if passphrase not in submitted:
        print(
            "[-] /challenge/interrogator: Incorrect passphrase on stdin.\n"
            "    Run `/challenge/stage1 | /challenge/stage2 | /challenge/stage3` first to get your passphrase.",
            file=sys.stderr,
        )
        return 1

    print("[+] Interrogator satisfied!")
    print(f"[+] Flag: {ctx['flag']}")
    print(f"    Submit with: quest submit {ctx['flag']}")
    return 0
