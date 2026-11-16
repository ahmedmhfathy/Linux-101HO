#!/usr/bin/env python3
"""Unit and integration tests for Cyberus Linux Quest Engine and Checkers."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.core import (  # noqa: E402
    FLAG_PREFIX,
    WARMUP_FLAG,
    CheckContext,
    QuestEngine,
    compute_export_token,
    compute_flag,
    deterministic_token,
    verify_flag,
)


def load_checker(mission_dir: Path):
    check_file = mission_dir / "check.py"
    spec = importlib.util.spec_from_file_location(f"check_{mission_dir.name}", check_file)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.check


class TestQuestEngineAndMissions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp_dir.name)
        self.state_dir = self.base / "state"
        self.home_dir = self.base / "home"
        self.challenge_dir = self.base / "challenge"
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.challenge_dir.mkdir(parents=True, exist_ok=True)
        self.engine = QuestEngine(
            quest_root=PROJECT_ROOT,
            state_dir=self.state_dir,
            home_dir=self.home_dir,
            challenge_dir=self.challenge_dir,
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_flag_format_is_cyberus(self) -> None:
        self.assertEqual(FLAG_PREFIX, "CYBERUS")
        self.assertEqual(WARMUP_FLAG, "CYBERUS{hello_linux}")
        flag_01 = compute_flag("testsecret", "student-123", "01")
        self.assertTrue(flag_01.startswith("CYBERUS{01_"))
        self.assertTrue(flag_01.endswith("}"))
        self.assertTrue(verify_flag(flag_01, flag_01))
        self.assertFalse(verify_flag(flag_01, "CYBERUS{01_000000000000}"))

    def test_all_session_missions_loaded_in_order(self) -> None:
        missions = self.engine.load_missions()
        ids = [m["id"] for m in missions]
        expected_ids = ["00", "01", "02", "04", "05", "07", "08"]
        self.assertEqual(ids, expected_ids)

    def test_linear_unlock_progression(self) -> None:
        state = self.engine.ensure_initialized()
        unlocked = [m["id"] for m in self.engine.get_unlocked_missions(state)]
        self.assertEqual(unlocked, ["00"])

        state["completed"]["00"] = "2026-11-14T00:00:00Z"
        self.engine.save_state(state)
        unlocked = [m["id"] for m in self.engine.get_unlocked_missions(state)]
        self.assertIn("01", unlocked)
        self.assertNotIn("02", unlocked)

        for mid in ("01", "02"):
            state["completed"][mid] = "2026-11-14T00:00:00Z"
        self.engine.save_state(state)
        unlocked = [m["id"] for m in self.engine.get_unlocked_missions(state)]
        self.assertIn("04", unlocked)
        self.assertEqual(self.engine.get_current_mission(state)["id"], "04")

    def test_check_context_refuses_external_paths_and_symlinks(self) -> None:
        outside_file = self.base / "secret_outside.txt"
        outside_file.write_text("TOP_SECRET", encoding="utf-8")

        ctx = CheckContext(
            home=self.home_dir,
            uid=1000,
            gid=1000,
            student_id="stu-1",
            flag="CYBERUS{test}",
            mission_id="02",
        )
        self.assertFalse(ctx.exists(str(outside_file)))
        self.assertFalse(ctx.exists("../secret_outside.txt"))
        with self.assertRaises(FileNotFoundError):
            ctx.read("../secret_outside.txt")

    def test_mission_02_04_07_checkers(self) -> None:
        student_id = "unit-test-student"
        missions_dir = PROJECT_ROOT / "missions"

        # Mission 02 checker
        check_02 = load_checker(missions_dir / "02-home-sweet-home")
        ctx02 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{02_test}", "02")
        ok, _ = check_02(ctx02)
        self.assertFalse(ok)
        hex_part = deterministic_token(student_id, "mission02_phrase", 8).upper()
        (self.home_dir / "myroom").mkdir(exist_ok=True)
        (self.home_dir / "myroom" / ".code.txt").write_text(
            f"# Instruction: Replace 'CYBERUS' with 'Tofa7aElSafa7a'\nTofa7aElSafa7a-NOTE-{hex_part}\n",
            encoding="utf-8",
        )
        ok, _ = check_02(ctx02)
        self.assertTrue(ok)

        # Mission 04 checker (case-insensitive evidence dir + any filename for top researcher)
        check_04 = load_checker(missions_dir / "04-evidence-room")
        ctx04 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{04_test}", "04")
        h04 = deterministic_token(student_id, "m04_evd", 10)
        (self.home_dir / "EVIDENCE").mkdir(parents=True, exist_ok=True)
        (self.home_dir / "EVIDENCE" / "record_01_02.evd").write_text(
            f"PHRASE: a3da2_sherket_nvidia_microntech\nSIGNATURE: {h04}\n", encoding="utf-8"
        )
        (self.home_dir / "EVIDENCE" / "winner_name.txt").write_text(
            f"hunter_{h04[:6]}\n", encoding="utf-8"
        )
        self.assertTrue(check_04(ctx04)[0])

        # Mission 07 checker
        check_07 = load_checker(missions_dir / "07-redirect-trilogy")
        ctx07 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{07_test}", "07")
        s1 = f"STAGE1-OK-{deterministic_token(student_id, 'm07_s1', 8).upper()}"
        p1 = f"HALF1:PART1-{deterministic_token(student_id, 'm07_p1', 6).upper()}"
        p2 = f"HALF2:PART2-{deterministic_token(student_id, 'm07_p2', 6).upper()}"
        s3 = f"STAGE3-STDERR-{deterministic_token(student_id, 'm07_s3', 8).upper()}"
        (self.home_dir / "myflag").write_text(s1 + "\n", encoding="utf-8")
        (self.home_dir / "twopart.txt").write_text(p1 + "\n" + p2 + "\n", encoding="utf-8")
        (self.home_dir / "stderr_flag.txt").write_text(s3 + "\n", encoding="utf-8")
        self.assertTrue(check_07(ctx07)[0])

    def test_export_token_format(self) -> None:
        state = self.engine.ensure_initialized()
        token = compute_export_token(self.engine.get_secret(), state)
        self.assertTrue(token.startswith("CYBERUS-PROGRESS-v1."))


if __name__ == "__main__":
    unittest.main()
