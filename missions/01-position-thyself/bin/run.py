#!/usr/bin/env python3
"""Challenge binary logic for Mission 01: Position Thyself."""

import os
import sys
from typing import Any, Dict

from engine.core import deterministic_choice


def run(ctx: Dict[str, Any]) -> int:
    invoked_as = ctx["invoked_as"]
    cwd = os.path.realpath(ctx["cwd"])
    student_id = ctx["student_id"]

    candidate_dirs = ["/var/log", "/etc", "/usr/share/doc", "/usr/include", "/var/backups"]
    existing_dirs = [d for d in candidate_dirs if os.path.isdir(d)] or ["/tmp"]
    required_dir = os.path.realpath(deterministic_choice(student_id, "mission01_dir", existing_dirs))

    is_absolute = invoked_as == "/challenge/run"
    is_right_cwd = cwd == required_dir

    if not is_absolute and not is_right_cwd:
        print(
            f"[-] Access denied!\n"
            f"    1. You invoked this program as `{invoked_as}` instead of its absolute path (`/challenge/run`).\n"
            f"    2. Your current directory is `{cwd}`, but you must stand in `{required_dir}`.\n"
            f"    Tip: Use `cd {required_dir}` and then run `/challenge/run`.",
            file=sys.stderr,
        )
        return 1

    if not is_absolute:
        print(
            f"[-] Almost there! You are in `{cwd}`, which is correct.\n"
            f"    However, you invoked the program as `{invoked_as}`.\n"
            f"    You must call it using its full absolute path: `/challenge/run`.",
            file=sys.stderr,
        )
        return 1

    if not is_right_cwd:
        print(
            f"[-] Wrong working directory!\n"
            f"    You invoked `/challenge/run` correctly by absolute path, but your current directory is `{cwd}`.\n"
            f"    Use `cd {required_dir}` first, verify with `pwd`, and run `/challenge/run` again.",
            file=sys.stderr,
        )
        return 1

    print("[+] Position and invocation verified!")
    print(f"[+] Here is your flag: {ctx['flag']}")
    print(f"    Submit it with: quest submit {ctx['flag']}")
    return 0
