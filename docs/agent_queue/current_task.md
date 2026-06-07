# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 059M-Impl + 059N-Design - ArchiveImporter Verification Skeleton and Archive Import Conflict Policy Design.

## Context Level

Level 2 for 059M implementation, Level 3 for 059N design.

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
9. `docs/review_notes/2026-06-07_task-059k-impl_059l-design_archive-exporter-folder-writer-and-importer-boundary_codex-review.md`
10. This task file

## Context

059K added a folder-only `ArchiveExporter` first pass that writes a reproducible experiment archive folder and produces hashes verified by `ArchiveVerifier`. 059L designed the future `ArchiveImporter` boundary.

This batch should introduce only the importer verification boundary, not actual importing into application state. Keep the implementation side-effect-free except reading the archive folder.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059M-Impl - ArchiveImporter verification skeleton
  - Task 059N-Design - Archive import conflict policy design
- For Task 059M:
  - Add `archive/importer.py`.
  - Implement a minimal `ArchiveImporter` that accepts an archive folder path.
  - Read `manifest.json` using `ArchiveManifest.read_from_folder(...)`.
  - Check archive schema compatibility by major version only.
    - Current supported major version: `1`.
    - Missing, malformed, non-numeric, or newer major versions must raise a clear importer exception.
  - Delegate content verification to `ArchiveVerifier.verify_all()`.
  - Return a small immutable import plan / verification summary object such as `ArchiveImportPlan`.
  - The plan may include archive root, archive version, experiment name, files, and a boolean verification flag.
  - Add focused tests using exported fake archive folders only.
- For Task 059N:
  - Create `docs/archive_import_conflict_policy_design_059N.md`.
  - Define conflict policy options for future imports:
    - reject duplicate,
    - overwrite with explicit opt-in,
    - keep existing and skip,
    - duplicate with suffix / new UID.
  - Define which policy should be the MVP default.
  - Define required user-facing warnings and audit/provenance records.
  - Recommend exactly one next two-task batch.
- Update:
  - `archive/__init__.py`
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059m-impl_059n-design_archive-importer-verification-and-conflict-policy_deepseek.md`

### Do Not

- Do not import anything into SQLite or repositories.
- Do not copy files into project data folders.
- Do not implement zip extraction.
- Do not wire importer into UI, services, CLI, or real repositories.
- Do not change repository schema or migrations.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not weaken `ArchiveVerifier` checks.
- Do not use runtime `assert` for validation.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/importer.py`
- `archive/__init__.py`
- `tests/test_archive_importer.py`
- `docs/archive_import_conflict_policy_design_059N.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059m-impl_059n-design_archive-importer-verification-and-conflict-policy_deepseek.md`

## Acceptance Criteria

1. `ArchiveImporter` is a verification skeleton only.
2. Valid exported folder archives produce an import plan / verification summary.
3. Missing manifest, malformed archive version, newer major archive version, and verifier integrity failure are tested.
4. No DB writes, file import/copy, zip extraction, UI/service/CLI wiring, schema, dependency, or engine changes are made.
5. Conflict policy design exists and recommends exactly one next two-task batch.
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
- Agent status shows Batch 059M-Impl + 059N-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
