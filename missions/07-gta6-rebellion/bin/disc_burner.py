#!/usr/bin/env python3
"""/challenge/disc_burner binary for Mission 07: GTA VI Physical Disc Rebellion."""

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
    if os.isatty(0) or not _is_pipe(0):
        print(
            "[-] /challenge/disc_burner: I must receive the build stream from /challenge/gta6_patcher through a pipe (|)!",
            file=sys.stderr,
        )
        return 1

    expected_tok = f"GTA6_PHYSICAL_DISC_STREAM:{deterministic_token(ctx['student_id'], 'm07_disc_payload', 12).upper()}"
    data = sys.stdin.read().strip()

    if not data:
        print(
            "[-] /challenge/disc_burner: Received empty input from the pipe!\n"
            "[*] Remember: /challenge/gta6_patcher prints on stderr (stream 2), which normal pipes ignore.\n"
            "[*] Redirect stderr to stdout before piping into /challenge/disc_burner!",
            file=sys.stderr,
        )
        return 1

    if expected_tok not in data:
        print(
            "[-] /challenge/disc_burner: Invalid build stream received on standard input.\n"
            "[*] Pipe the output of /challenge/gta6_patcher into /challenge/disc_burner!",
            file=sys.stderr,
        )
        return 1

    print("[+] Physical Disc Edition burned successfully! Death to Digital-Only DRM!")
    print(f"[+] Flag: {ctx['flag']}")
    print(f"    Submit with: quest submit {ctx['flag']}")
    return 0
