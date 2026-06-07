# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 059C-Impl + 059D-Design - Archive Manifest Verifier Skeleton and Dataset Snapshot Format Decision.

## Context Level

Level 2 for 059C implementation, Level 3 for 059D design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/archive_architecture_059A.md`
9. `docs/provenance_integrity_design_059B.md`
10. `docs/review_notes/2026-06-07_task-059a-design_059b-design_reproducible-experiment-archive-and-provenance-integrity_codex-review.md`
11. This task file

## Context

059A/059B designed the reproducible experiment archive direction. Codex accepted the design after correcting the wording from signed manifests to hash-verified manifests. The next implementation must stay deliberately small and must not implement full archive export/import or dataset snapshot writing yet.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059C-Impl - Archive manifest and verifier skeleton
  - Task 059D-Design - Dataset snapshot format and dependency decision
- For Task 059C:
  - Create a new `archive/` package with minimal `__init__.py`.
  - Add an `ArchiveManifest` dataclass with fields needed for manifest metadata, files, content hashes, and disclaimer path.
  - Add an `ArchiveIntegrityError` exception.
  - Add an `ArchiveVerifier` that can:
    - verify listed files exist,
    - verify SHA-256 hashes for listed files,
    - verify `disclaimer.txt` exists and is non-empty.
  - Add focused unit tests for success, missing file, hash mismatch, and missing/empty disclaimer.
- For Task 059D:
  - Create `docs/dataset_snapshot_format_decision_059D.md`.
  - Compare CSV, JSON-lines, Parquet, and "defer snapshot writer" options.
  - Explicitly discuss dependency impact. Do not add `pyarrow` or any dependency.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059c-impl_059d-design_archive-manifest-verifier-and-dataset-snapshot-decision_deepseek.md`

### Do Not

- Do not implement ArchiveBuilder, ArchiveExporter, or ArchiveImporter.
- Do not write dataset snapshot export/import.
- Do not add `pyarrow` or any other dependency.
- Do not change repository schema or migrations.
- Do not change UI code.
- Do not change existing engine behavior.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/__init__.py`
- `archive/manifest.py`
- `archive/verifier.py`
- `tests/test_archive_verifier.py`
- `docs/dataset_snapshot_format_decision_059D.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059c-impl_059d-design_archive-manifest-verifier-and-dataset-snapshot-decision_deepseek.md`

## Acceptance Criteria

1. `ArchiveManifest`, `ArchiveIntegrityError`, and `ArchiveVerifier` exist with type hints.
2. Verifier tests cover success, missing file, hash mismatch, and missing/empty disclaimer.
3. No full archive builder/exporter/importer is implemented.
4. No dataset snapshot writer is implemented.
5. No dependency, schema, UI, or engine behavior changes are made.
6. Dataset snapshot decision doc exists and recommends exactly one next two-task batch.
7. Changelog, task board, and completion report are updated.
8. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_archive_verifier.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused archive verifier tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059C-Impl + 059D-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
