#!/usr/bin/env python3
"""Dispatcher for setuid challenge binaries in /challenge/<prog_name>."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR.parent))

from engine.core import STUDENT_GID, STUDENT_UID, QuestEngine  # noqa: E402


def _fd_target(fd: int) -> str:
    try:
        return os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        return ""


def _resolve_mission_id_for_call(
    engine: QuestEngine,
    state: Dict[str, Any],
    prog_name: str,
    prog_args: List[str],
    invoked_as: str,
    caller_cwd: str,
) -> str:
    """Route /challenge/<prog_name> intelligently so students can solve missions in any order."""
    if prog_name == "run2":
        return "05"
    if prog_name in ("stage1", "stage2", "stage3", "checker"):
        return "06"

    if prog_name == "run":
        home_real = os.path.realpath(str(engine.home_dir))
        cwd_real = os.path.realpath(caller_cwd)
        var_log_real = os.path.realpath("/var/log")
        stdout_target = _fd_target(1)

        # 1. Explicit Stage 2 redirection flags (--part1 / --part2) or stdout redirected to file in ~ -> Mission 05
        if any(a in ("--part1", "--part2") for a in prog_args):
            return "05"
        if stdout_target.startswith(home_real + "/"):
            return "05"

        # 2. Any other CLI option (-p, --please, -h, --help, -v, -d, etc.) -> Mission 02
        if prog_args:
            return "02"

        # 3. No CLI options and stdout is terminal:
        #    If standing in /var/log or invoked via relative path -> Mission 01
        if cwd_real == var_log_real or invoked_as != "/challenge/run":
            return "01"

        #    If standing inside a subdirectory of ~ -> Mission 02 (Case A: forgot -p/--please)
        if cwd_real.startswith(home_real + "/"):
            return "02"

        #    Otherwise fall back to the student's current active mission if it uses /challenge/run
        current = engine.get_current_mission(state)
        if current and current["id"] in ("01", "02", "05"):
            return current["id"]
        if "01" not in state.get("completed", {}):
            return "01"
        if "02" not in state.get("completed", {}):
            return "02"
        return "05"

    marker = engine.challenge_dir / f".mission_{prog_name}"
    if marker.is_file():
        return marker.read_text(encoding="utf-8").strip()
    return "01"


def main() -> int:
    if len(sys.argv) < 2:
        print("Invalid challenge invocation.", file=sys.stderr)
        return 1

    prog_name = sys.argv[1]
    prog_args = sys.argv[2:]

    engine = QuestEngine()
    state = engine.load_state()

    invoked_as = os.environ.get("QUEST_INVOKED_AS", f"/challenge/{prog_name}")
    caller_cwd = os.environ.get("QUEST_CALLER_CWD", os.getcwd())
    caller_uid = int(os.environ.get("QUEST_CALLER_UID", str(STUDENT_UID)))
    caller_gid = int(os.environ.get("QUEST_CALLER_GID", str(STUDENT_GID)))

    mission_id = _resolve_mission_id_for_call(
        engine, state, prog_name, prog_args, invoked_as, caller_cwd
    )
    mission = engine.get_mission(mission_id)
    if mission is None:
        print("Mission metadata not found.", file=sys.stderr)
        return 1

    script_path = mission["dir"] / "bin" / f"{prog_name}.py"
    if not script_path.is_file():
        print(f"Challenge handler for '{prog_name}' not found.", file=sys.stderr)
        return 1

    flag = engine.get_flag(mission["id"], state)

    ctx: Dict[str, Any] = {
        "mission_id": mission["id"],
        "student_id": state["student_id"],
        "flag": flag,
        "invoked_as": invoked_as,
        "cwd": caller_cwd,
        "uid": caller_uid,
        "gid": caller_gid,
        "home": str(engine.home_dir),
        "args": prog_args,
        "prog_name": prog_name,
    }

    code_str = script_path.read_text(encoding="utf-8")
    namespace: Dict[str, Any] = {"__file__": str(script_path), "__name__": "__main__"}
    exec(compile(code_str, str(script_path), "exec"), namespace)
    run_fn = namespace.get("run")
    if callable(run_fn):
        return int(run_fn(ctx) or 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
