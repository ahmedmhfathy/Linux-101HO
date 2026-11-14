"""State checker for Mission 04: The Evidence Room."""

from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    # Accepted variations:
    # - Real .evd file was either copied (`cp`) or moved (`mv`) to ~/evidence/case.txt
    # - ~/archive/decoy_trap directory has been removed (`rm -r`)
    # - ~/evidence/top.txt contains the top scorer handle (either `hunter_xxxxxx` or `9945 hunter_xxxxxx`)
    h = deterministic_token(ctx.student_id, "m04_evd", 10)
    expected_sig = f"SIGNATURE: {h}"
    top_handle = f"hunter_{h[:6]}"

    if not ctx.is_dir("evidence"):
        return False, "Directory `~/evidence` does not exist yet. Create it with `mkdir`."

    if not ctx.exists("evidence/case.txt"):
        return False, "`~/evidence/case.txt` is missing. Copy or move the genuine `.evd` file there."

    case_content = ctx.read("evidence/case.txt")
    if "EVIDENCE_MARKER_CYBERUS" not in case_content or expected_sig not in case_content:
        return (
            False,
            "`~/evidence/case.txt` does not match the genuine `.evd` file containing `EVIDENCE_MARKER_CYBERUS`.",
        )

    if ctx.exists("archive/decoy_trap") or ctx.is_dir("archive/decoy_trap"):
        return False, "The decoy folder `~/archive/decoy_trap` still exists. Remove it with `rm -r ~/archive/decoy_trap`."

    if not ctx.exists("evidence/top.txt"):
        return False, "`~/evidence/top.txt` is missing. Write the highest scorer's handle from `scores.txt` into it."

    top_content = ctx.read("evidence/top.txt").strip()
    if top_handle not in top_content:
        return False, "`~/evidence/top.txt` does not contain the researcher handle with the highest score in `scores.txt`."

    return True, "Evidence filed, decoy trap removed, and top researcher identified!"
