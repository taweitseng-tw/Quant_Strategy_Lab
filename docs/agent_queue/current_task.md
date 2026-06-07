# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 059E-Impl + 059F-Design - Deterministic CSV Dataset Snapshot Writer and Archive Builder Input Contract.

## Context Level

Level 2 for 059E implementation, Level 3 for 059F design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/dataset_snapshot_format_decision_059D.md`
9. `docs/review_notes/2026-06-07_task-059c-impl_059d-design_archive-manifest-verifier-and-dataset-snapshot-decision_codex-review.md`
10. This task file

## Context

059C created the archive manifest/verifier skeleton. Codex accepted it after adding required-hash enforcement and archive-root path escape rejection. 059D chose deterministic CSV as the first dataset snapshot format, with no new dependency.

The next implementation must stay standalone. Do not wire the snapshot writer into repository, ArchiveBuilder, UI, or full archive export yet.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059E-Impl - Deterministic CSV dataset snapshot writer
  - Task 059F-Design - Archive builder input-contract design
- For Task 059E:
  - Add `archive/dataset_snapshot.py`.
  - Implement a small `DatasetSnapshotResult` dataclass.
  - Implement a deterministic CSV snapshot writer for a provided pandas `DataFrame` and output path.
  - The writer must:
    - write CSV with stable column order from the input DataFrame,
    - use `index=False`,
    - use deterministic float formatting,
    - normalize line endings to `\n`,
    - compute SHA-256 from the exact bytes written,
    - return row count, column names, output filename, and hash.
  - Add focused tests covering stable hash for same data, hash change when data changes, row/column metadata, and `\n` line endings.
- For Task 059F:
  - Create `docs/archive_builder_input_contract_059F.md`.
  - Define the future `ArchiveBuilder` inputs and boundaries without implementation.
  - Specify which data comes from repository, which data comes from file paths, and which data remains caller-provided.
  - Identify failure modes and required errors for missing strategy, missing dataset snapshot, missing validation result, and missing disclaimer.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059e-impl_059f-design_csv-dataset-snapshot-and-archive-builder-contract_deepseek.md`

### Do Not

- Do not implement ArchiveBuilder, ArchiveExporter, or ArchiveImporter.
- Do not wire dataset snapshot writing into repository, UI, or services.
- Do not change repository schema or migrations.
- Do not add `pyarrow` or any other dependency.
- Do not change existing engine behavior.
- Do not write zip export logic.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/dataset_snapshot.py`
- `archive/__init__.py`
- `tests/test_dataset_snapshot.py`
- `docs/archive_builder_input_contract_059F.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059e-impl_059f-design_csv-dataset-snapshot-and-archive-builder-contract_deepseek.md`

## Acceptance Criteria

1. CSV snapshot writer exists and is standalone.
2. Snapshot writer returns deterministic metadata and SHA-256 hash from written bytes.
3. Tests cover stable hash, changed-data hash change, metadata, and LF line endings.
4. No ArchiveBuilder/Exporter/Importer is implemented.
5. No repository, UI, schema, dependency, or engine changes are made.
6. Archive builder input-contract design exists and recommends exactly one next two-task batch.
7. Changelog, task board, and completion report are updated.
8. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_dataset_snapshot.py tests/test_archive_verifier.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused archive dataset snapshot and verifier tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059E-Impl + 059F-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
