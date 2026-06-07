# Dataset Snapshot Hash Schema Migration Design — Task 060F

> Design-only. No production code changed.

## 1. Purpose

Define the additive schema migration that adds a `snapshot_hash` column to the `datasets` table, enabling strict content-based duplicate-reject for imported datasets (060D Mode B).

## 2. Current Schema (`repository/db.py`)

```sql
CREATE TABLE IF NOT EXISTS datasets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER DEFAULT NULL,
    name            TEXT    NOT NULL,
    symbol          TEXT    NOT NULL DEFAULT '',
    timeframe       TEXT    NOT NULL DEFAULT '',
    source_type     TEXT    NOT NULL DEFAULT 'csv',
    source_path     TEXT    NOT NULL DEFAULT '',
    normalized_path TEXT    NOT NULL DEFAULT '',
    row_count       INTEGER NOT NULL DEFAULT 0,
    start_datetime  TEXT    NOT NULL DEFAULT '',
    end_datetime    TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL
);
```

## 3. Migration SQL

### For existing databases (ALTER TABLE)

```sql
ALTER TABLE datasets ADD COLUMN snapshot_hash TEXT NOT NULL DEFAULT '';
```

### For new databases (CREATE TABLE)

Add `snapshot_hash TEXT NOT NULL DEFAULT ''` after `end_datetime`:

```sql
CREATE TABLE IF NOT EXISTS datasets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER DEFAULT NULL,
    name            TEXT    NOT NULL,
    symbol          TEXT    NOT NULL DEFAULT '',
    timeframe       TEXT    NOT NULL DEFAULT '',
    source_type     TEXT    NOT NULL DEFAULT 'csv',
    source_path     TEXT    NOT NULL DEFAULT '',
    normalized_path TEXT    NOT NULL DEFAULT '',
    row_count       INTEGER NOT NULL DEFAULT 0,
    start_datetime  TEXT    NOT NULL DEFAULT '',
    end_datetime    TEXT    NOT NULL DEFAULT '',
    snapshot_hash   TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL
);
```

## 4. Idempotency Strategy

| Scenario | Approach |
|---|---|
| ALTER TABLE on already-migrated column | `ALTER TABLE datasets ADD COLUMN snapshot_hash ...` → SQLite ignores if column already exists? **No** — SQLite raises error. Must check column existence first. |
| Schema check | Query `PRAGMA table_info(datasets)` for `snapshot_hash` column. Only run ALTER TABLE if absent. |
| SCHEMA_SQL | Always uses the new CREATE TABLE — harmless for existing tables (IF NOT EXISTS). |

### Idempotent migration helper

```python
def ensure_dataset_snapshot_hash_column(connection: sqlite3.Connection) -> None:
    """Add snapshot_hash column idempotently."""
    cursor = connection.execute("PRAGMA table_info(datasets)")
    columns = {row["name"] for row in cursor.fetchall()}
    if "snapshot_hash" not in columns:
        connection.execute(
            "ALTER TABLE datasets ADD COLUMN snapshot_hash TEXT NOT NULL DEFAULT ''"
        )
        connection.commit()
```

## 5. Index Decision

| Decision | Rationale |
|---|---|
| **No index on `snapshot_hash` in first migration.** | The column will be used for duplicate-reject scans which are infrequent (archive import). An index can be added later if the scan becomes a bottleneck. |

## 6. Rollback / Compatibility

| Operation | Safe? |
|---|---|
| DROP COLUMN `snapshot_hash` | SQLite 3.35.0+ supports DROP COLUMN. If older version, recreate table. |
| Old code with new schema | SELECT/INSERT on `datasets` works — new column has DEFAULT ''. |
| New code with old schema (no column) | `INSERT` without `snapshot_hash` is fine. `SELECT` without referencing column is fine. Only Mode B code that queries `snapshot_hash` would fail — which is why it must probe schema at init time (060D design). |

## 7. How This Enables 060D Mode B

After migration:
1. `DatasetRepoAdapter` init probes `PRAGMA table_info(datasets)` → sets `self._has_snapshot_hash = True` if column exists.
2. On duplicate check: `_dedup_where()` uses `snapshot_hash = ?` for strict content dedup.
3. On insert: the adapter writes `snapshot_hash` value from `ImportDatasetDTO.snapshot_hash`.
4. Tests prove duplicate by SHA-256 hash is rejected.

## 8. Migration Implementation Plan

| Step | Action |
|---|---|
| 1 | Add `ensure_dataset_snapshot_hash_column()` to `repository/db.py` |
| 2 | Update `DatabaseManager.initialize()` to call it after main SCHEMA_SQL |
| 3 | Update `SCHEMA_SQL` for new databases (add `snapshot_hash` column) |
| 4 | Add tests: new column exists, ALTER TABLE idempotent, INSERT with hash, duplicate by hash |
| 5 | Update `ArchiveManifest` → `ImportDatasetDTO` mapping to include `content_hashes["ohlcv_snapshot.csv"]` as `snapshot_hash` |

## 9. Focused Tests (Future Implementation)

| # | Test | Scope |
|---|---|---|
| 1 | `ensure_dataset_snapshot_hash_column` adds column to existing table | Migration |
| 2 | Idempotency — calling migration helper twice does not error | Idempotency |
| 3 | New database has `snapshot_hash` column in SCHEMA_SQL | Schema |
| 4 | INSERT with `snapshot_hash` succeeds | Compatibility |
| 5 | Duplicate `snapshot_hash` rejected via adapter | Strict dedup |

## 10. Next Two-Task Batch

**Batch 060G-Impl + 060H-Design — Dataset Snapshot Hash Schema Migration Implementation + Post-Migration DatasetRepoAdapter Insert-Only Design (with Old-DB Fallback)**

- 060G: Implement idempotent migration + SCHEMA_SQL update + tests.
- 060H: Design-only — DatasetRepoAdapter insert-only design targeting post-migration schema (`snapshot_hash` column available), with fallback path for pre-migration databases. The primary dedup key is `snapshot_hash`; the fallback is `(symbol, timeframe, source_path)` for old DBs. This is not a "Mode A implementation" — it is the full adapter design that handles both schema states.

## 11. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
