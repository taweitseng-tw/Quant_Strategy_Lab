Completed:
- Batch 060G-Impl + 060H-Design — Dataset Snapshot Hash Schema Migration and Post-Migration DatasetRepoAdapter Insert-Only Design.

Files changed:
- repository/db.py (SCHEMA_SQL + migration helper + initialize wiring)
- tests/test_dataset_snapshot_hash_migration.py (created, 5 tests)
- docs/dataset_repo_adapter_post_migration_insert_only_design_060H.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. New databases: SCHEMA_SQL includes snapshot_hash TEXT NOT NULL DEFAULT ''.
2. Existing databases: ensure_dataset_snapshot_hash_column() runs ALTER TABLE idempotently via PRAGMA table_info.
3. DatabaseManager.initialize() now calls ensure_dataset_snapshot_hash_column after schema creation.
4. DatasetRepository.insert() unchanged — compatible with new column (DEFAULT '' fills it).
5. 060H design: DatasetRepoAdapter with schema probing, dual dedup (hash or fallback), no-commit + auto-commit methods.

Tests run:
- test_dataset_snapshot_hash_migration.py: 5 passed.
- Full suite: 1191 passed, 0 warnings.

Assumptions:
- PRAGMA table_info returns (cid, name, type, notnull, dflt_value, pk) — column name at index 1.
- ALTER TABLE ADD COLUMN with NOT NULL DEFAULT '' is safe for existing databases.

Known risks:
- No index on snapshot_hash (per 060F design). Acceptable for low-volume import scans.
- Existing DatasetRepository.insert() does not populate snapshot_hash — relies on DEFAULT ''.

Reviewer focus:
- ensure_dataset_snapshot_hash_column() — PRAGMA probe + ALTER TABLE, idempotent.
- 060H design: _dedup_where() dual-mode logic (hash vs fallback).
- 060H design: insert_dataset_no_commit() method for coordinator alignment.
