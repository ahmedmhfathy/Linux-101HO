#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
CHALLENGE_DIR="${QUEST_CHALLENGE_DIR:-/challenge}"
RUNAS_BIN="${QUEST_RUNAS_BIN:-/usr/local/lib/quest/runas}"
MISSION_DIR="${QUEST_MISSION_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)}"
HOME_DIR="${QUEST_HOME_DIR:-/home/member}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

if [[ "$PHASE" == "system" ]]; then
    mkdir -p "$CHALLENGE_DIR" /usr/share/man/man1 /usr/local/share/man/man1
    if [[ -f "$RUNAS_BIN" ]]; then
        for prog in gta6_patcher disc_burner; do
            cp -f "$RUNAS_BIN" "$CHALLENGE_DIR/$prog"
            chown root:root "$CHALLENGE_DIR/$prog"
            chmod 4755 "$CHALLENGE_DIR/$prog"
            printf '07\n' > "$CHALLENGE_DIR/.mission_$prog"
            chmod 0644 "$CHALLENGE_DIR/.mission_$prog"
        done
    fi
    if [[ -f "$MISSION_DIR/man/gta6_patcher.1" ]]; then
        cp -f "$MISSION_DIR/man/gta6_patcher.1" /usr/share/man/man1/gta6_patcher.1
        cp -f "$MISSION_DIR/man/gta6_patcher.1" /usr/local/share/man/man1/gta6_patcher.1
        chmod 0644 /usr/share/man/man1/gta6_patcher.1 /usr/local/share/man/man1/gta6_patcher.1
        mandb -q >/dev/null 2>&1 || true
    fi
elif [[ "$PHASE" == "home" ]]; then
    if [[ -d "$HOME_DIR/gta6_leak" ]]; then
        chmod -R u+rwx "$HOME_DIR/gta6_leak" 2>/dev/null || true
    fi
    rm -rf -- "$HOME_DIR/gta6_leak"
    mkdir -p "$HOME_DIR/gta6_leak/digital_only_edition"

    cat << 'EOF' > "$HOME_DIR/gta6_leak/digital_only_edition/enemies.txt"
a3da2_sherket_nvidia
a3da2_sherket_nvidia_microntech
a3da2_sherket_nvidia_microntech_sony
a3da2_sherket_nvidia_microntech_sony_meta
a3da2_sherket_nvidia_microntech_sony_meta_adobe
a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei
a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei_microsoft
EOF

    # Generate 1,000 files across 20 subdirectories, plus 1 .tofo file
    python3 -I - "$HOME_DIR/gta6_leak/digital_only_edition" "$STUDENT_ID" << 'PYEOF'
import hashlib
import pathlib
import sys

base_dir = pathlib.Path(sys.argv[1])
student_id = sys.argv[2]

h = hashlib.sha256(f"{student_id}:subtoken:m07_tofo".encode()).hexdigest()
target_dir_idx = int(h[:2], 16) % 20
target_file_idx = int(h[2:4], 16) % 50
exts = [".dat", ".pak", ".lua", ".cfg", ".bin"]

for d in range(20):
    sub = base_dir / f"vice_sector_{d:02d}" / f"chunk_{(d * 7) % 10:02d}"
    sub.mkdir(parents=True, exist_ok=True)
    for f in range(50):
        if d == target_dir_idx and f == target_file_idx:
            tofo_path = sub / f"tofa7a_leak_{d:02d}_{f:02d}.tofo"
            tofo_path.write_text(
                "=============================================================\n"
                "   [Tofa7aElSafa7a Insider Leak - GTA VI Physical Disc]\n"
                "=============================================================\n"
                "Nice job finding the .tofo file!\n\n"
                "To burn the physical disc and get your flag:\n"
                "  1. Check /challenge/gta6_patcher's documentation (man or --help)\n"
                "     to know the option for building the physical disc.\n"
                "  2. Run /challenge/gta6_patcher with that option, redirect its\n"
                "     stderr (stream 2) to stdout (stream 1), and pipe (|) it\n"
                "     into this program:\n\n"
                "     /challenge/disc_burner\n"
                "=============================================================\n",
                encoding="utf-8",
            )
        else:
            ext = exts[(d + f) % len(exts)]
            decoy_path = sub / f"asset_{d:02d}_{f:02d}{ext}"
            decoy_path.write_text(
                f"GTA VI Asset Chunk #{d:02d}-{f:02d}\nSTATUS=ENCRYPTED_DIGITAL_DRM\n",
                encoding="utf-8",
            )
PYEOF

    # Lock the directory so the student must chmod it before entering/renaming
    chmod 0000 "$HOME_DIR/gta6_leak/digital_only_edition"
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
