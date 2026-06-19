---
name: python-testing
description: |
  Universal Python testing patterns with pytest. Covers unit/integration/e2e strategy,
  AAA pattern, naming conventions, mocking strategy, fixtures, LDD telemetry verification,
  and test organization. Applies to any Python project (scripts, backends, data pipelines, CLI tools).
user-invocable: true
---

# Python Testing Patterns

Universal testing strategy and patterns for Python projects using pytest.

## When to Activate

- Writing new tests
- Reviewing test code
- Setting up test infrastructure
- After creating a new module, service, or data handler

---

## Test Strategy

### Three Layers

| Layer | What | How | Speed |
|-------|------|-----|-------|
| **Unit** | Business logic, pure functions | Mock all external deps | Fast (ms) |
| **Integration** | Module + DB / file / config | Real files via `tmp_path` | Medium (100ms+) |
| **E2E** | Full data-flow slice | Real DB + config + output verification | Slow (seconds) |

> **Rule:** Every module with logic gets unit tests. Every module with I/O gets integration tests. E2E only for critical happy paths.

---

## Test Structure (AAA — Arrange, Act, Assert)

```python
def test_calculate_total_applies_discount_for_premium_user(tmp_path):
    # Arrange — set up inputs and dependencies
    config_file = tmp_path / "config.json"
    config_file.write_text('{"discount": 0.1}')

    # Act — call the function under test
    result = calculate_total(items=[100, 200], config_path=str(config_file))

    # Assert — verify the outcome
    assert result == 270.0
```

> **Rule:** One test = one behavior. If `# Act` has more than 2 lines, the test may be doing too much.

---

## Naming Convention

```python
# Pattern: test_<function>_<expected_result>_when_<condition>
def test_calculate_total_raises_when_items_empty(): ...
def test_load_config_returns_defaults_when_file_missing(): ...
def test_save_to_db_persists_row_when_valid_input(): ...
def test_process_data_returns_empty_df_when_source_empty(): ...
```

> **Rule:** Test name must describe behavior, not implementation.

---

## What to Mock vs Not Mock

### Mock (external boundaries):
- External HTTP calls (httpx, requests)
- Email / notification sending
- File storage (S3, remote paths)
- Database (in **unit** tests only — use `tmp_path` for integration)
- `datetime.now()`, `uuid4()` — time/randomness
- Third-party APIs (Stripe, OpenAI, etc.)

### Never Mock (domain logic):
- Business logic / calculation rules
- Data transformations
- Validation functions
- Pure functions

```python
from unittest.mock import patch, Mock

# GOOD — mock external, test real logic
def test_fetch_data_raises_when_api_unavailable():
    with patch("mymodule.requests.get") as mock_get:
        mock_get.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            fetch_data(url="http://api.example.com")

# BAD — mocking the thing you're testing
def test_process():
    processor = Mock(spec=DataProcessor)
    processor.run.return_value = []  # testing nothing!
```

---

## Fixtures

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def temp_db(tmp_path):
    """Real SQLite DB in a temporary directory."""
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    return str(db_path)

@pytest.fixture
def temp_config(tmp_path):
    """Config file in a temporary directory."""
    config = {"key": "value", "threshold": 10}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return str(config_path)
```

> **Rule:** Always use `tmp_path` for files and DBs — never hardcode paths. Tests must be isolated and repeatable.

---

## LDD Telemetry Verification

Every integration/E2E test **must** verify that production code emitted a Belief State log (`[IMP:9]`).
This confirms the business logic path was actually executed, not just that no exception was raised.

```python
def test_process_data_emits_belief_state(temp_db, caplog):
    import logging
    with caplog.at_level(logging.DEBUG):
        result = process_data(db_path=temp_db)

    # Verify LDD Belief State was emitted
    found_belief = any(
        "[IMP:" in r.message and int(r.message.split("[IMP:")[1].split("]")[0]) >= 9
        for r in caplog.records
    )
    assert found_belief, "Critical LDD Error: Belief State [IMP:9] not found in logs"
    assert result is not None
```

> **Rule:** If `[IMP:9]` is missing, the production function is missing its telemetry — fix the function, not the test.

---

## Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_returns_data_when_valid_url():
    result = await fetch_async(url="http://example.com")
    assert result is not None
```

> **Requirements:** `pip install pytest-asyncio` and add to `pyproject.toml`:
> ```toml
> [tool.pytest.ini_options]
> asyncio_mode = "auto"
> ```

---

## Test Commands

```bash
# Run single test file
python -m pytest tests/test_module.py -s -v

# Run single test by name
python -m pytest -k "test_calculate_total" -v

# Run full test suite
python -m pytest tests/ -s -v

# Run with coverage
python -m pytest --cov=src --cov-report=term-missing -v

# Run only fast unit tests (skip integration)
python -m pytest -m "not integration" -v
```

> **Rule:** After changes, run tests only for changed files + files that import them. Never run the full suite without explicit request.

---

## Test Organization

```
tests/
├── conftest.py              # Anti-Loop Protocol + shared fixtures
├── test_guide.md            # QA guide: entry data, SQL queries, expected log markers
├── test_<module_a>.py       # Tests for module_a (backend logic, DB, config)
├── test_<module_b>.py       # Tests for module_b
└── test_<module_c>_ui.py    # UI handler tests (headless, if applicable)
```

> Mirror the source module structure in `tests/`. One test file per source module.

---

## Markers

```python
# conftest.py
import pytest

# Usage
@pytest.mark.integration
def test_db_saves_row(temp_db): ...
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: tests that require real DB or filesystem",
    "slow: tests that take > 1 second",
]
```

---

## Anti-Patterns

```python
# BAD: Hardcoded file paths — breaks on other machines
def test_load_config():
    cfg = load_config("/home/user/myproject/config.json")  # never!

# GOOD: tmp_path fixture
def test_load_config(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text('{"key": "val"}')
    cfg = load_config(str(cfg_path))
    assert cfg["key"] == "val"

# BAD: Test depends on execution order
class TestPipeline:
    result = None
    def test_step1(self): self.result = step1()
    def test_step2(self): step2(self.result)  # fails if step1 didn't run!

# BAD: No assertions
def test_process():
    process_data(db_path="test.db")  # ... and then what?

# BAD: Testing implementation, not behavior
def test_save():
    save(data)
    assert save._call_count == 1  # who cares HOW it saves?

# GOOD: Test behavior and outcome
def test_save_persists_record_when_valid_input(temp_db):
    save(data, db_path=temp_db)
    rows = query_all(db_path=temp_db)
    assert len(rows) == 1
    assert rows[0]["value"] == data["value"]
```
