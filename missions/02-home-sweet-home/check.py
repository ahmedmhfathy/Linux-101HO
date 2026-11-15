"""State checker for Mission 02: Home Sweet Home."""

from pathlib import Path
from typing import List, Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    hex8 = deterministic_token(ctx.student_id, "mission02_phrase", 8).upper()
    expected = f"tofa7aelsafa7a-note-{hex8.lower()}"

    # Find .code.txt inside any subdirectory of ~ (~/<folder>/.code.txt, not ~/.code.txt)
    candidates: List[Path] = []
    if ctx.home.is_dir():
        for p in ctx.home.rglob(".code.txt"):
            try:
                rel = p.relative_to(ctx.home)
            except ValueError:
                continue
            # Must be inside a subdirectory of ~ (at least 2 parts: <folder>/.code.txt)
            if len(rel.parts) >= 2 and not p.is_symlink() and p.is_file():
                rel_str = str(rel).replace("\\", "/")
                if ctx.exists(rel_str):
                    candidates.append(p)

    # Check 1 (Missing file or wrong location)
    if not candidates:
        return (
            False,
            "[-] I don't see '.code.txt' in a folder inside your home directory. Did you wander off?",
        )

    # Check 2 (Validation rule: ignore comment lines starting with # and leading/trailing whitespace)
    for cpath in candidates:
        rel_str = str(cpath.relative_to(ctx.home)).replace("\\", "/")
        raw = ctx.read(rel_str)
        non_comment_lines = [
            line.strip()
            for line in raw.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if any(line.lower() == expected for line in non_comment_lines):
            # Check 3 (Success)
            return True, f"[+] Spot on! Here is your flag: {ctx.flag}"

    return (
        False,
        "[-] Close, but that code doesn't look right. Read the instructions inside '.code.txt' carefully!",
    )
