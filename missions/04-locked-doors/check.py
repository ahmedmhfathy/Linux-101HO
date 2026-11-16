"""State checker for Mission 04: Locked Doors."""

import stat
from typing import Tuple

from engine.core import CheckContext


def check(ctx: CheckContext) -> Tuple[bool, str]:
    if not ctx.is_dir("doors"):
        return False, "[-] Directory ~/doors is missing. Run quest reset 04."

    try:
        m1 = ctx.mode("doors/door1.txt")
    except FileNotFoundError:
        return False, "[-] ~/doors/door1.txt is missing. Run quest reset 04."

    if not (m1 & stat.S_IRUSR):
        return False, "[-] Door 1 (~/doors/door1.txt) is still unreadable. Make it readable first."

    try:
        m2 = ctx.mode("doors/door2.key")
    except FileNotFoundError:
        return False, "[-] ~/doors/door2.key is missing. Run quest reset 04."

    if m2 != 0o640:
        return (
            False,
            f"[-] Door 2 (~/doors/door2.key) has permissions {oct(m2)[2:]} instead of 640 (rw-r-----).",
        )

    try:
        mu = ctx.mode("doors/unlock.sh")
    except FileNotFoundError:
        return False, "[-] ~/doors/unlock.sh is missing. Run quest reset 04."

    if not (mu & stat.S_IXUSR):
        return False, "[-] The Lock (~/doors/unlock.sh) is not runnable yet. Make it runnable and run it."

    return (
        True,
        f"[+] Doors verified! Read /opt/vault/flag.txt with sudo (or here is your flag: {ctx.flag})",
    )
