# Cyberus Linux Quest

An interactive, Docker-based Linux hands-on lab featuring progressive command-line challenges.

## Challenges Overview

### Warm-Up
- **Mission `00` – Hello, Linux (`Warm-Up`)**: Getting started with the `quest` CLI and submitting your first `CYBERUS{...}` flag.

### Part 1 – Navigation & Working with Files
- **Mission `01` – Right Place, Right Path (`Navigation`)**: Navigating the Linux filesystem and executing programs from specific directories.
- **Mission `02` – Home Sweet Home (`Working with Files`)**: Reading program documentation, working with directories and hidden files, and editing text files in the terminal.

### Part 2 – Searching, Organizing & Permissions
- **Mission `03` – The Evidence Room (`Searching & Organizing Files`)**: Searching through a large directory archive, organizing files, and cleaning up decoy directories.
- **Mission `04` – Locked Doors (`Permissions & Privileges`)**: Inspecting and modifying file permissions and using elevated privileges to access restricted files.

### Part 3 – Redirection & Pipelines
- **Mission `05` – Redirect Trilogy (`Input & Output Redirection`)**: Controlling standard output (`stdout`) and standard error (`stderr`) streams across three stages.
- **Mission `06` – Pipe Dream (`Pipelines & Standard Input`)**: Chaining multiple programs together in an assembly line and feeding data into standard input (`stdin`).

---

## Lab Commands Inside the Container

```bash
quest                        # Show your current challenge
quest list                   # List all available challenges
quest show <ID>              # Switch to a challenge
quest status                 # View your progress and completed missions
quest check                  # Verify mission state (for state-based missions)
quest submit CYBERUS{...}    # Submit a captured flag
reset-machine                # Reset lab files (keeps your progress)
killswitch                   # Wipe all progress and restart from 0
```

---

## Quick Start

### Option 1: Run Online in Your Browser (GitHub Codespaces — No Linux or Docker Needed)

If you are on Windows, macOS, or do not have Linux/Docker installed locally, you can launch the lab directly in your browser using **GitHub Codespaces**:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ahmedmhfathy/Linux-101HO?quickstart=1)

1. Click the **Open in GitHub Codespaces** button above (or click **Code → Codespaces → Create codespace on main** on this repository).
2. Wait ~1 minute for the container to build and open in your browser.
3. Open the terminal panel (`Ctrl+\``) — you will land directly at `member@cyberus:~$` with the lab ready to play!

---

### Option 2: Run Locally with Docker (Kali / Debian / Ubuntu / WSL2)

> **Note:** `setup-docker.sh` works on **Debian-based distributions only** (Kali, Debian, Ubuntu, and similar). On any other distribution, install Docker yourself by following the official guide at <https://docs.docker.com/engine/install/>, then continue from the `docker build` step.

```bash
# install
git clone https://github.com/ahmedmhfathy/Linux-101HO.git
cd Linux-101HO

# Docker setup (if Docker is not installed yet)
chmod +x setup-docker.sh ; ./setup-docker.sh

# Build the runtime image
docker build --target runtime -t linux-quest:1.0 .

# Run the automated end-to-end test harness
docker run --rm --network none linux-quest:1.0 /opt/quest/tests/run_all.sh

# Launch the interactive student lab
chmod +x start.sh ; ./start.sh
```

> 🎥 **[Setup Walkthrough](https://drive.google.com/file/d/1ad6Zwo1yqg8rPoZeE4z26rXRzkU5NFxZ/view?usp=sharing)**

---

## Running It Again Later

After the first setup, you don't need to install or build anything again. Just run:

```bash
./start.sh
```

Your progress is saved, and the lab works offline once the image is built.
