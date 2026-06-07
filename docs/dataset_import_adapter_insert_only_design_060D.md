# DatasetRepoAdapter Insert-Only Slice Design — Task 060D (Fix)

> Design-only. No production code changed.

## 1. Purpose

Define a future `DatasetRepoAdapter.insert_dataset()` for inserting imported dataset metadata into the existing `datasets` table. Duplicate-reject semantics. No overwrite/update/upsert.

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

**Note**: The current schema has no `snapshot_hash` column. Strict duplicate-reject by content hash is **not possible** in the current schema. A schema migration (add `snapshot_hash TEXT NOT NULL DEFAULT ''`) is a prerequisite for hash-based dedup. Until then, the adapter can only provide approximate dedup via `(symbol, timeframe, source_path)` with an acknowledged false-positive risk.

## 3. Immutable DTO

```python
@dataclass(frozen=True, slots=True)
class ImportDatasetDTO:
    """Immutable DTO for an imported dataset row.

    Fields
    ------
    name : str
        Dataset name — derived from archive experiment_name + symbol + timeframe.
    symbol : str
        Instrument symbol from the archive.
    timeframe : str
        Bar timeframe from the archive.
    source_type : str
        Always ``'archive_import'`` for archive-imported datasets.
    source_path : str
        Original archive source path (folder or zip path).
    normalized_path : str
        Final destination path after staging — deterministic path
        calculated before DB insert; move happens after commit.
    row_count : int
        Number of rows in the dataset snapshot.
    start_datetime : str
        First bar timestamp from the archive manifest or snapshot.
    end_datetime : str
        Last bar timestamp from the archive manifest or snapshot.
    snapshot_hash : str
        SHA-256 hex of ``ohlcv_snapshot.csv`` from manifest.content_hashes.
        The authoritative dedup key (requires schema migration).
    project_id : int | None
        Project database foreign key, if available.
    """
    name: str
    symbol: str
    timeframe: str
    source_type: str = "archive_import"
    source_path: str = ""
    normalized_path: str = ""
    row_count: int = 0
    start_datetime: str = ""
    end_datetime: str = ""
    snapshot_hash: str = ""
    project_id: int | None = None
```

## 4. Duplicate-Reject Key

### Primary (Ideal): `snapshot_hash`

The archive manifest's `content_hashes["ohlcv_snapshot.csv"]` is a SHA-256 hex string that uniquely identifies the dataset snapshot content. Two archives with identical snapshot content have the same hash.

**Requires schema prerequisite**: The `datasets` table must have a `snapshot_hash TEXT` column. This is a schema migration outside the adapter's scope. Until added, the adapter cannot enforce strict content-based dedup.

### Fallback (Current schema): `(symbol, timeframe, source_path)`

A composite key available in the current schema. `source_path` is the archive root path, which is unique per import. This prevents re-importing the same archive but does NOT prevent importing a different archive that happens to contain the same dataset content.

| Key | Dedup strength | Available now? |
|---|---|---|
| `snapshot_hash` | ✅ Strict content dedup | ❌ Requires schema migration |
| `(symbol, timeframe, source_path)` | ⚠️ Archive-level dedup only | ✅ Yes |

### Two-Mode Design (Strict Separation)

**Mode A — Current-schema mode** (no `snapshot_hash` column available):

- Dedup key: `(symbol, timeframe, source_path)` — available in current schema.
- The adapter never queries a non-existent `snapshot_hash` column.
- `ImportDatasetDTO.snapshot_hash` is accepted and stored in a local variable but is NOT used in SQL queries.
- If `source_path` is empty, dedup falls back to `(symbol, timeframe)` only with a warning.

```python
def _dedup_where_current_schema(self, dto: ImportDatasetDTO) -> tuple[str, list]:
    """Current-schema dedup — never touches snapshot_hash column."""
    if dto.source_path:
        return "symbol = ? AND timeframe = ? AND source_path = ?", [
            dto.symbol, dto.timeframe, dto.source_path
        ]
    return "symbol = ? AND timeframe = ?", [dto.symbol, dto.timeframe]
```

**Mode B — Post-migration mode** (after `snapshot_hash TEXT` column added):

- Dedup key: `snapshot_hash` — strict content-based dedup.
- The adapter queries the `snapshot_hash` column.
- The adapter checks a class-level flag (e.g. `self._has_snapshot_hash` set during `__init__` by probing the schema) to decide which mode to use.

```python
def _dedup_where(self, dto: ImportDatasetDTO) -> tuple[str, list]:
    """Return SQL WHERE + params for the dedup check based on available schema."""
    if self._has_snapshot_hash and dto.snapshot_hash:
        return "snapshot_hash = ?", [dto.snapshot_hash]
    # Fallback — current schema
    return self._dedup_where_current_schema(dto)
```

The schema migration task (add `snapshot_hash` column + set `_has_snapshot_hash = True`) is a separate prerequisite. The first adapter implementation only implements Mode A. Mode B tests are written but marked `skip` until migration is applied.

## 5. Behaviour Matrix

| Condition | Action |
|---|---|
| Normal insert | Insert row with all DTO fields. Return `row id`. |
| Duplicate by hash (or fallback key) | Raise `DuplicateDatasetError`. No row inserted. |
| Missing `symbol` | Raise `DatasetRepoAdapterError` — required field. |
| `row_count <= 0` | Raise `DatasetRepoAdapterError` — non-zero rows expected. |
| `normalized_path` empty | Raise `DatasetRepoAdapterError` — must know final destination. |

## 6. Exception Hierarchy

```python
class DatasetRepoAdapterError(Exception):
    """Base for dataset repository adapter errors."""


class DuplicateDatasetError(DatasetRepoAdapterError):
    """Raised when a dataset with the same identity already exists."""
```

## 7. No Overwrite / Update / Upsert

Insert-only. Duplicate → `DuplicateDatasetError`. No `update()`, `save()`, or `upsert()`.

## 8. Coordinator Timing: Deterministic Path (Selected)

**Chosen: Option A — Deterministic final path calculated before DB insert, file move after commit.**

The final destination path is deterministic from the archive manifest:

```python
final_path = f"data/imported/{experiment_name}/ohlcv.csv"
```

This is known **before** any filesystem operation. The coordinator sequence:

```
1. Preflight (no DB writes)
2. Stage snapshot to .staging/  (temp path, not final)
3. Verify staged file hash
4. DB transaction open
5. insert_strategy_no_commit(dto)
6. insert_dataset(dataset_dto)  # normalized_path = deterministic final path
7. conn.commit()                 # strategy + dataset rows durable
8. Move file: .staging/ → data/imported/<exp>/ohlcv.csv
9. If move fails → strategy + dataset rows exist, file missing
   → acknowledged MVP gap (partial import)
```

**Why not Option B (move first, then insert):** Moving before DB commit would mean the dataset file exists on disk but no DB row refers to it — also a partial state. The chosen order avoids orphaned files.

## 9. Schema Prerequisite for Strict Hash Dedup

| Task | Description |
|---|---|
| Add `snapshot_hash TEXT NOT NULL DEFAULT ''` to `datasets` table | `ALTER TABLE datasets ADD COLUMN snapshot_hash TEXT NOT NULL DEFAULT ''` |
| Update `DatabaseManager.SCHEMA_SQL` | Include the column in CREATE TABLE for new projects |
| Mark migration in docs/changelog | Non-destructive additive migration |

Until this migration is done:
- The adapter's fallback dedup by `(symbol, timeframe, source_path)` is used.
- The `snapshot_hash` DTO field is accepted but not used for dedup.

## 10. Focused Tests (Future Implementation)

### Current-schema tests (Mode A — implement first)

| # | Test | Scope |
|---|---|---|
| 1 | `insert_dataset` succeeds with valid DTO | Happy path |
| 2 | Duplicate by `(symbol, timeframe, source_path)` rejected | Current-schema dedup |
| 3 | Duplicate by `(symbol, timeframe)` when `source_path` empty | Fallback dedup |
| 4 | Missing `symbol` rejected | Validation |
| 5 | `row_count <= 0` rejected | Validation |
| 6 | Empty `normalized_path` rejected | Validation |
| 7 | `snapshot_hash` in DTO is accepted but not queried | Boundary |
| 8 | No other tables modified | Boundary |

### Post-migration tests (Mode B — skip until migration applied)

| # | Test | Scope |
|---|---|---|
| 9 | Duplicate by `snapshot_hash` rejected (after migration) | Strict dedup |
| 10 | `snapshot_hash` empty falls back to current-schema key | Graceful degradation |

## 11. Next Two-Task Batch

**Batch 060E-Impl + 060F-Design — StrategyRepoAdapter Transaction Refactor Implementation + Dataset Snapshot Hash Schema Migration Design**

- 060E: Implement Option B (no-commit split) following 060C design.
- 060F: Design-only — dataset `snapshot_hash` schema migration (ALTER TABLE + SCHEMA_SQL update). Do NOT implement migration.
- No coordinator implementation.
- No DatasetRepoAdapter implementation (hash schema prerequisite not yet designed/completed).

## 12. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
- **Last fix**: Dedup key changed to `snapshot_hash` + fallback. Schema prerequisite documented. Coordinator timing resolved to Option A (deterministic path before insert, move after commit). Section 8/9 contradiction fixed.
