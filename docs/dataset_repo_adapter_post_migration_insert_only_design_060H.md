# DatasetRepoAdapter Post-Migration Insert-Only Design with Old-DB Fallback — Task 060H

> Design-only. No production code changed.

## 1. Purpose

Define a future `DatasetRepoAdapter` for inserting imported dataset metadata into the `datasets` table. Post-migration primary dedup key is `snapshot_hash`; old-DB fallback is `(symbol, timeframe, source_path)` when the column is absent or hash is empty.

## 2. Schema Probing at Init

```python
class DatasetRepoAdapter:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        cursor = connection.execute("PRAGMA table_info(datasets)")
        column_names = {row[1] for row in cursor.fetchall()}
        self._has_snapshot_hash = "snapshot_hash" in column_names
```

## 3. Immutable DTO

```python
@dataclass(frozen=True, slots=True)
class ImportDatasetDTO:
    name: str
    symbol: str
    timeframe: str
    snapshot_hash: str = ""
    source_type: str = "archive_import"
    source_path: str = ""
    normalized_path: str = ""
    row_count: int = 0
    start_datetime: str = ""
    end_datetime: str = ""
    project_id: int | None = None
```

## 4. Duplicate-Reject Logic

```python
def _dedup_where(self, dto: ImportDatasetDTO) -> tuple[str, list]:
    """Return SQL WHERE + params based on available schema and hash value."""
    if self._has_snapshot_hash and dto.snapshot_hash:
        # Post-migration: strict content dedup
        return "snapshot_hash = ?", [dto.snapshot_hash]
    elif dto.source_path:
        # Old-DB fallback with source path
        return "symbol = ? AND timeframe = ? AND source_path = ?", [
            dto.symbol, dto.timeframe, dto.source_path
        ]
    else:
        # Old-DB fallback without source path
        return "symbol = ? AND timeframe = ?", [dto.symbol, dto.timeframe]
```

## 5. Dual SQL for Post-Migration vs Old-DB

```python
_INSERT_SQL_POST_MIGRATION = """
    INSERT INTO datasets
        (project_id, name, symbol, timeframe, source_type, source_path,
         normalized_path, row_count, start_datetime, end_datetime,
         snapshot_hash, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_SQL_OLD_DB = """
    INSERT INTO datasets
        (project_id, name, symbol, timeframe, source_type, source_path,
         normalized_path, row_count, start_datetime, end_datetime,
         created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
```

## 6. Core Insert Method

```python
def _insert_dataset_core(self, dto: ImportDatasetDTO) -> int:
    """Validate + dedup + INSERT (no commit/rollback)."""
    if not dto.name or not dto.symbol:
        raise DatasetRepoAdapterError("Name and symbol are required.")

    # dedup check
    where, params = self._dedup_where(dto)
    existing = self._conn.execute(
        f"SELECT id FROM datasets WHERE {where}", params
    ).fetchone()
    if existing is not None:
        raise DuplicateDatasetError(...)

    now = datetime.now(timezone.utc).isoformat()
    try:
        if self._has_snapshot_hash:
            cur = self._conn.execute(
                self._INSERT_SQL_POST_MIGRATION,
                (dto.project_id, dto.name, dto.symbol, dto.timeframe,
                 dto.source_type, dto.source_path, dto.normalized_path,
                 dto.row_count, dto.start_datetime, dto.end_datetime,
                 dto.snapshot_hash, now),
            )
        else:
            cur = self._conn.execute(
                self._INSERT_SQL_OLD_DB,
                (dto.project_id, dto.name, dto.symbol, dto.timeframe,
                 dto.source_type, dto.source_path, dto.normalized_path,
                 dto.row_count, dto.start_datetime, dto.end_datetime,
                 now),
            )
        return cur.lastrowid
    except sqlite3.Error as exc:
        raise DatasetRepoAdapterError(
            f"Failed to insert dataset '{dto.name}': {exc}"
        ) from exc
```

## 7. Transaction Methods

```python
def insert_dataset(self, dto: ImportDatasetDTO) -> int:
    """Auto-commit wrapper.  Rolls back only on SQLite write / commit failure.

    Validation errors, DuplicateDatasetError, and other non-SQLite errors
    are NOT rolled back — caller's uncommitted data is preserved.
    """
    try:
        row_id = self._insert_dataset_core(dto)
    except DatasetRepoAdapterError as exc:
        if isinstance(exc.__cause__, sqlite3.Error):
            self._conn.rollback()
        raise
    try:
        self._conn.commit()
        return row_id
    except sqlite3.Error as exc:
        self._conn.rollback()
        raise DatasetRepoAdapterError(...) from exc

def insert_dataset_no_commit(self, dto: ImportDatasetDTO) -> int:
    """Coordinator-facing.  No commit or rollback is performed."""
    return self._insert_dataset_core(dto)
```

## 8. No Overwrite / Update / Upsert

Insert-only. Duplicate → `DuplicateDatasetError`. No `update()`, `save()`, or `upsert()`.

## 9. Exception Hierarchy

```python
class DatasetRepoAdapterError(Exception): ...
class DuplicateDatasetError(DatasetRepoAdapterError): ...
```

## 10. Focused Tests (Future Implementation)

| # | Test | Schema State |
|---|---|---|
| 1 | Insert succeeds | Post-migration |
| 2 | Duplicate by `snapshot_hash` rejected | Post-migration |
| 3 | Duplicate by fallback `(symbol, timeframe, source_path)` rejected | Old-DB |
| 4 | Old-DB INSERT does not include snapshot_hash column | Old-DB |
| 5 | Empty `snapshot_hash` falls back to old-DB key | Post-migration |
| 6 | Missing name/symbol rejected | Any |
| 7 | `insert_dataset_no_commit` + caller commit | Any |
| 8 | `insert_dataset_no_commit` + caller rollback | Any |
| 9 | SQLite INSERT failure triggers rollback | Any |
| 10 | Validation error does NOT rollback caller uncommitted | Any |
| 11 | Duplicate error does NOT rollback caller uncommitted | Any |
| 12 | No other tables modified | Any |

## 11. Next Two-Task Batch

**Batch 060I-Impl + 060J-Design — DatasetRepoAdapter Implementation + ArchiveStager Implementation Design.**

- 060I: Implement DatasetRepoAdapter per this design.
- 060J: Design ArchiveStager for filesystem copy + hash verify + temp cleanup per 059Z.

## 12. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
