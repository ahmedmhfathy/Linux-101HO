#!/usr/bin/env python3
"""Core state, flag generation, privilege separation, and mission management."""

import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import secrets
import shutil
import stat
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import fcntl
except ImportError:
    fcntl = None  # Fallback for non-POSIX unit test hosts

ENGINE_VERSION = "1.0.0"
FLAG_PREFIX = "CYBERUS"
WARMUP_FLAG = f"{FLAG_PREFIX}{{hello_linux}}"

STUDENT_USER = "student"
STUDENT_UID = 1000
STUDENT_GID = 1000

DEFAULT_QUEST_ROOT = Path(os.environ.get("QUEST_ROOT", "/opt/quest"))
DEFAULT_STATE_DIR = Path(os.environ.get("QUEST_STATE_DIR", "/var/lib/quest"))
DEFAULT_HOME_DIR = Path(os.environ.get("QUEST_HOME_DIR", "/home/student"))
DEFAULT_CHALLENGE_DIR = Path(os.environ.get("QUEST_CHALLENGE_DIR", "/challenge"))
RUNAS_TEMPLATE_BIN = Path(os.environ.get("QUEST_RUNAS_BIN", "/usr/local/lib/quest/runas"))


class QuestError(Exception):
    """User-facing quest engine error."""


class FileLock:
    """Advisory file lock using fcntl.flock when available."""

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = lock_path
        self._fd: Optional[int] = None

    def __enter__(self) -> "FileLock":
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        if fcntl is not None:
            fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._fd is not None:
            if fcntl is not None:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                except OSError:
                    pass
            os.close(self._fd)
            self._fd = None


class CheckContext:
    """Safe filesystem helper passed to mission check.py scripts.

    Never follows symlinks escaping the student's home directory.
    """

    def __init__(
        self,
        home: Path,
        uid: int,
        gid: int,
        student_id: str,
        flag: str,
        mission_id: str,
    ) -> None:
        self.home = home.resolve()
        self.uid = uid
        self.gid = gid
        self.student_id = student_id
        self.flag = flag
        self.mission_id = mission_id

    def _safe_resolve(self, path_str: str, allow_symlink_leaf: bool = False) -> Optional[Path]:
        raw = Path(path_str)
        if not raw.is_absolute():
            candidate = self.home / raw
        else:
            candidate = raw

        # Check every prefix component for symlinks escaping self.home
        try:
            rel_parts = candidate.relative_to(self.home).parts
        except ValueError:
            # Try resolving parent in case self.home had a non-canonical prefix
            try:
                rel_parts = candidate.resolve().relative_to(self.home).parts
            except ValueError:
                return None

        curr = self.home
        for idx, part in enumerate(rel_parts):
            curr = curr / part
            is_last = idx == len(rel_parts) - 1
            if curr.is_symlink():
                if is_last and allow_symlink_leaf:
                    target = curr.resolve()
                else:
                    return None
                try:
                    target.relative_to(self.home)
                except ValueError:
                    return None
        try:
            resolved = candidate.resolve()
            resolved.relative_to(self.home)
        except ValueError:
            return None
        return candidate

    def exists(self, path_str: str) -> bool:
        target = self._safe_resolve(path_str)
        if target is None:
            return False
        return target.exists() and not target.is_symlink()

    def is_dir(self, path_str: str) -> bool:
        target = self._safe_resolve(path_str)
        if target is None:
            return False
        return target.is_dir() and not target.is_symlink()

    def read(self, path_str: str, max_bytes: int = 1024 * 1024) -> str:
        target = self._safe_resolve(path_str)
        if target is None or not target.is_file() or target.is_symlink():
            raise FileNotFoundError(f"File not found or invalid path: {path_str}")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(str(target), flags)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise FileNotFoundError(f"Not a regular file: {path_str}")
            data = os.read(fd, max_bytes)
            return data.decode("utf-8", errors="replace")
        finally:
            os.close(fd)

    def stat(self, path_str: str) -> os.stat_result:
        target = self._safe_resolve(path_str)
        if target is None or target.is_symlink():
            raise FileNotFoundError(f"File not found or symlink refused: {path_str}")
        return os.lstat(str(target))

    def mode(self, path_str: str) -> int:
        return stat.S_IMODE(self.stat(path_str).st_mode)


def compute_flag(secret: str, student_id: str, mission_id: str) -> str:
    """Deterministically compute per-student HMAC flag in CYBERUS{} format."""
    if mission_id == "00":
        return WARMUP_FLAG
    msg = f"{student_id}:{mission_id}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()[:12]
    return f"{FLAG_PREFIX}{{{mission_id}_{digest}}}"


def verify_flag(expected_flag: str, submitted_flag: str) -> bool:
    """Constant-time flag comparison."""
    return hmac.compare_digest(expected_flag.strip(), submitted_flag.strip())


def compute_export_token(secret: str, state: Dict[str, Any]) -> str:
    """Generate a signed progress token for instructor verification."""
    completed = sorted(state.get("completed", {}).keys())
    payload_obj = {
        "student_id": state.get("student_id", "unknown"),
        "completed": completed,
        "count": len(completed),
        "version": state.get("version", ENGINE_VERSION),
    }
    payload_json = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True)
    sig = hmac.new(
        secret.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]
    import base64

    b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii").rstrip("=")
    return f"CYBERUS-PROGRESS-v1.{b64}.{sig}"


def deterministic_choice(student_id: str, salt: str, items: List[Any]) -> Any:
    """Pick a deterministic item based on student_id and salt."""
    h = hashlib.sha256(f"{student_id}:{salt}".encode("utf-8")).hexdigest()
    idx = int(h[:8], 16) % len(items)
    return items[idx]


def deterministic_token(student_id: str, label: str, length: int = 10) -> str:
    """Generate a deterministic mission sub-token from student_id + label."""
    h = hashlib.sha256(f"{student_id}:subtoken:{label}".encode("utf-8")).hexdigest()
    return h[:length]


class QuestEngine:
    """Manages state, missions, privilege-separated setups, and validation."""

    def __init__(
        self,
        quest_root: Path = DEFAULT_QUEST_ROOT,
        state_dir: Path = DEFAULT_STATE_DIR,
        home_dir: Path = DEFAULT_HOME_DIR,
        challenge_dir: Path = DEFAULT_CHALLENGE_DIR,
    ) -> None:
        self.quest_root = quest_root
        self.missions_dir = quest_root / "missions"
        self.state_dir = state_dir
        self.home_dir = home_dir
        self.challenge_dir = challenge_dir
        self.secret_file = state_dir / "secret"
        self.state_file = state_dir / "state.json"
        self.lock_file = state_dir / "state.lock"

    def ensure_initialized(self) -> Dict[str, Any]:
        """Initialize /var/lib/quest secret and state.json atomically if needed."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(str(self.state_dir), 0o700)
        except OSError:
            pass

        with FileLock(self.lock_file):
            if not self.secret_file.exists():
                secret_val = secrets.token_hex(32)
                self._atomic_write_text(self.secret_file, secret_val + "\n", mode=0o600)

            if not self.state_file.exists():
                initial_state = {
                    "student_id": str(uuid.uuid4()),
                    "completed": {},
                    "hints_used": {},
                    "initialized_home": [],
                    "version": ENGINE_VERSION,
                    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                self._save_state_unlocked(initial_state)
                return initial_state

            return self._load_state_unlocked()

    def _atomic_write_text(self, path: Path, content: str, mode: int = 0o600) -> None:
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(fd, mode)
            os.write(fd, content.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, str(path))

    def _load_state_unlocked(self) -> Dict[str, Any]:
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        data.setdefault("completed", {})
        data.setdefault("hints_used", {})
        data.setdefault("initialized_home", [])
        data.setdefault("version", ENGINE_VERSION)
        return data

    def _save_state_unlocked(self, state: Dict[str, Any]) -> None:
        text = json.dumps(state, indent=2, sort_keys=True) + "\n"
        self._atomic_write_text(self.state_file, text, mode=0o600)

    def load_state(self) -> Dict[str, Any]:
        self.ensure_initialized()
        with FileLock(self.lock_file):
            return self._load_state_unlocked()

    def save_state(self, state: Dict[str, Any]) -> None:
        self.ensure_initialized()
        with FileLock(self.lock_file):
            self._save_state_unlocked(state)

    def get_secret(self) -> str:
        self.ensure_initialized()
        return self.secret_file.read_text(encoding="utf-8").strip()

    def load_missions(self) -> List[Dict[str, Any]]:
        """Load all missions sorted in canonical progression order."""
        if not self.missions_dir.exists():
            return []
        missions: List[Dict[str, Any]] = []
        for entry in sorted(self.missions_dir.iterdir()):
            mfile = entry / "mission.json"
            if entry.is_dir() and mfile.is_file():
                meta = json.loads(mfile.read_text(encoding="utf-8"))
                meta["dir"] = entry
                missions.append(meta)

        order_map = {
            "00": 0,
            "01": 10,
            "02": 20,
            "03": 30,
            "B1": 35,
            "04": 40,
            "05": 50,
            "06": 60,
            "B2": 65,
            "07": 70,
            "08": 80,
            "09": 90,
            "B3": 95,
        }
        missions.sort(key=lambda m: (order_map.get(m["id"], 999), m["id"]))
        return missions

    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        target = mission_id.upper() if mission_id.upper().startswith("B") else mission_id.zfill(2)
        for m in self.load_missions():
            if m["id"].upper() == target.upper() or m.get("slug", "").lower() == mission_id.lower():
                return m
        return None

    def get_unlocked_missions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine which missions are currently unlocked.

        - Mission 00 is always unlocked.
        - Hands-on required missions (non-bonus, non-bug_hunting) unlock linearly.
        - Missions labeled `bug_hunting` or `bonus` are locked for at-home tasks unless
          `homework_unlocked` is enabled in state (via `quest unlock-homework`), and they
          NEVER block subsequent hands-on missions from unlocking.
        """
        missions = self.load_missions()
        completed = set(state.get("completed", {}).keys())
        homework_unlocked = bool(state.get("homework_unlocked", False))
        unlocked: List[Dict[str, Any]] = []

        all_prev_req_done = True
        unlocked_parts = {0}
        if "00" in completed:
            unlocked_parts.add(1)

        # First pass: hands-on required missions (skipping bonus and bug_hunting)
        for m in missions:
            if m.get("bonus", False) or m.get("bug_hunting", False):
                continue
            mid = m["id"]
            if mid == "00" or all_prev_req_done:
                unlocked.append(m)
                unlocked_parts.add(int(m.get("part", 1)))
            if mid not in completed:
                all_prev_req_done = False

        if not homework_unlocked:
            return unlocked

        # When homework is unlocked, include bug_hunting and bonus missions for unlocked parts
        unlocked_ids = {m["id"] for m in unlocked}
        result: List[Dict[str, Any]] = []
        for m in missions:
            if m["id"] in unlocked_ids:
                result.append(m)
            elif (m.get("bonus", False) or m.get("bug_hunting", False)) and int(
                m.get("part", 1)
            ) in unlocked_parts:
                result.append(m)
        return result

    def get_current_mission(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the first incomplete hands-on required mission, or first incomplete unlocked mission."""
        unlocked = self.get_unlocked_missions(state)
        completed = set(state.get("completed", {}).keys())
        for m in unlocked:
            if not m.get("bonus", False) and not m.get("bug_hunting", False) and m["id"] not in completed:
                return m
        for m in unlocked:
            if m["id"] not in completed:
                return m
        return unlocked[-1] if unlocked else None

    def get_flag(self, mission_id: str, state: Optional[Dict[str, Any]] = None) -> str:
        if state is None:
            state = self.load_state()
        secret = self.get_secret()
        return compute_flag(secret, state["student_id"], mission_id)

    def _build_setup_env(self, mission: Dict[str, Any], state: Dict[str, Any], phase: str) -> Dict[str, str]:
        mid = mission["id"]
        student_id = state["student_id"]
        env = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "LANG": "C.UTF-8",
            "TERM": os.environ.get("TERM", "xterm-256color"),
            "HOME": str(self.home_dir) if phase == "home" else "/root",
            "QUEST_MISSION_ID": mid,
            "QUEST_MISSION_DIR": str(mission["dir"]),
            "QUEST_STUDENT_ID": student_id,
            "QUEST_HOME_DIR": str(self.home_dir),
            "QUEST_CHALLENGE_DIR": str(self.challenge_dir),
            "QUEST_RUNAS_BIN": str(RUNAS_TEMPLATE_BIN),
        }
        # Only pass the raw mission flag to root-executed system phase or B1/B2/B3 setups that bake a file
        if phase == "system" or mid in ("B1",):
            env["QUEST_FLAG"] = self.get_flag(mid, state)
        return env

    def run_setup_phase(self, mission: Dict[str, Any], state: Dict[str, Any], phase: str) -> None:
        """Run setup.sh with strict privilege separation.

        - 'system' runs as root (uid=0, euid=0).
        - 'home' permanently drops privileges to student (uid=1000, gid=1000) so symlinks
          inside /home/student can never overwrite root-owned files.
        """
        setup_script = mission["dir"] / "setup.sh"
        if not setup_script.is_file():
            return

        env = self._build_setup_env(mission, state, phase)

        if phase == "home":
            # Read setup.sh as root before dropping privileges (since /opt/quest/missions is 0700),
            # and pass via `bash -c` so no file open on /opt/quest/missions or /dev/fd is needed
            # after dropping to student, and stdin remains free for heredocs.
            script_content = setup_script.read_text(encoding="utf-8")

            def drop_privs() -> None:
                if hasattr(os, "setresgid") and os.geteuid() == 0:
                    os.setresgid(STUDENT_GID, STUDENT_GID, STUDENT_GID)
                    os.setresuid(STUDENT_UID, STUDENT_UID, STUDENT_UID)

            proc = subprocess.run(
                ["/bin/bash", "-c", script_content, str(setup_script), "home"],
                text=True,
                env=env,
                cwd=str(self.home_dir) if self.home_dir.exists() else None,
                preexec_fn=drop_privs if os.name == "posix" else None,
                capture_output=True,
                timeout=30,
                check=False,
            )
        else:
            proc = subprocess.run(
                ["/bin/bash", str(setup_script), "system"],
                text=True,
                env=env,
                cwd=str(mission["dir"]),
                capture_output=True,
                timeout=30,
                check=False,
            )

        if proc.returncode != 0:
            raise QuestError(
                f"Setup phase '{phase}' failed for mission {mission['id']}: {proc.stderr.strip()}"
            )

    def sync_active_environment(self, force_system_for_current: bool = True) -> None:
        """Ensure unlocked bonuses and current active mission are set up properly."""
        state = self.load_state()
        unlocked = self.get_unlocked_missions(state)
        current = self.get_current_mission(state)
        initialized_home = set(state.get("initialized_home", []))
        state_changed = False

        # Ensure /challenge exists and is root:root 0755
        if os.name == "posix" and os.geteuid() == 0:
            self.challenge_dir.mkdir(parents=True, exist_ok=True)
            os.chown(str(self.challenge_dir), 0, 0)
            os.chmod(str(self.challenge_dir), 0o755)

        # Replay system phase for unlocked non-conflicting missions + current mission
        for m in unlocked:
            mid = m["id"]
            is_current = current is not None and current["id"] == mid
            if is_current or m.get("bonus", False) or mid in ("05", "06"):
                self.run_setup_phase(m, state, "system")

            if (is_current or m.get("bonus", False)) and mid not in initialized_home:
                self.run_setup_phase(m, state, "home")
                initialized_home.add(mid)
                state_changed = True

        # Re-run current mission's system phase last so /challenge/* matches the active mission
        if force_system_for_current and current is not None:
            self.run_setup_phase(current, state, "system")
            if current["id"] not in initialized_home:
                self.run_setup_phase(current, state, "home")
                initialized_home.add(current["id"])
                state_changed = True

        if state_changed:
            with FileLock(self.lock_file):
                latest = self._load_state_unlocked()
                merged = sorted(set(latest.get("initialized_home", [])) | initialized_home)
                latest["initialized_home"] = merged
                self._save_state_unlocked(latest)

    def activate_mission(self, mission_id: str, reset_home: bool = False) -> Dict[str, Any]:
        """Set up a specific unlocked mission's system and (if needed) home phase."""
        state = self.load_state()
        mission = self.get_mission(mission_id)
        if mission is None:
            raise QuestError(f"Unknown mission '{mission_id}'. Run `quest list` to see missions.")

        unlocked_ids = {m["id"] for m in self.get_unlocked_missions(state)}
        if mission["id"] not in unlocked_ids:
            raise QuestError(f"Mission {mission['id']} is still locked. Complete earlier missions first!")

        self.run_setup_phase(mission, state, "system")
        initialized_home = set(state.get("initialized_home", []))
        if reset_home or mission["id"] not in initialized_home:
            self.run_setup_phase(mission, state, "home")
            initialized_home.add(mission["id"])
            with FileLock(self.lock_file):
                latest = self._load_state_unlocked()
                latest["initialized_home"] = sorted(
                    set(latest.get("initialized_home", [])) | initialized_home
                )
                self._save_state_unlocked(latest)
        return mission

    def run_checker(self, mission_id: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Run mission's check.py in a privilege-dropped child process."""
        state = self.load_state()
        if mission_id:
            mission = self.get_mission(mission_id)
        else:
            mission = self.get_current_mission(state)

        if mission is None:
            raise QuestError("No mission found to check.")

        unlocked_ids = {m["id"] for m in self.get_unlocked_missions(state)}
        if mission["id"] not in unlocked_ids:
            raise QuestError(f"Mission {mission['id']} is currently locked.")

        check_file = mission["dir"] / "check.py"
        if not check_file.is_file():
            return False, (
                f"Mission {mission['id']} ({mission['title']}) is a program/flag mission. "
                f"Find the flag and run `quest submit CYBERUS{{...}}`."
            ), mission

        # Read check.py source as root (since /opt/quest/missions is 0700), then execute check(ctx)
        # after dropping privileges to student in a forked child process on POSIX.
        code_str = check_file.read_text(encoding="utf-8")
        flag = self.get_flag(mission["id"], state)

        if os.name == "posix" and os.geteuid() == 0 and hasattr(os, "fork"):
            r_fd, w_fd = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r_fd)
                try:
                    os.setresgid(STUDENT_GID, STUDENT_GID, STUDENT_GID)
                    os.setresuid(STUDENT_UID, STUDENT_UID, STUDENT_UID)
                    ctx = CheckContext(
                        home=self.home_dir,
                        uid=STUDENT_UID,
                        gid=STUDENT_GID,
                        student_id=state["student_id"],
                        flag=flag,
                        mission_id=mission["id"],
                    )
                    namespace: Dict[str, Any] = {"__file__": str(check_file)}
                    exec(compile(code_str, str(check_file), "exec"), namespace)
                    ok, msg = namespace["check"](ctx)
                    payload = json.dumps({"ok": bool(ok), "msg": str(msg)})
                except Exception as exc:
                    payload = json.dumps({"ok": False, "msg": f"Check error: {exc}"})
                os.write(w_fd, payload.encode("utf-8"))
                os.close(w_fd)
                os._exit(0)
            else:
                os.close(w_fd)
                raw = b""
                while True:
                    chunk = os.read(r_fd, 4096)
                    if not chunk:
                        break
                    raw += chunk
                os.close(r_fd)
                os.waitpid(pid, 0)
                try:
                    res = json.loads(raw.decode("utf-8"))
                    return bool(res.get("ok", False)), str(res.get("msg", "")), mission
                except Exception:
                    return False, "Checker subprocess failed unexpectedly.", mission
        else:
            # Non-root or unit test execution
            ctx = CheckContext(
                home=self.home_dir,
                uid=STUDENT_UID,
                gid=STUDENT_GID,
                student_id=state["student_id"],
                flag=flag,
                mission_id=mission["id"],
            )
            namespace = {"__file__": str(check_file)}
            exec(compile(code_str, str(check_file), "exec"), namespace)
            ok, msg = namespace["check"](ctx)
            return bool(ok), str(msg), mission

    def submit_flag(self, submitted_flag: str) -> Tuple[bool, str]:
        """Validate a submitted CYBERUS{...} flag against unlocked missions."""
        cleaned = submitted_flag.strip()
        if not (cleaned.startswith(f"{FLAG_PREFIX}{{") and cleaned.endswith("}")):
            return False, f"Invalid flag format. Flags must look like `{FLAG_PREFIX}{{...}}`."

        state = self.load_state()
        unlocked = self.get_unlocked_missions(state)

        matched_mission: Optional[Dict[str, Any]] = None
        for m in unlocked:
            expected = self.get_flag(m["id"], state)
            if verify_flag(expected, cleaned):
                matched_mission = m
                break

        if matched_mission is None:
            return False, "Incorrect flag (or that mission is not unlocked yet). Keep trying!"

        mid = matched_mission["id"]
        already_done = mid in state.get("completed", {})
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with FileLock(self.lock_file):
            latest = self._load_state_unlocked()
            if mid not in latest["completed"]:
                latest["completed"][mid] = now_iso
                self._save_state_unlocked(latest)

        # Sync environment so newly unlocked mission sets up its files immediately
        self.sync_active_environment(force_system_for_current=True)

        updated_state = self.load_state()
        next_mission = self.get_current_mission(updated_state)
        status_prefix = "Already completed" if already_done else "Mission complete"

        if next_mission and next_mission["id"] not in updated_state["completed"]:
            return (
                True,
                f"[+] {status_prefix}: {mid} – {matched_mission['title']}!\n"
                f"Next up: [{next_mission['id']}] {next_mission['title']}. Run `quest` to view your briefing.",
            )
        return (
            True,
            f"[+] {status_prefix}: {mid} – {matched_mission['title']}!\n"
            f"Congratulations! You have completed all unlocked missions! Run `quest status` or `quest export`.",
        )
