# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 060K-Impl + 060L-Design - ArchiveStager Implementation and ArchiveImportCoordinator First-Pass Wiring Design.

## Context Level

Level 3 for 060K implementation, Level 3 for 060L design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `archive/importer.py`
9. `archive/verifier.py`
10. `archive/manifest.py`
11. `archive/__init__.py`
12. `docs/archive_stager_implementation_design_060J.md`
13. `docs/archive_import_filesystem_staging_design_059Z.md`
14. `docs/archive_import_coordinator_architecture_060A.md`
15. `docs/review_notes/2026-06-07_task-060i-impl_060j-design_dataset-adapter-and-archive-stager-design_codex-review.md`
16. This task file

## Context

060J accepted a project-local ArchiveStager design. The implementation must copy `ohlcv_snapshot.csv` from a verified archive folder into `<project_root>/.staging/<experiment_name>_<run_id>/`, verify SHA-256, and move to `<project_root>/data/imported/<experiment_name>/ohlcv.csv` only after DB commit. This batch may implement ArchiveStager only and design the coordinator wiring only.

## Scope

### Do

- Complete two sequential tasks:
  - Task 060K-Impl - implement `ArchiveStager`.
  - Task 060L-Design - design `ArchiveImportCoordinator` first-pass wiring.
- For Task 060K:
  - Create `archive/stager.py`.
  - Export the stager from `archive/__init__.py` only if that package already exports peer archive classes in the local style.
  - Implement:
    - `ArchiveStager`
    - `HashMismatchError`
    - any small stager-specific base exception if useful.
  - Constructor must accept:
    - `archive_root`
    - `project_root`
    - `experiment_name`
    - `run_id`
  - Use project-local staging:
    - `<project_root>/.staging/<experiment_name>_<run_id>/`
  - Use final destination:
    - `<project_root>/data/imported/<experiment_name>/ohlcv.csv`
  - Implement source validation:
    - archive root is a directory;
    - `manifest.json` exists;
    - `ohlcv_snapshot.csv` exists;
    - reject path traversal / symlink outside archive root.
  - Implement `stage_dataset_snapshot(expected_hash)`:
    - copy `ohlcv_snapshot.csv` to staging;
    - verify SHA-256 of staged file;
    - on hash mismatch, delete staged file and raise `HashMismatchError`;
    - return staged path on success.
  - Implement `move_to_final_destination()`:
    - require a staged file;
    - move staged file to final destination;
    - clear tracked staged path only after successful move;
    - if move fails, preserve staged file and tracked staged path for repair.
  - Implement `cleanup_temp()`:
    - remove the staging directory and its contents.
  - Add focused tests in `tests/test_archive_stager.py` for:
    - missing `ohlcv_snapshot.csv` raises;
    - hash mismatch raises and staged file is deleted;
    - hash match returns a path under project-local `.staging`;
    - final move writes to `data/imported/<experiment_name>/ohlcv.csv`;
    - cleanup removes staging dir;
    - DB-failure cleanup scenario cleans temp only and creates no final files;
    - final move failure preserves staged file and tracked path;
    - path traversal or symlink outside archive is rejected.
- For Task 060L:
  - Create `docs/archive_import_coordinator_first_pass_wiring_design_060L.md`.
  - Design only. Do not implement coordinator.
  - Describe first-pass wiring across:
    - archive preview / verifier;
    - `ArchiveStager`;
    - `StrategyRepoAdapter.insert_strategy_no_commit`;
    - `DatasetRepoAdapter.insert_dataset_no_commit`;
    - one shared SQLite transaction;
    - final file move after DB commit;
    - failure audit remains isolated.
  - Specify ordering:
    - verify archive;
    - preflight duplicates;
    - stage and verify file;
    - begin/write DB rows with no-commit adapters;
    - commit;
    - final move;
    - cleanup;
    - audit failure path.
  - Include focused future tests using fakes/spies for success, duplicate, staging failure, DB failure, commit failure, final move failure, and audit failure.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060k-impl_060l-design_archive-stager-and-coordinator-wiring-design_deepseek.md`

### Do Not

- Do not implement `ArchiveImportCoordinator`.
- Do not alter repository adapters unless tests prove a bug directly blocks `ArchiveStager`.
- Do not write success audit rows.
- Do not touch UI, CLI, backtest engine, validation engine, strategy generator, or report exporters.
- Do not add dependencies.
- Do not move, copy, or delete files outside pytest temporary directories during tests.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. `ArchiveStager` is implemented under the archive layer and imports no UI/engine modules.
2. Staging is project-local under `.staging`.
3. Hash mismatch deletes the staged file and raises a stager error.
4. Final move happens only through explicit `move_to_final_destination()`.
5. Final move failure preserves staged file for repair.
6. `cleanup_temp()` removes the staging directory.
7. 060L is design-only and creates no coordinator production code.
8. Full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Full suite passes.
- `git diff --check` has no errors.
- Agent status shows the 060K/060L completion report as latest report.
- `git status --short` shows only files within this task scope.

## Completion Report Format

Use:

```text
Completed:
Files changed:
Behavior changed:
Tests run:
Assumptions:
Known risks:
Reviewer focus:
```

Then stop.
