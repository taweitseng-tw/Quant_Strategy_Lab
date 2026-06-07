# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Flash or Gemini 3.5 Flash

## Current Task

Batch 060G-Impl + 060H-Design - Dataset Snapshot Hash Schema Migration Implementation and Post-Migration DatasetRepoAdapter Insert-Only Design with Old-DB Fallback.

## Context Level

Level 3 for 060G implementation, Level 3 for 060H design.

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
10. `docs/dataset_snapshot_hash_schema_migration_design_060F.md`
11. `docs/dataset_import_adapter_insert_only_design_060D.md`
12. `docs/review_notes/2026-06-07_task-060e-impl_060f-design_strategy-transaction-refactor-and-dataset-hash-migration_codex-review.md`
13. This task file

## Context

060F accepted the additive `datasets.snapshot_hash` migration design. The next safe step is to implement only the schema migration in `repository/db.py` and tests. DatasetRepoAdapter remains design-only in this batch: describe the post-migration insert-only adapter contract, including old-DB fallback, but do not implement it yet.

## Scope

### Do

- Complete two sequential tasks:
  - Task 060G-Impl - implement dataset `snapshot_hash` schema migration.
  - Task 060H-Design - design post-migration DatasetRepoAdapter insert-only behavior with old-DB fallback.
- For Task 060G:
  - Update `repository/db.py` only as needed.
  - Add `snapshot_hash TEXT NOT NULL DEFAULT ''` to the `datasets` table definition in `SCHEMA_SQL` for new databases.
  - Add an idempotent helper such as `ensure_dataset_snapshot_hash_column(connection)`.
  - Ensure `DatabaseManager.initialize()` applies the migration after creating base schema.
  - The helper must use `PRAGMA table_info(datasets)` before `ALTER TABLE`.
  - The helper must not create an index in this task.
  - Preserve existing dataset inserts that omit `snapshot_hash`.
  - Add focused tests for:
    - new in-memory DB includes `snapshot_hash`;
    - old-style DB without the column is migrated;
    - migration helper is idempotent;
    - existing dataset rows survive migration with `snapshot_hash = ''`;
    - existing `DatasetRepository.insert()` still works when it does not pass `snapshot_hash`.
- For Task 060H:
  - Create `docs/dataset_repo_adapter_post_migration_insert_only_design_060H.md`.
  - Design only. Do not implement DatasetRepoAdapter.
  - Define `ImportDatasetDTO` fields, including `snapshot_hash`.
  - Define duplicate-reject behavior:
    - Primary post-migration key: non-empty `snapshot_hash`.
    - Old-DB fallback: `(symbol, timeframe, source_path)` only when the column is absent or hash is empty.
  - Define schema probing at adapter initialization.
  - Define insert-only semantics: no overwrite, no update, no upsert, no file moves, no audit writes.
  - Define no-commit coordinator-facing method and optional auto-commit wrapper, aligned with `StrategyRepoAdapter`.
  - Include focused future tests, including old-DB fallback and post-migration hash duplicate rejection.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-060g-impl_060h-design_dataset-hash-migration-and-dataset-adapter-design_gemini.md`

### Do Not

- Do not implement `DatasetRepoAdapter`.
- Do not implement archive import coordinator.
- Do not modify filesystem staging or file move behavior.
- Do not add success audit writes.
- Do not touch UI, CLI, backtest engine, validation engine, strategy generator, or report exporters.
- Do not add dependencies.
- Do not create an index on `snapshot_hash`.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Acceptance Criteria

1. New databases have `datasets.snapshot_hash TEXT NOT NULL DEFAULT ''`.
2. Existing databases without the column are migrated idempotently.
3. Existing dataset rows remain intact and receive default `snapshot_hash = ''`.
4. Existing `DatasetRepository.insert()` behavior remains backward-compatible.
5. 060H is design-only and does not create production adapter code.
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
- Agent status shows the 060G/060H completion report as latest report.
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
