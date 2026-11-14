#!/usr/bin/env python3
"""Challenge binary for Mission 02: Home Sweet Home."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from engine.core import deterministic_token


def print_help() -> None:
    print("Usage: /challenge/run <ABSOLUTE_PATH_IN_HOME>")
    print("")
    print("Stage A of Mission 02 (Home Sweet Home):")
    print("  Pass an absolute file path inside /home/student as the first argument.")
    print("  Tip: In Bash, `~/stage_a.txt` automatically expands to `/home/student/stage_a.txt`!")
    print("")
    print("Examples:")
    print("  /challenge/run ~/stage_a.txt")
    print("  man run")


def run(ctx: Dict[str, Any]) -> int:
    args = ctx["args"]
    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        return 0

    target_arg = args[0]
    home_dir = Path(ctx["home"]).resolve()

    if not target_arg.startswith("/"):
        print(
            f"[-] Error: `{target_arg}` is a relative path.\n"
            f"    Pass an absolute path inside `{home_dir}` (or use `~/filename`).\n"
            f"    Run `man run` or `/challenge/run --help` for usage.",
            file=sys.stderr,
        )
        return 1

    # Drop privileges to student BEFORE touching /home/student (prevents symlink attacks)
    uid = int(ctx["uid"])
    gid = int(ctx["gid"])
    if os.name == "posix" and os.geteuid() == 0 and uid != 0:
        os.setresgid(gid, gid, gid)
        os.setresuid(uid, uid, uid)

    target_path = Path(target_arg)
    try:
        resolved_parent = target_path.parent.resolve(strict=True)
        resolved_parent.relative_to(home_dir)
    except Exception:
        print(
            f"[-] Error: Target path must be inside an existing directory under `{home_dir}`.",
            file=sys.stderr,
        )
        return 1

    if target_path.is_symlink() or target_path.is_dir():
        print("[-] Error: Target path must be a regular file (not a directory or symlink).", file=sys.stderr)
        return 1

    phrase = f"CYBERUS-NOTE-{deterministic_token(ctx['student_id'], 'mission02_phrase', 8).upper()}"
    content = (
        "=== Cyberus Mission 02: Stage A Complete ===\n"
        f"Secret Phrase for Stage B: {phrase}\n\n"
        "Next step (Stage B):\n"
        "  1. Create the directory ~/notes using `mkdir`\n"
        "  2. Create ~/notes/plan.txt using `nano` (or another tool) containing the Secret Phrase above.\n"
        "  3. Run `quest check` to claim your CYBERUS{...} flag!\n"
    )

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        fd = os.open(str(target_path), flags, 0o644)
        try:
            os.write(fd, content.encode("utf-8"))
        finally:
            os.close(fd)

        marker_path = home_dir / ".stage02_a_done"
        mfd = os.open(str(marker_path), flags, 0o644)
        try:
            os.write(mfd, f"{phrase}\n".encode("utf-8"))
        finally:
            os.close(mfd)
    except OSError as exc:
        print(f"[-] Failed to write to `{target_path}`: {exc}", file=sys.stderr)
        return 1

    print(f"[+] Stage A complete! Wrote instructions and secret phrase to `{target_path}`.")
    print(f"    Read it now with: cat {target_path}")
    return 0
