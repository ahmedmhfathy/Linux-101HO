"""State checker for Mission 04: The Evidence Room."""

from pathlib import Path
from typing import List, Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    # Accepted variations:
    # - Real .evd file was copied (`cp`) or moved (`mv`) to `case.txt` inside ANY folder inside `~` (excluding `~/archive`)
    # - ~/archive/decoy_trap directory has been removed (`rm -r`)
    # - `top.txt` inside ANY folder inside `~` contains the top scorer handle
    h = deterministic_token(ctx.student_id, "m04_evd", 10)
    expected_sig = f"SIGNATURE: {h}"
    top_handle = f"hunter_{h[:6]}"

    case_files: List[Path] = []
    top_files: List[Path] = []
    if ctx.home.is_dir():
        for p in ctx.home.rglob("case.txt"):
            try:
                rel = p.relative_to(ctx.home)
            except ValueError:
                continue
            if len(rel.parts) >= 2 and rel.parts[0] != "archive" and not p.is_symlink() and p.is_file():
                rel_str = str(rel).replace("\\", "/")
                if ctx.exists(rel_str):
                    case_files.append(p)

        for p in ctx.home.rglob("top.txt"):
            try:
                rel = p.relative_to(ctx.home)
            except ValueError:
                continue
            if len(rel.parts) >= 2 and rel.parts[0] != "archive" and not p.is_symlink() and p.is_file():
                rel_str = str(rel).replace("\\", "/")
                if ctx.exists(rel_str):
                    top_files.append(p)

    if not case_files:
        return (
            False,
            "[-] Could not find `case.txt` inside a directory in your home folder (`~/<folder>/case.txt`).",
        )

    case_ok = False
    for cp in case_files:
        rel_str = str(cp.relative_to(ctx.home)).replace("\\", "/")
        case_content = ctx.read(rel_str)
        if "EVIDENCE_MARKER_CYBERUS" in case_content and expected_sig in case_content:
            case_ok = True
            break

    if not case_ok:
        return (
            False,
            "[-] `case.txt` does not match the genuine `.evd` file containing `EVIDENCE_MARKER_CYBERUS`.",
        )

    if ctx.exists("archive/decoy_trap") or ctx.is_dir("archive/decoy_trap"):
        return (
            False,
            "[-] The decoy folder `~/archive/decoy_trap` still exists. Delete it completely!",
        )

    if not top_files:
        return (
            False,
            "[-] Could not find `top.txt` inside a directory in your home folder (`~/<folder>/top.txt`).",
        )

    top_ok = False
    for tp in top_files:
        rel_str = str(tp.relative_to(ctx.home)).replace("\\", "/")
        if top_handle in ctx.read(rel_str).strip():
            top_ok = True
            break

    if not top_ok:
        return (
            False,
            "[-] `top.txt` does not contain the researcher handle with the highest score in `scores.txt`.",
        )

    return True, f"[+] Evidence filed, decoy trap removed, and top researcher identified! Here is your flag: {ctx.flag}"
