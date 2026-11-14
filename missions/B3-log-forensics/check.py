"""State checker for Mission B3: Log Forensics."""

import hashlib
from typing import Tuple

from engine.core import CheckContext


def check(ctx: CheckContext) -> Tuple[bool, str]:
    h = hashlib.sha256(f"{ctx.student_id}:subtoken:mB3_ip".encode("utf-8")).hexdigest()
    octet3 = (int(h[:4], 16) % 200) + 10
    octet4 = (int(h[4:8], 16) % 200) + 20
    attacker_ip = f"198.51.{octet3}.{octet4}"

    if not ctx.exists("forensics/attacker_ip.txt"):
        return (
            False,
            "`~/forensics/attacker_ip.txt` does not exist yet. Write the top HTTP 401 attacker IP into it.",
        )

    content = ctx.read("forensics/attacker_ip.txt").strip()
    if attacker_ip not in content:
        return (
            False,
            f"`~/forensics/attacker_ip.txt` does not contain the IP address with the most HTTP 401 responses.",
        )

    return True, f"Brute-force attacker IP ({attacker_ip}) verified!"
