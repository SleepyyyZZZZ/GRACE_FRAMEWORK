$START_DOC_NAME

**PURPOSE:** [Business requirements for $PROJECT_NAME]
**SCOPE:** [Functional areas covered]
**KEYWORDS:** [DOMAIN: ...; CONCEPT: ...; TECH: ...]

$START_DOCUMENT_PLAN
### Document Plan
<!--
AI-Agent: Generate this entire block before expanding sections.
Format: TYPE [Description] => [Artifact_ID]
-->

**SECTION_GOALS:**
- GOAL [Goal description] => [GOAL_ID]

**SECTION_USE_CASES:**
- USE_CASE [Actor] -> [Action] -> [Business result] => [UC_ID]

$END_DOCUMENT_PLAN

$START_SECTION_FUNCTIONAL_REQUIREMENTS
### Functional Requirements

$START_ARTIFACT_EXAMPLE_MODULE
#### [Module Name]
**TYPE:** GOAL
**KEYWORDS:** [TECH: ...; PATTERN: ...]
$START_CONTRACT
**PURPOSE:** [What this module does]
**DESCRIPTION:** [Detailed description. Use AAG notation for USE_CASE.]
**RATIONALE:** [WHY is this module important?]
**ACCEPTANCE_CRITERIA:** [How do we verify correct implementation?]
$END_CONTRACT
$END_ARTIFACT_EXAMPLE_MODULE

$END_SECTION_FUNCTIONAL_REQUIREMENTS

$END_DOC_NAME
