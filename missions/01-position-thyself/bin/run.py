#!/usr/bin/env python3
"""Challenge binary logic for Mission 01: Position Thyself."""

import os
import sys
from typing import Any, Dict


def run(ctx: Dict[str, Any]) -> int:
    invoked_as = ctx["invoked_as"]
    cwd = os.path.realpath(ctx["cwd"])
    required_dir = os.path.realpath("/var/log")

    is_absolute = invoked_as == "/challenge/run"
    is_right_cwd = cwd == required_dir

    if not is_absolute:
        print("Wrong path yasta I TOLD YOU TO USE ABSOLUTE PATHS YA3AM ENTA", file=sys.stderr)
        return 1

    if not is_right_cwd:
        print(
            f"[-] Wrong working directory!\n"
            f"    You are currently in `{cwd}`, but you need to stand in `/var/log`.",
            file=sys.stderr,
        )
        return 1

    print("[+] Position and invocation verified!")
    print(f"[+] Here is your flag: {ctx['flag']}")
    return 0
