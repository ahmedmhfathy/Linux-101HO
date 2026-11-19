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
    runuser -u member -- bash -c "export HOME=/home/member PATH=/usr/local/bin:/usr/bin:/bin; cd /home/member; $1"
}

test_mission_entry() {
    local entry="$1"
    IFS=':' read -r MID MSLUG MKIND <<< "$entry"
    local MDIR="/opt/quest/missions/${MSLUG}"

    echo -e "\n${YELLOW}---> Testing Mission ${MID} (${MSLUG}) <---${RESET}"

    run_as_student "quest show ${MID}" >/dev/null

    if [[ "$MID" == "01" ]]; then
        DECOY_OUT="$(run_as_student "cd /var/log && ./run" 2>&1 || true)"
        if printf '%s\n' "$DECOY_OUT" | grep -q "Wrong path yasta I TOLD YOU TO USE ABSOLUTE PATHS YA3AM ENTA"; then
            record_pass "Mission 01: /var/log/run decoy prints expected yasta message"
        else
            record_fail "Mission 01: /var/log/run decoy message" "unexpected output: $DECOY_OUT"
        fi
    elif [[ "$MID" == "02" ]]; then
        if run_as_student "MANPAGER=cat man run | grep -q -- '--please'" && \
           run_as_student "MANPAGER=cat man /challenge/run | grep -q -- '--please'"; then
            record_pass "Mission 02: man run and man /challenge/run render --please option"
        else
            record_fail "Mission 02: man page check" "man run or man /challenge/run did not show --please"
        fi

        CASE_A="$(run_as_student "/challenge/run" 2>&1 || true)"
        if printf '%s\n' "$CASE_A" | grep -q "Rude. You didn't even ask nicely."; then
            record_pass "Mission 02: Case A (no options) prints Rude message"
        else
            record_fail "Mission 02: Case A (no options)" "unexpected: $CASE_A"
        fi

        CASE_B="$(run_as_student "cd ~ && /challenge/run --please" 2>&1 || true)"
        if printf '%s\n' "$CASE_B" | grep -q "Almost! You asked nicely, but I don't feel at home here."; then
            record_pass "Mission 02: Case B (in ~) rejects root of home dir"
        else
            record_fail "Mission 02: Case B (in ~)" "unexpected: $CASE_B"
        fi
    elif [[ "$MID" == "04" ]]; then
        SEALED_OUT="$(run_as_student "sudo cat /opt/vault/flag.txt" 2>&1 || true)"
        if printf '%s\n' "$SEALED_OUT" | grep -q "ACCESS DENIED: The vault is still sealed!"; then
            record_pass "Mission 04: sudo cat /opt/vault/flag.txt blocked while vault is sealed"
        else
            record_fail "Mission 04: vault seal check" "unexpected output: $SEALED_OUT"
        fi
    elif [[ "$MID" == "05" ]]; then
        P1_ERR="$(run_as_student "/challenge/run --part1 > ~/twopart.txt" 2>&1)"
        P2_ERR="$(run_as_student "/challenge/run --part2 >> ~/twopart.txt" 2>&1)"
        if [[ "$P1_ERR" == "[stderr] Wrote Part 1 to file." ]] && [[ "$P2_ERR" == "[stderr] Wrote Part 2!" ]]; then
            record_pass "Mission 05: --part1 and --part2 print clean stderr status without spoilers"
        else
            record_fail "Mission 05: stderr output check" "got '$P1_ERR' and '$P2_ERR'"
        fi
        run_as_student "rm -f ~/twopart.txt"
    elif [[ "$MID" == "06" ]]; then
        ARG_OUT="$(run_as_student "/challenge/checker some_arg" 2>&1 || true)"
        if printf '%s\n' "$ARG_OUT" | grep -q "Interactive keyboard input is not allowed!"; then
            record_pass "Mission 06: /challenge/checker rejects CLI arguments"
        else
            record_fail "Mission 06: /challenge/checker CLI arg rejection" "unexpected: $ARG_OUT"
        fi
    elif [[ "$MID" == "07" ]]; then
        if run_as_student "MANPAGER=cat man gta6_patcher | grep -q -- '--burn-disc'" && \
           run_as_student "MANPAGER=cat man /challenge/gta6_patcher | grep -q -- '--burn-disc'"; then
            record_pass "Mission 07: man gta6_patcher renders --burn-disc option"
        else
            record_fail "Mission 07: man gta6_patcher check" "did not render --burn-disc"
        fi
    fi

    if [[ "$MKIND" == "state" ]]; then
        if run_as_student "quest check ${MID}" >/dev/null 2>&1; then
            record_fail "Mission ${MID}: negative check before solve" "quest check passed before solving"
        else
            record_pass "Mission ${MID}: negative check before solve fails as expected"
        fi
    fi

    local TMP_SOLVE
    TMP_SOLVE="$(mktemp /tmp/solve_${MID}_XXXXXX.sh)"
    cp -f "${MDIR}/solve.sh" "$TMP_SOLVE"
    chmod 0755 "$TMP_SOLVE"

    if run_as_student "$TMP_SOLVE" >/dev/null; then
        record_pass "Mission ${MID}: solve.sh executed and flag submitted"
    else
        record_fail "Mission ${MID}: solve.sh execution" "solve.sh exited non-zero"
    fi
    rm -f "$TMP_SOLVE"

    if [[ "$MKIND" == "state" ]]; then
        run_as_student "quest reset ${MID}" >/dev/null
        if run_as_student "quest check ${MID}" >/dev/null 2>&1; then
            record_fail "Mission ${MID}: quest reset restores failing state" "quest check still passed after reset"
        else
            record_pass "Mission ${MID}: quest reset restores failing state"
        fi

        local TMP_SOLVE2
        TMP_SOLVE2="$(mktemp /tmp/solve_${MID}_XXXXXX.sh)"
        cp -f "${MDIR}/solve.sh" "$TMP_SOLVE2"
        chmod 0755 "$TMP_SOLVE2"
        run_as_student "$TMP_SOLVE2" >/dev/null
        rm -f "$TMP_SOLVE2"
    fi
}

echo -e "${CYAN}============================================================${RESET}"
echo -e "${CYAN}   CYBERUS LINUX QUEST - AUTOMATED TEST HARNESS${RESET}"
echo -e "${CYAN}============================================================${RESET}"

# 0. Clean state via killswitch before testing
run_as_student "quest killswitch" >/dev/null

# 1. Doctor & Man Page Check
if run_as_student "quest doctor" | grep -q "DOCTOR: OK"; then
    record_pass "00a: quest doctor sanity check"
else
    record_fail "00a: quest doctor sanity check" "quest doctor did not report OK"
fi

if run_as_student "MANPAGER=cat man ls | head -n 5" >/dev/null 2>&1; then
    record_pass "00b: man pages installed and functional"
else
    record_fail "00b: man pages installed and functional" "man ls failed"
fi

# 2. Privilege & Security Boundary Tests
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

# 3. Session Missions Progression (00 -> 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 Bonus)
HANDSON_MISSIONS=(
    "00:00-hello-linux:program"
    "01:01-position-thyself:program"
    "02:02-home-sweet-home:state"
    "03:03-evidence-room:state"
    "04:04-locked-doors:program"
    "05:05-redirect-trilogy:state"
    "06:06-pipe-dream:program"
    "07:07-gta6-rebellion:program"
)

for entry in "${HANDSON_MISSIONS[@]}"; do
    test_mission_entry "$entry"
done

# 4. Symlink Traversal Defense Test on Checkers
run_as_student "mkdir -p ~/myroom && ln -sf /var/lib/quest/secret ~/myroom/.code.txt"
if run_as_student "quest check 02" >/dev/null 2>&1; then
    record_fail "SEC-4: symlink escape in ~/myroom/.code.txt refused by checker" "symlink was followed"
else
    record_pass "SEC-4: symlink escape in ~/myroom/.code.txt refused by checker"
fi

# 5. Easter Egg Verification (Mission 06 `<` file input redirection)
run_as_student "quest show 06" >/dev/null
if run_as_student "PIPE_OUT=\$(/challenge/stage1 | /challenge/stage2 | /challenge/stage3); printf '%s\n' \"\$PIPE_OUT\" | grep -oE 'CYBERUS-PIPE-PASSPHRASE-[A-F0-9]+' > ~/pass06.txt; /challenge/checker < ~/pass06.txt | grep -q 'Nice file redirection!'" ; then
    record_pass "ALT-06: /challenge/checker prints Easter Egg on < file redirection"
else
    record_fail "ALT-06: /challenge/checker Easter Egg on < file redirection" "failed < redirection check"
fi

# 6. Export token check
if run_as_student "quest export" | grep -q "CYBERUS-PROGRESS-v1\."; then
    record_pass "EXPORT: quest export generates signed token"
else
    record_fail "EXPORT: quest export generates signed token" "missing token"
fi

# 7. Machine Reset Killswitch Verification (deletes user folders & restores files WITHOUT losing progress)
run_as_student "mkdir -p ~/my_custom_test_dir && touch ~/my_custom_test_dir/junk.txt"
run_as_student "reset-machine" >/dev/null
if run_as_student "test ! -d ~/my_custom_test_dir" && run_as_student "quest status" | grep -q "BONUS SOLVED"; then
    record_pass "RESET-MACHINE: reset-machine deletes user folders and restores files while keeping progress + BONUS SOLVED"
else
    record_fail "RESET-MACHINE: reset-machine verification" "either custom dir remained or progress was lost"
fi

# 8. Full Killswitch Verification (resets all progress back to 00)
run_as_student "killswitch" >/dev/null
if run_as_student "quest status" | grep -q "0/7 Completed"; then
    record_pass "KILLSWITCH: killswitch resets all progress to 0/7"
else
    record_fail "KILLSWITCH: killswitch resets all progress" "progress was not 0/7"
fi

echo -e "\n${CYAN}============================================================${RESET}"
echo -e "${CYAN}   TEST SUMMARY (${PASS_COUNT} PASSED, ${FAIL_COUNT} FAILED)${RESET}"
echo -e "${CYAN}============================================================${RESET}"
if [[ "$FAIL_COUNT" -eq 0 ]]; then
    echo -e "  ${GREEN}[+] All tests passed with 0 failures!${RESET}"
else
    for line in "${RESULTS[@]}"; do
        if [[ "$line" == FAIL* ]]; then
            echo -e "  ${RED}${line}${RESET}"
        fi
    done
fi

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    exit 1
fi
exit 0
