# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 060E-Impl + 060F-Design - StrategyRepoAdapter Transaction Refactor Implementation and Dataset Snapshot Hash Schema Migration Design.

## Context Level

Level 2 for 060E implementation, Level 3 for 060F design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `repository/strategy_import_adapter.py`
9. `tests/test_strategy_import_adapter.py`
10. `repository/db.py`
11. `docs/strategy_import_adapter_transaction_boundary_design_060C.md`
12. `docs/dataset_import_adapter_insert_only_design_060D.md`
13. `docs/review_notes/2026-06-07_task-060c-design_060d-design_fix_snapshot-hash-schema-boundary_codex-review.md`
14. This task file

## Context

060C selected a transaction-boundary refactor for `StrategyRepoAdapter`: keep `insert_strategy()` backward compatible as the auto-commit wrapper, add `insert_strategy_no_commit()` for coordinator-owned transactions, and extract a shared private core helper. 060D clarified that strict dataset hash dedup requires a future `snapshot_hash` schema migration. This batch may implement only the strategy adapter refactor and design only the dataset schema migration.

## Scope

### Do

- Complete two sequential tasks:
  - Task 060E-Impl - implement `StrategyRepoAdapter` transaction refactor.
  - Task 060F-Design - design dataset `snapshot_hash` schema migration.
- For Task 060E:
  - Modify `repository/strategy_import_adapter.py` only as needed.
  - Extract a private `_insert_strategy_core(dto)` helper containing validation, UID duplicate check, and SQL insert execute without commit/rollback.
  - Keep `insert_strategy(dto)` backward-compatible: it must commit on success and rollback on SQLite write/commit failure.
  - Add `insert_strategy_no_commit(dto)` as the coordinator-facing method: it must not call `commit()` or `rollback()`.
  - Preserve existing exception semantics:
    - `DuplicateStrategyUIDError` for duplicate UID.
    - `StrategyRepoAdapterError` for validation, JSON, and SQLite failures.
  - Add focused tests in `tests/test_strategy_import_adapter.py` for:
    - existing `insert_strategy()` behavior still passes,
    - `insert_strategy_no_commit()` insert can be rolled back by caller,
    - `insert_strategy_no_commit()` insert can be committed by caller,
    - duplicate UID in `insert_strategy_no_commit()` raises without committing,
    - no dataset/validation/audit tables are modified.
- For Task 060F:
  - Create `docs/dataset_snapshot_hash_schema_migration_design_060F.md`.
  - Design only the future additive migration:
    - `ALTER TABLE datasets ADD COLUMN snapshot_hash TEXT NOT NULL DEFAULT ''`
    - `DatabaseManager.SCHEMA_SQL` update for new projects
    - optional index decision for `snapshot_hash`
    - idempotency strategy
    - rollback / compatibility notes
    - focused tests for future implementation
  - Explain how this migration enables 060D Mode B without implementing `DatasetRepoAdapter`.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060e-impl_060f-design_strategy-transaction-refactor-and-dataset-hash-migration-design_gemini.md`

### Do Not

- Do not implement coordinator.
- Do not implement dataset adapter.
- Do not implement dataset schema migration.
- Do not edit `repository/db.py` for 060F; it is design-only.
- Do not add audit success writes.
- Do not implement filesystem staging.
- Do not touch UI, CLI, backtest engine, validation engine, or strategy generator.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. `insert_strategy()` remains backward-compatible and all existing strategy import tests still pass.
2. `insert_strategy_no_commit()` performs no commit/rollback and caller rollback/commit behavior is proven by tests.
3. No dataset, validation, audit, filesystem, coordinator, UI, CLI, or engine behavior is implemented.
4. 060F is design-only and does not edit schema code.
5. Full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_strategy_import_adapter.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused strategy import tests pass.
- Full suite passes.
- `git diff --check` has no errors.
- Agent status shows the 060E/060F completion report as latest report.
- `git status --short` shows only files within this task scope.

## Completion Report Format

Use:

```text
Completed:
Files changed:
Behavior changed:
Tests run:
Assumptions:
Known risks:
Reviewer focus:
```

Then stop.
