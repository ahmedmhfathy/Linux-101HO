"""State checker for Mission 04: The Evidence Room."""

import re
from pathlib import Path
from typing import List, Optional, Tuple

from engine.core import CheckContext, deterministic_token

TARGET_PHRASE = "a3da2_sherket_nvidia_microntech"
DECOY_PHRASES = (
    "a3da2_sherket_nvidia_microntech_sony",
    "a3da2_sherket_nvidia_microntech_sony_meta",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei_microsoft",
)


def check(ctx: CheckContext) -> Tuple[bool, str]:
    h = deterministic_token(ctx.student_id, "m04_evd", 10)
    expected_sig = f"SIGNATURE: {h}"
    top_handle = f"hunter_{h[:6]}"

    # 1. Locate ~/evidence directory (case-insensitive: evidence, EVIDENCE, Evidence, etc.)
    evd_dir: Optional[Path] = None
    if ctx.home.is_dir():
        for entry in sorted(ctx.home.iterdir()):
            if entry.name.lower() == "evidence" and not entry.is_symlink() and entry.is_dir():
                if ctx.is_dir(entry.name):
                    evd_dir = entry
                    break

    if evd_dir is None:
        return (
            False,
            "[-] Directory `~/evidence/` does not exist yet. Create it with `mkdir`.",
        )

    # Collect all regular files inside ~/evidence/
    evd_files: List[Tuple[str, str]] = []
    for p in sorted(evd_dir.rglob("*")):
        if p.is_symlink() or not p.is_file():
            continue
        try:
            rel_str = str(p.relative_to(ctx.home)).replace("\\", "/")
            if ctx.exists(rel_str):
                evd_files.append((rel_str, ctx.read(rel_str)))
        except Exception:
            continue

    # 2. Check that the genuine .evd file (and no decoy .evd files) is inside ~/evidence/
    exact_phrase_re = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(TARGET_PHRASE)}(?![A-Za-z0-9_])")
    found_real_evd = False
    found_decoy_evd = False

    for rel_str, content in evd_files:
        if any(dp in content for dp in DECOY_PHRASES) or re.search(
            r"(?<![A-Za-z0-9_])a3da2_sherket_nvidia(?![A-Za-z0-9_])", content
        ):
            found_decoy_evd = True
        if exact_phrase_re.search(content) and expected_sig in content:
            found_real_evd = True

    if found_decoy_evd:
        return (
            False,
            "[-] Found a decoy file inside `~/evidence/`! Move ONLY the genuine `.evd` file containing the exact phrase `a3da2_sherket_nvidia_microntech`.",
        )

    if not found_real_evd:
        return (
            False,
            "[-] Could not find the genuine `.evd` file containing the exact phrase `a3da2_sherket_nvidia_microntech` inside `~/evidence/`.",
        )

    # 3. Check that ~/archive/decoy_trap is deleted
    if ctx.exists("archive/decoy_trap") or ctx.is_dir("archive/decoy_trap"):
        return (
            False,
            "[-] The decoy folder `~/archive/decoy_trap` still exists. Delete it completely!",
        )

    # 4. Check that a file inside ~/evidence/ contains the top researcher handle (under any filename)
    found_top_handle = False
    for rel_str, content in evd_files:
        if expected_sig in content:
            # Skip the .evd evidence file itself
            continue
        if top_handle in content and "rookie_01" not in content and "null_byte" not in content:
            found_top_handle = True
            break

    if not found_top_handle:
        return (
            False,
            "[-] Could not find a file inside `~/evidence/` containing the researcher handle with the highest numeric score from `~/archive/scores.txt`.",
        )

    return True, f"[+] Evidence filed, decoy trap removed, and top researcher identified! Here is your flag: {ctx.flag}"
