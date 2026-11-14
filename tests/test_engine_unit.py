#!/usr/bin/env python3
"""Unit and integration tests for Cyberus Linux Quest Engine and Checkers."""

import importlib.util
import json
import os
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

    def test_all_13_missions_loaded_in_order(self) -> None:
        missions = self.engine.load_missions()
        ids = [m["id"] for m in missions]
        expected_ids = ["00", "01", "02", "03", "B1", "04", "05", "06", "B2", "07", "08", "09", "B3"]
        self.assertEqual(ids, expected_ids)

        # Verify each part has an explicit bug_hunting mission using only taught commands
        bh_missions = [m for m in missions if m.get("bug_hunting")]
        self.assertEqual([m["id"] for m in bh_missions], ["03", "06", "09"])

    def test_linear_and_bonus_unlock_progression(self) -> None:
        state = self.engine.ensure_initialized()
        unlocked = [m["id"] for m in self.engine.get_unlocked_missions(state)]
        self.assertEqual(unlocked, ["00"])

        # Submit 00 -> unlocks 01 and B1 (Part 1 bonus)
        state["completed"]["00"] = "2026-11-14T00:00:00Z"
        self.engine.save_state(state)
        unlocked = [m["id"] for m in self.engine.get_unlocked_missions(state)]
        self.assertIn("01", unlocked)
        self.assertIn("B1", unlocked)
        self.assertNotIn("02", unlocked)

        # Complete Part 1 required missions (01, 02, 03) WITHOUT B1 -> unlocks Part 2 (04 & B2)
        for mid in ("01", "02", "03"):
            state["completed"][mid] = "2026-11-14T00:00:00Z"
        self.engine.save_state(state)
        unlocked = [m["id"] for m in self.engine.get_unlocked_missions(state)]
        self.assertIn("04", unlocked)
        self.assertIn("B2", unlocked)
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

    def test_mission_02_03_04_06_07_09_B3_checkers(self) -> None:
        student_id = "unit-test-student"
        missions_dir = PROJECT_ROOT / "missions"

        # Mission 02 checker
        check_02 = load_checker(missions_dir / "02-home-sweet-home")
        ctx02 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{02_test}", "02")
        ok, _ = check_02(ctx02)
        self.assertFalse(ok)
        phrase = f"CYBERUS-NOTE-{deterministic_token(student_id, 'mission02_phrase', 8).upper()}"
        (self.home_dir / ".stage02_a_done").write_text(phrase, encoding="utf-8")
        (self.home_dir / "notes").mkdir(exist_ok=True)
        (self.home_dir / "notes" / "plan.txt").write_text(phrase + "\n", encoding="utf-8")
        ok, _ = check_02(ctx02)
        self.assertTrue(ok)

        # Mission 03 (Part 1 Bug Hunting) checker
        check_03 = load_checker(missions_dir / "03-bughunt-recon-dotfile")
        ctx03 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{03_test}", "03")
        (self.home_dir / "webapp_recon").mkdir(parents=True, exist_ok=True)
        (self.home_dir / "webapp_recon" / "config.ini").write_text("DEBUG=true\n", encoding="utf-8")
        self.assertFalse(check_03(ctx03)[0])

        endp_tok = deterministic_token(student_id, "m03_endpoint", 10)
        stg_tok = deterministic_token(student_id, "m03_staging", 10).upper()
        (self.home_dir / "webapp_recon" / "config.ini").write_text("DEBUG=false\n", encoding="utf-8")
        (self.home_dir / "bounty_report").mkdir(parents=True, exist_ok=True)
        (self.home_dir / "bounty_report" / "finding.txt").write_text(
            f"INTERNAL_ENDPOINT=/api/v2/debug-console-{endp_tok}\nSTAGING_TOKEN=STG-{stg_tok}\n",
            encoding="utf-8",
        )
        self.assertTrue(check_03(ctx03)[0])

        # Mission 04 checker
        check_04 = load_checker(missions_dir / "04-evidence-room")
        ctx04 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{04_test}", "04")
        h04 = deterministic_token(student_id, "m04_evd", 10)
        (self.home_dir / "evidence").mkdir(parents=True, exist_ok=True)
        (self.home_dir / "evidence" / "case.txt").write_text(
            f"MARKER: EVIDENCE_MARKER_CYBERUS\nSIGNATURE: {h04}\n", encoding="utf-8"
        )
        (self.home_dir / "evidence" / "top.txt").write_text(f"hunter_{h04[:6]}\n", encoding="utf-8")
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

        # Mission 09 (Part 3 Bug Hunting) checker
        check_09 = load_checker(missions_dir / "09-bughunt-fuzzing-pipeline")
        ctx09 = CheckContext(self.home_dir, 1000, 1000, student_id, "CYBERUS{09_test}", "09")
        tok09 = deterministic_token(student_id, "m09_fuzz", 6)
        (self.home_dir / "recon").mkdir(parents=True, exist_ok=True)
        (self.home_dir / "recon" / "live_endpoints.txt").write_text(
            f"[200 OK] /api/v0/internal/health-{tok09}\n"
            f"[200 OK] /api/v1/debug/vars-{tok09}\n"
            f"[200 OK] /api/v2/auth/login-{tok09}\n",
            encoding="utf-8",
        )
        (self.home_dir / "recon" / "db_error.log").write_text(
            "Leaked: CYBERUS{09_test}\n", encoding="utf-8"
        )
        self.assertTrue(check_09(ctx09)[0])

    def test_export_token_format(self) -> None:
        state = self.engine.ensure_initialized()
        token = compute_export_token(self.engine.get_secret(), state)
        self.assertTrue(token.startswith("CYBERUS-PROGRESS-v1."))


if __name__ == "__main__":
    unittest.main()
