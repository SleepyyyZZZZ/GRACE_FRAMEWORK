#!/usr/bin/env python3
# FILE: tools/check_semantics.py
# VERSION: 1.2.0
# START_MODULE_CONTRACT:
# PURPOSE: Automated semantic markup compliance validator for the GRACE framework codebase.
#          Checks Python backend files, frontend TS/JS/TSX/Vue files, and AppGraph.xml files
#          for adherence to the semantic template protocol defined in CLAUDE.md / AGENTS.md.
# SCOPE: File scanning, regex-based pattern matching, XML structural validation, terminal reporting.
# INPUT: Root directory path (default: project root), optional CLI flags.
# OUTPUT: Colored terminal report with per-file issue lists. Optional JSON output.
#         Exit code: 0=all passed, 1=errors found, 2=warnings only.
# KEYWORDS: [DOMAIN(9): CodeQuality; CONCEPT(9): SemanticMarkup; TECH(7): StaticAnalysis]
# LINKS: [READS_DATA_FROM(9): CLAUDE.md semantic template; READS_DATA_FROM(8): docs/AppGraph.xml]
# END_MODULE_CONTRACT
#
# START_INVARIANTS:
# - Script never modifies any source file. Read-only analysis only.
# - Exit code 0 only when zero errors AND zero warnings (or --strict not set).
# - Files smaller than MIN_LINES_THRESHOLD are always skipped.
# - Files containing '# SEMANTIC_CHECK: SKIP' on any of the first 10 lines are always skipped.
# END_INVARIANTS
#
# START_RATIONALE:
# Q: Why use regex instead of Python AST for function detection?
# A: AST parses the code tree but cannot see the comment-based semantic markup that lives
#    *above* the def statement. Regex operates on raw text and captures both def declarations
#    and their surrounding comment annotations in one pass.
# Q: Why not require START_MODULE_MAP as an ERROR?
# A: Existing reference files in the template (test_lib.py, conftest.py) do not have MODULE_MAP.
#    Making it an ERROR would cause the validator to report errors on its own template files on
#    first run, which is misleading. It is reported as WARNING so the user sees it but can triage.
# Q: Why does the AppGraph validator expect <KnowledgeGraph> root and not <AppGraph>?
# A: Inspecting docs/AppGraph.xml in this repo reveals the actual root tag is <KnowledgeGraph>.
#    The CLAUDE.md protocol comment mentions AppGraph.xml as a filename but the XML root tag
#    in the reference template is <KnowledgeGraph>.
# Q: Why does the script skip __init__.py?
# A: __init__.py files are package markers, typically containing only re-exports or empty content.
#    They are structural not behavioral, and semantic markup adds no value to them.
# END_RATIONALE
#
# START_CHANGE_SUMMARY:
# LAST_CHANGE: v1.2.0 — Added two-level AppGraph hierarchy validation (check_graph_hierarchy): verifies local AppGraph.xml existence per source module directory, global↔local bridge references (orphaned local graph detection), and broken LOCAL_GRAPH_REF entries. All violations are ERROR severity (GRAPH_VIOLATION). Added GRAPH_EXEMPT_DIRS config.
# PREV_CHANGE_SUMMARY: v1.1.0 — Added presence checks: USE_CASES, RATIONALE, INVARIANTS blocks; MODULE_CONTRACT internal fields (PURPOSE, KEYWORDS, LINKS); CHANGE_SUMMARY internal field (LAST_CHANGE); function CONTRACT fields (PURPOSE, COMPLEXITY_SCORE); COMPLEXITY_SCORE>7→mandatory blocks correlation; START_BLOCK/END_BLOCK orphan detection. Mirrored for frontend.
# END_CHANGE_SUMMARY
#
# START_MODULE_MAP:
# FUNC 10[CLI entry point — orchestrates all checks and output] => main
# FUNC  9[Validates a single Python file for semantic markup compliance] => check_python_file
# FUNC  8[Validates a single frontend TS/JS/TSX/Vue file for semantic markup] => check_frontend_file
# FUNC  9[Validates an AppGraph.xml for structural integrity] => check_appgraph
# FUNC  7[Recursively finds all Python and frontend source files] => find_source_files
# FUNC  7[Locates global and local AppGraph.xml files in the project] => find_appgraphs
# FUNC  9[Validates two-level AppGraph hierarchy: local graph existence and global↔local bridge] => check_graph_hierarchy
# FUNC  8[Prints the full colored compliance report to stdout] => print_report
# FUNC  6[Serializes all results to JSON for machine consumption] => output_json_report
# CLASS 7[Represents a single compliance issue with severity and message] => CheckIssue
# CLASS 8[Aggregates all issues for one analyzed file] => FileCheckResult
# CLASS 5[ANSI color code container; supports disable() for no-color mode] => Color
# END_MODULE_MAP
#
# START_USE_CASES:
# - [main]: Developer/CI -> RunValidator -> SemanticComplianceReported
# - [check_python_file]: Validator -> InspectPyFile -> ComplianceStatusDetermined
# - [check_frontend_file]: Validator -> InspectFEFile -> FrontendComplianceReported
# - [check_appgraph]: Validator -> InspectXMLGraph -> GraphStructureValidated
# - [check_graph_hierarchy]: Validator -> VerifyGraphHierarchy -> TwoLevelGraphIntegrityConfirmed
# END_USE_CASES

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════
# START_BLOCK_CONFIGURATION: Global validator configuration constants
# ═══════════════════════════════════════════════════════
MIN_LINES_THRESHOLD: int = 20  # Files with fewer lines are skipped entirely

SKIP_DIRS: set = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv', '.mypy_cache',
    'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache', '.ruff_cache',
    '.omc', '.agent', '.codex',
}

SKIP_FILENAMES: set = {
    '__init__.py',
    'setup.py',
    'setup.cfg',
}

PYTHON_EXTENSIONS: frozenset = frozenset({'.py'})
FRONTEND_EXTENSIONS: frozenset = frozenset({'.ts', '.tsx', '.js', '.jsx', '.vue'})

# AppGraph.xml locations: global is docs/AppGraph.xml; all others are local
GLOBAL_APPGRAPH_REL_PATH: str = 'docs/AppGraph.xml'

# Directories exempt from the "must have local AppGraph.xml" rule.
# These are utility/infrastructure directories, not source module packages.
GRAPH_EXEMPT_DIRS: set = {
    'tools', 'tests', 'docs', 'plans', 'scripts', 'migrations',
    'config', 'configs', 'fixtures', 'static', 'templates', 'public',
}

# Tag that marks a file as exempt from semantic checks
SKIP_PRAGMA: str = 'SEMANTIC_CHECK: SKIP'
# ═══════════════════════════════════════════════════════
# END_BLOCK_CONFIGURATION
# ═══════════════════════════════════════════════════════


# START_FUNCTION_Color
# START_CONTRACT:
# PURPOSE: ANSI terminal color codes container with a disable() class method
#          for no-color / JSON output modes.
# COMPLEXITY_SCORE: 1[Trivial constants class]
# END_CONTRACT
class Color:
    """
    Holds ANSI escape codes for terminal colorization. All attributes are mutable
    class-level strings so that Color.disable() can zero them out in-place, affecting
    all downstream f-string formatting without passing color flags through every function.
    """
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    RESET  = '\033[0m'

    @classmethod
    def disable(cls) -> None:
        """Zero out all color codes, making all formatted output plain text."""
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
        cls.CYAN = cls.BOLD = cls.DIM = cls.RESET = ''
# END_FUNCTION_Color


# START_FUNCTION_CheckIssue
# START_CONTRACT:
# PURPOSE: Immutable value object representing one semantic markup violation or advisory.
# COMPLEXITY_SCORE: 1[Simple dataclass]
# END_CONTRACT
@dataclass
class CheckIssue:
    """
    Represents a single discovered compliance issue. The severity field drives
    report formatting and exit-code determination: 'error' causes exit 1,
    'warning' causes exit 2 (or 1 in --strict mode), 'info' is purely informational.
    The optional line_hint allows future enhancements to show exact source locations.
    """
    severity: str            # 'error' | 'warning' | 'info'
    message: str
    line_hint: Optional[int] = None
# END_FUNCTION_CheckIssue


# START_FUNCTION_FileCheckResult
# START_CONTRACT:
# PURPOSE: Aggregated compliance result for a single analyzed file.
# COMPLEXITY_SCORE: 2[Dataclass with computed properties]
# END_CONTRACT
@dataclass
class FileCheckResult:
    """
    Collects all CheckIssue instances for a single file after analysis. Provides
    computed properties (errors, warnings, passed) that downstream report generation
    and exit-code logic rely on. The file_type field ('python' | 'frontend' | 'appgraph')
    routes the result into the correct report section.
    """
    file_path: str           # Relative path from project root (for display)
    file_type: str           # 'python' | 'frontend' | 'appgraph'
    issues: List[CheckIssue] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ''

    @property
    def errors(self) -> List[CheckIssue]:
        """Returns only error-severity issues."""
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[CheckIssue]:
        """Returns only warning-severity issues."""
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def passed(self) -> bool:
        """Returns True only if zero error-severity issues are present."""
        return len(self.errors) == 0
# END_FUNCTION_FileCheckResult


# START_FUNCTION_find_source_files
# START_CONTRACT:
# PURPOSE: Recursively scan a directory tree to collect Python and frontend source files.
# INPUTS:
# - Root directory path to begin scanning => root_dir: Path
# OUTPUTS:
# - Tuple[List[Path], List[Path]] — (python_files, frontend_files), both sorted
# SIDE_EFFECTS: None. Read-only filesystem traversal.
# KEYWORDS: [PATTERN(5): Traversal; CONCEPT(6): FileDiscovery; TECH(5): os.walk]
# COMPLEXITY_SCORE: 4[Recursive directory walk with multi-condition filtering]
# END_CONTRACT
def find_source_files(root_dir: Path) -> Tuple[List[Path], List[Path]]:
    """
    Walks the entire project directory tree starting from root_dir. Prunes SKIP_DIRS
    and hidden directories (starting with '.') in-place from the os.walk traversal to
    avoid descending into them. Collects files by extension into two separate lists —
    Python backend and frontend — to allow category-specific validation rules downstream.
    """
    python_files: List[Path] = []
    frontend_files: List[Path] = []

    # START_BLOCK_TRAVERSE_TREE: [Walk the directory tree with skip-dir pruning]
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune skip directories in-place to prevent os.walk from descending into them
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith('.')
        ]

        for filename in filenames:
            if filename in SKIP_FILENAMES:
                continue
            filepath = Path(dirpath) / filename
            ext = filepath.suffix.lower()
            if ext in PYTHON_EXTENSIONS:
                python_files.append(filepath)
            elif ext in FRONTEND_EXTENSIONS:
                frontend_files.append(filepath)
    # END_BLOCK_TRAVERSE_TREE

    return sorted(python_files), sorted(frontend_files)
# END_FUNCTION_find_source_files


# START_FUNCTION_find_appgraphs
# START_CONTRACT:
# PURPOSE: Locate the global AppGraph.xml (docs/AppGraph.xml) and all local AppGraph.xml
#          files residing in subdirectories of the project.
# INPUTS:
# - Root directory path => root_dir: Path
# OUTPUTS:
# - Tuple[Optional[Path], List[Path]] — (global_path_or_None, sorted_local_paths)
# SIDE_EFFECTS: None.
# KEYWORDS: [CONCEPT(7): GraphDiscovery; TECH(6): XMLFiles; PATTERN(5): Locator]
# COMPLEXITY_SCORE: 3[Simple walk with filename filter]
# END_CONTRACT
def find_appgraphs(root_dir: Path) -> Tuple[Optional[Path], List[Path]]:
    """
    Identifies the global knowledge graph at the canonical path docs/AppGraph.xml.
    Then performs a full directory walk to find any additional AppGraph.xml files
    in subdirectories, treating them as local module-level graphs. Returns both
    the global path (or None if absent) and the sorted list of local graph paths.
    """
    global_candidate: Path = root_dir / GLOBAL_APPGRAPH_REL_PATH
    global_graph: Optional[Path] = global_candidate if global_candidate.exists() else None
    local_graphs: List[Path] = []

    # START_BLOCK_FIND_LOCAL_GRAPHS: [Walk tree to collect non-global AppGraph.xml files]
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith('.')
        ]
        for filename in filenames:
            if filename == 'AppGraph.xml':
                filepath = Path(dirpath) / filename
                if filepath.resolve() != global_candidate.resolve():
                    local_graphs.append(filepath)
    # END_BLOCK_FIND_LOCAL_GRAPHS

    return global_graph, sorted(local_graphs)
# END_FUNCTION_find_appgraphs


# ───────────────────────────────────────────────────────
# START_BLOCK_HELPER_FUNCTIONS: Shared utilities for check functions
# ───────────────────────────────────────────────────────

def _has_skip_pragma(lines: List[str]) -> bool:
    """Returns True if any of the first 10 lines contains the SKIP_PRAGMA string."""
    return any(SKIP_PRAGMA in line for line in lines[:10])


def _check_paired_block(
    content: str,
    start_tag: str,
    end_tag: str,
    severity: str,
    label: str,
) -> List[CheckIssue]:
    """
    Checks that both start_tag and end_tag are present in content.
    Returns a list of CheckIssue objects: empty list means the block is present and paired.
    Reports a single combined issue when both are absent, or individual issues for
    orphaned start/end tags to pinpoint the specific violation.
    """
    issues: List[CheckIssue] = []
    has_start = start_tag in content
    has_end = end_tag in content

    if not has_start and not has_end:
        issues.append(CheckIssue(severity, f'Missing {label}: neither {start_tag} nor {end_tag} found'))
    elif not has_start:
        issues.append(CheckIssue('error', f'{label}: {end_tag} found but {start_tag} is missing (orphaned END)'))
    elif not has_end:
        issues.append(CheckIssue('error', f'{label}: {start_tag} found but {end_tag} is missing (unclosed block)'))
    return issues

# ───────────────────────────────────────────────────────
# END_BLOCK_HELPER_FUNCTIONS
# ───────────────────────────────────────────────────────


# START_FUNCTION_check_python_file
# START_CONTRACT:
# PURPOSE: Full semantic markup compliance validator for a single Python source file.
#          Checks module-level required blocks, then validates every non-trivial function
#          definition for its wrapper tags, CONTRACT block, docstring, and code blocks.
# INPUTS:
# - Absolute path to the Python file => file_path: Path
# - Project root for computing display-friendly relative paths => root_dir: Path
# OUTPUTS:
# - FileCheckResult — aggregated compliance result with all discovered issues
# SIDE_EFFECTS: None. Read-only.
# KEYWORDS: [PATTERN(7): Validator; CONCEPT(9): SemanticMarkup; TECH(7): RegexParsing]
# LINKS: [READS_DATA_FROM(9): CLAUDE.md semantic template specification]
# COMPLEXITY_SCORE: 8[Multi-pass regex analysis: module blocks + per-function structural checks]
# END_CONTRACT
def check_python_file(file_path: Path, root_dir: Path) -> FileCheckResult:
    """
    Performs a multi-pass validation of a Python source file against the GRACE semantic
    protocol. Pass 1 reads and size-checks the file. Pass 2 checks module-level required
    blocks (FILE header, VERSION header, MODULE_CONTRACT, CHANGE_SUMMARY, MODULE_MAP).
    Pass 3 extracts all function definitions via regex and for each non-trivial function
    verifies the START_FUNCTION/END_FUNCTION wrapper, START_CONTRACT block, docstring
    presence, and at least one START_BLOCK/END_BLOCK pair inside the function body.
    Pass 4 checks LDD log format usage when a logger is detected.
    Returns a FileCheckResult containing all issues found across all passes.
    """
    rel_path = str(file_path.relative_to(root_dir))
    result = FileCheckResult(file_path=rel_path, file_type='python')

    # START_BLOCK_READ_FILE: [Load file content; abort on read error]
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as exc:
        result.issues.append(CheckIssue('error', f'Cannot read file: {exc}'))
        return result
    lines = content.splitlines()
    # END_BLOCK_READ_FILE

    # START_BLOCK_SKIP_CHECKS: [Evaluate skip conditions before any analysis]
    if len(lines) < MIN_LINES_THRESHOLD:
        result.skipped = True
        result.skip_reason = f'Too small ({len(lines)} lines, threshold={MIN_LINES_THRESHOLD})'
        return result

    if _has_skip_pragma(lines):
        result.skipped = True
        result.skip_reason = f'Contains {SKIP_PRAGMA} pragma'
        return result
    # END_BLOCK_SKIP_CHECKS

    # START_BLOCK_MODULE_HEADER: [Validate # FILE: and # VERSION: headers]
    has_file_header = any(re.match(r'#\s*FILE\s*:', line) for line in lines[:5])
    has_version_header = any(re.match(r'#\s*VERSION\s*:', line) for line in lines[:10])
    if not has_file_header:
        result.issues.append(CheckIssue('error', 'Missing  # FILE: <path>  header (expected in first 5 lines)'))
    if not has_version_header:
        result.issues.append(CheckIssue('error', 'Missing  # VERSION: <x.y.z>  header (expected in first 10 lines)'))
    # END_BLOCK_MODULE_HEADER

    # START_BLOCK_MODULE_REQUIRED_BLOCKS: [Check mandatory module-level semantic blocks]
    result.issues.extend(_check_paired_block(
        content, 'START_MODULE_CONTRACT', 'END_MODULE_CONTRACT',
        'error', 'MODULE_CONTRACT block'
    ))
    result.issues.extend(_check_paired_block(
        content, 'START_CHANGE_SUMMARY', 'END_CHANGE_SUMMARY',
        'error', 'CHANGE_SUMMARY block'
    ))
    # MODULE_MAP is in the template but omitted in some reference files → WARNING
    result.issues.extend(_check_paired_block(
        content, 'START_MODULE_MAP', 'END_MODULE_MAP',
        'warning', 'MODULE_MAP block'
    ))
    # USE_CASES — mandatory per semantic template (AAG notation)
    result.issues.extend(_check_paired_block(
        content, 'START_USE_CASES', 'END_USE_CASES',
        'warning', 'USE_CASES block'
    ))
    # RATIONALE — recommended for all but trivial modules
    result.issues.extend(_check_paired_block(
        content, 'START_RATIONALE', 'END_RATIONALE',
        'info', 'RATIONALE block (recommended)'
    ))
    # INVARIANTS — optional, for stateful modules
    result.issues.extend(_check_paired_block(
        content, 'START_INVARIANTS', 'END_INVARIANTS',
        'info', 'INVARIANTS block (for stateful modules)'
    ))
    # END_BLOCK_MODULE_REQUIRED_BLOCKS

    # START_BLOCK_MODULE_INTERNAL_FIELDS: [Check key fields inside MODULE_CONTRACT and CHANGE_SUMMARY]
    mc_start = content.find('START_MODULE_CONTRACT')
    mc_end = content.find('END_MODULE_CONTRACT')
    if mc_start != -1 and mc_end != -1 and mc_end > mc_start:
        mc_body = content[mc_start:mc_end]
        if 'PURPOSE' not in mc_body:
            result.issues.append(CheckIssue('error', 'MODULE_CONTRACT: missing PURPOSE field'))
        if 'KEYWORDS' not in mc_body:
            result.issues.append(CheckIssue('error', 'MODULE_CONTRACT: missing KEYWORDS field'))
        if 'LINKS' not in mc_body:
            result.issues.append(CheckIssue('info', 'MODULE_CONTRACT: missing LINKS field'))

    cs_start = content.find('START_CHANGE_SUMMARY')
    cs_end = content.find('END_CHANGE_SUMMARY')
    if cs_start != -1 and cs_end != -1 and cs_end > cs_start:
        cs_body = content[cs_start:cs_end]
        if 'LAST_CHANGE' not in cs_body:
            result.issues.append(CheckIssue('error', 'CHANGE_SUMMARY: missing LAST_CHANGE field'))
    # END_BLOCK_MODULE_INTERNAL_FIELDS

    # START_BLOCK_EXTRACT_FUNCTIONS: [Find all top-level and class-level def statements]
    # Captures function name from lines like: [async] def func_name(
    func_pattern = re.compile(r'^[ \t]*(?:async\s+)?def\s+(\w+)\s*\(', re.MULTILINE)
    func_matches = list(func_pattern.finditer(content))
    # END_BLOCK_EXTRACT_FUNCTIONS

    # START_BLOCK_BUILD_WRAPPER_SPANS: [Build coverage map of existing START_FUNCTION/END_FUNCTION zones]
    # Methods defined inside an already-wrapped class/function (e.g. Color.disable inside
    # START_FUNCTION_Color / END_FUNCTION_Color) do not need their own wrapper per CLAUDE.md.
    wrapper_spans: list = []
    wrapper_start_pattern = re.compile(r'#\s*START_FUNCTION_(\w+)')
    wrapper_end_pattern = re.compile(r'#\s*END_FUNCTION_(\w+)')
    for ws_match in wrapper_start_pattern.finditer(content):
        ws_name = ws_match.group(1)
        we_match = wrapper_end_pattern.search(content, ws_match.end())
        if we_match and we_match.group(1) == ws_name:
            wrapper_spans.append((ws_match.start(), we_match.end(), ws_name))
    # END_BLOCK_BUILD_WRAPPER_SPANS

    # START_BLOCK_VALIDATE_FUNCTIONS: [Check semantic wrapper for each function]
    for match in func_matches:
        func_name: str = match.group(1)

        # Skip dunder methods (structural Python boilerplate) except __init__
        if func_name.startswith('__') and func_name.endswith('__') and func_name != '__init__':
            continue
        # Skip pytest test functions — they follow a different (assertion-based) protocol
        if func_name.startswith('test_') or func_name.startswith('pytest_'):
            continue
        # Skip all private helpers (underscore-prefixed) — they are implementation details,
        # not exported contracts. Includes nested closures like _print_section.
        if func_name.startswith('_'):
            continue

        # Skip @property, @staticmethod, @abstractmethod — truly trivial, no semantic wrapper needed.
        # @classmethod is NOT skipped: factory classmethods (e.g. from_root) can be complex.
        pre_lines = content[:match.start()].rstrip().split('\n')
        pre_nearby = [line.strip() for line in pre_lines[-5:]]
        trivial_decorators = {'@property', '@staticmethod', '@abstractmethod'}
        if any(line in trivial_decorators for line in pre_nearby):
            continue

        # Skip methods already nested inside another START_FUNCTION_X / END_FUNCTION_X wrapper
        # (e.g. Color.disable inside START_FUNCTION_Color). Per CLAUDE.md, only top-level
        # entities need their own wrapper; class methods are covered by the class wrapper.
        func_pos = match.start()
        is_nested = any(
            s < func_pos < e and ws_name != func_name
            for s, e, ws_name in wrapper_spans
        )
        if is_nested:
            continue

        start_tag = f'START_FUNCTION_{func_name}'
        end_tag   = f'END_FUNCTION_{func_name}'
        has_start = start_tag in content
        has_end   = end_tag in content

        # START_BLOCK_CHECK_WRAPPER: [Verify START_FUNCTION / END_FUNCTION presence]
        if not has_start and not has_end:
            result.issues.append(CheckIssue(
                'error',
                f"def {func_name}(): missing # {start_tag} / # {end_tag} wrapper"
            ))
            continue   # No point checking internals if wrapper is absent
        if not has_start:
            result.issues.append(CheckIssue(
                'error',
                f"def {func_name}(): # {end_tag} present but # {start_tag} missing"
            ))
        if not has_end:
            result.issues.append(CheckIssue(
                'error',
                f"def {func_name}(): # {start_tag} present but # {end_tag} missing (unclosed)"
            ))
        # END_BLOCK_CHECK_WRAPPER

        # START_BLOCK_EXTRACT_FUNCTION_BODY: [Isolate text between wrapper tags for deeper checks]
        start_idx = content.find(f'# {start_tag}')
        if start_idx == -1:
            start_idx = content.find(start_tag)
        end_idx = content.find(f'# {end_tag}')
        if end_idx == -1:
            end_idx = content.find(end_tag)

        func_body = ''
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            func_body = content[start_idx:end_idx]
        # END_BLOCK_EXTRACT_FUNCTION_BODY

        if func_body:
            # START_BLOCK_CHECK_CONTRACT: [Verify START_CONTRACT / END_CONTRACT inside wrapper + internal fields]
            if 'START_CONTRACT' not in func_body:
                result.issues.append(CheckIssue(
                    'error',
                    f"def {func_name}(): missing # START_CONTRACT block (SFT context protocol)"
                ))
            elif 'END_CONTRACT' not in func_body:
                result.issues.append(CheckIssue(
                    'error',
                    f"def {func_name}(): START_CONTRACT found but END_CONTRACT missing"
                ))
            else:
                fc_start = func_body.find('START_CONTRACT')
                fc_end = func_body.find('END_CONTRACT')
                if fc_start != -1 and fc_end != -1 and fc_end > fc_start:
                    fc_body = func_body[fc_start:fc_end]
                    if 'PURPOSE' not in fc_body:
                        result.issues.append(CheckIssue(
                            'warning',
                            f"def {func_name}(): CONTRACT missing PURPOSE field"
                        ))
                    if 'COMPLEXITY_SCORE' not in fc_body:
                        result.issues.append(CheckIssue(
                            'warning',
                            f"def {func_name}(): CONTRACT missing COMPLEXITY_SCORE field"
                        ))
            # END_BLOCK_CHECK_CONTRACT

            # START_BLOCK_CHECK_DOCSTRING: [Verify triple-quoted docstring in function body]
            # Pattern: 'def func_name(...):' followed (optionally across lines) by whitespace + """
            docstring_pattern = re.compile(
                r'def\s+' + re.escape(func_name) + r'\s*\(.*?\)\s*(?:->[^:]+)?\s*:\s*\n\s*"""',
                re.DOTALL
            )
            has_docstring = bool(docstring_pattern.search(func_body))
            if not has_docstring:
                result.issues.append(CheckIssue(
                    'error',
                    f"def {func_name}(): missing docstring — required for SFT priming (CLAUDE.md §Technique)"
                ))
            # END_BLOCK_CHECK_DOCSTRING

            # START_BLOCK_CHECK_CODE_BLOCKS: [Verify START_BLOCK/END_BLOCK pairs + COMPLEXITY_SCORE correlation]
            has_start_block = bool(re.search(r'#\s*START_BLOCK_\w+', func_body))
            has_end_block   = bool(re.search(r'#\s*END_BLOCK_\w+', func_body))

            # Parse COMPLEXITY_SCORE value for correlation check
            cs_match = re.search(r'COMPLEXITY_SCORE\s*:\s*(\d+)', func_body)
            complexity_score = int(cs_match.group(1)) if cs_match else None

            if not has_start_block and not has_end_block:
                if complexity_score is not None and complexity_score > 7:
                    result.issues.append(CheckIssue(
                        'error',
                        f"def {func_name}(): COMPLEXITY_SCORE={complexity_score} (>7) — "
                        f"block segmentation via START_BLOCK_*/END_BLOCK_* is mandatory"
                    ))
                else:
                    result.issues.append(CheckIssue(
                        'info',
                        f"def {func_name}(): no START_BLOCK_*/END_BLOCK_* pairs "
                        f"(required for COMPLEXITY_SCORE > 7)"
                    ))
            elif has_start_block and not has_end_block:
                result.issues.append(CheckIssue(
                    'error',
                    f"def {func_name}(): START_BLOCK found but no matching END_BLOCK tags"
                ))
            elif not has_start_block and has_end_block:
                result.issues.append(CheckIssue(
                    'error',
                    f"def {func_name}(): END_BLOCK found but no matching START_BLOCK tags"
                ))
            else:
                start_count = len(re.findall(r'#\s*START_BLOCK_\w+', func_body))
                end_count = len(re.findall(r'#\s*END_BLOCK_\w+', func_body))
                if start_count != end_count:
                    result.issues.append(CheckIssue(
                        'warning',
                        f"def {func_name}(): mismatched block tags — "
                        f"{start_count} START_BLOCK vs {end_count} END_BLOCK"
                    ))
            # END_BLOCK_CHECK_CODE_BLOCKS

    # END_BLOCK_VALIDATE_FUNCTIONS

    # START_BLOCK_CHECK_LDD: [Validate LDD log format: 5-bracket prefix + STATUS presence]
    # Only trigger when file explicitly creates a logger via logging.getLogger() —
    # this avoids false positives when 'logger.' appears inside string literals.
    has_logger_instance = bool(re.search(
        r'\blogger\s*=\s*(?:logging\.getLogger|logging\.Logger)', content
    ))
    if has_logger_instance:
        # Full 5-bracket prefix: [CLASSIFIER][IMP:N][FUNC_NAME][BLOCK_NAME][OP_TYPE]
        ldd_full_prefix = re.compile(
            r'\[[^\]]+\]\[IMP:\d+\]\[[^\]]+\]\[[^\]]+\]\[[^\]]+\]'
        )
        has_any_ldd = False
        incomplete_prefix_count = 0
        missing_status_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if '[IMP:' not in line:
                continue
            # Verify this [IMP:] is within a logger call context (same line or up to 3 lines above)
            context_start = max(0, i - 3)
            nearby = '\n'.join(lines[context_start:i + 1])
            if 'logger.' not in nearby:
                continue

            has_any_ldd = True
            prefix_match = ldd_full_prefix.search(line)
            if not prefix_match:
                incomplete_prefix_count += 1
            else:
                # Check STATUS bracket: [WORD] or [{expr}] after the 5-bracket prefix.
                # Look on the same line first, then check up to 2 continuation lines
                # (for multi-line f-string logger calls).
                after_prefix = line[prefix_match.end():]
                has_status = bool(re.search(r'\[[\w{]', after_prefix))
                if not has_status:
                    continuation = '\n'.join(lines[i + 1:min(i + 3, len(lines))])
                    has_status = bool(re.search(r'\[[\w{]', continuation))
                if not has_status:
                    missing_status_count += 1

        if not has_any_ldd:
            result.issues.append(CheckIssue(
                'warning',
                'Logger instance found but no LDD-format entries — '
                'expected: logger.xxx(f"[CLASSIFIER][IMP:N][FuncName][Block][OpType] msg [STATUS]")'
            ))
        else:
            if incomplete_prefix_count > 0:
                result.issues.append(CheckIssue(
                    'warning',
                    f'{incomplete_prefix_count} LDD log entry(ies) with incomplete prefix — '
                    f'must have: [CLASSIFIER][IMP:N][FuncName][BlockName][OpType]'
                ))
            if missing_status_count > 0:
                result.issues.append(CheckIssue(
                    'warning',
                    f'{missing_status_count} LDD log entry(ies) missing trailing [STATUS] tag'
                ))
    # END_BLOCK_CHECK_LDD

    return result
# END_FUNCTION_check_python_file


# START_FUNCTION_check_frontend_file
# START_CONTRACT:
# PURPOSE: Semantic markup compliance validator for frontend TypeScript/JavaScript/TSX/Vue files.
#          Uses // comment prefix convention for all semantic tags.
# INPUTS:
# - Absolute path to the frontend file => file_path: Path
# - Project root for relative display paths => root_dir: Path
# OUTPUTS:
# - FileCheckResult — aggregated compliance result
# SIDE_EFFECTS: None.
# KEYWORDS: [PATTERN(7): Validator; CONCEPT(8): SemanticMarkup; TECH(7): FrontendFiles]
# LINKS: [READS_DATA_FROM(8): CLAUDE.md semantic template (JS comment variant)]
# COMPLEXITY_SCORE: 7[Multi-pass validation matching Python checker but adapted for JS/TS syntax]
# END_CONTRACT
def check_frontend_file(file_path: Path, root_dir: Path) -> FileCheckResult:
    """
    Validates TypeScript / JavaScript / TSX / JSX / Vue source files against the GRACE
    semantic protocol adapted for JS-style comments (// prefix). Runs module-level checks
    for FILE/VERSION headers and required block pairs, then detects function and component
    definitions using patterns for named functions, arrow functions, and React components.
    For each discovered function/component above a minimum name length, verifies that
    START_FUNCTION_X / END_FUNCTION_X wrappers and START_CONTRACT blocks are present.
    Returns a FileCheckResult with all discovered issues.
    """
    rel_path = str(file_path.relative_to(root_dir))
    result = FileCheckResult(file_path=rel_path, file_type='frontend')

    # START_BLOCK_READ_FILE: [Load frontend file content]
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as exc:
        result.issues.append(CheckIssue('error', f'Cannot read file: {exc}'))
        return result
    lines = content.splitlines()
    # END_BLOCK_READ_FILE

    # START_BLOCK_SKIP_CHECKS: [Size and pragma skip evaluation]
    if len(lines) < MIN_LINES_THRESHOLD:
        result.skipped = True
        result.skip_reason = f'Too small ({len(lines)} lines, threshold={MIN_LINES_THRESHOLD})'
        return result

    if _has_skip_pragma(lines):
        result.skipped = True
        result.skip_reason = f'Contains {SKIP_PRAGMA} pragma'
        return result
    # END_BLOCK_SKIP_CHECKS

    # START_BLOCK_FE_MODULE_HEADER: [Validate // FILE: and // VERSION: headers]
    has_file_header = any(re.match(r'//\s*FILE\s*:', line) for line in lines[:5])
    has_ver_header  = any(re.match(r'//\s*VERSION\s*:', line) for line in lines[:10])
    if not has_file_header:
        result.issues.append(CheckIssue('error', 'Missing  // FILE: <path>  header (expected in first 5 lines)'))
    if not has_ver_header:
        result.issues.append(CheckIssue('error', 'Missing  // VERSION: <x.y.z>  header (expected in first 10 lines)'))
    # END_BLOCK_FE_MODULE_HEADER

    # START_BLOCK_FE_MODULE_BLOCKS: [Check required module-level semantic block pairs]
    result.issues.extend(_check_paired_block(
        content, 'START_MODULE_CONTRACT', 'END_MODULE_CONTRACT',
        'error', 'MODULE_CONTRACT block'
    ))
    result.issues.extend(_check_paired_block(
        content, 'START_CHANGE_SUMMARY', 'END_CHANGE_SUMMARY',
        'error', 'CHANGE_SUMMARY block'
    ))
    result.issues.extend(_check_paired_block(
        content, 'START_MODULE_MAP', 'END_MODULE_MAP',
        'warning', 'MODULE_MAP block'
    ))
    # USE_CASES — mandatory per semantic template (AAG notation)
    result.issues.extend(_check_paired_block(
        content, 'START_USE_CASES', 'END_USE_CASES',
        'warning', 'USE_CASES block'
    ))
    # RATIONALE — recommended for all but trivial modules
    result.issues.extend(_check_paired_block(
        content, 'START_RATIONALE', 'END_RATIONALE',
        'info', 'RATIONALE block (recommended)'
    ))
    # INVARIANTS — optional, for stateful modules
    result.issues.extend(_check_paired_block(
        content, 'START_INVARIANTS', 'END_INVARIANTS',
        'info', 'INVARIANTS block (for stateful modules)'
    ))
    # END_BLOCK_FE_MODULE_BLOCKS

    # START_BLOCK_FE_MODULE_INTERNAL_FIELDS: [Check key fields inside MODULE_CONTRACT and CHANGE_SUMMARY]
    mc_start = content.find('START_MODULE_CONTRACT')
    mc_end = content.find('END_MODULE_CONTRACT')
    if mc_start != -1 and mc_end != -1 and mc_end > mc_start:
        mc_body = content[mc_start:mc_end]
        if 'PURPOSE' not in mc_body:
            result.issues.append(CheckIssue('error', 'MODULE_CONTRACT: missing PURPOSE field'))
        if 'KEYWORDS' not in mc_body:
            result.issues.append(CheckIssue('error', 'MODULE_CONTRACT: missing KEYWORDS field'))
        if 'LINKS' not in mc_body:
            result.issues.append(CheckIssue('info', 'MODULE_CONTRACT: missing LINKS field'))

    cs_start = content.find('START_CHANGE_SUMMARY')
    cs_end = content.find('END_CHANGE_SUMMARY')
    if cs_start != -1 and cs_end != -1 and cs_end > cs_start:
        cs_body = content[cs_start:cs_end]
        if 'LAST_CHANGE' not in cs_body:
            result.issues.append(CheckIssue('error', 'CHANGE_SUMMARY: missing LAST_CHANGE field'))
    # END_BLOCK_FE_MODULE_INTERNAL_FIELDS

    # START_BLOCK_FE_DETECT_FUNCTIONS: [Detect exported and local functions/components]
    fe_func_patterns = [
        # export default function ComponentName( | export function foo(
        re.compile(r'(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)\s*[\(<]', re.MULTILINE),
        # export const foo = (...) =>  |  const Foo = () =>
        re.compile(r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(', re.MULTILINE),
        # const Foo = React.memo(... | React.forwardRef(
        re.compile(r'(?:export\s+)?const\s+(\w+)\s*=\s*React\.(?:memo|forwardRef|lazy)\s*\(', re.MULTILINE),
    ]
    found_funcs: set = set()
    for pat in fe_func_patterns:
        for m in pat.finditer(content):
            name = m.group(1)
            # Skip very short names (likely single-char params or abbreviations)
            if len(name) >= 3:
                found_funcs.add(name)
    # END_BLOCK_FE_DETECT_FUNCTIONS

    # START_BLOCK_FE_VALIDATE_FUNCTIONS: [Check wrapper and contract for each function]
    for func_name in sorted(found_funcs):
        start_tag = f'START_FUNCTION_{func_name}'
        end_tag   = f'END_FUNCTION_{func_name}'
        has_start = start_tag in content
        has_end   = end_tag in content

        if not has_start and not has_end:
            result.issues.append(CheckIssue(
                'error',
                f"function/component '{func_name}': missing // {start_tag} / // {end_tag} wrapper"
            ))
            continue

        if not has_start:
            result.issues.append(CheckIssue(
                'error', f"'{func_name}': // {end_tag} present but // {start_tag} missing"
            ))
        if not has_end:
            result.issues.append(CheckIssue(
                'error', f"'{func_name}': // {start_tag} present but // {end_tag} missing"
            ))

        # Check START_CONTRACT inside the function block
        if has_start and has_end:
            # Find block boundaries (supports both // and /* comment styles)
            start_idx = next(
                (content.find(f'// {start_tag}'), content.find(f'/* {start_tag}')),
                -1
            )
            # Simpler: just scan for either prefix
            si = content.find(f'// {start_tag}')
            if si == -1:
                si = content.find(start_tag)
            ei = content.find(f'// {end_tag}')
            if ei == -1:
                ei = content.find(end_tag)

            if si != -1 and ei != -1 and ei > si:
                func_body = content[si:ei]
                if 'START_CONTRACT' not in func_body:
                    result.issues.append(CheckIssue(
                        'error',
                        f"'{func_name}': missing // START_CONTRACT block inside wrapper"
                    ))
                elif 'END_CONTRACT' not in func_body:
                    result.issues.append(CheckIssue(
                        'error',
                        f"'{func_name}': START_CONTRACT found but END_CONTRACT missing"
                    ))
                else:
                    fc_start = func_body.find('START_CONTRACT')
                    fc_end = func_body.find('END_CONTRACT')
                    if fc_start != -1 and fc_end != -1 and fc_end > fc_start:
                        fc_body = func_body[fc_start:fc_end]
                        if 'PURPOSE' not in fc_body:
                            result.issues.append(CheckIssue(
                                'warning',
                                f"'{func_name}': CONTRACT missing PURPOSE field"
                            ))
                        if 'COMPLEXITY_SCORE' not in fc_body:
                            result.issues.append(CheckIssue(
                                'warning',
                                f"'{func_name}': CONTRACT missing COMPLEXITY_SCORE field"
                            ))

                # START_BLOCK_CHECK_JSDOC: [Verify JSDoc /** */ block — SFT priming equivalent for JS/TS]
                has_jsdoc = bool(re.search(r'/\*\*[\s\S]*?\*/', func_body))
                if not has_jsdoc:
                    result.issues.append(CheckIssue(
                        'error',
                        f"'{func_name}': missing JSDoc /** */ block — required for SFT priming (CLAUDE.md §Technique)"
                    ))
                # END_BLOCK_CHECK_JSDOC

                # Block segmentation checks with COMPLEXITY_SCORE correlation
                has_start_block = bool(re.search(r'//\s*START_BLOCK_\w+', func_body))
                has_end_block   = bool(re.search(r'//\s*END_BLOCK_\w+', func_body))

                cs_match = re.search(r'COMPLEXITY_SCORE\s*:\s*(\d+)', func_body)
                complexity_score = int(cs_match.group(1)) if cs_match else None

                if not has_start_block and not has_end_block:
                    if complexity_score is not None and complexity_score > 7:
                        result.issues.append(CheckIssue(
                            'error',
                            f"'{func_name}': COMPLEXITY_SCORE={complexity_score} (>7) — "
                            f"block segmentation via START_BLOCK_*/END_BLOCK_* is mandatory"
                        ))
                    else:
                        result.issues.append(CheckIssue(
                            'info',
                            f"'{func_name}': no // START_BLOCK_*/END_BLOCK_* pairs found"
                        ))
                elif has_start_block and not has_end_block:
                    result.issues.append(CheckIssue(
                        'error',
                        f"'{func_name}': START_BLOCK found but no matching END_BLOCK tags"
                    ))
                elif not has_start_block and has_end_block:
                    result.issues.append(CheckIssue(
                        'error',
                        f"'{func_name}': END_BLOCK found but no matching START_BLOCK tags"
                    ))
                else:
                    start_count = len(re.findall(r'//\s*START_BLOCK_\w+', func_body))
                    end_count = len(re.findall(r'//\s*END_BLOCK_\w+', func_body))
                    if start_count != end_count:
                        result.issues.append(CheckIssue(
                            'warning',
                            f"'{func_name}': mismatched block tags — "
                            f"{start_count} START_BLOCK vs {end_count} END_BLOCK"
                        ))
    # END_BLOCK_FE_VALIDATE_FUNCTIONS

    return result
# END_FUNCTION_check_frontend_file


# START_FUNCTION_check_appgraph
# START_CONTRACT:
# PURPOSE: Validates an AppGraph.xml (global or local) for XML integrity, structural compliance,
#          and real-world consistency with the actual source files on disk.
# INPUTS:
# - Absolute path to AppGraph.xml => graph_path: Path
# - Whether this is the global graph (docs/AppGraph.xml) => is_global: bool
# - Project root for relative display paths => root_dir: Path
# - Known source files for coverage cross-reference (optional) => known_source_files: Optional[List[Path]]
# OUTPUTS:
# - FileCheckResult — structural, content, and cross-reference compliance issues
# SIDE_EFFECTS: Reads source files referenced in FILE= attributes for function existence checks.
# KEYWORDS: [PATTERN(6): XMLValidator; CONCEPT(9): KnowledgeGraph; TECH(7): ElementTree]
# LINKS: [READS_DATA_FROM(9): docs/AppGraph.xml GRACE knowledge graph protocol]
# COMPLEXITY_SCORE: 8[XML parsing + structural checks + 3 cross-reference consistency checks]
# END_CONTRACT
def check_appgraph(
    graph_path: Path,
    is_global: bool,
    root_dir: Path,
    known_source_files: Optional[List[Path]] = None,
) -> FileCheckResult:
    """
    Validates an AppGraph.xml file on three levels:
    (1) Structural — valid XML, correct root tag <KnowledgeGraph>, TYPE attributes on all elements,
        naming conventions for module tags.
    (2) Real-world file existence — every FILE="..." attribute in the graph points to a file
        that actually exists on disk; missing files are reported as errors.
    (3) Cross-reference consistency — if known_source_files is provided, checks that all source
        files are registered in the graph (coverage), and that every _FUNC/_METHOD entity with
        a NAME attribute has a corresponding START_FUNCTION_NAME wrapper in the source file.
    Returns all issues aggregated in a single FileCheckResult.
    """
    rel_path  = str(graph_path.relative_to(root_dir))
    is_global_label = 'global' if is_global else 'local'
    result = FileCheckResult(file_path=rel_path, file_type='appgraph')

    # START_BLOCK_PARSE_XML: [Read and parse XML; handle empty file and parse errors]
    try:
        raw = graph_path.read_text(encoding='utf-8')
    except Exception as exc:
        result.issues.append(CheckIssue('error', f'Cannot read file: {exc}'))
        return result

    if not raw.strip():
        result.issues.append(CheckIssue('error', f'AppGraph.xml ({is_global_label}) is completely empty'))
        return result

    try:
        tree = ET.parse(graph_path)
        xml_root = tree.getroot()
    except ET.ParseError as exc:
        result.issues.append(CheckIssue('error', f'Invalid XML — parse error: {exc}'))
        return result
    # END_BLOCK_PARSE_XML

    # START_BLOCK_CHECK_ROOT_TAG: [Validate root element name and attributes]
    expected_root = 'KnowledgeGraph'
    if xml_root.tag != expected_root:
        result.issues.append(CheckIssue(
            'error',
            f"Root element must be <{expected_root}>, found <{xml_root.tag}>"
        ))
    # END_BLOCK_CHECK_ROOT_TAG

    # START_BLOCK_CHECK_TYPE_ATTRS: [Every element should carry a TYPE attribute]
    elements_without_type: List[str] = []
    for elem in tree.iter():
        # Skip the root element itself (it's a container, TYPE not required)
        if elem is xml_root:
            continue
        # Skip XML comments (they appear as special elements in ElementTree)
        if not isinstance(elem.tag, str):
            continue
        if elem.get('TYPE') is None and elem.get('type') is None:
            elements_without_type.append(elem.tag)

    if elements_without_type:
        # Report only first 5 to avoid report spam
        sample = ', '.join(f'<{t}>' for t in elements_without_type[:5])
        extra = f' (and {len(elements_without_type) - 5} more)' if len(elements_without_type) > 5 else ''
        result.issues.append(CheckIssue(
            'warning',
            f'Elements missing TYPE attribute — protocol requires all tags have TYPE: {sample}{extra}'
        ))
    # END_BLOCK_CHECK_TYPE_ATTRS

    # START_BLOCK_CHECK_MODULE_ENTRIES: [Count and validate module-like entries]
    # Module entries are direct children of KnowledgeGraph with FILE attribute
    module_entries = [
        child for child in xml_root
        if isinstance(child.tag, str) and child.get('FILE')
    ]

    if is_global and len(module_entries) == 0:
        result.issues.append(CheckIssue(
            'info',
            'Global AppGraph has no module entries yet — add entries as source modules are created'
        ))
    elif not is_global and len(module_entries) == 0:
        result.issues.append(CheckIssue(
            'warning',
            'Local AppGraph.xml has no module entries — it should document at least the owning module'
        ))
    else:
        # START_BLOCK_CHECK_MODULE_IDS: [Validate naming convention for module IDs]
        for mod in module_entries:
            mod_id = mod.tag
            if '.' in mod_id:
                result.issues.append(CheckIssue(
                    'warning',
                    f"Module tag <{mod_id}> contains dots — convention: replace dots with underscores "
                    f"(e.g., src_auth_service_py)"
                ))
            # Expected suffixes: _py, _ts, _tsx, _js, _jsx, _vue, _CLASS, _FUNC, _METHOD
            known_suffixes = ('_py', '_ts', '_tsx', '_js', '_jsx', '_vue',
                              '_CLASS', '_FUNC', '_METHOD', '_LOCAL')
            if not any(mod_id.endswith(s) for s in known_suffixes):
                result.issues.append(CheckIssue(
                    'info',
                    f"Module tag <{mod_id}> has no recognized suffix "
                    f"(expected: _py, _ts, _tsx, _CLASS, _FUNC, _LOCAL, etc.)"
                ))
        # END_BLOCK_CHECK_MODULE_IDS
    # END_BLOCK_CHECK_MODULE_ENTRIES

    # START_BLOCK_CHECK_CROSSLINKS: [Verify ProjectCrossLinks section exists]
    has_crosslinks = any(
        isinstance(child.tag, str) and 'CrossLink' in child.tag
        for child in xml_root
    )
    if not has_crosslinks:
        result.issues.append(CheckIssue(
            'info',
            'No <ProjectCrossLinks> section found — add module dependency links as the project grows'
        ))
    # END_BLOCK_CHECK_CROSSLINKS

    # START_BLOCK_CROSSREF_FILE_EXISTS: [Check 1 — FILE= paths in graph actually exist on disk]
    for mod in module_entries:
        file_attr = mod.get('FILE', '')
        if not file_attr:
            continue
        actual_path = root_dir / file_attr
        if not actual_path.exists():
            result.issues.append(CheckIssue(
                'error',
                f'<{mod.tag}> FILE="{file_attr}" — файл не найден на диске'
            ))
    # END_BLOCK_CROSSREF_FILE_EXISTS

    # START_BLOCK_CROSSREF_COVERAGE: [Check 2 — all source files are registered in graph]
    if known_source_files:
        graph_file_attrs: set = {
            mod.get('FILE', '')
            for mod in module_entries
            if mod.get('FILE')
        }
        for src_path in known_source_files:
            rel = str(src_path.relative_to(root_dir))
            if rel not in graph_file_attrs:
                result.issues.append(CheckIssue(
                    'error',
                    f'Файл "{rel}" не зарегистрирован в AppGraph — добавь модульную запись'
                ))
    # END_BLOCK_CROSSREF_COVERAGE

    # START_BLOCK_CROSSREF_FUNCTIONS: [Check 3 — _FUNC/_METHOD entities exist as START_FUNCTION_X in source]
    # Tags ending with _FUNC, _FUNCTION, _METHOD, or _BUSINESS_LOGIC represent callable entities.
    func_entity_suffixes = ('_FUNC', '_FUNCTION', '_METHOD')
    func_entity_types    = {'FUNC', 'FUNCTION', 'METHOD', 'BUSINESS_LOGIC', 'CORE_LOGIC'}

    for mod in module_entries:
        file_attr = mod.get('FILE', '')
        if not file_attr:
            continue
        actual_path = root_dir / file_attr
        if not actual_path.exists():
            continue  # already reported in CROSSREF_FILE_EXISTS block
        try:
            src_content = actual_path.read_text(encoding='utf-8')
        except Exception:
            continue

        for entity in mod.iter():
            if entity is mod:
                continue
            if not isinstance(entity.tag, str):
                continue
            entity_name = entity.get('NAME', '')
            entity_type = entity.get('TYPE', '')
            # Match by tag suffix OR by TYPE attribute value
            is_func_entity = (
                any(entity.tag.endswith(s) for s in func_entity_suffixes)
                or entity_type in func_entity_types
            )
            if is_func_entity and entity_name:
                if f'START_FUNCTION_{entity_name}' not in src_content:
                    result.issues.append(CheckIssue(
                        'error',
                        f'AppGraph: <{entity.tag} NAME="{entity_name}"> в {file_attr} — '
                        f'нет # START_FUNCTION_{entity_name} в исходном файле'
                    ))
    # END_BLOCK_CROSSREF_FUNCTIONS

    return result
# END_FUNCTION_check_appgraph


# START_FUNCTION_check_graph_hierarchy
# START_CONTRACT:
# PURPOSE: Validates the two-level AppGraph hierarchy integrity defined in the GRACE protocol.
#          Ensures every source module directory has a local AppGraph.xml, that the global graph
#          references all local graphs via LOCAL_GRAPH_REF, and that no broken references exist.
#          All violations are ERROR severity (GRAPH_VIOLATION) — agents MUST fix them.
# INPUTS:
# - Global AppGraph.xml path or None => global_graph_path: Optional[Path]
# - Discovered local AppGraph.xml paths => local_graph_paths: List[Path]
# - All discovered Python source files => python_files: List[Path]
# - Project root directory => root_dir: Path
# OUTPUTS:
# - FileCheckResult — aggregated hierarchy issues; empty issues list means hierarchy is valid
# SIDE_EFFECTS: Reads global AppGraph.xml for LOCAL_GRAPH_REF parsing.
# KEYWORDS: [PATTERN(7): HierarchyValidator; CONCEPT(9): TwoLevelGraph; TECH(6): ElementTree]
# LINKS: [READS_DATA_FROM(9): docs/AppGraph.xml LOCAL_GRAPH_REF entries]
# COMPLEXITY_SCORE: 7[Directory grouping + XML cross-reference + set-difference checks]
# END_CONTRACT
def check_graph_hierarchy(
    global_graph_path: Optional[Path],
    local_graph_paths: List[Path],
    python_files: List[Path],
    root_dir: Path,
) -> FileCheckResult:
    """
    Validates the two-level AppGraph hierarchy mandated by the GRACE framework protocol.
    The protocol requires that every source module directory has its own local AppGraph.xml
    covering only that module's entities, and that the global graph (docs/AppGraph.xml)
    references every local graph via a LOCAL_GRAPH_REF entry. This function performs three
    critical checks: (1) source module directories missing a local AppGraph.xml,
    (2) local AppGraph.xml files not referenced from the global graph (orphaned graphs),
    (3) LOCAL_GRAPH_REF entries in the global graph pointing to non-existent files on disk
    (broken references). All violations are reported as errors to halt the agent workflow
    until the two-level graph hierarchy is fully consistent.
    """
    result = FileCheckResult(file_path='[GRAPH_HIERARCHY]', file_type='appgraph')

    # START_BLOCK_FIND_MODULE_DIRS: [Identify source module directories that need local AppGraph.xml]
    # Heuristic: for each Python source file, determine its "module root" directory.
    # If under src/, the module root is src/<first_subdir>/.
    # Otherwise, the module root is the top-level directory containing the file.
    # Top-level files (e.g., manage.py) and files in GRAPH_EXEMPT_DIRS are excluded.
    source_module_dirs: set = set()
    for py_file in python_files:
        rel = py_file.relative_to(root_dir)
        parts = rel.parts
        if len(parts) < 2:
            continue  # top-level files do not require a local graph
        top_dir = parts[0]
        if top_dir.lower() in GRAPH_EXEMPT_DIRS:
            continue
        # If the top directory is 'src', the module root is src/<next_dir>/
        if top_dir == 'src' and len(parts) >= 3:
            module_dir = root_dir / parts[0] / parts[1]
        else:
            module_dir = root_dir / parts[0]
        source_module_dirs.add(module_dir)

    local_graph_dirs = {p.parent.resolve() for p in local_graph_paths}
    for src_dir in sorted(source_module_dirs):
        if src_dir.resolve() not in local_graph_dirs:
            rel_dir = str(src_dir.relative_to(root_dir))
            result.issues.append(CheckIssue(
                'error',
                f'GRAPH_VIOLATION: Директория "{rel_dir}/" содержит исходные файлы, '
                f'но не имеет локального AppGraph.xml'
            ))
    # END_BLOCK_FIND_MODULE_DIRS

    # START_BLOCK_CHECK_BRIDGE: [Verify global graph ↔ local graph cross-references]
    if global_graph_path and global_graph_path.exists():
        try:
            tree = ET.parse(global_graph_path)
            xml_root = tree.getroot()
        except ET.ParseError:
            result.issues.append(CheckIssue(
                'error',
                'GRAPH_VIOLATION: Не удалось распарсить docs/AppGraph.xml для проверки иерархии'
            ))
            return result

        # Collect all LOCAL_GRAPH_REF entries from global graph
        # Match by TYPE="LOCAL_GRAPH_REF" attribute or by tag name ending with _LOCAL
        global_ref_files: dict = {}
        for elem in xml_root:
            if not isinstance(elem.tag, str):
                continue
            elem_type = elem.get('TYPE', '')
            if elem_type == 'LOCAL_GRAPH_REF' or elem.tag.endswith('_LOCAL'):
                file_attr = elem.get('FILE', '')
                if file_attr:
                    global_ref_files[file_attr] = elem.tag

        # Check: every local AppGraph.xml must be referenced in global graph
        for local_path in local_graph_paths:
            rel_local = str(local_path.relative_to(root_dir))
            if rel_local not in global_ref_files:
                result.issues.append(CheckIssue(
                    'error',
                    f'GRAPH_VIOLATION: Локальный граф "{rel_local}" не имеет ссылки '
                    f'LOCAL_GRAPH_REF в docs/AppGraph.xml (orphaned graph)'
                ))

        # Check: every LOCAL_GRAPH_REF must point to an existing file on disk
        for file_attr, tag_name in global_ref_files.items():
            actual_path = root_dir / file_attr
            if not actual_path.exists():
                result.issues.append(CheckIssue(
                    'error',
                    f'GRAPH_VIOLATION: <{tag_name} FILE="{file_attr}"> в docs/AppGraph.xml — '
                    f'файл не найден на диске (broken reference)'
                ))
    # END_BLOCK_CHECK_BRIDGE

    return result
# END_FUNCTION_check_graph_hierarchy


# START_FUNCTION_print_report
# START_CONTRACT:
# PURPOSE: Render the full compliance report to stdout using ANSI colors,
#          grouped by Backend / Frontend / Graphs sections.
# INPUTS:
# - Python file results => python_results: List[FileCheckResult]
# - Frontend file results => frontend_results: List[FileCheckResult]
# - Global AppGraph result or None => global_graph_result: Optional[FileCheckResult]
# - Local AppGraph results => local_graph_results: List[FileCheckResult]
# - Whether global graph file is missing => global_graph_missing: bool
# OUTPUTS:
# - Tuple[int, int] — (total_errors, total_warnings) for exit-code determination
# SIDE_EFFECTS: Writes to stdout.
# KEYWORDS: [PATTERN(5): Reporter; CONCEPT(6): TerminalOutput; TECH(5): ANSIColors]
# COMPLEXITY_SCORE: 6[Iterative formatting across three report sections]
# END_CONTRACT
def print_report(
    python_results: List[FileCheckResult],
    frontend_results: List[FileCheckResult],
    global_graph_result: Optional[FileCheckResult],
    local_graph_results: List[FileCheckResult],
    global_graph_missing: bool,
) -> Tuple[int, int]:
    """
    Renders the formatted semantic compliance report to stdout. Organizes output into
    three sections (Backend Python, Frontend TS/JS, Graphs). Each file line shows a
    pass/fail status icon, relative file path, and error/warning counts. Issues are
    printed below each file with colored severity prefix tags [ERR], [WRN], [INF].
    A summary section at the end aggregates total counts across all file types.
    Returns (total_errors, total_warnings) so main() can determine the exit code.
    """
    c = Color
    total_errors   = 0
    total_warnings = 0

    # START_BLOCK_PRINT_HEADER: [Print validator banner]
    print(f"\n{c.BOLD}{c.CYAN}╔══════════════════════════════════════════════════════╗{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}║    GRACE  Semantic Markup Validator  v1.0.0          ║{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}╚══════════════════════════════════════════════════════╝{c.RESET}\n")
    # END_BLOCK_PRINT_HEADER

    # START_BLOCK_PRINT_SECTION: [Generic helper for printing one results section]
    def _print_section(title: str, results: List[FileCheckResult]) -> Tuple[int, int]:
        """Prints one report section and returns (section_errors, section_warnings)."""
        sec_errors = 0
        sec_warnings = 0
        print(f"{c.BOLD}{title}{c.RESET}")
        print(f"{c.DIM}{'─' * 56}{c.RESET}")
        if not results:
            print(f"  {c.DIM}(no files found){c.RESET}\n")
            return 0, 0

        for res in results:
            if res.skipped:
                print(f"  {c.DIM}⊘  {res.file_path}   ← skipped: {res.skip_reason}{c.RESET}")
                continue
            status_str = f"{c.GREEN}✓  PASS{c.RESET}" if res.passed else f"{c.RED}✗  FAIL{c.RESET}"
            ec = len(res.errors)
            wc = len(res.warnings)
            ic = len([i for i in res.issues if i.severity == 'info'])
            meta = f"{c.DIM}({ec} err, {wc} wrn, {ic} inf){c.RESET}"
            print(f"  {status_str}  {c.BOLD}{res.file_path}{c.RESET}  {meta}")

            for issue in res.issues:
                if issue.severity == 'error':
                    pfx = f"{c.RED}     [ERR]{c.RESET}"
                elif issue.severity == 'warning':
                    pfx = f"{c.YELLOW}     [WRN]{c.RESET}"
                else:
                    pfx = f"{c.BLUE}     [INF]{c.RESET}"
                loc = f"  (line {issue.line_hint})" if issue.line_hint else ""
                print(f"{pfx} {issue.message}{loc}")

            sec_errors   += ec
            sec_warnings += wc
        print()
        return sec_errors, sec_warnings
    # END_BLOCK_PRINT_SECTION

    # START_BLOCK_PRINT_PYTHON: [Backend Python section]
    pe, pw = _print_section("[BACKEND]  Python Files", python_results)
    total_errors   += pe
    total_warnings += pw
    # END_BLOCK_PRINT_PYTHON

    # START_BLOCK_PRINT_FRONTEND: [Frontend section]
    fe, fw = _print_section("[FRONTEND]  TS / JS / TSX / Vue Files", frontend_results)
    total_errors   += fe
    total_warnings += fw
    # END_BLOCK_PRINT_FRONTEND

    # START_BLOCK_PRINT_GRAPHS: [AppGraph.xml section]
    print(f"{c.BOLD}[GRAPHS]  AppGraph.xml Files{c.RESET}")
    print(f"{c.DIM}{'─' * 56}{c.RESET}")
    if global_graph_missing:
        print(f"  {c.RED}✗  MISSING{c.RESET}  {GLOBAL_APPGRAPH_REL_PATH}   "
              f"{c.RED}[ERR]{c.RESET} Global knowledge graph file not found")
        total_errors += 1
    elif global_graph_result:
        ge, gw = _print_section.__wrapped__ if hasattr(_print_section, '__wrapped__') else (0, 0)
        # Inline: print global graph result
        res = global_graph_result
        status_str = f"{c.GREEN}✓  PASS{c.RESET}" if res.passed else f"{c.RED}✗  FAIL{c.RESET}"
        ec = len(res.errors)
        wc = len(res.warnings)
        ic = len([i for i in res.issues if i.severity == 'info'])
        meta = f"{c.DIM}(GLOBAL — {ec} err, {wc} wrn, {ic} inf){c.RESET}"
        print(f"  {status_str}  {c.BOLD}{res.file_path}{c.RESET}  {meta}")
        for issue in res.issues:
            if issue.severity == 'error':
                pfx = f"{c.RED}     [ERR]{c.RESET}"
            elif issue.severity == 'warning':
                pfx = f"{c.YELLOW}     [WRN]{c.RESET}"
            else:
                pfx = f"{c.BLUE}     [INF]{c.RESET}"
            print(f"{pfx} {issue.message}")
        total_errors   += ec
        total_warnings += wc

    if not local_graph_results:
        print(f"  {c.DIM}No local AppGraph.xml files found in subdirectories{c.RESET}")
    else:
        for res in local_graph_results:
            status_str = f"{c.GREEN}✓  PASS{c.RESET}" if res.passed else f"{c.RED}✗  FAIL{c.RESET}"
            ec = len(res.errors)
            wc = len(res.warnings)
            ic = len([i for i in res.issues if i.severity == 'info'])
            meta = f"{c.DIM}(LOCAL — {ec} err, {wc} wrn, {ic} inf){c.RESET}"
            print(f"  {status_str}  {c.BOLD}{res.file_path}{c.RESET}  {meta}")
            for issue in res.issues:
                if issue.severity == 'error':
                    pfx = f"{c.RED}     [ERR]{c.RESET}"
                elif issue.severity == 'warning':
                    pfx = f"{c.YELLOW}     [WRN]{c.RESET}"
                else:
                    pfx = f"{c.BLUE}     [INF]{c.RESET}"
                print(f"{pfx} {issue.message}")
            total_errors   += ec
            total_warnings += wc
    print()
    # END_BLOCK_PRINT_GRAPHS

    # START_BLOCK_PRINT_SUMMARY: [Overall summary line]
    py_active  = [r for r in python_results  if not r.skipped]
    fe_active  = [r for r in frontend_results if not r.skipped]
    py_pass    = sum(1 for r in py_active if r.passed)
    fe_pass    = sum(1 for r in fe_active if r.passed)
    py_skip    = sum(1 for r in python_results  if r.skipped)
    fe_skip    = sum(1 for r in frontend_results if r.skipped)

    print(f"{c.BOLD}{'═' * 56}{c.RESET}")
    print(f"{c.BOLD}SUMMARY{c.RESET}")
    print(f"{'─' * 56}")
    print(f"  Backend  (Python) :  {py_pass}/{len(py_active)} passed  "
          f"{c.DIM}({py_skip} skipped){c.RESET}")
    print(f"  Frontend (TS/JS)  :  {fe_pass}/{len(fe_active)} passed  "
          f"{c.DIM}({fe_skip} skipped){c.RESET}")

    if total_errors > 0:
        print(f"\n  {c.RED}{c.BOLD}✗  FAILED — {total_errors} error(s), {total_warnings} warning(s){c.RESET}")
    elif total_warnings > 0:
        print(f"\n  {c.YELLOW}{c.BOLD}⚠  WARNINGS — 0 errors, {total_warnings} warning(s){c.RESET}")
    else:
        print(f"\n  {c.GREEN}{c.BOLD}✓  ALL CHECKS PASSED{c.RESET}")
    print()
    # END_BLOCK_PRINT_SUMMARY

    return total_errors, total_warnings
# END_FUNCTION_print_report


# START_FUNCTION_output_json_report
# START_CONTRACT:
# PURPOSE: Serialize all FileCheckResult objects to a structured JSON document.
# INPUTS:
# - Python file results => python_results: List[FileCheckResult]
# - Frontend file results => frontend_results: List[FileCheckResult]
# - Global AppGraph result or None => global_graph_result: Optional[FileCheckResult]
# - Local AppGraph results => local_graph_results: List[FileCheckResult]
# - Missing global graph flag => global_graph_missing: bool
# - File path to write JSON to, or None for stdout => output_path: Optional[str]
# OUTPUTS:
# - None (side-effect: writes JSON to stdout or file)
# SIDE_EFFECTS: May create/overwrite file at output_path.
# KEYWORDS: [PATTERN(5): Serializer; CONCEPT(6): CIReport; TECH(6): JSON]
# COMPLEXITY_SCORE: 4[Dict construction + json.dumps]
# END_CONTRACT
def output_json_report(
    python_results: List[FileCheckResult],
    frontend_results: List[FileCheckResult],
    global_graph_result: Optional[FileCheckResult],
    local_graph_results: List[FileCheckResult],
    global_graph_missing: bool,
    output_path: Optional[str] = None,
) -> None:
    """
    Converts all FileCheckResult objects into a hierarchically structured JSON document
    suitable for CI/CD tooling, agent orchestrators, or automated dashboards. Each file
    entry includes its path, type, skip status, pass/fail flag, and a list of issues with
    severity, message, and optional line number. A top-level summary provides aggregated
    error and warning counts. Writes to stdout when output_path is None; otherwise writes
    to the specified file path.
    """

    # START_BLOCK_SERIALIZE: [Build the JSON-serializable report dictionary]
    def _res_to_dict(res: FileCheckResult) -> dict:
        """Convert a single FileCheckResult to a JSON-serializable dictionary."""
        return {
            'file':        res.file_path,
            'type':        res.file_type,
            'skipped':     res.skipped,
            'skip_reason': res.skip_reason,
            'passed':      res.passed,
            'issues': [
                {
                    'severity': i.severity,
                    'message':  i.message,
                    'line':     i.line_hint,
                }
                for i in res.issues
            ],
        }

    all_results = (
        python_results + frontend_results
        + ([global_graph_result] if global_graph_result else [])
        + local_graph_results
    )
    total_errors   = sum(len(r.errors) for r in all_results) + (1 if global_graph_missing else 0)
    total_warnings = sum(len(r.warnings) for r in all_results)

    report = {
        'validator': 'GRACE Semantic Markup Validator v1.0.0',
        'summary': {
            'total_errors':   total_errors,
            'total_warnings': total_warnings,
            'passed':         total_errors == 0,
        },
        'python_files':   [_res_to_dict(r) for r in python_results],
        'frontend_files': [_res_to_dict(r) for r in frontend_results],
        'global_appgraph': _res_to_dict(global_graph_result) if global_graph_result
                           else {'missing': True, 'error': 'docs/AppGraph.xml not found'},
        'local_appgraphs': [_res_to_dict(r) for r in local_graph_results],
    }
    # END_BLOCK_SERIALIZE

    # START_BLOCK_WRITE_JSON: [Output JSON to file or stdout]
    json_str = json.dumps(report, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(json_str, encoding='utf-8')
        print(f"JSON report written to: {output_path}", file=sys.stderr)
    else:
        print(json_str)
    # END_BLOCK_WRITE_JSON
# END_FUNCTION_output_json_report


# START_FUNCTION_main
# START_CONTRACT:
# PURPOSE: CLI entry point — parses arguments, orchestrates all checks, prints report, exits.
# INPUTS:
# - sys.argv CLI arguments:
#   --path PATH       Root directory to scan (default: '.')
#   --json            Emit machine-readable JSON instead of colored report
#   --output FILE     Write JSON report to FILE (requires --json)
#   --no-color        Disable ANSI color escape codes
#   --strict          Treat warnings as errors (exit 1 on any warning)
# OUTPUTS:
# - Exit code 0 (all passed), 1 (errors or --strict+warnings), 2 (warnings only)
# SIDE_EFFECTS: Reads filesystem extensively. Writes to stdout/stderr. Calls sys.exit().
# KEYWORDS: [PATTERN(8): EntryPoint; CONCEPT(7): Orchestration; TECH(6): ArgParse]
# COMPLEXITY_SCORE: 5[Sequential orchestration: discover → check → report → exit]
# END_CONTRACT
def main() -> None:
    """
    CLI entry point for the GRACE semantic validator. Parses command-line arguments,
    resolves the project root, discovers all Python and frontend source files along with
    AppGraph.xml files, runs all validation checks in sequence, then either prints a
    colored terminal report or emits JSON. Determines the process exit code based on
    the aggregate error and warning counts: 0 for clean, 1 for errors (or warnings in
    --strict mode), 2 for warnings only. Designed to integrate into CI/CD pipelines
    as a pre-commit gate or standalone compliance audit tool.
    """

    # START_BLOCK_PARSE_ARGS: [Argument parser definition and parsing]
    parser = argparse.ArgumentParser(
        prog='check_semantics',
        description='GRACE Semantic Markup Validator — checks Python / Frontend / AppGraph.xml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  All checks passed (zero errors, zero warnings)
  1  One or more ERROR-level issues found (or --strict with warnings)
  2  No errors but WARNING-level issues found

Examples:
  python tools/check_semantics.py
  python tools/check_semantics.py --path src/
  python tools/check_semantics.py --strict --no-color
  python tools/check_semantics.py --json --output report.json
        """,
    )
    parser.add_argument(
        '--path', default='.',
        help='Root directory to scan (default: current directory)',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Output results as JSON (implies --no-color)',
    )
    parser.add_argument(
        '--output', default=None,
        help='Write JSON report to this file path (requires --json)',
    )
    parser.add_argument(
        '--no-color', action='store_true',
        help='Disable ANSI color codes in terminal output',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Treat warnings as errors — exit 1 if any warnings present',
    )
    args = parser.parse_args()
    # END_BLOCK_PARSE_ARGS

    # START_BLOCK_SETUP: [Configure color mode and resolve root path]
    if args.no_color or args.json:
        Color.disable()

    root_dir = Path(args.path).resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"ERROR: --path '{args.path}' does not exist or is not a directory", file=sys.stderr)
        sys.exit(2)
    # END_BLOCK_SETUP

    # START_BLOCK_DISCOVER: [Find all source files and AppGraph.xml locations]
    python_files, frontend_files = find_source_files(root_dir)
    global_graph_path, local_graph_paths = find_appgraphs(root_dir)
    # END_BLOCK_DISCOVER

    # START_BLOCK_RUN_CHECKS: [Execute validation for each discovered file]
    python_results:   List[FileCheckResult] = [check_python_file(f, root_dir) for f in python_files]
    frontend_results: List[FileCheckResult] = [check_frontend_file(f, root_dir) for f in frontend_files]
    global_graph_missing: bool = global_graph_path is None
    all_source_files: List[Path] = python_files + frontend_files
    global_graph_result: Optional[FileCheckResult] = (
        check_appgraph(global_graph_path, True, root_dir, known_source_files=all_source_files)
        if global_graph_path else None
    )
    local_graph_results: List[FileCheckResult] = [
        check_appgraph(p, False, root_dir) for p in local_graph_paths
    ]

    # Two-level hierarchy validation: local graph existence + global↔local bridge
    hierarchy_result: FileCheckResult = check_graph_hierarchy(
        global_graph_path, local_graph_paths, python_files, root_dir,
    )
    if hierarchy_result.issues:
        local_graph_results.append(hierarchy_result)
    # END_BLOCK_RUN_CHECKS

    # START_BLOCK_OUTPUT: [Render report or JSON]
    if args.json:
        output_json_report(
            python_results, frontend_results,
            global_graph_result, local_graph_results,
            global_graph_missing,
            output_path=args.output,
        )
        all_results = (
            python_results + frontend_results
            + ([global_graph_result] if global_graph_result else [])
            + local_graph_results
        )
        total_errors   = sum(len(r.errors) for r in all_results) + (1 if global_graph_missing else 0)
        total_warnings = sum(len(r.warnings) for r in all_results)
    else:
        total_errors, total_warnings = print_report(
            python_results, frontend_results,
            global_graph_result, local_graph_results,
            global_graph_missing,
        )
    # END_BLOCK_OUTPUT

    # START_BLOCK_EXIT: [Determine exit code and terminate]
    if total_errors > 0:
        sys.exit(1)
    elif total_warnings > 0 and args.strict:
        sys.exit(1)
    elif total_warnings > 0:
        sys.exit(2)
    else:
        sys.exit(0)
    # END_BLOCK_EXIT
# END_FUNCTION_main


if __name__ == '__main__':
    main()
