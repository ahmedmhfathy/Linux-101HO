"""State checker for Mission 03: Bug Hunt: Recon & Dotfile Leak."""

from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    # Accepted variations:
    # - config.ini has DEBUG=false (case-insensitive key/value check, no DEBUG=true remaining)
    # - ~/bounty_report/finding.txt contains both the leaked endpoint and the staging token
    #   (either full KEY=VALUE or the value itself).
    endp_tok = deterministic_token(ctx.student_id, "m03_endpoint", 10)
    stg_tok = deterministic_token(ctx.student_id, "m03_staging", 10).upper()
    expected_endpoint = f"/api/v2/debug-console-{endp_tok}"
    expected_staging = f"STG-{stg_tok}"

    if not ctx.exists("webapp_recon/config.ini"):
        return False, "`~/webapp_recon/config.ini` is missing! Run `quest reset 03` if you deleted it."

    cfg = ctx.read("webapp_recon/config.ini")
    cfg_lines = [line.strip().replace(" ", "") for line in cfg.splitlines() if not line.strip().startswith("#")]
    if any(line.upper() == "DEBUG=TRUE" for line in cfg_lines) or not any(
        line.upper() == "DEBUG=FALSE" for line in cfg_lines
    ):
        return False, "`~/webapp_recon/config.ini` still has `DEBUG=true` (or is missing `DEBUG=false`). Edit it with `nano`."

    if not ctx.is_dir("bounty_report"):
        return False, "Directory `~/bounty_report` does not exist yet. Create it with `mkdir`."

    if not ctx.exists("bounty_report/finding.txt"):
        return False, "Report file `~/bounty_report/finding.txt` does not exist yet."

    report = ctx.read("bounty_report/finding.txt")
    if expected_endpoint not in report:
        return (
            False,
            "`~/bounty_report/finding.txt` is missing the leaked `INTERNAL_ENDPOINT` from the hidden `.env.bak` file.",
        )

    if expected_staging not in report:
        return (
            False,
            "`~/bounty_report/finding.txt` is missing the leaked `STAGING_TOKEN` from `~/webapp_recon/logs/http_response.txt`.",
        )

    return True, "Bug bounty recon report and config hardening verified!"
