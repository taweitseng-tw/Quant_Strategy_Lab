# Full UI Export Boundary Design — Task 060Y

> Design-only. No production code changed.

## 1. The Raw-Row Provider Problem

`ProjectArchiveDataSource.get_strategy()` needs row-like dicts with a `"strategy_json"` key. However, `StrategyRepository.list_all()` returns `Strategy` objects, not raw SQLite rows.

The current test fake returns raw dicts. A real MainWindow wiring would need a
provider that wraps `StrategyRepository` and returns dicts with the expected keys.

## 2. Option Comparison

### Option A: Add `list_all_raw()` to StrategyRepository

Add a method that returns raw SQLite rows (as dicts) instead of `Strategy` objects.

```python
class StrategyRepository:
    def list_all_raw(self) -> list[dict]:
        rows = self._db.connection.execute(
            "SELECT id, name, strategy_json, created_at, updated_at FROM strategies "
            "ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
```

| Pro | Con |
|---|---|
| Minimal change, single method | Adds a method that may tempt callers to bypass `Strategy` model |
| Works directly with `ProjectArchiveDataSource` | — |
| Already follows project pattern (raw SQL queries exist in other repos) | — |

### Option B: Dedicated ArchiveRepositoryAdapter

Create a new `archive/archive_repository.py` that encapsulates raw SQL queries for archive export.

```python
class ArchiveRepository:
    def __init__(self, connection: sqlite3.Connection) -> None: ...
    def get_strategy_row(self, uid: str) -> dict | None: ...
    def get_dataset_row(self, did: int) -> dict | None: ...
    def get_validation_row(self, uid: str) -> dict | None: ...
```

| Pro | Con |
|---|---|
| Clean separation of concerns | More files, more surface area |
| No changes to existing repositories | Over-engineering for a single caller |
| Future import coordinator already uses direct adapters | — |

### Option C: Inline the Provider in MainWindow

Write a thin lambda inside `_handle_export_archive()` that queries SQLite directly.

```python
def _get_raw_strategies() -> list[dict]:
    conn = self.project_service.repo.db.connection
    rows = conn.execute("SELECT * FROM strategies ORDER BY id").fetchall()
    return [dict(r) for r in rows]
```

| Pro | Con |
|---|---|
| No new file, no new repository method | Duplicates SQL logic in UI layer |
| Quick to wire | Violates architecture boundary (UI layer queries raw SQL) |

## 3. Recommendation

**Option A — `list_all_raw()` on `StrategyRepository`.**

Rationale:
- Single, minimal, testable addition.
- Keeps SQL logic in the repository layer.
- Already matches the pattern used by `DatasetRepository` (which uses `DatasetMeta` models but the adapter converts to dicts).
- Does not require a new module or architecture change.

### Supporting addition to `DatasetRepository`

Also add a method to look up a dataset dict by ID (or by name) to avoid exposing raw connections:

```python
class DatasetRepository:
    def get_raw_by_id(self, dataset_id: int) -> dict | None:
        row = self._db.connection.execute(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        return dict(row) if row else None
```

## 4. Exact Data Contracts

| Provider Signature | Returns | Notes |
|---|---|---|
| `StrategyRepository.list_all_raw()` | `list[dict]` | Each dict has `id`, `name`, `strategy_json`, `created_at`, `updated_at` |
| `DatasetRepository.get_raw_by_id(did)` | `dict \| None` | Full dataset row dict |
| `MainWindow._fetch_validation(uid)` | `dict \| None` | From `latest_validation_result` dict or `PipelineResult` field |

## 5. User-Facing Errors

| Condition | User Message |
|---|---|
| Strategy UID not found in any row | "Could not locate strategy UID in the project database. The strategy may have been removed." |
| Dataset ID not found for strategy | "No dataset metadata found for the selected strategy. Dataset metadata is required for archive export." |
| Dataset snapshot file missing | "Dataset OHLCV file not found at <path>. Please re-run backtest or import the dataset again." |
| Validation result missing | "The selected strategy has not been validated. Run validation on at least one strategy before exporting an archive." |
| Storage I/O failure | "Failed to write archive to <path>. Check disk space and permissions." |

## 6. Focused Tests (Future)

| # | Test | Scope |
|---|---|---|
| 1 | `list_all_raw()` returns rows with expected keys | Repository |
| 2 | `get_raw_by_id()` returns row or None | Repository |
| 3 | `ProjectArchiveDataSource` wired with `list_all_raw` finds correct UID | Integration |
| 4 | Adapter returns None for UID present in `Strategy` but not in raw rows | Edge case |
| 5 | Full export pipeline: `list_all_raw` → `ProjectArchiveDataSource` → `ArchiveExportService` → verify | Acceptance |

## 7. Out of Scope

- Import UI.
- Zip archive support.
- Live trading, broker API, GA/GP expansion, portfolio backtest.
- Success audit log writes.

## 8. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
