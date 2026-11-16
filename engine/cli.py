#!/usr/bin/env python3
"""Command-line interface for Cyberus Linux Quest (`quest`)."""

import os
import re
import shutil
import stat
import sys
import textwrap
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
CYAN_NORMAL = "\033[0;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
WHITE = "\033[1;37m"
GRAY = "\033[0;90m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BOX_INNER_WIDTH = 65
RIGHT_BORDER_COL = 3 + BOX_INNER_WIDTH + 1  # Column 69

HIGHLIGHT_PATTERNS = re.compile(
    r"(`[^`]+`"
    r"|CYBERUS\{[^}]+\}"
    r"|a3da2_sherket_nvidia_microntech"
    r"|rw-r-----"
    r"|(?<![A-Za-z0-9_])(?:~/[A-Za-z0-9_./-]*|/[A-Za-z0-9_./-]+|\.evd|\.code\.txt|quest check|quest submit|quest list|quest status|reset-machine|killswitch)(?![A-Za-z0-9_]))"
)


def print_header_box(left_title: str, right_plain: str = "", right_colored: str = "") -> None:
    """Render the rounded top header box matching the Cyberus Linux 101 UI."""
    top = f"{GRAY}  ╭{'─' * BOX_INNER_WIDTH}╮{RESET}"
    bot = f"{GRAY}  ╰{'─' * BOX_INNER_WIDTH}╯{RESET}"
    col_end = f"\033[{RIGHT_BORDER_COL}G"
    if right_plain:
        right_col_pos = max(30, RIGHT_BORDER_COL - 2 - len(right_plain))
        right_part = f"\033[{right_col_pos}G{right_colored}"
    else:
        right_part = ""
    mid = (
        f"{GRAY}  │{RESET}  {YELLOW}🐧 LINUX 101{RESET}  {GRAY}│{RESET}  "
        f"{WHITE}{left_title}{RESET}{right_part}{col_end}{GRAY}│{RESET}"
    )
    print(top)
    print(mid)
    print(bot)


def highlight_inline(text: str) -> str:
    """Highlight inline paths, commands, and tokens in Bold Cyan/White."""
    def _repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("`") and token.endswith("`"):
            token = token[1:-1]
        return f"{CYAN}{token}{RESET}"

    return HIGHLIGHT_PATTERNS.sub(_repl, text)


def format_indented_block(text: str, student_id: str, highlight: bool = True) -> str:
    """Substitute dynamic placeholders, wrap at ~66 cols with 2-space indent, and optionally highlight."""
    dirs_01 = ["/var/log"]
    req_dir_01 = deterministic_choice(student_id, "mission01_dir", dirs_01)
    phrase_02 = f"CYBERUS-NOTE-{deterministic_token(student_id, 'mission02_phrase', 8).upper()}"
    rendered = (
        text.replace("{MISSION01_DIR}", req_dir_01)
        .replace("{MISSION02_PHRASE}", phrase_02)
    )
    out_lines: List[str] = []
    for raw_line in rendered.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            out_lines.append("")
            continue
        wrapped = textwrap.wrap(
            stripped,
            width=66,
            break_long_words=False,
            break_on_hyphens=False,
        )
        for wline in wrapped:
            formatted = highlight_inline(wline) if highlight else wline
            out_lines.append(f"  {formatted}")
    return "\n".join(out_lines)


def cmd_show(engine: QuestEngine, mission_id: Optional[str] = None) -> int:
    state = engine.load_state()
    if mission_id:
        mission = engine.get_mission(mission_id)
        if mission is None:
            print(f"{RED}[!] Unknown mission '{mission_id}'. Run `quest list`.{RESET}")
            return 1
        engine.activate_mission(mission["id"], reset_home=False)
        state = engine.load_state()
    else:
        engine.sync_active_environment(force_system_for_current=True)
        state = engine.load_state()
        mission = engine.get_current_mission(state)

    if mission is None:
        print(f"{GREEN}All missions completed!{RESET}")
        return 0

    mid = mission["id"]
    is_done = mid in state.get("completed", {})
    if is_done:
        badge_plain = "[COMPLETED]"
        badge_colored = f"{GREEN}[COMPLETED]{RESET}"
    else:
        badge_plain = "[IN PROGRESS]"
        badge_colored = f"{YELLOW}[IN PROGRESS]{RESET}"

    student_id = state["student_id"]
    part_num = int(mission.get("part", 0))
    default_cat = "Warm-Up" if part_num == 0 else f"Part {part_num}"
    category_label = mission.get("category", default_cat)

    intro_raw = mission.get("intro", "").strip()
    story_raw = mission.get("story", "").strip()
    if intro_raw:
        full_story_raw = f"{intro_raw}\n\n{story_raw}"
    else:
        full_story_raw = story_raw

    story_block = format_indented_block(full_story_raw, student_id, highlight=True)
    desc_raw = mission.get("description", mission.get("objective", "")).strip()
    desc_block = format_indented_block(desc_raw, student_id, highlight=True)

    print()
    print_header_box(category_label, badge_plain, badge_colored)
    print(f"\n  {WHITE}Mission {mid} – {mission['title']}{RESET}\n")
    print(f"  {WHITE}STORY{RESET}")
    print(f"{story_block}\n")
    print(f"  {WHITE}OBJECTIVE{RESET}")
    print(f"{desc_block}\n")
    print(f"{GRAY}  {'─' * (BOX_INNER_WIDTH + 2)}{RESET}")
    if mission.get("kind") == "state":
        print(f"  {CYAN_NORMAL}❯{RESET} Verify progress:  {WHITE}quest check{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} Submit flag:      {WHITE}quest submit {FLAG_PREFIX}{{...}}{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} All challenges:   {WHITE}quest list{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} Check progress:   {WHITE}quest status{RESET}")
    print()
    return 0


def cmd_list(engine: QuestEngine) -> int:
    state = engine.load_state()
    missions = engine.load_missions()
    completed = state.get("completed", {})
    current = engine.get_current_mission(state)
    current_id = current["id"] if current else None

    done_count = sum(1 for m in missions if m["id"] in completed)
    total_count = len(missions)
    right_plain = f"{done_count}/{total_count} Completed"
    right_colored = f"{WHITE}{right_plain}{RESET}"

    print()
    print_header_box("All Challenges", right_plain, right_colored)

    current_part = -1
    for m in missions:
        part = int(m.get("part", 0))
        if part != current_part:
            current_part = part
            part_title = "Warm-Up" if part == 0 else f"Part {part}"
            print(f"\n  {BOLD}{CYAN}--- {part_title} ---{RESET}")

        mid = m["id"]
        if mid in completed:
            status = f"{GREEN}[DONE]  {RESET}"
        elif mid == current_id:
            status = f"{YELLOW}[ACTIVE]{RESET}"
        else:
            status = f"{CYAN}[OPEN]  {RESET}"

        cat = m.get("category", "")
        cat_str = f" {DIM}({cat}){RESET}" if cat else ""
        print(f"    {status}  {BOLD}{mid:<3}{RESET} {m['title']}{cat_str}")

    print(f"\n{GRAY}  {'─' * (BOX_INNER_WIDTH + 2)}{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} View challenge:   {WHITE}quest show <ID>{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} Check progress:   {WHITE}quest status{RESET}")
    print()
    return 0


def cmd_status(engine: QuestEngine) -> int:
    state = engine.load_state()
    missions = engine.load_missions()
    completed = state.get("completed", {})

    done_count = sum(1 for m in missions if m["id"] in completed)
    total_count = len(missions)
    pct = int(round((done_count / total_count) * 100)) if total_count else 0
    bar_width = 20
    filled = int(round((done_count / total_count) * bar_width)) if total_count else 0
    filled = max(0, min(bar_width, filled))
    if done_count > 0 and filled == 0:
        filled = 1
    bar_str = f"{WHITE}{'█' * filled}{GRAY}{'░' * (bar_width - filled)}{RESET}"

    right_plain = f"{done_count}/{total_count} Completed"
    right_colored = f"{WHITE}{right_plain}{RESET}"

    print()
    print_header_box("Mission Status", right_plain, right_colored)
    print(f"\n  {WHITE}PROGRESS{RESET}")
    print(f"  [{bar_str}] {WHITE}{pct}%{RESET}  ({done_count} of {total_count} solved)\n")

    print(f"  {WHITE}ACTIVE MISSION{RESET}")
    current = engine.get_current_mission(state)
    if current and current["id"] not in completed:
        cat = current.get("category", "")
        cat_part = f"  ({cat})" if cat else ""
        print(f"  {CYAN_NORMAL}❯{RESET} [{current['id']}] {WHITE}{current['title']}{RESET}{cat_part}\n")
    elif current:
        cat = current.get("category", "")
        cat_part = f"  ({cat})" if cat else ""
        print(f"  {GREEN}✔{RESET} All missions completed! (Last: [{current['id']}] {current['title']}{cat_part})\n")
    else:
        print(f"  {GREEN}✔ All missions completed!{RESET}\n")

    print(f"  {WHITE}COMPLETED MISSIONS{RESET}")
    completed_missions = [m for m in missions if m["id"] in completed]
    if completed_missions:
        for m in completed_missions:
            print(f"  {GREEN}✔{RESET} [{m['id']}] {m['title']}")
    else:
        print(f"  {GRAY}None yet — run `quest` to start Mission 00!{RESET}")

    print(f"\n{GRAY}  {'─' * (BOX_INNER_WIDTH + 2)}{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} Resume active:    {WHITE}quest{RESET}")
    print(f"  {CYAN_NORMAL}❯{RESET} All challenges:   {WHITE}quest list{RESET}")
    print()
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


def cmd_reset_machine(engine: QuestEngine) -> int:
    """Reset the machine filesystem state (delete user folders/files & restore challenge files) WITHOUT losing progress."""
    state = engine.load_state()
    active_id = state.get("active_mission")
    state["initialized_home"] = []
    state.pop("m05_vault_unsealed", None)
    engine.save_state(state)

    engine.wipe_home_directory()
    for m in engine.load_missions():
        try:
            engine.run_setup_phase(m, state, "home")
        except Exception:
            pass
    engine.sync_active_environment(force_system_for_current=True)
    if active_id:
        try:
            engine.activate_mission(active_id, reset_home=True)
        except Exception:
            pass

    print(
        f"{YELLOW}[MACHINE RESET]{RESET} {GREEN}All user-created files/folders removed and challenge files restored to original state (mission progress preserved).{RESET}"
    )
    return 0


def cmd_killswitch(engine: QuestEngine, args: Optional[List[str]] = None) -> int:
    """Immediate killswitch that wipes all progress and resets all missions without prompting."""
    if args and any(a in ("--soft", "-s", "machine", "files", "--machine") for a in args):
        return cmd_reset_machine(engine)

    state = engine.load_state()
    state["completed"] = {}
    state["hints_used"] = {}
    state["initialized_home"] = []
    state["homework_unlocked"] = False
    state.pop("active_mission", None)
    state.pop("m05_vault_unsealed", None)
    engine.save_state(state)

    engine.wipe_home_directory()
    for m in engine.load_missions():
        try:
            engine.run_setup_phase(m, state, "home")
        except Exception:
            pass
    engine.sync_active_environment(force_system_for_current=True)
    print(f"{RED}[KILLSWITCH ACTIVATED]{RESET} {GREEN}All progress wiped and all mission files reset to Mission 00.{RESET}")
    return 0


def cmd_internal_unseal_vault(engine: QuestEngine, args: List[str]) -> int:
    """Validate Mission 04 Door 1, Door 2, unlock.sh, and passcode, then unseal /opt/vault/flag.txt."""
    state = engine.load_state()
    doors_dir = engine.home_dir / "doors"
    door1 = doors_dir / "door1.txt"
    door2 = doors_dir / "door2.key"
    unlock_sh = doors_dir / "unlock.sh"

    if not door1.is_file() or door1.is_symlink():
        print("[-] ~/doors/door1.txt is missing! Run `quest reset 04`.", file=sys.stderr)
        return 1
    m1 = stat.S_IMODE(door1.lstat().st_mode)
    if not (m1 & stat.S_IRUSR):
        print("[-] Door 1 (~/doors/door1.txt) is still locked! Make it readable first.", file=sys.stderr)
        return 1

    if not door2.is_file() or door2.is_symlink():
        print("[-] ~/doors/door2.key is missing! Run `quest reset 04`.", file=sys.stderr)
        return 1
    m2 = stat.S_IMODE(door2.lstat().st_mode)
    if m2 != 0o640:
        print(
            f"[-] Door 2 (~/doors/door2.key) is still jammed (current mode: {oct(m2)[2:]})! "
            "Change its permissions so they read exactly rw-r----- (640).",
            file=sys.stderr,
        )
        return 1

    if not unlock_sh.is_file() or unlock_sh.is_symlink():
        print("[-] ~/doors/unlock.sh is missing! Run `quest reset 04`.", file=sys.stderr)
        return 1
    m_unlock = stat.S_IMODE(unlock_sh.lstat().st_mode)
    if not (m_unlock & stat.S_IXUSR):
        print("[-] ~/doors/unlock.sh is not runnable yet!", file=sys.stderr)
        return 1

    expected_code = deterministic_token(state["student_id"], "m05_door1_code", 8).upper()
    raw_input_code = " ".join(args).strip()
    if raw_input_code.upper().startswith("PASSCODE:"):
        raw_input_code = raw_input_code.split(":", 1)[1].strip()

    if raw_input_code.upper() != expected_code:
        print("[-] Invalid passcode! Read ~/doors/door1.txt to get the Door 1 PASSCODE.", file=sys.stderr)
        return 1

    flag = engine.get_flag("04", state)
    vault_dir = Path("/opt/vault")
    vault_dir.mkdir(parents=True, exist_ok=True)
    vault_text = (
        f"[+] VAULT UNLOCKED!\n"
        f"Flag: {flag}\n"
        f"Submit your flag with: quest submit {flag}\n"
    )
    for vfile in (vault_dir / "flag.txt", vault_dir / "vault.txt"):
        vfile.write_text(vault_text, encoding="utf-8")
        os.chown(str(vfile), 0, 0)
        os.chmod(str(vfile), 0o600)

    state["m05_vault_unsealed"] = True
    engine.save_state(state)
    print("[+] Door 1 and Door 2 verified!")
    print("[+] The Vault (/opt/vault/flag.txt) is now UNSEALED. Use super powers (sudo) to read it!")
    return 0


def cmd_internal_check_vault(engine: QuestEngine) -> int:
    """Verify whether Mission 04 doors and unlock.sh have unsealed the vault."""
    state = engine.load_state()
    doors_dir = engine.home_dir / "doors"
    door1 = doors_dir / "door1.txt"
    door2 = doors_dir / "door2.key"
    unlock_sh = doors_dir / "unlock.sh"

    unsealed = bool(state.get("m05_vault_unsealed", False))
    try:
        m1 = stat.S_IMODE(door1.lstat().st_mode)
        m2 = stat.S_IMODE(door2.lstat().st_mode)
        mu = stat.S_IMODE(unlock_sh.lstat().st_mode)
        doors_ok = bool(m1 & stat.S_IRUSR) and (m2 == 0o640) and bool(mu & stat.S_IXUSR)
    except OSError:
        doors_ok = False

    if not (unsealed and doors_ok):
        print("[-] ACCESS DENIED: The vault is still sealed!")
        print("[*] Unlock Door 1 and Door 2 using ~/doors/unlock.sh first.")
        return 1

    flag = engine.get_flag("04", state)
    print(f"[+] VAULT UNLOCKED!\nFlag: {flag}\nSubmit your flag with: quest submit {flag}")
    return 0


def cmd_reset(engine: QuestEngine, args: List[str]) -> int:
    auto_yes = "--yes" in args or "-y" in args
    filtered = [a for a in args if a not in ("--yes", "-y")]

    if filtered and filtered[0] in ("--machine", "machine"):
        return cmd_reset_machine(engine)

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

    engine.activate_mission(mission["id"], reset_home=True)
    print(f"{GREEN}[+] Mission {mission['id']} ({mission['title']}) files have been restored.{RESET}")
    return 0


def cmd_doctor(engine: QuestEngine) -> int:
    print()
    print_header_box("System Diagnostics", f"v{ENGINE_VERSION}", f"{WHITE}v{ENGINE_VERSION}{RESET}")
    print(f"\n  {BOLD}Running Cyberus Linux Quest diagnostics...{RESET}")
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
        if sub == "--internal-unseal-vault":
            return cmd_internal_unseal_vault(engine, rest)
        if sub == "--internal-check-vault":
            return cmd_internal_check_vault(engine)
        if sub in ("show", "mission"):
            return cmd_show(engine, rest[0] if rest else None)
        if sub == "list":
            return cmd_list(engine)
        if sub == "status":
            return cmd_status(engine)
        if sub == "submit":
            return cmd_submit(engine, rest[0] if rest else None)
        if sub == "check":
            return cmd_check(engine, rest[0] if rest else None)
        if sub == "killswitch":
            return cmd_killswitch(engine, rest)
        if sub in ("reset-machine", "softswitch", "clean-machine"):
            return cmd_reset_machine(engine)
        if sub == "reset":
            return cmd_reset(engine, rest)
        if sub == "doctor":
            return cmd_doctor(engine)
        if sub == "export":
            return cmd_export(engine)
        if sub in ("-h", "--help", "help"):
            print()
            print_header_box("Command Reference", f"v{ENGINE_VERSION}", f"{WHITE}v{ENGINE_VERSION}{RESET}")
            print("\n  Usage:")
            print("    quest                        Show current challenge")
            print("    quest show [id]              Show (and activate) a challenge")
            print("    quest list                   List all available challenges")
            print("    quest status                 View your progress and completed missions")
            print(f"    quest submit {FLAG_PREFIX}{{...}}    Submit a captured flag")
            print("    quest check [id]             Validate mission state and reveal flag")
            print("    reset-machine                Reset lab files (keeps your progress)")
            print("    killswitch                   Wipe all progress and restart from 0")
            print("    quest doctor                 Run environment health check")
            print("    quest export                 Print signed progress token for instructor\n")
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
