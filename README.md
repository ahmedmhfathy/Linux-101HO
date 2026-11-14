# Cyberus Linux Quest (`CYBERUS{}` Bug Hunting Edition)

A Docker-based, hands-on Linux & Bug Hunting CTF activity designed for university cybersecurity and bug-hunting sessions.

## Features

- **100% Isolated Local Container (`ubuntu:24.04`)**: Zero modifications to the student's host OS beyond Docker Engine; runs completely offline (`--network none`).
- **Real Interactive Bash + TTY**: Full support for `man`, `less`, `nano`, `tree`, pipes (`|`), and streams (`stdin`, `stdout`, `stderr`).
- **Hardened Privilege Dispatcher (`src/runas.c`)**:
  - Resolves `/proc/self/exe` rather than accepting arbitrary file paths on the command line (mitigating `runas` bypasses).
  - Preserves exact kernel `argv[0]` (`QUEST_INVOKED_AS`) and real caller UID (`QUEST_CALLER_UID`) after `clearenv()`.
  - Drops privileges permanently to `student` (`uid=1000, gid=1000`) before executing `setup.sh home` or running `check.py` state checkers (preventing symlink/TOCTOU attacks inside `/home/student`).
- **`CYBERUS{...}` Per-Student Dynamic Flags**:
  - Warm-up (`00`): `CYBERUS{hello_linux}`
  - Missions `01`–`09` and `B1`–`B3`: `CYBERUS{<id>_<12hex_hmac>}`
- **13 Missions Across 3 Parts (Including Dedicated Bug Hunting Missions)**:
  - **Warm-up**: `00` – Hello, Linux
  - **Part 1 (Navigation, Help, Files)**:
    - `01` – Position Thyself (`pwd`, `cd`, absolute vs relative paths)
    - `02` – Home Sweet Home (`help`, `man`, `--help`, `~`, `mkdir`, `nano`, `cat`)
    - `03` – **Bug Hunt: Recon & Dotfile Leak** (`cd`, `ls -a`, `tree`, `cat`, `head`, `tail`, `less`, `mkdir`, `nano`)
    - `B1` – Treasure Hunt *(Bonus)*
  - **Part 2 (Files, Permissions, Sudo)**:
    - `04` – The Evidence Room (`find`, `grep -r`, `sort -n`, `cp`, `mv`, `rm -r`)
    - `05` – Locked Doors (`ls -l`, `chmod`, `sudo -l`, `sudo`)
    - `06` – **Bug Hunt: Source Audit & Webshell Triage** (`find`, `grep -r`, `sort -n`, `cp`, `mv`, `rm`, `chmod`, `sudo`)
    - `B2` – GTFO *(Bonus – GTFOBins `sudo less` `!sh` escape)*
  - **Part 3 (Redirection & Pipes)**:
    - `07` – Redirect Trilogy (`>`, `>>`, `2>`, `2>&1`, `2>/dev/null`)
    - `08` – Pipe Dream (`|`, `stdin`, `<`)
    - `09` – **Bug Hunt: Fuzzing & Exploit Pipeline** (`>`, `2>`, `2>/dev/null`, `<`, `|`, `grep`, `sort`)
    - `B3` – Log Forensics *(Bonus)*

## Quick Start (Development & Testing)

```bash
# Build the runtime image
docker build --target runtime -t linux-quest:1.0 .

# Run the automated end-to-end test harness (all 13 missions + security checks)
docker run --rm --network none linux-quest:1.0 /opt/quest/tests/run_all.sh

# Launch the interactive student lab
./start.sh
```

## Building Offline Release Archives (`amd64` / `arm64`)

```bash
./build-release.sh --arch all
```
