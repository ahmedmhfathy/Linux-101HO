"""State checker for Mission 02: Home Sweet Home."""

from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    # Accepted variations:
    # 1. Stage A marker file (~/.stage02_a_done) must exist from running /challenge/run <path-in-home>
    # 2. ~/notes/plan.txt must exist and contain the student's deterministic phrase (whitespace-tolerant).
    phrase = f"CYBERUS-NOTE-{deterministic_token(ctx.student_id, 'mission02_phrase', 8).upper()}"

    if not ctx.exists(".stage02_a_done"):
        return False, "Stage A is not complete yet. Run `/challenge/run` with a file path inside your home directory first (see `man run`)."

    if not ctx.is_dir("notes"):
        return False, "Directory `~/notes` does not exist yet. Create it with `mkdir`."

    if not ctx.exists("notes/plan.txt"):
        return False, "File `~/notes/plan.txt` does not exist yet."

    content = ctx.read("notes/plan.txt")
    if phrase not in content:
        return False, f"`~/notes/plan.txt` does not contain the expected phrase (`{phrase}`)."

    return True, "Both Stage A and `~/notes/plan.txt` verified!"
