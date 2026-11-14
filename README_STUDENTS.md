# Cyberus Linux Quest – Student Quickstart Guide

Welcome to **Cyberus Linux Quest**, the hands-on Linux & Bug Hunting lab!
Everything runs inside an isolated local Docker container—nothing on your host operating system is modified.

---

## 1. System Requirements

- **OS:** Kali Linux, Ubuntu, or Debian (VM, dual-boot, or WSL2 with systemd enabled).
- **Resources:** At least **2 GB RAM** and **4 GB free disk space**.
- **Architecture:**
  - Standard Intel/AMD PCs & VMs use `linux-quest-v1.0-amd64.tar`.
  - Apple Silicon Macs (M1/M2/M3/M4 running an ARM64 Kali VM in UTM/Parallels/VMware) use `linux-quest-v1.0-arm64.tar`.

---

## 2. One-Time Setup (Before the Session — Needs Internet)

Open a terminal inside the lab folder and run:

```bash
chmod +x setup-docker.sh start.sh reset.sh
./setup-docker.sh
```

> **Security Note on the `docker` Group:**
> `setup-docker.sh` will ask if you want to add your user to the `docker` group. Adding a user to the `docker` group allows running `docker` commands without `sudo`, which grants root-equivalent privileges on the host OS. If you prefer not to join the `docker` group (for example, on a personal dual-boot laptop), simply answer `N`—`./start.sh` will automatically use `sudo docker` when needed.

---

## 3. Starting the Lab (Works 100% Offline)

Whenever you want to enter the lab, run:

```bash
./start.sh
```

On first launch, `./start.sh` automatically verifies and loads the offline `.tar` image for your CPU architecture and drops you into the container shell as `student@lab:~$`.

Verify your setup before the session by running inside the container:

```bash
quest doctor
```

---

## 4. Essential `quest` Commands Inside the Lab

| Command | Description |
|---|---|
| `quest` | View your current mission briefing and objective |
| `quest list` | List all missions (`00`, `01`–`09`, and bonuses `B1`–`B3`) |
| `quest hint` | Reveal the next hint for the current mission (up to 3 tiers, no penalty!) |
| `quest check` | Validate your mission state and reveal your `CYBERUS{...}` flag |
| `quest submit CYBERUS{...}` | Submit a captured flag to unlock the next mission |
| `quest status` | View your overall progress and Student ID |
| `quest reset <id>` | Restore a mission's files in `/home/student` if you accidentally delete something |
| `quest export` | Print a signed progress token to share with your instructor |

---

## 5. Saving & Resetting Progress

- **Your progress is saved automatically!** Even if you type `exit` or close your terminal, your files in `/home/student` and your quest progress are stored in Docker volumes (`cyberus-quest-v1-home` and `cyberus-quest-v1-state`).
- To reset a single mission inside the container:
  ```bash
  quest reset 03
  ```
- To wipe everything on the host and start fresh:
  ```bash
  ./reset.sh
  ```
- **Uninstalling after the activity (for dual-boot users):**
  ```bash
  ./reset.sh
  sudo apt-get remove -y docker.io
  ```
