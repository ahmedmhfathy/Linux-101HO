#!/usr/bin/env python3
"""Challenge binary for Mission 02: Home Sweet Home."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from engine.core import deterministic_token


def print_help() -> None:
    print("Usage: /challenge/run [OPTIONS]")
    print("")
    print("Options:")
    print("  -v, --verbose        Print extra diagnostic status messages.")
    print("  -p, --please         Ask nicely to reveal instructions for claiming the flag.")
    print("  -d, --dry-run        Simulate execution without writing any files.")
    print("  -h, --help           Display this help message and exit.")


def run(ctx: Dict[str, Any]) -> int:
    args = ctx["args"]

    if args == ["-h"] or args == ["--help"]:
        print_help()
        return 0

    # Case A: Run with no options or invalid/dummy options
    if args not in (["-p"], ["--please"]):
        print("[-] Rude. You didn't even ask nicely.")
        print("[*] Hint: Check my documentation to learn some manners.")
        return 1

    # Drop privileges to student before checking/writing inside /home/student
    uid = int(ctx["uid"])
    gid = int(ctx["gid"])
    if os.name == "posix" and os.geteuid() == 0 and uid != 0:
        os.setresgid(gid, gid, gid)
        os.setresuid(uid, uid, uid)

    home_dir = Path(ctx["home"]).resolve()
    try:
        cwd = Path(ctx["cwd"]).resolve()
    except Exception:
        cwd = Path("/")

    # Case B: Run with -p or --please in the WRONG directory (must be a subdirectory inside ~)
    is_subdir_of_home = False
    try:
        rel = cwd.relative_to(home_dir)
        if len(rel.parts) >= 1:
            is_subdir_of_home = True
    except ValueError:
        is_subdir_of_home = False

    if not is_subdir_of_home:
        print("[-] Almost! You asked nicely, but I don't feel at home here.")
        print("[*] Create a directory inside your home folder (~), step inside it, and ask me again.")
        return 1

    # Case C: Run with -p or --please in the RIGHT directory (~/<folder>)
    hex8 = deterministic_token(ctx["student_id"], "mission02_phrase", 8).upper()
    code_str = f"CYBERUS-NOTE-{hex8}"
    file_content = (
        "# Instruction: Replace 'CYBERUS' with 'Tofa7aElSafa7a' (case-insensitive) and save the file.\n"
        f"{code_str}\n"
    )

    code_path = cwd / ".code.txt"
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        fd = os.open(str(code_path), flags, 0o644)
        try:
            os.write(fd, file_content.encode("utf-8"))
        finally:
            os.close(fd)
    except OSError as exc:
        print(f"[-] Failed to write '.code.txt': {exc}", file=sys.stderr)
        return 1

    print("[+] Much better! Welcome home.")
    print("[*] I've stashed a secret code inside a hidden file in your current directory.")
    print("[*] Find it, read the instructions inside, make the required edit, and save it.")
    print("[*] Once you're done, run the check command to claim your flag!")
    return 0
