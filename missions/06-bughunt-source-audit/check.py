"""State checker for Mission 06: Bug Hunt: Source Audit & Webshell Triage."""

from pathlib import Path
from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    sec_tok = f"SK_LIVE_{deterministic_token(ctx.student_id, 'm06_secret', 12).upper()}"
    vuln_id = f"VULN-RCE-{deterministic_token(ctx.student_id, 'm06_vuln', 6).upper()}"

    if not ctx.is_dir("target_app"):
        return False, "`~/target_app` is missing! Run `quest reset 06`."

    # 1. Webshell must be deleted
    if ctx.exists("target_app/uploads/avatars/.cache/c99_backdoor.shell.php"):
        return (
            False,
            "The attacker's webshell (`c99_backdoor.shell.php`) is still inside `~/target_app/`. Find it with `find` and delete it with `rm`.",
        )

    # 2. SQL backup must be moved (not still in target_app) into ~/quarantine/
    if ctx.exists("target_app/db/.backups/prod_dump.sql.bak"):
        return (
            False,
            "The exposed SQL backup (`prod_dump.sql.bak`) is still inside `~/target_app/`. Move (`mv`) it to `~/quarantine/`.",
        )

    if not ctx.is_dir("quarantine"):
        return False, "Directory `~/quarantine` does not exist yet. Create it with `mkdir`."

    # Accept either ~/quarantine/prod_dump.sql.bak or any .sql.bak inside ~/quarantine
    q_dir = ctx.home / "quarantine"
    has_backup = ctx.exists("quarantine/prod_dump.sql.bak") or any(
        p.name.endswith(".sql.bak") and not p.is_symlink() for p in q_dir.iterdir() if p.is_file()
    )
    if not has_backup:
        return False, "`prod_dump.sql.bak` was not found inside `~/quarantine/`. Move it there with `mv`."

    # 3. deploy_key permissions must be 600
    try:
        key_mode = ctx.mode("target_app/config/deploy_key")
    except FileNotFoundError:
        return False, "`~/target_app/config/deploy_key` is missing! Run `quest reset 06`."

    if key_mode != 0o600:
        return (
            False,
            f"`~/target_app/config/deploy_key` has mode `{oct(key_mode)[2:]}` instead of `600`. Run `chmod 600 ~/target_app/config/deploy_key`.",
        )

    # 4. triage_report.txt must contain both the hardcoded secret and the top VULN ID
    if not ctx.exists("quarantine/triage_report.txt"):
        return False, "`~/quarantine/triage_report.txt` does not exist yet."

    report = ctx.read("quarantine/triage_report.txt")
    if sec_tok not in report:
        return (
            False,
            "`~/quarantine/triage_report.txt` is missing the hardcoded `CYBERUS_SECRET_KEY` found in `~/target_app/`.",
        )

    if vuln_id not in report:
        return (
            False,
            f"`~/quarantine/triage_report.txt` is missing the highest-scoring vulnerability ID from `~/target_app/vulns.txt`.",
        )

    return True, "Source code audit, webshell removal, backup quarantine, key permissions, and vuln triage verified!"
