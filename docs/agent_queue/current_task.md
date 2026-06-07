# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059U-Impl + 059V-Design - ImportAuditLog Migration Skeleton and Import Adapter Implementation Slice Design.

## Context Level

Level 2 for 059U implementation, Level 3 for 059V design.

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
10. `docs/review_notes/2026-06-07_task-059s-design_059t-design_import-audit-migration-and-adapter-test-contract_codex-review.md`
11. This task file

## Context

059S designed the future `ImportAuditLog` schema with `archive_source` and `manifest_hash` traceability fields. 059T designed repository/filesystem adapter test contracts.

This batch may add a narrowly scoped schema helper for the audit log table. It must not wire importer write behavior, copy files, implement repository adapters, or add UI/CLI/service integration.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059U-Impl - ImportAuditLog migration skeleton
  - Task 059V-Design - first importer adapter implementation slice design
- For Task 059U:
  - Add the smallest suitable migration/schema helper in the existing repository layer.
  - Prefer extending `repository/db.py` with an idempotent helper such as `ensure_import_audit_log_schema(connection)` and SQL constants, unless the existing structure clearly suggests a better small location.
  - The helper may create only:
    - `ImportAuditLog` table,
    - `idx_import_audit_log_strategy_uid`,
    - `idx_import_audit_log_imported_at`.
  - Include the fields from 059S, including `archive_source` and `manifest_hash`.
  - Add focused tests using an in-memory SQLite connection or `DatabaseManager(":memory:")`.
  - Tests must verify:
    - table exists,
    - indexes exist,
    - helper is idempotent,
    - invalid `status` fails,
    - invalid `conflict_policy_applied` fails,
    - valid minimal failed audit row can be inserted directly by the test.
- For Task 059V:
  - Create `docs/archive_import_adapter_slice_design_059V.md`.
  - Design only the first minimal future adapter slice, likely `AuditLogRepositoryAdapter.insert_failure_log()`.
  - Define DTO fields, transaction boundary, failure behavior, and tests for that future slice.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059u-impl_059v-design_import-audit-migration-skeleton-and-adapter-slice_deepseek.md`

### Do Not

- Do not implement importer DB writes.
- Do not implement strategy/dataset/validation repository adapters.
- Do not copy archive files into project folders.
- Do not wire importer into UI, services, CLI, or real repositories.
- Do not implement zip extraction.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not run destructive migration rollback logic.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `repository/db.py`
- `tests/test_import_audit_log_schema.py`
- `docs/archive_import_adapter_slice_design_059V.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059u-impl_059v-design_import-audit-migration-skeleton-and-adapter-slice_deepseek.md`

## Acceptance Criteria

1. ImportAuditLog schema helper is idempotent and narrowly scoped.
2. Schema includes `archive_source` and `manifest_hash`.
3. Tests verify table, indexes, idempotency, CHECK constraints, and a valid direct insert.
4. No importer DB writes, file copies, real repository adapter implementation, UI/service/CLI wiring, zip extraction, dependencies, or engine changes are made.
5. 059V design exists and recommends exactly one next two-task batch.
6. Changelog, task board, and completion report are updated.
7. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_import_audit_log_schema.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused audit schema tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059U-Impl + 059V-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
