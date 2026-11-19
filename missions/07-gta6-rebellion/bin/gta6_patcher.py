#!/usr/bin/env python3
"""/challenge/gta6_patcher binary for Mission 07: GTA VI Physical Disc Rebellion."""

import os
import stat
import sys
from pathlib import Path
from typing import Any, Dict

from engine.core import deterministic_token

ORIGINAL_COMPANIES = (
    "a3da2_sherket_nvidia",
    "a3da2_sherket_nvidia_microntech",
    "a3da2_sherket_nvidia_microntech_sony",
    "a3da2_sherket_nvidia_microntech_sony_meta",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei_microsoft",
)
ROCKSTAR_LINE = "a3da2_sherket_nvidia_microntech_sony_rockstar"


def print_help() -> None:
    print("Usage: /challenge/gta6_patcher [OPTIONS]")
    print("")
    print("Strip digital-only DRM from the leaked GTA VI build.")
    print("")
    print("Options:")
    print("  -v, --verify-drm     Check current Rockstar digital storefront lock status.")
    print("  -b, --burn-disc      Strip digital-only DRM and emit physical disc stream on stderr.")
    print("  -t, --telemetry      Run dummy online telemetry diagnostics.")
    print("  -h, --help           Display this help message and exit.")


def _is_pipe(fd: int) -> bool:
    try:
        if os.readlink(f"/proc/self/fd/{fd}").startswith("pipe:"):
            return True
    except OSError:
        pass
    try:
        return stat.S_ISFIFO(os.fstat(fd).st_mode)
    except OSError:
        return False


def run(ctx: Dict[str, Any]) -> int:
    args = ctx["args"]

    if args in (["-h"], ["--help"]):
        print_help()
        return 0

    if args in (["-v"], ["--verify-drm"]):
        print("[*] Rockstar DRM Status: 100% DIGITAL-ONLY LOCK ACTIVE.")
        return 0

    if args in (["-t"], ["--telemetry"]):
        print("[*] Telemetry: Always-online heartbeat ping active.")
        return 0

    if args not in (["-b"], ["--burn-disc"]):
        print(
            "[-] /challenge/gta6_patcher: Missing or invalid option!\n"
            "[*] Check /challenge/gta6_patcher's documentation (man or --help) to find the option for building the physical disc.",
            file=sys.stderr,
        )
        return 1

    home_dir = Path(ctx["home"]).resolve()
    leak_dir = home_dir / "gta6_leak"
    old_dir = leak_dir / "digital_only_edition"
    phys_dir = leak_dir / "physical_disc_edition"

    # 1. Check permissions and rename of digital_only_edition -> physical_disc_edition
    if old_dir.exists() and not phys_dir.exists():
        try:
            old_mode = stat.S_IMODE(old_dir.lstat().st_mode)
        except OSError:
            old_mode = 0
        if not (old_mode & stat.S_IRUSR) or not (old_mode & stat.S_IXUSR):
            print(
                "[-] ~/gta6_leak/digital_only_edition is still locked by its permissions!\n"
                "[*] Fix its permissions so you can open it, then rename it to ~/gta6_leak/physical_disc_edition.",
                file=sys.stderr,
            )
            return 1
        print(
            "[-] You unlocked ~/gta6_leak/digital_only_edition, but you haven't renamed it yet!\n"
            "[*] Rename ~/gta6_leak/digital_only_edition to ~/gta6_leak/physical_disc_edition.",
            file=sys.stderr,
        )
        return 1

    if not phys_dir.exists() or phys_dir.is_symlink() or not phys_dir.is_dir():
        print(
            "[-] Could not find directory ~/gta6_leak/physical_disc_edition!\n"
            "[*] Fix permissions on ~/gta6_leak/digital_only_edition and rename it to ~/gta6_leak/physical_disc_edition.",
            file=sys.stderr,
        )
        return 1

    try:
        phys_mode = stat.S_IMODE(phys_dir.lstat().st_mode)
    except OSError:
        phys_mode = 0

    # Accept ANY permission mode that allows the owner to enter and read the directory (u+rx)
    if not (phys_mode & stat.S_IRUSR) or not (phys_mode & stat.S_IXUSR):
        print(
            "[-] ~/gta6_leak/physical_disc_edition does not have permissions allowing you to open it!\n"
            "[*] Grant read and execute permissions on ~/gta6_leak/physical_disc_edition.",
            file=sys.stderr,
        )
        return 1

    # 2. Check enemies.txt append
    enemies_file = phys_dir / "enemies.txt"
    if not enemies_file.is_file() or enemies_file.is_symlink():
        print(
            "[-] ~/gta6_leak/physical_disc_edition/enemies.txt is missing!",
            file=sys.stderr,
        )
        return 1

    try:
        lines = [ln.strip() for ln in enemies_file.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    except OSError:
        lines = []

    missing_originals = [comp for comp in ORIGINAL_COMPANIES if comp not in lines]
    if missing_originals:
        print(
            "[-] You erased the original companies in ~/gta6_leak/physical_disc_edition/enemies.txt!\n"
            "[*] Use append redirection (>>) so Rockstar is added to the bottom without erasing existing lines.\n"
            "[*] (Run `quest reset 07` if you need to restore enemies.txt).",
            file=sys.stderr,
        )
        return 1

    if ROCKSTAR_LINE not in lines or lines[-1] != ROCKSTAR_LINE:
        print(
            "[-] a3da2_sherket_nvidia_microntech_sony_rockstar has not been appended to the bottom of\n"
            "    ~/gta6_leak/physical_disc_edition/enemies.txt yet!",
            file=sys.stderr,
        )
        return 1

    # 3. Check that stderr (fd 2) has been redirected to stdout into a pipe (2>&1 | /challenge/disc_burner)
    if not _is_pipe(2):
        print(
            "[-] /challenge/gta6_patcher: My output is printed on standard error (stderr), which normal pipes (|) ignore!\n"
            "[*] Redirect stderr to stdout and pipe it into the program mentioned inside the .tofo file!",
            file=sys.stderr,
        )
        return 1

    tok = deterministic_token(ctx["student_id"], "m07_disc_payload", 12).upper()
    print(f"GTA6_PHYSICAL_DISC_STREAM:{tok}", file=sys.stderr)
    return 0
