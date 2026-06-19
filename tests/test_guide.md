# QA Test Guide: $PROJECT_NAME

## Summary
This document is for QA agents to verify the implementation against business requirements.

## Tools
- **Pytest**: `python -m pytest tests/ -s -v`
- **SQLite3 CLI**: `sqlite3 <db_path>` (if applicable)

## Entry Data
- **Config:** `config.json` — keys: [list keys and expected types]
- **Database:** `<db_name>.db` — tables: [list tables and schemas]

## Verification Scenarios

### 1. [Scenario Name]
```sql
-- SQL query to verify data integrity
SELECT COUNT(*) FROM <table>;
```
**Expected result:** [description]

### 2. [Scenario Name]
```sql
-- SQL query to verify constraints
SELECT * FROM <table> WHERE <condition>;
```
**Expected result:** [description]

## Expected Log Markers [IMP:9-10]
1. `[BeliefState][IMP:9][<function_name>][<block_name>][AAGGoal] <description> [SUCCESS]`
2. In case of error: `[SystemError][IMP:10][<function_name>]... [FATAL]`

## QA Checklist
- [ ] Database table(s) exist and have correct schema
- [ ] Data integrity verified via SQL queries
- [ ] Log evidence of [IMP:9] markers in test output
- [ ] All business requirements from DevelopmentPlan.md are covered
- [ ] Headless UI tests verify return types (DataFrame, Figure, etc.)
