# Archive UI Data-Source Adapter Design — Task 060V

> Design-only. No production code changed.

## 1. Purpose

Define a future adapter that provides `ArchiveExportService` with real strategy, dataset, and validation data from the current project's repository layer, enabling full production archive export from the Results page.

## 2. Interface

```python
class ProjectArchiveDataSource:
    """Translates active project repository state into ArchiveDataSource protocol."""

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        dataset_repo: DatasetRepository,
        validation_service,     # provides get_validation_result(strategy_name) -> dict
    ) -> None: ...

    def get_strategy(self, strategy_uid: str) -> dict | None: ...
    def get_dataset(self, dataset_id: int) -> dict | None: ...
    def get_validation_result(self, strategy_uid: str) -> dict | None: ...
```

## 3. Input → Output Mappings

| ArchiveDataSource method | Source | Notes |
|---|---|---|
| `get_strategy(uid)` | `StrategyRepository.list_all()` filtered by UID in `strategy_json` | Requires scanning stored JSON for `strategy_uid` field |
| `get_dataset(did)` | `DatasetRepository.get_by_name()` or direct query | Requires `dataset_id` from strategy record |
| `get_validation_result(uid)` | `PipelineResult` dict stored in `self.latest_validation_result` | Must be present and `elimination_result.passed=True` |

### UID Mapping from Repository

```python
def _strategy_uid_from_row(self, row: sqlite3.Row) -> str | None:
    payload = json.loads(row["strategy_json"])
    return payload.get("strategy_uid")
```

### Dataset Snapshot Path

The dataset snapshot CSV must exist on disk for the export. It can be:
- The original `datasets.normalized_path` (imported or generated dataset)
- A newly written deterministic snapshot using `archive.dataset_snapshot.write_dataset_snapshot()`

## 4. Failure Modes

| Condition | Action |
|---|---|
| Strategy UID not found in repository | `get_strategy()` returns `None` → `MissingStrategyError` from builder |
| No dataset for strategy's `dataset_id` | `get_dataset()` returns `None` → `MissingDatasetError` |
| No validation result | `get_validation_result()` returns `None` → `MissingValidationResultError` |
| Validation `elimination_result.passed=False` | → `StrategyValidationFailedError` |
| Dataset snapshot file missing on disk | `MissingDatasetSnapshotError` from builder |

## 5. How MainWindow Wiring Changes (Future)

```python
# In _handle_export_archive(), replace guard-only handler with:
adapter = ProjectArchiveDataSource(
    strategy_repo=self.strategy_service.strategy_repo,
    dataset_repo=self.data_service.dataset_repo,
    validation_service=self,  # or delegate method
)
export_service = ArchiveExportService(adapter)
output_dir = Path(self._project_root) / "exports" / "archives" / strategy_uid
result = export_service.export_strategy_archive(
    strategy_uid=strategy_uid,
    dataset_snapshot_path=dataset_snapshot_path,
    output_dir=output_dir,
)
```

## 6. Next Two-Task Batch

**Batch 060W-Impl + 060X-Design — ProjectArchiveDataSource Implementation + Full Archive Export UI Wiring.**

- 060W: Implement `ProjectArchiveDataSource` adapter.
- 060X: Wire full `_handle_export_archive()` with real service calls.

## 7. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
