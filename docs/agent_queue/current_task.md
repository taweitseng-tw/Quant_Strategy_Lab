# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059S-Design + 059T-Design - ImportAuditLog Migration Plan and Repository Adapter Test Contract Design.

## Context Level

Level 3 design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/archive_importer_boundary_design_059L.md`
9. `docs/archive_import_conflict_policy_design_059N.md`
10. `docs/archive_import_repository_contract_design_059O.md`
11. `docs/archive_import_audit_schema_design_059P.md`
12. `docs/archive_import_transaction_sequence_design_059R.md`
13. `docs/review_notes/2026-06-07_task-059q-impl_059r-design_archive-importer-read-only-plan-and-transaction-sequence_codex-review.md`
14. This task file

## Context

059Q added a read-only `ArchiveImporter.build_preview()` that verifies archives, reads JSON payloads, extracts immutable preview data, and reports collision status using a read-only detector keyed by `strategy_uid`.

059R designed the future write transaction sequence. Codex accepted it only on the condition that the next batch remains design-only and does not implement migrations, DB writes, file copies, repository adapters, UI, CLI, service wiring, or zip behavior.

## Scope

### Do

- Complete two sequential design tasks:
  - Task 059S-Design - ImportAuditLog migration plan
  - Task 059T-Design - Repository adapter test contract design
- For Task 059S:
  - Create `docs/archive_import_audit_migration_plan_059S.md`.
  - Define the future migration plan for `ImportAuditLog`.
  - Include proposed table columns, indexes, constraints, enum/check constraints, rollback plan, compatibility notes, and migration verification criteria.
  - Explicitly state that this task does not execute or implement a migration.
- For Task 059T:
  - Create `docs/archive_import_repository_adapter_test_contract_059T.md`.
  - Define test contracts for future repository/filesystem adapters.
  - Include mock/spy behavior expectations, duplicate rejection tests, rollback acceptance criteria, failed audit logging acceptance criteria, read/write boundary tests, and edge-case error scenarios.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059s-design_059t-design_import-audit-migration-and-adapter-test-contract_deepseek.md`

### Do Not

- Do not modify production Python code.
- Do not implement or run migrations.
- Do not implement SQLite insertion.
- Do not copy archive files into project folders.
- Do not implement real repository adapters.
- Do not wire importer into UI, services, CLI, or real repositories.
- Do not implement zip extraction.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/archive_import_audit_migration_plan_059S.md`
- `docs/archive_import_repository_adapter_test_contract_059T.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059s-design_059t-design_import-audit-migration-and-adapter-test-contract_deepseek.md`

## Acceptance Criteria

1. 059S migration plan exists and is specific enough to guide future implementation.
2. 059T adapter test contract exists and includes rollback, duplicate, failed audit, and read/write boundary acceptance criteria.
3. The recommended next batch is exactly one two-task batch and does not skip into broad UI/CLI/service wiring or zip work.
4. No production Python code, migrations, schema files, DB writes, file copies, repository adapter implementation, UI/service/CLI wiring, zip extraction, dependencies, or engine behavior are changed.
5. Changelog, task board, and completion report are updated.
6. Full suite, `git diff --check`, and agent status pass.

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
- `git diff --check` passes.
- Agent status shows Batch 059S-Design + 059T-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
