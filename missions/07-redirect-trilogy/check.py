"""State checker for Mission 07: Redirect Trilogy."""

from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    s1_tok = f"STAGE1-OK-{deterministic_token(ctx.student_id, 'm07_s1', 8).upper()}"
    p1_tok = f"HALF1:PART1-{deterministic_token(ctx.student_id, 'm07_p1', 6).upper()}"
    p2_tok = f"HALF2:PART2-{deterministic_token(ctx.student_id, 'm07_p2', 6).upper()}"
    s3_tok = f"STAGE3-STDERR-{deterministic_token(ctx.student_id, 'm07_s3', 8).upper()}"

    if not ctx.exists("myflag"):
        return False, "Stage 1: `~/myflag` does not exist. Run `/challenge/run > ~/myflag`."

    c1 = ctx.read("myflag")
    if s1_tok not in c1:
        return False, "Stage 1: `~/myflag` does not contain the Stage 1 token from `/challenge/run > ~/myflag`."

    if not ctx.exists("twopart.txt"):
        return (
            False,
            "Stage 2: `~/twopart.txt` does not exist. Use `>` for `--part1` and `>>` for `--part2`.",
        )

    c2 = ctx.read("twopart.txt")
    if p1_tok not in c2 and p2_tok in c2:
        return (
            False,
            "Stage 2: `~/twopart.txt` only has Part 2! Did you use `>` instead of `>>` on the second command?",
        )
    if p1_tok not in c2 or p2_tok not in c2:
        return (
            False,
            "Stage 2: `~/twopart.txt` must contain both Part 1 (`--part1 >`) and Part 2 (`--part2 >>`).",
        )
    if c2.index(p1_tok) > c2.index(p2_tok):
        return False, "Stage 2: Part 1 must appear before Part 2 in `~/twopart.txt`."

    if not ctx.exists("stderr_flag.txt"):
        return (
            False,
            "Stage 3: `~/stderr_flag.txt` does not exist. Redirect stderr with `/challenge/run2 2> ~/stderr_flag.txt > /dev/null`.",
        )

    c3 = ctx.read("stderr_flag.txt")
    if "DECOY_STREAM_NOISE" in c3:
        return (
            False,
            "Stage 3: `~/stderr_flag.txt` contains `stdout` decoy lines! Use `2> ~/stderr_flag.txt` for stderr only, not `> ~/stderr_flag.txt 2>&1`.",
        )
    if s3_tok not in c3:
        return False, "Stage 3: `~/stderr_flag.txt` is missing the Stage 3 token from `/challenge/run2`."

    return True, "All 3 redirection stages verified!"
