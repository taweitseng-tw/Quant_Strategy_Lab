# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059Q-Impl + 059R-Design - ArchiveImporter Read-Only Import Plan Builder and Import Transaction Sequence Design.

## Context Level

Level 2 for 059Q implementation, Level 3 for 059R design.

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
12. `docs/review_notes/2026-06-07_task-059o-design_059p-design_archive-importer-repository-contract-and-audit-schema_codex-review.md`
13. This task file

## Context

059M added a side-effect-free `ArchiveImporter` verification skeleton. 059N defined conflict policies with "Reject Duplicate" as the MVP default. 059O and 059P designed future repository contracts, audit schema, collision boundaries, and transaction sequence.

Codex accepted those designs only on the condition that the next implementation remains read-only. Do not implement database writes, file copy, real repository adapters, UI, CLI, or zip handling.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059Q-Impl - ArchiveImporter read-only import plan builder
  - Task 059R-Design - Import transaction sequence design hardening
- For Task 059Q:
  - Extend `archive/importer.py` with a read-only preview / plan-building method, such as `build_preview()` or `build_import_preview()`.
  - The method may:
    - call existing verification logic,
    - read `strategy.json`,
    - read `dataset_meta.json`,
    - read `validation_result.json`,
    - extract immutable DTO/summary objects,
    - optionally use a fake/read-only collision source protocol in tests only to report strategy/dataset collision status.
  - It must return an immutable preview/result object suitable for a future dry-run summary.
  - Add focused tests using exported fake archive folders only.
  - Tests should cover:
    - valid archive preview,
    - missing/corrupt archive payload file after manifest verification fails,
    - strategy collision reported read-only,
    - dataset collision reported read-only,
    - no filesystem mutation and no database writes.
- For Task 059R:
  - Create `docs/archive_import_transaction_sequence_design_059R.md`.
  - Define the future write sequence in precise phases:
    - verification,
    - read-only collision preview,
    - user approval boundary,
    - DB transaction begin,
    - file copy staging,
    - DB writes,
    - commit,
    - rollback,
    - file cleanup,
    - independent failed audit logging.
  - Clearly mark what is implemented now versus future implementation.
  - Recommend exactly one next two-task batch.
- Update:
  - `archive/__init__.py` if new public preview types are added.
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059q-impl_059r-design_archive-importer-read-only-plan-and-transaction-sequence_deepseek.md`

### Do Not

- Do not implement SQLite insertion.
- Do not add or modify migrations.
- Do not copy archive files into project folders.
- Do not implement real repository adapters.
- Do not wire importer into UI, services, CLI, or real repositories.
- Do not implement zip extraction.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not use runtime `assert` for validation.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/importer.py`
- `archive/__init__.py`
- `tests/test_archive_importer.py`
- `docs/archive_import_transaction_sequence_design_059R.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059q-impl_059r-design_archive-importer-read-only-plan-and-transaction-sequence_deepseek.md`

## Acceptance Criteria

1. Import preview / plan builder is read-only.
2. Preview result is immutable and contains enough strategy/dataset/validation summary data for a future dry run.
3. Collision checks, if implemented, use fake/read-only test doubles only and do not touch SQLite directly.
4. No DB writes, file copies, real repository adapters, UI/service/CLI wiring, zip extraction, schema/migration, dependency, or engine changes are made.
5. Transaction sequence design exists and recommends exactly one next two-task batch.
6. Changelog, task board, and completion report are updated.
7. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_archive_importer.py tests/test_archive_exporter.py tests/test_archive_verifier.py tests/test_archive_manifest_json.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused archive importer/exporter/verifier/manifest tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059Q-Impl + 059R-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
