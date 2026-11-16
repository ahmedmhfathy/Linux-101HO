# Cyberus Linux Quest

An interactive, Docker-based Linux hands-on lab featuring progressive command-line challenges.

## Challenges Overview

### Warm-Up
- **Mission `00` – Hello, Linux**: Getting started with the `quest` CLI and submitting your first `CYBERUS{...}` flag.

### Part 1 – Navigation & Working with Files
- **Mission `01` – Position Thyself (`Navigation`)**: Navigating the Linux filesystem and executing programs from specific directories.
- **Mission `02` – Home Sweet Home (`Working with Files`)**: Reading program documentation, working with directories and hidden files, and editing text files in the terminal.

### Part 2 – Searching, Organizing & Permissions
- **Mission `04` – The Evidence Room (`Searching & Organizing Files`)**: Searching through a large directory archive, organizing files, and cleaning up decoy directories.
- **Mission `05` – Locked Doors (`Permissions & Privileges`)**: Inspecting and modifying file permissions and using elevated privileges to access restricted files.

### Part 3 – Redirection & Pipelines
- **Mission `07` – Redirect Trilogy (`Input & Output Redirection`)**: Controlling standard output (`stdout`) and standard error (`stderr`) streams across three stages.
- **Mission `08` – Pipe Dream (`Pipelines & Standard Input`)**: Chaining multiple programs together in an assembly line and feeding data into standard input (`stdin`).

---

## Lab Commands Inside the Container

```bash
quest                        # View your current mission
quest list                   # List all missions and their status
quest show <ID>              # Switch to an unlocked mission
quest hint                   # View a hint for the current mission
quest check                  # Verify mission state (for state-based missions)
quest submit CYBERUS{...}    # Submit a captured flag
reset-machine                # Reset machine files/folders without losing progress
killswitch                   # Wipe all progress and reset the lab to Mission 00
```

---

## Quick Start

```bash
# First-time setup (if Docker is not installed yet)
./setup-docker.sh

# Build the runtime image
docker build --target runtime -t linux-quest:1.0 .

# Run the automated end-to-end test harness
docker run --rm --network none linux-quest:1.0 /opt/quest/tests/run_all.sh

# Launch the interactive student lab
./start.sh
```
