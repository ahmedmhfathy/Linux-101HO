#!/usr/bin/env python3
"""Command-line interface for Cyberus Linux Quest (`quest`)."""

import os
import shutil
import stat
import sys
from pathlib import Path
from typing import List, Optional

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR.parent))

from engine.core import (  # noqa: E402
    ENGINE_VERSION,
    FLAG_PREFIX,
    STUDENT_UID,
    QuestEngine,
    QuestError,
    compute_export_token,
    deterministic_choice,
    deterministic_token,
)

# ANSI Colors
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
MAGENTA = "\033[1;35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_mission_text(text: str, student_id: str) -> str:
    """Substitute dynamic per-student placeholders in mission descriptions."""
    dirs_01 = ["/var/log"]
    req_dir_01 = deterministic_choice(student_id, "mission01_dir", dirs_01)
    phrase_02 = f"CYBERUS-NOTE-{deterministic_token(student_id, 'mission02_phrase', 8).upper()}"
    return (
        text.replace("{MISSION01_DIR}", req_dir_01)
        .replace("{MISSION02_PHRASE}", phrase_02)
    )


def print_banner() -> None:
    print(f"{CYAN}============================================================{RESET}")
    print(f"{BOLD}{CYAN}   CYBERUS LINUX QUEST  {RESET}{DIM}(v{ENGINE_VERSION} - Bug Hunting Lab){RESET}")
    print(f"{CYAN}============================================================{RESET}")


def cmd_show(engine: QuestEngine, mission_id: Optional[str] = None) -> int:
    state = engine.load_state()
    if mission_id:
        mission = engine.get_mission(mission_id)
        if mission is None:
            print(f"{RED}[!] Unknown mission '{mission_id}'. Run `quest list`.{RESET}")
            return 1
        unlocked_ids = {m["id"] for m in engine.get_unlocked_missions(state)}
        if mission["id"] not in unlocked_ids:
            if mission.get("bug_hunting") or mission.get("bonus"):
                print(
                    f"{YELLOW}[!] Mission {mission['id']} ({mission['title']}) is locked for at-home practice.{RESET}"
                )
            else:
                print(
                    f"{YELLOW}[!] Mission {mission['id']} is locked. Complete earlier missions first.{RESET}"
                )
            return 1
        engine.activate_mission(mission["id"], reset_home=False)
    else:
        engine.sync_active_environment(force_system_for_current=True)
        state = engine.load_state()
        mission = engine.get_current_mission(state)

    if mission is None:
        print(f"{GREEN}All missions completed!{RESET}")
        return 0

    mid = mission["id"]
    is_done = mid in state.get("completed", {})
    status_badge = f"{GREEN}[COMPLETED]{RESET}" if is_done else f"{YELLOW}[IN PROGRESS]{RESET}"
    tag = ""
    if mission.get("bonus"):
        tag = f" {MAGENTA}[BONUS]{RESET}"
    elif mission.get("bug_hunting"):
        tag = f" {RED}[BUG HUNTING]{RESET}"

    student_id = state["student_id"]
    intro = format_mission_text(mission.get("intro", ""), student_id)
    story = format_mission_text(mission.get("story", ""), student_id)
    desc = format_mission_text(
        mission.get("description", mission.get("objective", "")), student_id
    )
    part_num = int(mission.get("part", 0))
    default_cat = "Warm-Up" if part_num == 0 else f"Part {part_num}"
    category_label = mission.get("category", default_cat)

    print_banner()
    print(f"{BOLD}{CYAN}{category_label}{RESET}")
    print(f"{BOLD}Mission {mid} – {mission['title']}{RESET}{tag}  {status_badge}")
    print("-" * 60)
    if intro:
        print(f"{intro}\n")
    print(f"{BOLD}Story:{RESET}\n{story}\n")
    print(f"{BOLD}Description:{RESET}\n{desc}\n")
    print("-" * 60)
    if mission.get("kind") == "state":
        print(f"When ready, verify with: `{CYAN}quest check{RESET}`  |  Submit flag: `{CYAN}quest submit {FLAG_PREFIX}{{...}}{RESET}`")
    else:
        print(f"Submit flag: `{CYAN}quest submit {FLAG_PREFIX}{{...}}{RESET}`")
    print(f"Need help? `{CYAN}quest hint{RESET}`  |  All missions: `{CYAN}quest list{RESET}`  |  Reset all: `{CYAN}quest killswitch{RESET}`")
    return 0


def cmd_list(engine: QuestEngine) -> int:
    state = engine.load_state()
    missions = engine.load_missions()
    unlocked_ids = {m["id"] for m in engine.get_unlocked_missions(state)}
    completed = state.get("completed", {})
    current = engine.get_current_mission(state)
    current_id = current["id"] if current else None

    print_banner()
    current_part = -1
    for m in missions:
        part = int(m.get("part", 0))
        if part != current_part:
            current_part = part
            part_title = "Warm-Up" if part == 0 else f"Part {part}"
            print(f"\n{BOLD}{CYAN}--- {part_title} ---{RESET}")

        mid = m["id"]
        if mid in completed:
            status = f"{GREEN}[DONE]  {RESET}"
        elif mid == current_id:
            status = f"{YELLOW}[ACTIVE]{RESET}"
        elif mid in unlocked_ids:
            status = f"{CYAN}[OPEN]  {RESET}"
        else:
            status = f"{DIM}[LOCKED]{RESET}"

        badges: List[str] = []
        if m.get("bug_hunting"):
            badges.append(f"{RED}[BugHunt - Home Task]{RESET}")
        if m.get("bonus"):
            badges.append(f"{MAGENTA}[Bonus - Home Task]{RESET}")
        badge_str = (" " + " ".join(badges)) if badges else ""
        cat = m.get("category", "")
        cat_str = f" {DIM}({cat}){RESET}" if cat else ""
        print(f"  {status}  {BOLD}{mid:<3}{RESET} {m['title']}{cat_str}{badge_str}")

    print(f"\nTip: Run `{CYAN}quest show <ID>{RESET}` to switch to any `[OPEN]` or `[DONE]` mission.")
    return 0


def cmd_status(engine: QuestEngine) -> int:
    state = engine.load_state()
    missions = engine.load_missions()
    completed = state.get("completed", {})
    handson_missions = [
        m for m in missions if not m.get("bonus", False) and not m.get("bug_hunting", False)
    ]
    home_missions = [
        m for m in missions if m.get("bonus", False) or m.get("bug_hunting", False)
    ]
    handson_done = sum(1 for m in handson_missions if m["id"] in completed)
    home_done = sum(1 for m in home_missions if m["id"] in completed)
    hints_total = sum(int(v) for v in state.get("hints_used", {}).values())

    print_banner()
    print(f"  {BOLD}Student ID     :{RESET} {state['student_id']}")
    print(f"  {BOLD}Lab Version    :{RESET} {state.get('version', ENGINE_VERSION)}")
    print(f"  {BOLD}Hands-On Quests:{RESET} {handson_done}/{len(handson_missions)} completed")
    print(f"  {BOLD}Home Tasks     :{RESET} {home_done}/{len(home_missions)} completed")
    print(f"  {BOLD}Hints Used     :{RESET} {hints_total}")

    current = engine.get_current_mission(state)
    if current and current["id"] not in completed:
        print(f"  {BOLD}Current        :{RESET} [{current['id']}] {current['title']}")
    else:
        print(f"  {BOLD}Current        :{RESET} {GREEN}All unlocked missions complete!{RESET}")
    return 0


def cmd_hint(engine: QuestEngine, mission_id: Optional[str] = None) -> int:
    state = engine.load_state()
    mission = engine.get_mission(mission_id) if mission_id else engine.get_current_mission(state)
    if mission is None:
        print(f"{RED}[!] Unknown mission.{RESET}")
        return 1

    unlocked_ids = {m["id"] for m in engine.get_unlocked_missions(state)}
    if mission["id"] not in unlocked_ids:
        print(f"{YELLOW}[!] Mission {mission['id']} is locked.{RESET}")
        return 1

    hints = mission.get("hints", [])
    if not hints:
        print("No hints available for this mission.")
        return 0

    mid = mission["id"]
    used = int(state.get("hints_used", {}).get(mid, 0))
    next_tier = min(used + 1, len(hints))
    state.setdefault("hints_used", {})[mid] = next_tier
    engine.save_state(state)

    print(f"{BOLD}Hints for Mission {mid} ({mission['title']}):{RESET}")
    for idx in range(next_tier):
        print(f"  {YELLOW}[Hint {idx + 1}/{len(hints)}]{RESET} {hints[idx]}")
    if next_tier < len(hints):
        print(f"{DIM}Run `quest hint {mid}` again for the next hint ({next_tier}/{len(hints)} shown).{RESET}")
    return 0


def cmd_submit(engine: QuestEngine, flag_arg: Optional[str]) -> int:
    if not flag_arg:
        print(f"Usage: `quest submit {FLAG_PREFIX}{{...}}`")
        return 1
    ok, msg = engine.submit_flag(flag_arg)
    color = GREEN if ok else RED
    print(f"{color}{msg}{RESET}")
    return 0 if ok else 1


def cmd_check(engine: QuestEngine, mission_id: Optional[str] = None) -> int:
    state = engine.load_state()
    target_mission = engine.get_mission(mission_id) if mission_id else engine.get_current_mission(state)
    if target_mission is None:
        print(f"{RED}[!] Mission not found.{RESET}")
        return 1

    unlocked_ids = {m["id"] for m in engine.get_unlocked_missions(state)}
    if target_mission["id"] not in unlocked_ids:
        print(f"{YELLOW}[!] Mission {target_mission['id']} is locked.{RESET}")
        return 1

    ok, msg, mission = engine.run_checker(target_mission["id"])
    if ok:
        flag = engine.get_flag(mission["id"], state)
        if msg.startswith("[+]"):
            print(f"{GREEN}{msg}{RESET}")
        else:
            print(f"{GREEN}[PASS] {msg}{RESET}")
            print(f"\n  {BOLD}Flag:{RESET} {CYAN}{flag}{RESET}")
        print(f"  Submit it now with: `{BOLD}quest submit {flag}{RESET}`")
        return 0
    else:
        if msg.startswith("[-]"):
            print(f"{RED}{msg}{RESET}")
        else:
            print(f"{RED}[FAIL] {msg}{RESET}")
        return 1


def cmd_killswitch(engine: QuestEngine) -> int:
    """Immediate killswitch that wipes all progress and resets all missions without prompting."""
    state = engine.load_state()
    state["completed"] = {}
    state["hints_used"] = {}
    state["initialized_home"] = []
    state["homework_unlocked"] = False
    state.pop("active_mission", None)
    engine.save_state(state)
    for m in engine.load_missions():
        try:
            engine.run_setup_phase(m, state, "home")
        except Exception:
            pass
    engine.sync_active_environment(force_system_for_current=True)
    print(f"{RED}[KILLSWITCH ACTIVATED]{RESET} {GREEN}All progress wiped and all mission files reset to Mission 00.{RESET}")
    return 0


def cmd_reset(engine: QuestEngine, args: List[str]) -> int:
    auto_yes = "--yes" in args or "-y" in args
    filtered = [a for a in args if a not in ("--yes", "-y")]

    if filtered and filtered[0] == "--all":
        if not auto_yes:
            ans = input("Are you sure you want to wipe ALL quest progress and reset home files? [y/N]: ")
            if ans.strip().lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        return cmd_killswitch(engine)

    state = engine.load_state()
    target_id = filtered[0] if filtered else None
    mission = engine.get_mission(target_id) if target_id else engine.get_current_mission(state)
    if mission is None:
        print(f"{RED}[!] Unknown mission.{RESET}")
        return 1

    unlocked_ids = {m["id"] for m in engine.get_unlocked_missions(state)}
    if mission["id"] not in unlocked_ids:
        print(f"{YELLOW}[!] Mission {mission['id']} is locked.{RESET}")
        return 1

    engine.activate_mission(mission["id"], reset_home=True)
    print(f"{GREEN}[+] Mission {mission['id']} ({mission['title']}) files have been restored.{RESET}")
    return 0


def cmd_unlock_homework(engine: QuestEngine, lock: bool = False) -> int:
    state = engine.load_state()
    state["homework_unlocked"] = not lock
    engine.save_state(state)
    engine.sync_active_environment(force_system_for_current=True)
    if lock:
        print(f"{YELLOW}[+] Bug Hunting & Bonus home-task missions are now LOCKED.{RESET}")
    else:
        print(f"{GREEN}[+] Bug Hunting & Bonus home-task missions are now UNLOCKED for unlocked parts.{RESET}")
    return 0


def cmd_doctor(engine: QuestEngine) -> int:
    print_banner()
    print(f"{BOLD}Running Cyberus Linux Quest diagnostics...{RESET}")
    issues: List[str] = []

    required_bins = ["bash", "man", "less", "nano", "tree", "find", "grep", "sort", "sudo", "python3"]
    for b in required_bins:
        if shutil.which(b) is None:
            issues.append(f"Missing binary in PATH: {b}")

    if not engine.home_dir.is_dir():
        issues.append(f"Home directory missing: {engine.home_dir}")

    try:
        state = engine.ensure_initialized()
        _ = state["student_id"]
    except Exception as exc:
        issues.append(f"State initialization check failed: {exc}")

    quest_bin = Path("/usr/local/bin/quest")
    if quest_bin.exists():
        st = quest_bin.stat()
        if not (st.st_mode & stat.S_ISUID):
            issues.append("/usr/local/bin/quest does not have setuid bit (mode 4755)")

    if issues:
        for item in issues:
            print(f"  {RED}[FAIL]{RESET} {item}")
        return 1

    print(f"  {GREEN}[OK]{RESET} Required CLI tools present ({', '.join(required_bins)})")
    print(f"  {GREEN}[OK]{RESET} Volumes & state verified (version {ENGINE_VERSION})")
    print(f"  {GREEN}[OK]{RESET} Privilege dispatcher & permissions healthy")
    print(f"\n{GREEN}DOCTOR: OK{RESET}")
    return 0


def cmd_export(engine: QuestEngine) -> int:
    state = engine.load_state()
    secret = engine.get_secret()
    token = compute_export_token(secret, state)
    print(f"{BOLD}Signed Instructor Progress Token:{RESET}")
    print(token)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    default_uid = os.getuid() if hasattr(os, "getuid") else STUDENT_UID
    caller_uid = int(os.environ.get("QUEST_CALLER_UID", str(default_uid)))
    if caller_uid not in (0, STUDENT_UID):
        print("Unauthorized user.", file=sys.stderr)
        return 1

    engine = QuestEngine()

    try:
        if not argv:
            return cmd_show(engine, None)

        sub = argv[0]
        rest = argv[1:]

        if sub == "--internal-init":
            engine.ensure_initialized()
            engine.sync_active_environment(force_system_for_current=True)
            return 0
        if sub in ("show", "mission"):
            return cmd_show(engine, rest[0] if rest else None)
        if sub == "list":
            return cmd_list(engine)
        if sub == "status":
            return cmd_status(engine)
        if sub == "hint":
            return cmd_hint(engine, rest[0] if rest else None)
        if sub == "submit":
            return cmd_submit(engine, rest[0] if rest else None)
        if sub == "check":
            return cmd_check(engine, rest[0] if rest else None)
        if sub == "killswitch":
            return cmd_killswitch(engine)
        if sub == "reset":
            return cmd_reset(engine, rest)
        if sub == "unlock-homework":
            return cmd_unlock_homework(engine, lock=False)
        if sub == "lock-homework":
            return cmd_unlock_homework(engine, lock=True)
        if sub == "doctor":
            return cmd_doctor(engine)
        if sub == "export":
            return cmd_export(engine)
        if sub in ("-h", "--help", "help"):
            print_banner()
            print("Usage:")
            print("  quest                        Show current mission")
            print("  quest show [id]              Show (and activate) an unlocked mission")
            print("  quest list                   List all missions and their status")
            print("  quest status                 Show overall progress and student ID")
            print("  quest hint [id]              Reveal the next hint tier (up to 3)")
            print(f"  quest submit {FLAG_PREFIX}{{...}}    Submit a captured flag")
            print("  quest check [id]             Validate mission state and reveal flag")
            print("  quest reset [id|--all]       Restore mission files (or reset all)")
            print("  quest killswitch             Immediately wipe all progress and reset all files")
            print("  quest doctor                 Run environment health check")
            print("  quest export                 Print signed progress token for instructor")
            return 0

        if engine.get_mission(sub) is not None:
            return cmd_show(engine, sub)

        print(f"{RED}Unknown command '{sub}'. Run `quest --help` for usage.{RESET}")
        return 1

    except QuestError as exc:
        print(f"{RED}[!] {exc}{RESET}", file=sys.stderr)
        return 1
    except Exception:
        print("Something went wrong, run `quest doctor`.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
