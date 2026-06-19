# Plans Directory

## Structure

```
plans/
  active/                         ← current iteration plans
    2026-04-04_auth_module.md     ← example: plan for auth module
    2026-04-10_payment_flow.md    ← example: plan for payment flow
  archive/                        ← completed/superseded plans
    2026-03-20_initial_setup.md   ← moved here after completion
```

## Rules

1. **One plan per iteration.** Each new task/feature/fix gets its own plan file.
2. **Naming:** `YYYY-MM-DD_short_description.md` — date of creation + what it covers.
3. **Format:** Use `$START_DEV_PLAN` / `$END_DEV_PLAN` from `devplan-protocol` skill.
4. **Lifecycle:**
   - Agent creates plan in `active/` during Architect phase.
   - User approves → Agent implements during Code phase.
   - After implementation is verified → move plan to `archive/`.
5. **Active plans** are the source of truth for current work.
6. **Archive** is history of decisions — agents can reference it but don't execute from it.
