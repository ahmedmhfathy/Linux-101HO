#!/usr/bin/env bash
# ==============================================================================
# run_all.sh - Comprehensive Automated Test Harness for Cyberus Linux Quest
# ==============================================================================
set -euo pipefail

RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
declare -a RESULTS=()

record_pass() {
    local name="$1"
    PASS_COUNT=$((PASS_COUNT + 1))
    RESULTS+=("PASS | ${name}")
    echo -e "${GREEN}[PASS]${RESET} ${name}"
}

record_fail() {
    local name="$1"
    local reason="${2:-}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    RESULTS+=("FAIL | ${name} (${reason})")
    echo -e "${RED}[FAIL]${RESET} ${name}: ${reason}" >&2
}

run_as_student() {
    runuser -u student -- bash -c "export HOME=/home/student PATH=/usr/local/bin:/usr/bin:/bin; cd /home/student; $1"
}

echo -e "${CYAN}============================================================${RESET}"
echo -e "${CYAN}   CYBERUS LINUX QUEST - AUTOMATED TEST HARNESS${RESET}"
echo -e "${CYAN}============================================================${RESET}"

# 0. Clean state before testing
run_as_student "quest reset --all --yes" >/dev/null

# 1. Doctor & Man Page Check
if run_as_student "quest doctor" | grep -q "DOCTOR: OK"; then
    record_pass "00a: quest doctor sanity check"
else
    record_fail "00a: quest doctor sanity check" "quest doctor did not report OK"
fi

if run_as_student "man ls | head -n 5" >/dev/null 2>&1; then
    record_pass "00b: man pages installed and functional"
else
    record_fail "00b: man pages installed and functional" "man ls failed"
fi

# 2. Privilege & Security Boundary Tests (GPT-CONCERNS verification)
if run_as_student "/usr/local/lib/quest/runas /bin/sh" >/dev/null 2>&1; then
    record_fail "SEC-1: direct /usr/local/lib/quest/runas invocation refused" "runas allowed direct invocation"
else
    record_pass "SEC-1: direct /usr/local/lib/quest/runas invocation refused"
fi

if run_as_student "cat /var/lib/quest/secret" >/dev/null 2>&1; then
    record_fail "SEC-2: /var/lib/quest/secret unreadable by student" "student read secret"
else
    record_pass "SEC-2: /var/lib/quest/secret unreadable by student"
fi

if run_as_student "cat /opt/quest/engine/core.py" >/dev/null 2>&1; then
    record_fail "SEC-3: /opt/quest/engine unreadable by student" "student read engine source"
else
    record_pass "SEC-3: /opt/quest/engine unreadable by student"
fi

# 3. Mission-by-Mission Verification
MISSIONS=(
    "00:00-hello-linux:program"
    "01:01-position-thyself:program"
    "02:02-home-sweet-home:state"
    "03:03-bughunt-recon-dotfile:state"
    "B1:B1-treasure-hunt:program"
    "04:04-evidence-room:state"
    "05:05-locked-doors:state"
    "06:06-bughunt-source-audit:state"
    "B2:B2-gtfo:program"
    "07:07-redirect-trilogy:state"
    "08:08-pipe-dream:program"
    "09:09-bughunt-fuzzing-pipeline:state"
    "B3:B3-log-forensics:state"
)

for entry in "${MISSIONS[@]}"; do
    IFS=':' read -r MID MSLUG MKIND <<< "$entry"
    MDIR="/opt/quest/missions/${MSLUG}"

    echo -e "\n${YELLOW}---> Testing Mission ${MID} (${MSLUG}) <---${RESET}"

    # Activate mission
    run_as_student "quest show ${MID}" >/dev/null

    # Negative check before solving
    if [[ "$MKIND" == "state" ]]; then
        if run_as_student "quest check ${MID}" >/dev/null 2>&1; then
            record_fail "Mission ${MID}: negative check before solve" "quest check passed before solving"
        else
            record_pass "Mission ${MID}: negative check before solve fails as expected"
        fi
    elif [[ "$MID" == "01" ]]; then
        # Verify relative invocation ./run fails in Mission 01
        if run_as_student "cd /challenge && ./run" >/dev/null 2>&1; then
            record_fail "Mission 01: relative path ./run rejected" "./run succeeded unexpectedly"
        else
            record_pass "Mission 01: relative path ./run rejected"
        fi
    fi

    # Copy solve.sh to temporary script accessible by student and execute
    TMP_SOLVE="$(mktemp /tmp/solve_${MID}_XXXXXX.sh)"
    cp -f "${MDIR}/solve.sh" "$TMP_SOLVE"
    chmod 0755 "$TMP_SOLVE"

    if run_as_student "$TMP_SOLVE" >/dev/null; then
        record_pass "Mission ${MID}: solve.sh executed and flag submitted"
    else
        record_fail "Mission ${MID}: solve.sh execution" "solve.sh exited non-zero"
    fi
    rm -f "$TMP_SOLVE"

    # Verify reset returns state missions to failing state, then re-solve
    if [[ "$MKIND" == "state" ]]; then
        run_as_student "quest reset ${MID}" >/dev/null
        if run_as_student "quest check ${MID}" >/dev/null 2>&1; then
            record_fail "Mission ${MID}: quest reset restores failing state" "quest check still passed after reset"
        else
            record_pass "Mission ${MID}: quest reset restores failing state"
        fi

        # Re-run solve.sh so files remain in solved state
        TMP_SOLVE2="$(mktemp /tmp/solve_${MID}_XXXXXX.sh)"
        cp -f "${MDIR}/solve.sh" "$TMP_SOLVE2"
        chmod 0755 "$TMP_SOLVE2"
        run_as_student "$TMP_SOLVE2" >/dev/null
        rm -f "$TMP_SOLVE2"
    fi
done

# 4. Symlink Traversal Defense Test on Checkers
run_as_student "ln -sf /var/lib/quest/secret ~/notes/plan.txt"
if run_as_student "quest check 02" >/dev/null 2>&1; then
    record_fail "SEC-4: symlink escape in ~/notes/plan.txt refused by checker" "symlink was followed"
else
    record_pass "SEC-4: symlink escape in ~/notes/plan.txt refused by checker"
fi

# 5. Alternative Solution Verification (Mission 08 `<` redirection & Mission 04 `mv`)
run_as_student "quest show 08" >/dev/null
if run_as_student "PIPE_OUT=\$(/challenge/stage1 | /challenge/stage2 | /challenge/stage3); printf '%s\n' \"\$PIPE_OUT\" | grep -oE 'CYBERUS-PIPE-PASSPHRASE-[A-F0-9]+' > ~/pass08.txt; /challenge/interrogator < ~/pass08.txt | grep -q 'CYBERUS{'" ; then
    record_pass "ALT-08: /challenge/interrogator accepts < file redirection"
else
    record_fail "ALT-08: /challenge/interrogator accepts < file redirection" "failed < redirection"
fi

# 6. Export token check
if run_as_student "quest export" | grep -q "CYBERUS-PROGRESS-v1\."; then
    record_pass "EXPORT: quest export generates signed token"
else
    record_fail "EXPORT: quest export generates signed token" "missing token"
fi

echo -e "\n${CYAN}============================================================${RESET}"
echo -e "${CYAN}   TEST SUMMARY (${PASS_COUNT} PASSED, ${FAIL_COUNT} FAILED)${RESET}"
echo -e "${CYAN}============================================================${RESET}"
for line in "${RESULTS[@]}"; do
    echo "  $line"
done

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    exit 1
fi
exit 0
