# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 060I-Impl + 060J-Design - DatasetRepoAdapter Implementation and ArchiveStager Implementation Design.

## Context Level

Level 3 for 060I implementation, Level 3 for 060J design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `repository/db.py`
9. `repository/dataset_repo.py`
10. `docs/dataset_repo_adapter_post_migration_insert_only_design_060H.md`
11. `docs/archive_import_filesystem_staging_design_059Z.md`
12. `docs/archive_import_coordinator_architecture_060A.md`
13. `docs/review_notes/2026-06-07_task-060g-impl_060h-design_dataset-hash-migration-and-adapter-design_codex-review.md`
14. This task file

## Context

060G added the additive `datasets.snapshot_hash` migration. 060H accepted a design for a repository-layer `DatasetRepoAdapter` that supports post-migration hash dedup and old-DB fallback. This batch may implement only the dataset repository adapter and design only the ArchiveStager. Do not implement coordinator or filesystem staging behavior.

## Scope

### Do

- Complete two sequential tasks:
  - Task 060I-Impl - implement `DatasetRepoAdapter`.
  - Task 060J-Design - design `ArchiveStager` implementation.
- For Task 060I:
  - Create a repository-layer adapter, suggested path `repository/dataset_import_adapter.py`.
  - Add immutable `ImportDatasetDTO` with fields from the 060H design, including `snapshot_hash`.
  - Add exceptions:
    - `DatasetRepoAdapterError`
    - `DuplicateDatasetError`
  - On init, probe `PRAGMA table_info(datasets)` and set whether `snapshot_hash` exists.
  - Implement insert-only behavior:
    - no overwrite;
    - no update;
    - no upsert;
    - duplicate raises `DuplicateDatasetError`.
  - Implement duplicate-reject behavior:
    - if `snapshot_hash` column exists and DTO hash is non-empty, dedup by `snapshot_hash`;
    - otherwise fallback to `(symbol, timeframe, source_path)` when `source_path` is non-empty;
    - otherwise fallback to `(symbol, timeframe)`.
  - Implement dual INSERT SQL:
    - post-migration insert includes `snapshot_hash`;
    - old-DB insert omits `snapshot_hash`.
  - Implement transaction methods aligned with `StrategyRepoAdapter`:
    - `_insert_dataset_core(dto)` validates, dedups, and executes INSERT with no commit/rollback;
    - `insert_dataset(dto)` auto-commits on success;
    - `insert_dataset(dto)` rolls back only on SQLite write failure or commit failure;
    - validation errors and `DuplicateDatasetError` must not rollback caller-owned uncommitted data;
    - `insert_dataset_no_commit(dto)` performs no commit/rollback.
  - Add focused tests for:
    - insert succeeds on post-migration schema;
    - duplicate by non-empty `snapshot_hash` rejected;
    - empty hash falls back to fallback key on post-migration schema;
    - old-DB schema insert omits `snapshot_hash` and succeeds;
    - duplicate by fallback key rejected on old-DB schema;
    - no-commit caller commit;
    - no-commit caller rollback;
    - SQLite INSERT failure triggers rollback;
    - validation error does not rollback caller uncommitted data;
    - duplicate error does not rollback caller uncommitted data;
    - no other tables modified.
- For Task 060J:
  - Create `docs/archive_stager_implementation_design_060J.md`.
  - Design only. Do not implement ArchiveStager.
  - Base it on `docs/archive_import_filesystem_staging_design_059Z.md`.
  - Specify source validation, deterministic temp directory, hash verification, cleanup, final move, and orphan-file handling.
  - Explicitly separate staging from SQLite transactions:
    - staging copies/verifies before durable DB write;
    - final move happens only after DB commit;
    - cleanup responsibilities for temp and final destination are documented.
  - Include focused future tests for success, hash mismatch, missing file, temp cleanup, final move failure, and DB-failure cleanup handoff.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060i-impl_060j-design_dataset-adapter-and-archive-stager-design_gemini.md`

### Do Not

- Do not implement ArchiveStager.
- Do not implement archive import coordinator.
- Do not move, copy, or delete real project data files.
- Do not add success audit writes.
- Do not touch UI, CLI, backtest engine, validation engine, strategy generator, or report exporters.
- Do not add dependencies.
- Do not create an index on `snapshot_hash`.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. `DatasetRepoAdapter` is repository-layer only and imports no UI/engine modules.
2. Post-migration schema uses `snapshot_hash` as the primary non-empty duplicate key.
3. Old-DB fallback never queries or inserts into a missing `snapshot_hash` column.
4. Transaction behavior is proven by tests, including rollback scope and no-commit behavior.
5. 060J is design-only and creates no production stager code.
6. Full suite, `git diff --check`, and agent status pass.

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
- Agent status shows the 060I/060J completion report as latest report.
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
