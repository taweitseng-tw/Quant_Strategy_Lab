# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 060C-Design + 060D-Design - StrategyRepoAdapter Transaction Boundary Refactor Design and DatasetRepoAdapter Insert-Only Slice Design.

## Context Level

Level 3 for both tasks.

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
9. `repository/db.py`
10. `repository/strategy_repo.py`
11. `docs/archive_import_coordinator_architecture_060A.md`
12. `docs/archive_import_coordinator_acceptance_test_contract_060B.md`
13. `docs/review_notes/2026-06-07_task-060a-design_060b-design_fix_coordinator-ordering-and-transaction-boundary_codex-review.md`
14. This task file

## Context

060A/060B fixed the coordinator ordering, but implementation remains deferred because `StrategyRepoAdapter.insert_strategy()` auto-commits and cannot participate in a unified coordinator transaction. The next safe step is design-only: define how to refactor transaction boundaries, and define the dataset repository insert-only slice before any coordinator implementation.

## Scope

### Do

- Complete two design-only tasks:
  - Task 060C-Design - `StrategyRepoAdapter` transaction boundary refactor design.
  - Task 060D-Design - `DatasetRepoAdapter` insert-only slice design.
- For Task 060C:
  - Create `docs/strategy_import_adapter_transaction_boundary_design_060C.md`.
  - Design how `StrategyRepoAdapter.insert_strategy()` can support external transaction control without breaking existing tests/callers.
  - Compare at least two options:
    - add `commit: bool = True`,
    - split into `insert_strategy_no_commit()` plus wrapper,
    - or another local-pattern-compatible option.
  - Recommend exactly one option.
  - Define migration path, compatibility behavior, exception semantics, rollback expectations, and focused tests for the future implementation.
  - Explicitly state that no code is changed in this design task.
- For Task 060D:
  - Create `docs/dataset_import_adapter_insert_only_design_060D.md`.
  - Design a future `DatasetRepoAdapter.insert_dataset()` insert-only slice for imported dataset metadata.
  - Define immutable DTO fields using current `datasets` schema from `repository/db.py`.
  - Define duplicate-reject key, likely based on imported dataset identity/hash/path metadata available from archive manifest and snapshot design.
  - Define behavior for missing dataset snapshot, hash mismatch, source path handling, project_id, row_count/start/end metadata, and no overwrite/update/upsert semantics.
  - Define focused tests for future implementation.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060c-design_060d-design_strategy-transaction-boundary-and-dataset-adapter_gemini.md`

### Do Not

- Do not modify production code.
- Do not implement tests.
- Do not implement coordinator.
- Do not implement dataset adapter.
- Do not implement filesystem staging.
- Do not add audit success writes.
- Do not change DB schema or migrations.
- Do not touch UI, CLI, backtest engine, validation engine, or strategy generator.
- Do not add dependencies.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. Both deliverables are design-only Markdown files.
2. 060C clearly resolves how future strategy inserts can participate in coordinator-controlled transactions.
3. 060C preserves backward compatibility for existing direct adapter usage.
4. 060D defines a narrow dataset insert-only repository slice using current schema and duplicate-reject semantics.
5. No production code or test code changes are made.
6. The next proposed batch remains narrow and reviewable.
7. Full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Full suite passes.
- `git diff --check` has no errors.
- Agent status shows the 060C/060D completion report as latest report.
- `git status --short` shows only docs/report files within this task scope.

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
