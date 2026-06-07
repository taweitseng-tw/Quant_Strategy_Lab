# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059W-Impl + 059X-Design - AuditLogRepositoryAdapter Failure Log Slice and Import Write Coordinator Design.

## Context Level

Level 2 for 059W implementation, Level 3 for 059X design.

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
10. `docs/archive_import_adapter_slice_design_059V.md`
11. `docs/review_notes/2026-06-07_task-059u-impl_059v-design_import-audit-migration-skeleton-and-adapter-slice_codex-review.md`
12. This task file

## Context

059U added `ImportAuditLog` schema initialization through `repository/db.py`. 059V designed the first minimal audit-log repository adapter slice.

This batch may implement only the failure-audit-log adapter slice. It must not implement importer DB writes, strategy/dataset/validation repository adapters, file copy, UI/CLI/service wiring, or zip behavior.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059W-Impl - `AuditLogRepositoryAdapter.insert_failure_log()` only
  - Task 059X-Design - import write coordinator design only
- For Task 059W:
  - Add the smallest suitable repository module for audit log writes, likely `repository/import_audit_repo.py`.
  - Define an immutable DTO such as `ImportAuditLogDTO`.
  - Implement `AuditLogRepositoryAdapter.insert_failure_log(dto)` only.
  - The adapter may insert one row into `ImportAuditLog` with `status='FAILED'`.
  - It must ensure the audit schema exists before insertion, using the helper from `repository/db.py`.
  - It may use the existing `DatabaseManager` / sqlite connection style.
  - Add focused tests for:
    - successful failed-audit insert,
    - all DTO fields persisted exactly, including `archive_source` and `manifest_hash`,
    - invalid status or policy is rejected by schema constraints,
    - adapter wraps sqlite write failures in a clear repository/audit exception,
    - no strategy/dataset/validation tables are modified.
- For Task 059X:
  - Create `docs/archive_import_write_coordinator_design_059X.md`.
  - Design future coordinator boundaries only.
  - Cover how `ArchiveImporter.build_preview()`, repository adapters, filesystem staging, and audit logging will be sequenced.
  - Explicitly separate what is implemented now from future implementation.
  - Recommend exactly one next two-task batch.
- Update:
  - `repository/__init__.py` only if the project pattern requires public exports.
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059w-impl_059x-design_audit-log-repository-adapter-and-write-coordinator_deepseek.md`

### Do Not

- Do not implement importer DB writes.
- Do not implement strategy/dataset/validation repository adapters.
- Do not copy archive files into project folders.
- Do not implement filesystem staging.
- Do not wire importer into UI, services, CLI, or real repositories beyond the audit log adapter.
- Do not implement zip extraction.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not run destructive migration rollback logic.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `repository/import_audit_repo.py`
- `repository/__init__.py`
- `tests/test_import_audit_repo.py`
- `docs/archive_import_write_coordinator_design_059X.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059w-impl_059x-design_audit-log-repository-adapter-and-write-coordinator_deepseek.md`

## Acceptance Criteria

1. `AuditLogRepositoryAdapter.insert_failure_log()` inserts only failed audit rows.
2. Adapter persists all DTO fields exactly, including `archive_source` and `manifest_hash`.
3. Adapter does not write strategy, dataset, validation, or filesystem state.
4. SQLite failures are surfaced through a clear audit/repository exception.
5. 059X coordinator design exists and recommends exactly one next two-task batch.
6. Changelog, task board, and completion report are updated.
7. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_import_audit_repo.py tests/test_import_audit_log_schema.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused audit repository/schema tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059W-Impl + 059X-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
