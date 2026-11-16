#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-system}"
HOME_DIR="${QUEST_HOME_DIR:-/home/member}"
STUDENT_ID="${QUEST_STUDENT_ID:-default-student}"

if [[ "$PHASE" == "system" ]]; then
    exit 0
elif [[ "$PHASE" == "home" ]]; then
    rm -rf -- "$HOME_DIR/archive"
    find "$HOME_DIR" -maxdepth 1 -mindepth 1 -iname "evidence" -exec rm -rf -- {} + 2>/dev/null || true
    mkdir -p "$HOME_DIR/archive/decoy_trap/nested"

    echo "TRAP FILE - DELETE THIS WHOLE decoy_trap FOLDER" > "$HOME_DIR/archive/decoy_trap/nested/trap.txt"

    # Generate ~300 decoy files deterministically in Python for speed
    python3 -I - "$HOME_DIR/archive" "$STUDENT_ID" << 'PYEOF'
import hashlib
import pathlib
import sys

archive_dir = pathlib.Path(sys.argv[1])
student_id = sys.argv[2]

h = hashlib.sha256(f"{student_id}:subtoken:m04_evd".encode()).hexdigest()[:10]
top_handle = f"hunter_{h[:6]}"

decoy_phrases = [
    "a3da2_sherket_nvidia",
    "a3da2_sherket_nvidia_microntech_sony",
    "a3da2_sherket_nvidia_microntech_sony_meta",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei",
    "a3da2_sherket_nvidia_microntech_sony_meta_adobe_huawei_microsoft",
]

# Create 15 folders x 20 files = 300 files
target_sector = int(h[:2], 16) % 15
target_idx = int(h[2:4], 16) % 20

for s in range(15):
    sec_dir = archive_dir / f"sector_{s:02d}" / f"box_{(s * 3) % 7:02d}"
    sec_dir.mkdir(parents=True, exist_ok=True)
    for i in range(20):
        if s == target_sector and i == target_idx:
            fpath = sec_dir / f"record_{s:02d}_{i:02d}.evd"
            fpath.write_text(
                f"CASE_ID: CYB-{h.upper()}\n"
                f"STATUS: VERIFIED\n"
                f"PHRASE: a3da2_sherket_nvidia_microntech\n"
                f"SIGNATURE: {h}\n",
                encoding="utf-8",
            )
        else:
            ext = ".evd" if (i % 5 == 0) else ".txt"
            phrase = decoy_phrases[(s * 20 + i) % len(decoy_phrases)]
            fpath = sec_dir / f"item_{s:02d}_{i:02d}{ext}"
            fpath.write_text(
                f"File #{s}-{i}\nPHRASE: {phrase}\nNothing to see here.\n",
                encoding="utf-8",
            )

# Create scores.txt with unsorted numeric scores
scores = [
    (412, "rookie_01"),
    (1890, "net_ninja"),
    (85, "null_byte"),
    (4320, "packet_fox"),
    (910, "shell_hawk"),
    (7840, "crypto_owl"),
    (295, "anon_user"),
    (9945, top_handle),
    (3110, "hex_knight"),
    (640, "zero_cool"),
    (5210, "root_runner"),
]
lines = [f"{score} {handle}" for score, handle in scores]
(archive_dir / "scores.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
PYEOF
else
    echo "Usage: $0 {system|home}" >&2
    exit 1
fi
