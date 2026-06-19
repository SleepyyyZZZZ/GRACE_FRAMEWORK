---
name: devplan-protocol
description: "CORE PROTOCOL for all development planning. Implementation agents will reject plans that do not strictly follow this schema. Mandatory for all development tasks."
---

# CORE PROTOCOL: Development Plan Template

**Objective:**
Standardize the development planning phase for AI agents to ensure structural and process consistency before implementation begins.

$START_DEV_PLAN

**PURPOSE:** [Primary goal and purpose of this development plan.]

---

### 1. Draft Code Graph

**MANDATORY:** This block MUST be in XML format using the rules from the `graph-protocol` skill.

```xml
<DraftCodeGraph>
  <MyComponent_py FILE="path/to/component.py" TYPE="COMPONENT_TYPE">
    <annotation>Component description.</annotation>
    <MyComponent_MyClass_CLASS NAME="MyClass" TYPE="IS_CLASS_OF_MODULE">
      <annotation>Class description.</annotation>
      <MyComponent_MyClass_my_method_METHOD NAME="my_method" TYPE="IS_METHOD_OF_CLASS">
        <annotation>Method description.</annotation>
        <CrossLinks>
          <Link TARGET="OtherComponent_OtherClass_other_method_METHOD" TYPE="CALLS_METHOD" />
        </CrossLinks>
      </MyComponent_MyClass_my_method_METHOD>
    </MyComponent_MyClass_CLASS>
  </MyComponent_py>
</DraftCodeGraph>
```

---

### 2. Step-by-step Data Flow

**MANDATORY:** Describe the key algorithms in a step-by-step sequence. Conduct a mental simulation to ensure logical consistency.

1.  **Step 1:** [First step of the algorithm.]
2.  **Step 2:** [Second step, including data transformations.]
3.  **Step 3:** [Final step.]

---

### 3. Acceptance Criteria

**MANDATORY:** List clear, measurable criteria to verify successful task completion.

- [ ] **Criterion 1:** [Description of the first criterion.]
- [ ] **Criterion 2:** [Description of the second criterion.]

$END_DEV_PLAN
