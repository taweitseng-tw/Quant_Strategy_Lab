# Full UI Export Wiring Design - Task 061B

> Design-only. No production code changed. Full UI export remains pending.

## 1. Future `_handle_export_archive()` Provider Shape

```python
def _handle_export_archive(self) -> None:
    from pathlib import Path
    from PySide6.QtWidgets import QMessageBox

    # Existing guard: project loaded, ranked data present, validation present,
    # and a strategy row is selected.
    if not self._guard_export_archive():
        return

    selected_ranges = self.results_table.table.selectedRanges()
    if not selected_ranges or not self.ranked_data:
        return

    row = selected_ranges[0].topRow()
    strat_item = self.ranked_data[row]
    strategy_uid = self._resolve_strategy_uid(strat_item.get("strategy"))
    if not strategy_uid:
        QMessageBox.warning(self, "Export Failed", "Could not determine strategy UID.")
        return

    # Repository instances must come from service/application state, not from
    # direct SQLite access inside MainWindow.
    strategy_repo = self.strategy_service.strategy_repo
    dataset_repo = self.data_service.dataset_repo

    from app.services.archive_project_data_source import ProjectArchiveDataSource
    from app.services.archive_export_service import ArchiveExportService

    adapter = ProjectArchiveDataSource(
        strategy_rows_provider=strategy_repo.list_all_raw,
        dataset_rows_provider=dataset_repo.get_raw_by_id,
        validation_result_provider=self._get_validation_result_for_archive,
    )

    dataset = adapter.get_dataset(dataset_id)
    snapshot_path = _resolve_project_path(project_root, dataset["normalized_path"])
    output_dir = Path(project_root) / "exports" / "archives" / strategy_uid

    service = ArchiveExportService(adapter)
    service.export_strategy_archive(strategy_uid, snapshot_path, output_dir)
```

The snippet above is a wiring shape, not final production code. The next
implementation must adapt the service attribute names to the current
`MainWindow` object and add explicit error handling around each lookup.

## 2. Required Wiring Steps

| Step | Method / Source | Notes |
|---|---|---|
| 1. Resolve strategy UID | Selected result row or strategy payload | Must not invent a UID when missing |
| 2. Build `ProjectArchiveDataSource` | `ProjectArchiveDataSource(strategy_rows_provider=..., dataset_rows_provider=..., validation_result_provider=...)` | Providers delegate to repository/service methods |
| 3. Strategy rows provider | `StrategyRepository.list_all_raw()` | Implemented in 061A |
| 4. Dataset rows provider | `DatasetRepository.get_raw_by_id(id)` | Implemented in 061A |
| 5. Validation result provider | `self._get_validation_result_for_archive(uid)` | Must reject mismatched UID instead of blindly using the latest run |
| 6. Resolve dataset snapshot path | `DatasetRepository.get_raw_by_id(dataset_id)["normalized_path"]` | Resolve relative paths against the project root |
| 7. Build `ArchiveExportService` | `ArchiveExportService(adapter)` | Service remains UI-free |
| 8. Call export | `service.export_strategy_archive(strategy_uid, snapshot_path, output_dir)` | Suggested output dir: `<project_root>/exports/archives/<uid>/` |
| 9. Feedback | `QMessageBox.information` on success; `QMessageBox.critical` on failure | Also write to `log_panel` |

## 3. User-Facing Error Messages

| Condition | Message |
|---|---|
| Strategy UID not found | "Could not locate strategy UID in the project database. The strategy may have been removed." |
| Dataset ID not found | "No dataset metadata found for this strategy. Dataset metadata is required for archive export." |
| Dataset snapshot file missing | "Dataset OHLCV file not found at <path>. Please re-run the backtest or import the dataset again." |
| Validation result missing | "The selected strategy has not been validated. Run validation first." |
| Archive export I/O failure | "Failed to write archive to <path>. Check disk space and permissions." |
| No project loaded | "No project is loaded. Open a project first." |
| No strategy selected | "Please select a strategy from the Results table first." |
| Strategy not validated | "This strategy did not pass validation. Only passed strategies can be exported." |

## 4. Focused UI Wiring Tests (Future)

| # | Test | Seam |
|---|---|---|
| 1 | Button enabled when strategy, dataset, and validation are present | Check UI state |
| 2 | `_handle_export_archive` calls `ArchiveExportService.export_strategy_archive` | Monkeypatch service |
| 3 | Success path shows `QMessageBox.information` and writes a log entry | Assert dialog/log |
| 4 | Failure path shows `QMessageBox.critical` | Simulate service error via monkeypatch |
| 5 | `ProjectArchiveDataSource` resolves UID correctly through `list_all_raw` | Integration test |
| 6 | Missing or mismatched validation UID blocks export | UI-service boundary test |

## 5. Open Items

| Item | Status | Action |
|---|---|---|
| `DatasetRepository` instance access from `MainWindow` | Not wired yet | Add a service-layer accessor; do not query SQLite in UI |
| Validation result per `strategy_uid` | No index | Prefer a UID-keyed validation cache; reject missing or mismatched UID |
| Dataset `normalized_path` resolution | File exists check needed | Verify file before calling export |
| `dataset_id` source | Needs confirmation | Use the selected strategy provenance or result payload; fail clearly if absent |

## 6. Next Two-Task Batch

**Batch 061C-Impl + 061D-Design - Full UI Archive Export Wiring and Milestone Documentation Finalization.**

- 061C: Wire `_handle_export_archive()` with real `ProjectArchiveDataSource` and `ArchiveExportService`.
- 061D: Final documentation and changelog finalization after UI export is implemented and verified.

## 7. Metadata

- **Author**: DeepSeek V4, amended by Codex review
- **Date**: 2026-06-08
