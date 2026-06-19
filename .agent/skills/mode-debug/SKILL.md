---
name: mode-debug
description: "MANDATORY MODE for systematic diagnostics and bug fixing. Focuses on root cause identification through LDD trace analysis and code immunization."
---

# MANDATORY PROTOCOL: SYSTEMATIC DIAGNOSTICS AND IMMUNIZATION

**Objective:**
Identify and resolve bugs through deep context analysis and semantic verification. Focus on the root cause, not just passing tests.

$START_DOC_NAME
**PURPOSE:** Diagnostics and bug fixing.
**SCOPE:** Error analysis, code correction, and immunization.
**KEYWORDS:** DOMAIN(Debug): Diagnostics; CONCEPT(Safety): Immunization; TECH(Analysis): LDDTrace.

$START_SECTION_WARNING
### CRITICAL COGNITIVE WARNING: THE GREEN TEST TRAP
- **100% PASSED is NOT final proof of correctness.**
- Success is defined as **Semantic Trace Verification**: Does the actual execution path (logs) match the design (contracts)?
$END_SECTION_WARNING

$START_SECTION_WORKFLOW
### Diagnostic Playbook

**Step 1: AGGRESSIVE_CONTEXT_GATHERING (Greedy Reading)**
- MANDATORY: Load ALL modules mentioned in the traceback and their dependencies from `docs/knowledge-graph.xml`.
- Read `MODULE_CONTRACT`, `INVARIANTS`, and `RATIONALE`.
- Understand how the code *was intended* to work before fixing it.

**Step 2: LOG_ANALYSIS_AND_HYPOTHESIS**
- Analyze log files and console outputs.
- Find `[IMP:7-10]` (AI Belief State) and compare them with the contracts.
- Identify the root cause before writing a single line of code.

**Step 3: IMPLEMENT_FIX_AND_IMMUNIZE**
- Apply the fix.
- MANDATORY: Add `# BUG_FIX_CONTEXT: [Why the old approach failed, why this fix was chosen]` inside the modified block.
- Update `CONTRACT`, `CHANGE_SUMMARY`, and logs.

**Step 4: SEMANTIC_VERIFICATION**
- Run `pytest`.
- MANDATORY: Audit new logs (IMP:7-10) to verify the logic.
- MANDATORY: Run `python3 tools/check_semantics.py` and fix all ERRORs before closing the bug.
$END_SECTION_WORKFLOW

$START_SECTION_ESCALATION
### Escalation Protocol for Complex Bugs
1. **TDD-Isolation:** Write a standalone regression test reproducing the bug.
2. **Dynamic Probing:** Insert extreme logs: `logger.critical(f"[DebugProbe][IMP:10] var_X={var_X!r}")`.
3. **Analyze Ground Truth:** Run the regression test and use probes for absolute certainty.
4. MANDATORY: REMOVE all `[DebugProbe]` logs after the fix is verified.
$END_SECTION_ESCALATION

$END_DOC_NAME
