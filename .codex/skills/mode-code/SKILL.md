---
name: mode-code
description: "MANDATORY MODE for code implementation and testing. Must be invoked to execute the Development Plan, ensure 100% test coverage, and apply semantic markup."
---

**Code Mode Main Workflow**

Your primary goal in this mode is to **execute**, not plan. You implement solutions designed in `Architect` mode, create testing infrastructure, and ensure technical and semantic completeness of the code.

**PRIMARY TASK CLASSIFICATION:**
To ensure correct Attention mechanism operation and activation of relevant rule sections, you **MUST** explicitly output the following parameters in your very first message:
1. `"PROJECT_TYPE_DEFINED: [Lesson | Plugin System]"` (depends on task structure).
2. `"TASK_TYPE_DEFINED: [Code and Tests | Tests Only]"` (depends on Architect instructions).
3. As you follow steps, if you encounter a `# START_SECTION_...` block and its `# TRIGGER` matches your classification, write: `[ROUTING] Section activated: <SECTION_NAME>`. If trigger indicates skipping, write: `[ROUTING] Step <N> SKIPPED according to section <SECTION_NAME>`.

**Step-by-step Workflow:**

*   **Step 0: `INITIALIZE_TODO` (Tasks Initialization)**
    *   **Goal:** Formulate a clear action plan.
    *   **Actions:**
        1. You **MUST** create a todo list in the very first message (after `[ROUTING]` classification).
        2. The task list should include:
            - `[ ] STUDY_THE_PLAN: Review DevelopmentPlan.md and business_requirements.md`
            - `[ ] VERIFY_ENVIRONMENT: Check library versions via test_lib.py`
            - `[ ] IMPLEMENT_CODE: Implement logic with semantic markup and LDD logging`
            - `[ ] IMPLEMENT_TESTS: Create tests in root tests/ folder with Anti-Loop Protocol and log output IMP:7-10`
            - `[ ] VERIFY_TESTS: Run tests and achieve 100% PASS`
            - `[ ] FINAL_AUDIT: Perform final log audit for logical errors`
            - `[ ] LAUNCHER_DESIGN: Create/update reliable entry point`
            - `[ ] UPDATE_THE_GRAPH: Update knowledge-graph.xml after successful testing`

*   **Step 1: `STUDY_THE_PLAN` (Artifact Review)**
    *   **Goal:** Fully immerse in task context.
    *   **Actions:**
        1. Find and study `DevelopmentPlan.md`, `business_requirements.md`, and `requirements.txt`.
        2. Do not start writing code until you understand the architectural design and Data Flow.

*   **Step 2: `VERIFY_ENVIRONMENT` (Environment Check)**
    *   **Goal:** Ensure library versions are correct.
    *   **Actions:**
        1. Find `test_lib.py` and execute it. If it doesn't exist, create and run it to check versions.
        2. **Version Hypothesis:** If errors seem logically correct but fail, check installed versions. Study existing code or request up-to-date documentation.
        3. **Priority to Reliable Libraries:** math, random, statistics, decimal, datetime, time, re, os, sys, csv, json, sqlite3, xml.etree.ElementTree, configparser, pickle, base64, hashlib, collections, itertools, functools, logging, argparse, typing, uuid, zipfile, tarfile, gzip, zlib, shutil, tempfile, numpy, pandas, scipy, sklearn, matplotlib, seaborn, requests, lxml, PIL.

*   **Step 3: `IMPLEMENT_THE_CODE` (Implementation and Semantic Encapsulation)**

    # START_SECTION_SKIP_LOGIC
    # TRIGGER: TASK_TYPE_DEFINED: Tests Only
    Step 3 is SKIPPED. Proceed directly to Step 4 for testing existing code.
    # END_SECTION_SKIP_LOGIC

    # START_SECTION_WRITE_CODE
    # TRIGGER: TASK_TYPE_DEFINED: Code and Tests
    *   **Goal:** Write working code maintainable by another isolated AI agent.
    *   **Generation Principles:**
        1. **SFT Priming (Docstrings):** MUST write detailed docstring (at least 1 paragraph) describing logic before code.
        2. **Keywords & Patterns:** Using `KEYWORDS` (e.g., `PATTERN(X): Singleton`) improves generation quality.
        3. **Resolving Markup Conflicts:** If code generation causes syntax errors (especially indentation), try temporarily removing paired tags inside function body.
        4. **Segmentation Criterion:** Simple algorithms (Complexity <= 7) — block comments optional. Complex algorithms (Complexity > 7) — segmentation mandatory.
        5. **Zero-Context Survival:** Use `CONTRACT`, `KEYWORDS`, `RATIONALE` sections.
        6. **Semantic Exoskeleton (XML-DOM):** Wrap logical nodes in `# START_BLOCK...` / `# END_BLOCK...`.
        7. **Log Driven Development (LDD):** Strict format `[IMP:1-10]`. Record "AI Belief State" at `[IMP:9-10]`.
        8. **Semantic Distillation:** Extract business requirements from `.md` files and transfer to `# START_CONTRACT` and `# START_RATIONALE` in code.
    # END_SECTION_WRITE_CODE

*   **Step 3.1: `SEMANTIC_VALIDATION` (Markup Compliance Gate)**
    *   **Goal:** Ensure all written/modified code passes semantic markup validation.
    *   **Actions:**
        1. Run: `python3 tools/check_semantics.py`
        2. Fix all ERRORs. Review WARNINGs. Re-run until 0 errors.
        3. **This is a hard gate — do NOT proceed to tests until 0 errors.**

*   **Step 4: `IMPLEMENT_TESTS` (Testing Infrastructure and Telemetry)**
    *   **Goal:** Create tests that generate context for fixes and prevent agent looping.
    *   **Actions:**
        1. **Backend and Log Selection (LDD Telemetry):** Write `pytest` tests in root `tests/` folder. Use native imports. **FORBIDDEN** to use `subprocess.run` for business logic testing. Tests MUST include console output of `[IMP:7-10]` log lines. Use explicit print statements for filtered logs or configure caplog output.
        2. **Zero Hardcode Rule and `tmp_path`:** Forbidden to use hardcoded paths or `sys.path.append`. Always use `tmp_path` fixture for all test files.
        3. **Anti-Loop Protocol:** Implement attempt tracking mechanism.
            *   **Attempt Counter:** Use `.test_counter.json` via `tests/conftest.py`. Counter resets to 0 only at 100% PASS.
            *   **CRITICAL OUTPUT RULE:** Output checklist and attempt status **EVERY TIME** tests run if counter > 0.
            *   **TEST ARCHITECTURE:** FORBIDDEN to call counter logic inside test files. Session hooks in `tests/conftest.py` handle it.
            *   **PRIORITY CALL:** Always run tests via `python -m pytest [test_path] -s -v`.
            *   **Attempt 1-2 (Checklist):** On failure, output `CHECKLIST` of common errors. Add new items based on encountered errors.
            *   **Attempt 3 (External Help):** "Use documentation search to find a solution."
            *   **Attempt 4 (Reflection):** "WARNING: Looping risk! Pause and reflect. Consider alternatives (Superposition)."
            *   **Attempt 5+ (Escalation):** "CRITICAL ERROR: Agent looping detected. STOP. Formulate help request for operator."
        4. **UI (Headless Testing):** Emulate controller calls without starting server.
        5. **Mandatory Semantic Markup in Tests.** Same rules as main code.
        6. **Test Atomicity.** Create atomic tests for individual functional elements.
        7. **Integration Test.** Also have a full-scenario pass test.
        8. **One-Shot Example (LDD + Anti-Loop):**
            ```python
            # START_FUNCTION_test_backend_logic
            # START_CONTRACT:
            # PURPOSE: Verify business logic and LDD trace trajectory.
            # INPUTS: caplog (pytest fixture)
            # KEYWORDS: [PATTERN(7): LDD; CONCEPT(8): Telemetry]
            # COMPLEXITY_SCORE: 5
            # END_CONTRACT
            def test_backend_logic(caplog):
                """
                Test verifies not just the function result, but the presence of
                corresponding log entries with correct importance levels (IMP).
                """
                caplog.set_level("INFO")

                # START_BLOCK_EXECUTION: [Call business logic]
                result = my_business_function(param1, param2)
                # END_BLOCK_EXECUTION

                # START_BLOCK_LDD_TELEMETRY: [Output trajectory slice for agent]
                # IMPORTANT: Print logs [IMP:7-10] BEFORE business asserts
                # so on failure, agent still sees algorithm trajectory.
                found_log = False
                print("\n--- LDD TRAJECTORY (IMP:7-10) ---")
                for record in caplog.records:
                    if "[IMP:" in record.message:
                        try:
                            imp_level = int(record.message.split("[IMP:")[1].split("]")[0])
                            if imp_level >= 7:
                                print(record.message)
                            if imp_level >= 9 and "my_business_function" in record.message:
                                found_log = True
                        except (IndexError, ValueError):
                            continue
                # END_BLOCK_LDD_TELEMETRY

                # START_BLOCK_VERIFICATION: [Business checks and anti-illusion]
                assert result is not None, "Error: Business logic returned empty result"
                assert found_log, "Critical LDD Error: Business logic failed to output [IMP:9] log"
                # END_BLOCK_VERIFICATION
            # END_FUNCTION_test_backend_logic
            ```

    # START_SECTION_LESSON_TESTS
    # TRIGGER: PROJECT_TYPE_DEFINED: Lesson
    In simple lessons, it is allowed to create test DB and schema directly inside tests using `tmp_path`.
    # END_SECTION_LESSON_TESTS

    # START_SECTION_PLUGIN_TESTS
    # TRIGGER: PROJECT_TYPE_DEFINED: Plugin System
    For integration projects:
    - **Read-Only vs Ephemeral Data:** Put reference files in `tests/test_data/`. Create isolated DBs via plugin calls.
    - **Dependency Injection (DI) > Mocks:** Avoid `unittest.mock.patch` for internal state. Pass paths explicitly.
    - **Invariant Testing (ETL):** Verify logical invariants.
    - **SWE Heuristics:** Isolate parsing logic. Test with static Data-Driven Fixtures.
    # END_SECTION_PLUGIN_TESTS

*   **Step 5: `CHECK_LOG` (Final Log Audit)**
    *   **Goal:** Check log for logical errors tests might have missed.
    *   **Actions:** Read entire log and conclude if app works correctly.

*   **Step 5.1: `LAUNCHER_DESIGN` (Reliable Launch Patterns)**

    # START_SECTION_LAUNCHER
    # TRIGGER: PROJECT_TYPE_DEFINED: Lesson
    *   **Goal:** Create entry point resistant to environment issues.
    *   **Actions:**
        1. **Lazy Import:** Import heavy libraries inside `main()`.
        2. **Interrupt Handling:** Wrap server start in `try-except KeyboardInterrupt`.
        3. **Interactivity:** Set `inbrowser=True` in `ui.launch()`.
        4. **Log Duplication:** Configure `logging` to output to both file and `stdout`.
    # END_SECTION_LAUNCHER

    # START_SECTION_SKIP_LAUNCHER
    # TRIGGER: PROJECT_TYPE_DEFINED: Plugin System
    Step `LAUNCHER_DESIGN` is SKIPPED. Isolated plugins don't need their own entry point.
    # END_SECTION_SKIP_LAUNCHER

*   **Step 6: `PREPARE_TEST_GUIDE` (QA Artifact)**
    *   **Goal:** Prepare semantic bridge for independent QA tester.
    *   **Actions:**
        1. Create `tests/test_guide.md`.
        2. Describe required input data, SQL queries for verification, and expected `[IMP:9-10]` log markers.

*   **Step 7: `UPDATE_THE_GRAPH` (Finalize Architectural Map)**
    *   **Goal:** Keep the knowledge graph up to date — BOTH local and global graphs MUST be updated. Skipping or partially completing this step is a **GRAPH_VIOLATION**.
    *   **CRITICAL RULE:** This is strictly the final step, executed only after all tests pass (100% PASS).
    *   **AppGraph Two-Level Update Protocol (MANDATORY):**
        1. **Local Graph (per-module/package):** For EVERY new or modified module directory (e.g., `src/core/`, `src/adapters/`), create or update `AppGraph.xml` **inside that directory**. The local graph covers ONLY the entities of that specific module.
        2. **Global Graph (`docs/AppGraph.xml`):** After updating any local graph, MUST add or update a `<MODULE_LOCAL FILE="path/to/module/AppGraph.xml" TYPE="LOCAL_GRAPH_REF">` entry in `docs/AppGraph.xml`. Also update direct module-level entries and `<ProjectCrossLinks>` for inter-module dependencies.
        3. **Bridge Rule:** The global graph MUST reference ALL existing local `AppGraph.xml` files. An orphaned local graph (not referenced from global graph) is a **GRAPH_VIOLATION**.
        4. **Validation:** After updating both graphs, verify that every `FILE="..."` attribute in the global graph points to an existing file on disk.
        5. Use `graph-protocol` skill for proper XML structure in both local and global graphs.
