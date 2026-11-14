#!/usr/bin/env python3
"""Dispatcher for setuid challenge binaries in /challenge/<prog_name>."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR.parent))

from engine.core import STUDENT_GID, STUDENT_UID, QuestEngine  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("Invalid challenge invocation.", file=sys.stderr)
        return 1

    prog_name = sys.argv[1]
    prog_args = sys.argv[2:]

    engine = QuestEngine()
    state = engine.load_state()

    # Determine which mission owns /challenge/<prog_name>
    marker = engine.challenge_dir / f".mission_{prog_name}"
    if not marker.is_file():
        marker = engine.challenge_dir / ".active_mission"

    if not marker.is_file():
        print(f"/challenge/{prog_name} is not active for the current mission.", file=sys.stderr)
        return 1

    mission_id = marker.read_text(encoding="utf-8").strip()
    mission = engine.get_mission(mission_id)
    if mission is None:
        print("Active mission metadata not found.", file=sys.stderr)
        return 1

    unlocked_ids = {m["id"] for m in engine.get_unlocked_missions(state)}
    if mission["id"] not in unlocked_ids:
        print(f"Mission {mission['id']} is locked.", file=sys.stderr)
        return 1

    script_path = mission["dir"] / "bin" / f"{prog_name}.py"
    if not script_path.is_file():
        print(f"Challenge handler for '{prog_name}' not found.", file=sys.stderr)
        return 1

    invoked_as = os.environ.get("QUEST_INVOKED_AS", f"/challenge/{prog_name}")
    caller_cwd = os.environ.get("QUEST_CALLER_CWD", os.getcwd())
    caller_uid = int(os.environ.get("QUEST_CALLER_UID", str(STUDENT_UID)))
    caller_gid = int(os.environ.get("QUEST_CALLER_GID", str(STUDENT_GID)))
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
