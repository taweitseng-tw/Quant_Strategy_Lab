Completed:
- Batch 060I-Impl + 060J-Design — DatasetRepoAdapter Implementation and ArchiveStager Implementation Design.

Files changed:
- repository/dataset_import_adapter.py (created)
- tests/test_dataset_import_adapter.py (created, 11 tests)
- docs/archive_stager_implementation_design_060J.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. DatasetRepoAdapter: schema probing at init (PRAGMA table_info), dual INSERT SQL (post-migration with snapshot_hash, old-DB without), duplicate-reject by snapshot_hash (or fallback key), insert_dataset() auto-commit with SQLite-error-only rollback guard, insert_dataset_no_commit() no commit/rollback.
2. 060J design: ArchiveStager with source validation, deterministic temp dir, stage + hash verify, final move after DB commit, cleanup zones, orphan handling.

Tests run:
- test_dataset_import_adapter.py: 11 passed.
- Full suite: 1203 passed, 0 warnings.

Assumptions:
- Empty snapshot_hash on post-migration schema falls back to old-DB dedup by design.
- Old-DB adapter fixture creates a minimal datasets table without snapshot_hash to simulate legacy databases.

Known risks:
- Old-DB fallback dedup by (symbol, timeframe, source_path) cannot detect content-identical datasets from different archive paths.

Reviewer focus:
- _dedup_where() dual-mode (hash vs fallback).
- _insert_dataset_core() try/except sqlite3.Error wrapping both INSERT branches.
- insert_dataset() rollback guard using isinstance(exc.__cause__, sqlite3.Error).
