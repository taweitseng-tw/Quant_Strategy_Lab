# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059I-Impl + 059J-Design - ArchiveBuilder First-Pass Collector and Folder Manifest Integration Design.

## Context Level

Level 2 for 059I implementation, Level 3 for 059J design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/archive_builder_input_contract_059F.md`
9. `docs/archive_builder_repository_adapter_059H.md`
10. `docs/review_notes/2026-06-07_task-059g-impl_059h-design_manifest-json-serialization-and-builder-adapter-contract_codex-review.md`
11. This task file

## Context

059G added manifest JSON serialization and folder read/write helpers. 059H defined the repository adapter contract with hard failures for required archive materials.

This batch must remain a first-pass collector only. Do not implement full archive export, zip output, importer behavior, UI/service wiring, or real repository adapters.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059I-Impl - ArchiveBuilder first-pass collector
  - Task 059J-Design - Folder manifest integration design
- For Task 059I:
  - Add `archive/builder.py`.
  - Define small exception classes for missing required materials:
    - `MissingStrategyError`
    - `MissingDatasetError`
    - `MissingDatasetSnapshotError`
    - `MissingValidationResultError`
    - `MissingDisclaimerError`
  - Implement a minimal `ArchiveBuilder` that accepts an `ArchiveDataSource`-like object and caller-provided paths/text.
  - The builder may collect strategy/dataset/validation metadata and produce an `ArchiveManifest`.
  - It must hard-fail on missing strategy, dataset metadata, dataset snapshot path, validation result, or disclaimer.
  - It must not write archive folders, zip files, or copied artifacts.
  - Add focused tests using a fake data source for success and each hard-failure case.
- For Task 059J:
  - Create `docs/folder_manifest_integration_design_059J.md`.
  - Design how future folder archive writing should combine manifest JSON, dataset snapshot, strategy JSON, validation JSON, and disclaimer.
  - Define exact responsibilities for future Builder vs Exporter vs Verifier.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059i-impl_059j-design_archive-builder-first-pass-and-folder-manifest-integration_deepseek.md`

### Do Not

- Do not implement ArchiveExporter or ArchiveImporter.
- Do not write zip export logic.
- Do not wire archive export into UI, services, CLI, or real repositories.
- Do not change repository schema or migrations.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/builder.py`
- `archive/__init__.py`
- `tests/test_archive_builder.py`
- `docs/folder_manifest_integration_design_059J.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059i-impl_059j-design_archive-builder-first-pass-and-folder-manifest-integration_deepseek.md`

## Acceptance Criteria

1. `ArchiveBuilder` exists but only performs first-pass collection and manifest creation.
2. Builder hard-fails on missing required materials.
3. Tests cover success plus each missing required material.
4. No exporter/importer/zip/UI/service/real repository wiring is implemented.
5. No schema, dependency, or engine changes are made.
6. Folder manifest integration design exists and recommends exactly one next two-task batch.
7. Changelog, task board, and completion report are updated.
8. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_archive_builder.py tests/test_archive_manifest_json.py tests/test_dataset_snapshot.py tests/test_archive_verifier.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused archive builder/manifest/snapshot/verifier tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059I-Impl + 059J-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
