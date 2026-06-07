# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059O-Design + 059P-Design - ArchiveImporter Repository Contract and Import Audit Schema Design.

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
10. `docs/review_notes/2026-06-07_task-059m-impl_059n-design_archive-importer-verification-and-conflict-policy_codex-review.md`
11. This task file

## Context

059M added a side-effect-free `ArchiveImporter` verification skeleton that reads a folder manifest, checks archive schema major version compatibility, delegates integrity checks to `ArchiveVerifier`, and returns an immutable `ArchiveImportPlan`.

059N defined import conflict policies and selected "Reject Duplicate" as the MVP default. Codex explicitly rejected jumping straight into SQLite import implementation before repository contracts, audit schema, and collision boundaries are designed.

This batch is design-only. It must not implement database writes.

## Scope

### Do

- Complete two sequential design tasks:
  - Task 059O-Design - ArchiveImporter repository contract design
  - Task 059P-Design - Import audit schema and collision detection boundary design
- For Task 059O:
  - Create `docs/archive_import_repository_contract_design_059O.md`.
  - Define repository/service adapter interfaces needed by a future importer.
  - Cover strategy import, dataset metadata import, dataset snapshot placement, validation result import, duplicate detection, transaction boundary expectations, and rollback expectations.
  - Define the data objects the importer should pass into repository adapters.
  - Define exception taxonomy for repository/import failures.
  - Explicitly state that the current importer remains verification-only.
- For Task 059P:
  - Create `docs/archive_import_audit_schema_design_059P.md`.
  - Design the import audit log schema and provenance fields.
  - Define collision detection queries/keys at a design level.
  - Define MVP default behavior for duplicates: reject without mutation.
  - Define how failed imports should be audited in future implementation.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059o-design_059p-design_archive-importer-repository-contract-and-audit-schema_deepseek.md`

### Do Not

- Do not modify production Python code.
- Do not implement SQLite insertion.
- Do not add or modify migrations.
- Do not copy archive files into project folders.
- Do not implement repository adapters.
- Do not wire importer into UI, services, CLI, or real repositories.
- Do not implement zip extraction.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `docs/archive_import_repository_contract_design_059O.md`
- `docs/archive_import_audit_schema_design_059P.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059o-design_059p-design_archive-importer-repository-contract-and-audit-schema_deepseek.md`

## Acceptance Criteria

1. 059O repository contract design exists and is specific enough to guide implementation.
2. 059P audit schema and collision detection design exists and keeps "Reject Duplicate" as MVP default.
3. The recommended next batch is exactly one two-task batch and does not skip directly into broad UI or zip work.
4. No production Python code, database schema, migrations, UI, service wiring, zip extraction, dependencies, or engine behavior are changed.
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
- Agent status shows Batch 059O-Design + 059P-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
