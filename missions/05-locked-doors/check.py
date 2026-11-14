"""State checker for Mission 05: Locked Doors."""

import stat
from typing import Tuple

from engine.core import CheckContext, deterministic_token


def check(ctx: CheckContext) -> Tuple[bool, str]:
    vault_tok = f"VAULT-{deterministic_token(ctx.student_id, 'm05_vault', 12).upper()}"

    if not ctx.is_dir("doors"):
        return False, "Directory `~/doors` is missing. Run `quest reset 05`."

    try:
        m1 = ctx.mode("doors/door1.txt")
    except FileNotFoundError:
        return False, "`~/doors/door1.txt` is missing. Run `quest reset 05`."

    if not (m1 & stat.S_IRUSR):
        return False, "Door 1 (`~/doors/door1.txt`) is still unreadable by owner. Use `chmod u+r ~/doors/door1.txt`."

    try:
        m2 = ctx.mode("doors/unlock.sh")
    except FileNotFoundError:
        return False, "`~/doors/unlock.sh` is missing. Run `quest reset 05`."

    if not (m2 & stat.S_IXUSR):
        return False, "Door 2 (`~/doors/unlock.sh`) is not executable yet. Use `chmod +x ~/doors/unlock.sh`."

    if not ctx.exists("doors/.door2_unlocked"):
        return False, "You made `~/doors/unlock.sh` executable, but haven't run it yet! Run `~/doors/unlock.sh`."

    try:
        m3 = ctx.mode("doors/door3.key")
    except FileNotFoundError:
        return False, "`~/doors/door3.key` is missing. Run `quest reset 05`."

    if m3 != 0o640:
        return (
            False,
            f"Door 3 (`~/doors/door3.key`) has octal permissions `{oct(m3)[2:]}` instead of `640` (`rw-r-----`).",
        )

    if not ctx.exists("doors/vault.txt"):
        return (
            False,
            "Vault file `~/doors/vault.txt` is missing. Run `sudo -l`, read `/opt/vault/flag.txt` with `sudo`, and write the `VAULT_SECRET` into `~/doors/vault.txt`.",
        )

    vault_content = ctx.read("doors/vault.txt")
    if vault_tok not in vault_content:
        return False, "`~/doors/vault.txt` does not contain the `VAULT_SECRET` from `/opt/vault/flag.txt`."

    return True, "All 3 permission doors and the root sudo vault verified!"
