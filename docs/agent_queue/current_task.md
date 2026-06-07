# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059Y-Impl + 059Z-Design - StrategyRepoAdapter Duplicate-Reject Insert-Only Slice and Filesystem Staging Design.

## Context Level

Level 2 for 059Y implementation, Level 3 for 059Z design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/archive_import_audit_migration_plan_059S.md`
9. `docs/archive_import_repository_adapter_test_contract_059T.md`
10. `docs/archive_import_write_coordinator_design_059X.md`
11. `docs/review_notes/2026-06-07_task-059w-impl_059x-design_fix_failure-only-audit-log_codex-review.md`
12. This task file

## Context

The archive importer currently has read-only preview building, import audit schema creation, and a failure-only audit log repository adapter. The next safe write slice is strategy import persistence only, with duplicate-reject semantics. This task must not implement the full import coordinator.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059Y-Impl - `StrategyRepoAdapter.insert_strategy()` duplicate-reject insert-only slice.
  - Task 059Z-Design - filesystem staging design only.
- For Task 059Y:
  - Add the smallest suitable repository adapter module or extend an existing repository module only if it clearly fits the project pattern.
  - Define a narrow immutable DTO for imported strategy persistence if needed.
  - Implement only `StrategyRepoAdapter.insert_strategy(strategy_dto)` or an equivalently named insert-only method.
  - The method must reject duplicate strategy UID before or during insert with a clear domain/repository exception.
  - It must not overwrite, update, rename, skip, merge, or mutate an existing strategy row.
  - It must write strategy data only. No dataset writes, no validation writes, no audit writes, no file copies.
  - Add focused tests for:
    - successful strategy insert from a DTO,
    - duplicate UID rejected and original row unchanged,
    - serialized strategy payload/provenance fields persisted exactly,
    - invalid or missing required strategy identifier rejected clearly,
    - no dataset/validation/audit tables are modified.
- For Task 059Z:
  - Create `docs/archive_import_filesystem_staging_design_059Z.md`.
  - Design filesystem staging boundaries only.
  - Cover source archive path validation, destination path policy, temporary staging path, hash verification, rollback cleanup, and transaction ordering with SQLite writes.
  - Explicitly separate design-only content from future implementation.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059y-impl_059z-design_strategy-repo-insert-only-and-filesystem-staging-design_gemini.md`

### Do Not

- Do not implement importer DB write coordinator.
- Do not implement dataset repository writes.
- Do not implement validation repository writes.
- Do not implement audit log success writes.
- Do not implement filesystem copy/staging.
- Do not implement zip behavior.
- Do not add UI, CLI, or service wiring.
- Do not add dependencies.
- Do not change existing strategy serialization behavior unless the adapter cannot work without a minimal, justified call to an existing serializer.
- Do not use overwrite/update/upsert semantics.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. Strategy insert adapter is repository-layer only and has no PySide6/UI imports.
2. Duplicate strategy UID is rejected and leaves the existing row unchanged.
3. Inserted strategy payload and provenance fields are persisted exactly according to existing repository/schema conventions.
4. No dataset, validation, audit, filesystem, coordinator, service, CLI, or UI behavior is implemented.
5. Filesystem staging document is design-only and includes rollback/hash/path-boundary details.
6. The next proposed batch remains narrow and reviewable.
7. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_import_audit_repo.py tests/test_import_audit_log_schema.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_strategy_repo*.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused tests pass.
- Full suite passes.
- `git diff --check` has no errors.
- Agent status shows the 059Y/059Z completion report as latest report.
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
