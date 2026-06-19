---
name: graph-protocol
description: "MANDATORY PROTOCOL for generating XML Knowledge Graphs. Must be invoked before creating or updating any knowledge-graph.xml or AppGraph.xml file. This is a strict formatting standard, not a guide."
---

# MANDATORY PROTOCOL: XML Knowledge Graph Generation

**Objective:**
Create a hierarchical and networked knowledge graph based on the project codebase in XML format. This serves as the primary semantic map for navigation and dependency understanding.

**General Graph Structure:**
1. Wrap the entire graph in a root `<KnowledgeGraph>` tag.
2. The first child element must describe the project as a whole (e.g., `<PROJECT_NAME_Version_Info>`).
3. It must contain global `keywords`, `terms`, and `annotation`, plus a `<BusinessScenarios>` section.

**Tag Naming Standards:**
1. **Uniqueness:** Each tag name must be unique.
2. **Formatting:** Replace dots (`.`) with underscores (`_`).
3. **Suffixes:** Add `_py` (module), `_CLASS` (class), `_FUNC` (function), or `_METHOD` (method).
   * Example: `utils.load_data` -> `<utils_load_data_FUNC>`.
4. **Attributes:** Use `FILE="..."` for modules and `NAME="..."` for other entities.

**Entity Structure:**
1. **TYPE Attribute:** Mandatory (e.g., `DATA_PROCESSING_MODULE`, `IS_FUNCTION_OF_MODULE`).
2. **Child Elements:** `<keywords>`, `<terms>`, `<annotation>`.
3. **Hierarchy:** Nest entities (module -> class -> method).
4. **Cross-Links:** Use `<Link TARGET="Unique_Tag_Name" TYPE="RELATIONSHIP_TYPE" />`.
    *   Types: `CALLS_FUNCTION`, `CALLS_METHOD`, `USES_API`, `READS_DATA_FROM`, `DEPENDS_ON`, `ORCHESTRATES_FLOW`, etc.

## ONE-SHOT EXAMPLE (Abstract)

```xml
<KnowledgeGraph>
  <MyProject_1_0_0_Info TYPE="PROJECT_INFO">
    <keywords>Keywords, Examples</keywords>
    <annotation>Project purpose annotation.</annotation>
    <BusinessScenarios>
      <Scenario NAME="CoreAction">Actor -> Action -> Result</Scenario>
    </BusinessScenarios>
  </MyProject_1_0_0_Info>

  <core_logic_py FILE="src/core_logic.py" TYPE="DATA_PROCESSING_MODULE">
    <annotation>Core business logic module.</annotation>
    <core_logic_DataProcessor_CLASS NAME="DataProcessor" TYPE="IS_CLASS_OF_MODULE">
      <core_logic_DataProcessor_process_data_METHOD NAME="process_data" TYPE="BUSINESS_LOGIC">
        <annotation>Transforms input data.</annotation>
      </core_logic_DataProcessor_process_data_METHOD>
    </core_logic_DataProcessor_CLASS>
  </core_logic_py>

  <main_ui_py FILE="src/main_ui.py" TYPE="UI_MODULE">
    <main_ui_on_click_handler_FUNC NAME="on_click_handler" TYPE="CONTROLLER">
      <CrossLinks>
        <Link TARGET="core_logic_DataProcessor_process_data_METHOD" TYPE="CALLS_METHOD" />
      </CrossLinks>
    </main_ui_on_click_handler_FUNC>
  </main_ui_py>

  <ProjectCrossLinks TYPE="MODULE_INTERACTIONS_OVERVIEW">
    <Link SOURCE="main_ui_py" TARGET="core_logic_py" TYPE="DEPENDS_ON" />
  </ProjectCrossLinks>
</KnowledgeGraph>
```
