# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059K-Impl + 059L-Design - ArchiveExporter Folder Writer First Pass and Importer Boundary Design.

## Context Level

Level 2 for 059K implementation, Level 3 for 059L design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/folder_manifest_integration_design_059J.md`
9. `docs/review_notes/2026-06-07_task-059i-impl_059j-design_archive-builder-first-pass-and-folder-manifest-integration_codex-review.md`
10. This task file

## Context

059I added a first-pass `ArchiveBuilder` that validates required materials and produces a side-effect-free `ArchiveManifest`. 059J designed the future folder archive layout and separated Builder, Exporter, Verifier, and Importer responsibilities.

This batch may introduce folder writes through a narrow `ArchiveExporter` first pass. It must not implement zip output, UI/service wiring, real repository adapters, or importer behavior.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059K-Impl - ArchiveExporter folder writer first pass
  - Task 059L-Design - ArchiveImporter boundary design
- For Task 059K:
  - Add `archive/exporter.py`.
  - Implement a minimal `ArchiveExporter` that accepts an `ArchiveBuilder` and a fake/in-memory data source style object.
  - Exporter may write to an output folder only.
  - It may:
    - call `ArchiveBuilder.build(...)`,
    - create the output folder,
    - write `disclaimer.txt`,
    - write `strategy.json`,
    - write `dataset_meta.json`,
    - write `validation_result.json`,
    - copy the provided CSV dataset snapshot to `ohlcv_snapshot.csv`,
    - compute SHA-256 hashes from the exact written/copied bytes,
    - write final `manifest.json`.
  - Add focused tests using fake data only for:
    - successful folder export,
    - manifest includes all written files,
    - hashes match written bytes,
    - verifier accepts exported folder,
    - output folder pre-exists.
- For Task 059L:
  - Create `docs/archive_importer_boundary_design_059L.md`.
  - Define future Importer responsibilities, non-goals, verification sequence, and failure modes.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059k-impl_059l-design_archive-exporter-folder-writer-and-importer-boundary_deepseek.md`

### Do Not

- Do not implement zip export.
- Do not implement ArchiveImporter.
- Do not wire archive export into UI, services, CLI, or real repositories.
- Do not change repository schema or migrations.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/exporter.py`
- `archive/__init__.py`
- `tests/test_archive_exporter.py`
- `docs/archive_importer_boundary_design_059L.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059k-impl_059l-design_archive-exporter-folder-writer-and-importer-boundary_deepseek.md`

## Acceptance Criteria

1. `ArchiveExporter` writes a folder archive only.
2. Exported folder contains `manifest.json`, `disclaimer.txt`, `strategy.json`, `dataset_meta.json`, `validation_result.json`, and `ohlcv_snapshot.csv`.
3. Manifest `files` and `content_hashes` match the written/copied files.
4. `ArchiveVerifier` accepts the exported folder in tests.
5. No zip, importer, UI/service wiring, real repository adapter, schema, dependency, or engine changes are made.
6. Importer boundary design exists and recommends exactly one next two-task batch.
7. Changelog, task board, and completion report are updated.
8. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_archive_exporter.py tests/test_archive_builder.py tests/test_archive_manifest_json.py tests/test_dataset_snapshot.py tests/test_archive_verifier.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused archive exporter/builder/manifest/snapshot/verifier tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059K-Impl + 059L-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
