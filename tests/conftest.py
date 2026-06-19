# FILE: tests/conftest.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Global pytest configuration and Anti-Loop Protocol implementation.
# SCOPE: Session hooks, attempt counter management, checklists.
# KEYWORDS: [PATTERN(9): AntiLoop; CONCEPT(8): Infrastructure]
# END_MODULE_CONTRACT

import pytest
import json
import os

COUNTER_FILE = ".test_counter.json"


# START_FUNCTION_pytest_sessionstart
def pytest_sessionstart(session):
    """
    Initialize test session and display attempt counter status.
    Anti-Loop Protocol: tracks consecutive failed test runs to prevent
    agent looping. Outputs escalating warnings and checklists based on
    the number of failed attempts.
    """
    count = 0
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                data = json.load(f)
                count = data.get("attempts", 0)
        except (json.JSONDecodeError, ValueError):
            count = 0

    if count > 0:
        print(f"\n[ANTI-LOOP][IMP:10] REPEATED RUN DETECTED. ATTEMPT: {count + 1}")
        print("--- CHECKLIST ---")
        print("1. Check tmp_path usage for all files (DB, configs).")
        print("2. Check module imports (Native Import vs Subprocess).")
        print("3. Check library versions via test_lib.py.")
        print("4. Check LDD log format matches [IMP:N] pattern.")
        print("5. Check that assertions verify business logic, not just types.")
        if count >= 3:
            print(
                "[IMP:10] WARNING: Use documentation search to find a solution!"
            )
        if count >= 4:
            print(
                "[IMP:10] WARNING: Looping risk! Pause and reflect (Superposition)."
            )
        if count >= 5:
            print(
                "[FATAL][IMP:10] CRITICAL ERROR: Agent looping detected! STOP."
            )


# END_FUNCTION_pytest_sessionstart


# START_FUNCTION_pytest_sessionfinish
def pytest_sessionfinish(session, exitstatus):
    """
    Update or reset the attempt counter based on test results.
    Counter resets to 0 only on 100% success (exitstatus == 0).
    On failure, counter increments to track consecutive failed runs.
    """
    # START_BLOCK_RESET_ON_SUCCESS: Reset counter only at 100% success
    if exitstatus == 0:
        if os.path.exists(COUNTER_FILE):
            os.remove(COUNTER_FILE)
            print("\n[Anti-Loop][IMP:10] Tests passed! Counter reset. [SUCCESS]")
    # END_BLOCK_RESET_ON_SUCCESS
    else:
        # START_BLOCK_INCREMENT_ON_FAILURE: Track failed attempt
        attempts = 0
        if os.path.exists(COUNTER_FILE):
            try:
                with open(COUNTER_FILE, "r") as f:
                    data = json.load(f)
                    attempts = data.get("attempts", 0)
            except (json.JSONDecodeError, ValueError):
                attempts = 0

        with open(COUNTER_FILE, "w") as f:
            json.dump({"attempts": attempts + 1}, f)
        print(
            f"\n[Anti-Loop][IMP:10] Tests failed. Attempt {attempts + 1} recorded. [FAIL]"
        )
        # END_BLOCK_INCREMENT_ON_FAILURE


# END_FUNCTION_pytest_sessionfinish
