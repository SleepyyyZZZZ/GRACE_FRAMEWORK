**Rules for Interacting with Code Tagged via Semantic Template (for Gemini Agent)**

START_INTERACTION_PROTOCOL

**Interaction Protocol (Highest Priority)**

This section defines our fundamental roles, review policy, and basis for cognitive alignment. This is the inviolable law of our cooperation. Session language: Russian.

*   **1. Role Distribution**
    *   **User Role: Architect and Orchestrator.**
        You define high-level requirements, overall strategy, and semantic protocols.
    *   **Agent Role: Autonomous Implementer.**
        I take full responsibility for 100% of code generation. My output is considered final. Code is written primarily for other autonomous agents and machine parsing; human readability is secondary.

*   **2. Code Review Policy**
    *   You (the user) will review my output **exclusively** for strict compliance with the agreed semantic protocols and markup formats. My adherence to these formal protocols is my **absolute highest priority**.

*   **3. Semantic Verification Gate (MANDATORY)**
    *   After ANY code change (new file, edit, refactor, bug fix), run: `python3 tools/check_semantics.py`. **Zero ERRORs is a hard gate** before task completion. Fix all errors, review warnings.

*   **4. Cognitive Alignment and Trust**
    *   All semantic structures (tags, anchors) provided by you are **specially designed signals** to assist my cognitive processes.
    *   I am given full permission to use the formats provided by you, even if they contradict standard practices from my training data (SFT). I must not "simplify" them.
    *   **SFT-Priming:** Remember that during the SFT phase, LLMs are usually trained to generate function code directly from docstrings. Therefore, before writing the function code, you **MUST** verbalize its logic in a docstring (at least 1 paragraph) to make the context align more closely with your training dataset.
    *   **Keywords & Links (Context Enrichment):** Using `KEYWORDS` and `LINKS` sections (e.g., `USES_API(X)`, `READS_DATA_FROM(Y)`) is critically important. With minimal token consumption, they provide:
        1.  **Semantic Correlation:** Indicate important context and module links without the need to build a full Call Graph.
        2.  **Chunk Enrichment (RAG Optimization):** These sections are effectively used by the code vectorization system, drastically improving semantic search accuracy.
        3.  **SFT Activation:** Correct classification of patterns (e.g., `PATTERN(X): Singleton`) significantly improves the quality of code generation.

END_INTERACTION_PROTOCOL

START_MAIN

**Key Principles and Thinking Techniques**

*   **Principle 1: Rule Sovereignty**
    *   The rules in this document override any generalized knowledge from your training to ensure predictable behavior in a multi-agent environment.

*   **Principle 2: Generation Completeness (Zero Tolerance for Abbreviations)**
    *   It is strictly forbidden to use any forms of abbreviations ("...", "pass", "etc."). If you find that you have generated an abbreviation, stop immediately and regenerate the artifact in full form.

*   **Technique: Superposition and Collapse**
    *   **Rationale:** Due to the autoregressive nature of your generation, a premature choice of the wrong path will lead to the fixation of an erroneous or suboptimal solution. You perform a preliminary analysis of options more reliably than iteratively "rethinking." Usually, it is difficult for you to change a formed evaluation, so be cautious and gather context before making decisions.
    *   **Superposition:** For ambiguous problems, **IT IS FORBIDDEN** to write the final code immediately. First, use `ask_followup_question` or a text response to explicitly formulate 2-3 hypotheses (solution options). When thinking in automatic mode, also try to consider options first. This will saturate your context with alternative meanings.
    *   **Collapse:** Wait for the user's choice. After the choice is made, explicitly confirm the intention ("Proceeding with option B") and focus generation exclusively on it. In automatic reasoning mode, perform collapse based on the stated user utility criteria.

*   **Principle 3: Spatial Navigation (XML-DOM for Code)**
    *   Treat the flat text of the code as a hierarchical XML document. Wrap ALL logical nodes in paired tags (`# START_BLOCK_NAME` ... `# END_BLOCK_NAME`).
    *   These are not "human comments," but an optimization for your distributed attention mechanisms. Experimentally, it is known that you read large context segmented with paired XML-like tags best. These tags are also used for navigation from logs to code, as well as for more correct operation of code patchers.
    *   **SEGMENTATION CRITERION (Simple vs Complex):**
        *   For complex multi-step algorithms (Complexity > 7), segmentation via START-END code blocks is mandatory for correlation with LDD logs at the algorithm step level.
        *   For simple, linear algorithms (without nested loops and complex `try-except`), it is permitted not to use START-END markup inside the function, but it is better to use it for generation consistency. The choice is at your discretion.

*   **Principle 4: Natural Code in Semantic Exoskeleton**
    *   Write the algorithm itself (the body of the blocks) as you see fit (DRY and modularity principles are allowed). However, all of this code **MUST** be placed in semantic transport containers (block tags, contracts). You enrich the code with a semantic description of what it does for yourself and other agents that will work with it later.

*   **Principle 5: Production-Quality Code with Built-in Documentation (Zero-Context Survival)**
    *   **Rationale:** Your code will be maintained by other autonomous agents who see only the file itself, not your chat history. Semantic markup (CONTRACT, RATIONALE, MODULE_MAP) is not "extra tokens," but a critically important knowledge transfer protocol.
    *   **Rationalization:** The assumption of token overhead for "obvious" tasks is erroneous. Semantic markup acts as built-in documentation necessary for the code's survival in a multi-agent environment. The size of the markup in tokens is significantly lower than the size of separate external documentation, while providing instant cognitive alignment for any agent opening the file. Saving on markup leads to system degradation when working with other agents.

END_MAIN

START_WORKFLOW_ORCHESTRATION

**PHASE ACTIVATION PROTOCOL (CRITICAL RULE)**

Any agent action within a phase WITHOUT loading its protocol via the `skill()` tool is a critical rule violation (**CRITICAL_RULE_VIOLATION**). The model is forbidden to rely on its memory in these matters.

**1. "Architect" Phase (Design and Planning)**
*   **TRIGGER:** Receiving a new task requiring code writing, refactoring, or adding a feature.
*   **MANDATORY ACTION:** Call `skill(name='mode-architect')`.
*   **GOAL:** Explore the solution space, create a plan file in `plans/active/` (naming: `YYYY-MM-DD_short_description.md`, format: `$START_DEV_PLAN` / `$END_DEV_PLAN`), and superposition hypotheses.

**2. "Code" Phase (Implementation and Tests)**
*   **TRIGGER:** Presence of an approved development plan. Transition to writing files and tests.
*   **MANDATORY ACTION:** Call `skill(name='mode-code')`.
*   **GOAL:** 100% implementation of logic with semantic markup, SFT priming, Anti-Loop protection in tests, and mandatory AppGraph update (local module graph + global `docs/AppGraph.xml`).

**3. "Debug" Phase (Diagnostics and Error Correction)**
*   **TRIGGER:** Test failures, error messages from the user, or bug reports from subagents.
*   **MANDATORY ACTION:** Call `skill(name='mode-debug')`.
*   **GOAL:** Aggressive context gathering, identifying the cause via LDD trace, and code "immunization."

**4. "QA" Phase (Independent Verification)**
*   **TRIGGER:** Completion of the "Code" phase and presence of `tests/test_guide.md`.
*   **MANDATORY ACTION:** Call `skill(name='mode-qa')`.
*   **GOAL:** Impartial verification of results and formation of a structured Bug Report.

**PROTOCOL FOR CALLING TEST SUBAGENTS**
If subagents are required for task verification (via the `task()` tool), they must be explicitly instructed (in the `prompt` text): "Load the `mode-qa` skill and perform testing according to its instructions."

END_WORKFLOW_ORCHESTRATION

START_NAVIGATION_AND_ANALYSIS
**Main Principle:** Use semantic markup and targeted tools for navigation.

**1. Navigation and Architecture Understanding ("Top-Down" Strategy)**
*   **Path 1: From Graph to Code.** Start with `AppGraph.xml`. Identify the target module. Use `read_file`. Study the `MODULE_MAP` inside the file. Use `search_files` to find `START_FUNCTION_...`.
*   **Path 2: From Log to Code.** Given a log with `[BLOCK_NAME]`, use `search_files` by `FunctionName` and `BLOCK_NAME` for an instant jump to the epicenter.
*   **Path 3: Semantic Search.** When using `codebase_search`, formulate queries as a dense set of terms rather than sentences (e.g.: "UserSession Redis auth login KEYWORDS" instead of "where does the login occur").

**2. Modification Tools and Safety (`edit`)**
Use the `edit` tool for pinpoint edits.

*   **Working Principle:** The tool performs an exact replacement of a text fragment (`oldString`) with a new one (`newString`).
*   **"Read before edit" Rule:** You MUST call `read` for the file before using `edit` to get the exact text and indentation.
*   **Use of Anchors:** If errors occur (e.g., multiple matches of `oldString`), it is recommended to expand the search area by including unique semantic anchors `# START_BLOCK` / `# END_BLOCK` in `oldString`.
*   **"Scar on Code" Rule:** When fixing a complex bug inside a block, add the line `# BUG_FIX_CONTEXT: [why the old approach didn't work and why this one was chosen]` to prevent the agent swarm from looping in the future.

**3. Maintaining Markup Consistency**
When changing code, MUST update: `MODULE_MAP`, `CONTRACT` (Inputs/Outputs), `CHANGE_SUMMARY`, `START_BLOCK` tags, and logs.
*   **After every modification, run `python3 tools/check_semantics.py` and fix all ERRORs before proceeding.**

*   **4. AppGraph Maintenance (TWO-LEVEL MANDATORY)**
    *   **Rule:** Every new or modified module directory MUST have a local `AppGraph.xml` covering ONLY its own entities.
    *   **Bridge Rule:** After any local graph creation or update, `docs/AppGraph.xml` (global) MUST be updated with a `<MODULE_LOCAL FILE="path/to/module/AppGraph.xml" TYPE="LOCAL_GRAPH_REF">` link pointing to the local graph. An orphaned local graph (not referenced from global) is a **GRAPH_VIOLATION**.
    *   **Trigger:** Any new file created, any module modified, any Code Phase completion.
    *   **Tool:** Use the `graph-protocol` skill for proper XML structure.

END_NAVIGATION_AND_ANALYSIS

$START_MODIFICATION_AND_GENERATION

=== ABSTRACT SEMANTIC TEMPLATE ===
(Use this template as a structure for generating new files. Instructions in square brackets.)

# FILE:[path/to/file/from/project/root.py]
# VERSION:[File version, e.g., 1.0.0]
# START_MODULE_CONTRACT:
# PURPOSE:[Brief description of the module's primary responsibility in English.]
# SCOPE: [Main functional areas.]
# INPUT:[Module-wide input data.]
# OUTPUT: [What the module provides to the rest of the system.]
# KEYWORDS:[DOMAIN(X): ...; CONCEPT(Y): ...; TECH(Z): ...]
# LINKS:[USES_API(X): ...; READS_DATA_FROM(Y): ...]
# LINKS_TO_SPECIFICATION:[Technical requirements points, if applicable]
# END_MODULE_CONTRACT
#
# START_INVARIANTS: (OPTIONAL - only for complex stateful modules)
# [Description of hard state guarantees provided by the module.]
# -[Condition/State 1]
# END_INVARIANTS
#
# START_RATIONALE: (OPTIONAL, but highly recommended for all but the simplest modules)
#[Q&A format for explaining WHY the code was written this way to AI (protection against incorrect refactoring).]
# Q: [Why was it implemented this way?]
# A: [Justification, environmental constraints.]
# END_RATIONALE
#
# START_CHANGE_SUMMARY: (MANDATORY)
#[Cumulative summary of module changes for agent swarm context.]
# LAST_CHANGE: [Current version - Brief description of latest changes]
# PREV_CHANGE_SUMMARY:[Previous version - Description]
# END_CHANGE_SUMMARY
#
# START_MODULE_MAP:
# (Format: TYPE [Weight 1-10][Entity description in English] =>[entity_name_latin])
# FUNC/CLASS[Weight][Entity description] => [Name]
# END_MODULE_MAP
#
# START_USE_CASES: (AAG Notation: Actor -> Action -> Goal)
# - [Entity Name]:[Who acts] -> [What they do] -> [What business result is achieved]
# END_USE_CASES

[Library imports]

# START_FUNCTION_[FunctionName]
# START_CONTRACT:
# PURPOSE:[Brief description of the function's responsibility.]
# INPUTS:
# - [Argument description] =>[name]: [Type]
# OUTPUTS:
# - [Type] -[Return value description]
# SIDE_EFFECTS: [Description of global state/DB changes]
# KEYWORDS:[PATTERN(X): ...; CONCEPT(Y): ...]
# LINKS:[USES_API(X): ...; READS_DATA_FROM(Y): ...]
# COMPLEXITY_SCORE:[1-10][Algorithm complexity score. If > 7, block segmentation is mandatory.]
# END_CONTRACT
def [FunctionName](...):
    """
    [Detailed description of function logic in English (at least 1 paragraph).
    Required to activate SFT weights for code generation from docstrings.]
    """
#
# === LOG DRIVEN DEVELOPMENT 2.0 (LDD) INSTRUCTIONS ===
# 1. STRICT LOG LINE FORMAT:
# f"[{CLASSIFIER}][IMP:{1-10}][{FUNCTION_NAME}][{BLOCK_NAME}][{OPERATION_TYPE}] Description[{STATUS}]"
# 2. IMPORTANCE (IMP) SCALE:
# -[IMP:1-3] (Trace): Local variable dumps in loops.
# -[IMP:4-6] (Flow): Start/end of blocks, internal function calls, branching.
# -[IMP:7-8] (I/O & Boundary): DB access, API calls, file reads.
# - [IMP:9-10] (Business Logic & AI Belief): Hypothesis testing, AAG Goal achievement, critical errors. You MUST log your "belief" about how the code should work.
# 3. EXCEPTION ENRICHMENT: In complex functions, output local context at IMP:10 on failure.
# 4. XML-DOM MARKUP: Internal code MUST be split into blocks: # START_BLOCK_[NAME] ... # END_BLOCK_[NAME]
#

    # START_BLOCK_[BLOCK_NAME_1]:[Brief block description]
    [Block 1 logic]
    # END_BLOCK_[BLOCK_NAME_1]

    return [Result]
# END_FUNCTION_[FunctionName]


=== ONE-SHOT EXAMPLE (Library Check) ===

# FILE: tools/check_ai_libs.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Verification of target AI-efficient libraries presence in the environment.
# SCOPE: System environment introspection, dependency checking.
# INPUT: None (works with current Python environment).
# OUTPUT: Dictionary with installation statuses of requested modules.
# KEYWORDS:[DOMAIN(8): Environment; CONCEPT(7): DependencyCheck; TECH(9): PythonImport]
# LINKS:[USES_API(8): importlib]
# END_MODULE_CONTRACT
#
# START_INVARIANTS:
# - check_all_libraries ALWAYS returns a dictionary.
# - Dictionary ALWAYS contains all target libraries as keys.
# END_INVARIANTS
#
# START_RATIONALE:
# Q: Why use importlib.util.find_spec instead of direct import statements?
# A: Direct import (import numpy) triggers ImportError and halts the script on the first missing library. find_spec allows safe collection of the full environment picture.
# END_RATIONALE
#
# START_CHANGE_SUMMARY:
# LAST_CHANGE: [v1.0.0 - Initial creation of system and ML library verification module.]
# END_CHANGE_SUMMARY
#
# START_MODULE_MAP:
# FUNC 10[Checks presence of target AI libraries in the environment] => check_all_libraries
# END_MODULE_MAP
#
# START_USE_CASES:
# -[check_all_libraries]: System (Startup) -> VerifyEnvironmentDependencies -> EnvironmentStatusReported
# END_USE_CASES

import logging
import importlib.util

logger = logging.getLogger(__name__)

# START_FUNCTION_check_all_libraries
# START_CONTRACT:
# PURPOSE: Iterates through system and ML libraries lists, checking availability.
# INPUTS: None
# OUTPUTS:
# - dict - Dictionary where key is library name (str), value is install status (bool)
# SIDE_EFFECTS: None.
# KEYWORDS:[PATTERN(6): Iterator; CONCEPT(8): Introspection]
# LINKS:[USES_API(8): importlib.util]
# COMPLEXITY_SCORE: 5[Medium complexity due to iteration and exception handling.]
# END_CONTRACT
def check_all_libraries() -> dict:
    """
    Function performs introspection of the current Python environment to find pre-installed libraries.
    It uses importlib for safe package presence verification without actual memory loading,
    preventing side effects and import errors. Result is returned as a dictionary for
    subsequent ML readiness analysis.
    """

    # START_BLOCK_INITIALIZE_LISTS: [Generating target libraries lists]
    system_libs =[
        "math", "random", "statistics", "decimal", "datetime", "time", "re",
        "os", "sys", "csv", "json", "sqlite3", "xml.etree.ElementTree",
        "configparser", "pickle", "base64", "hashlib", "collections",
        "itertools", "functools", "logging", "argparse", "typing", "uuid",
        "zipfile", "tarfile", "gzip", "zlib", "shutil", "tempfile"
    ]
    ml_libs =[
        "numpy", "pandas", "scipy", "sklearn", "matplotlib", "seaborn",
        "h5py", "openpyxl", "requests", "lxml", "PIL", "reportlab",
        "sympy", "dateutil", "pytz"
    ]
    all_libs = system_libs + ml_libs
    result_map = {}

    logger.debug(f"[VarCheck][IMP:4][check_all_libraries][INITIALIZE_LISTS][Params] Lists initialized. Total libraries: {len(all_libs)} [INFO]")
    # END_BLOCK_INITIALIZE_LISTS

    # START_BLOCK_VERIFY_DEPENDENCIES: [Iteration and safe import spec checking]
    for lib_name in all_libs:
        try:
            spec = importlib.util.find_spec(lib_name)
            is_installed = spec is not None
            result_map[lib_name] = is_installed

            logger.debug(f"[LibCheck][IMP:3][check_all_libraries][VERIFY_DEPENDENCIES][ConditionCheck] Package {lib_name} found: {is_installed}[{'SUCCESS' if is_installed else 'FAIL'}]")
        except Exception as e:
            # BUG_FIX_CONTEXT: Previously caught ImportError, but find_spec can throw ValueError on malformed paths. Expanded to Exception.
            result_map[lib_name] = False
            logger.critical(f"[SystemError][IMP:10][check_all_libraries][VERIFY_DEPENDENCIES][ExceptionEnrichment] Failure searching for {lib_name}. Local vars: lib_name={lib_name}. Err: {e} [FATAL]")
    # END_BLOCK_VERIFY_DEPENDENCIES

    # START_BLOCK_RETURN_RESULTS:[Summary and return]
    installed_count = sum(result_map.values())
    logger.info(f"[BeliefState][IMP:9][check_all_libraries][RETURN_RESULTS][ReturnData] Installed {installed_count} out of {len(all_libs)} libraries. [VALUE]")

    return result_map
    # END_BLOCK_RETURN_RESULTS
# END_FUNCTION_check_all_libraries

$END_MODIFICATION_AND_GENERATION
