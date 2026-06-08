# Full UI Export Delegation Design — Task 060X

> Design-only. No production code changed.

## 1. Future Wiring in `_handle_export_archive()`

The current handler in `MainWindow` has guard checks but does not call `ArchiveExportService`. The full delegation should be:

```python
def _handle_export_archive(self) -> None:
    # — guards (existing) —
    if not self._guard_export_archive():
        return

    # — resolve strategy and dataset —
    row = self._ranked_data[selected_row]
    strategy = row["strategy"]
    strategy_uid = self._resolve_strategy_uid(strategy)

    # — build data source adapter —
    adapter = ProjectArchiveDataSource(
        strategy_rows_provider=lambda: self.strategy_service.strategy_repo.list_all(),
        dataset_rows_provider=lambda did: self._fetch_dataset(did),
        validation_result_provider=lambda uid: self._fetch_validation(uid),
    )

    # — build export service —
    export_service = ArchiveExportService(adapter)

    # — determine output path —
    output_dir = Path(self._project_root) / "exports" / "archives" / strategy_uid

    # — resolve dataset snapshot path —
    snapshot_path = self._resolve_dataset_snapshot_path(strategy_uid)

    # — export —
    try:
        archive_path = export_service.export_strategy_archive(
            strategy_uid=strategy_uid,
            dataset_snapshot_path=snapshot_path,
            output_dir=output_dir,
        )
        self.log_panel.add_message("INFO", f"Archive exported to {archive_path}")
        QMessageBox.information(self, "Export Successful", f"Archive exported to:\n{archive_path}")
    except ArchiveExportServiceError as exc:
        self.log_panel.add_message("ERROR", f"Archive export failed: {exc}")
        QMessageBox.critical(self, "Export Failed", str(exc))
```

## 2. Helper Methods

| Helper | Responsibility |
|---|---|
| `_resolve_strategy_uid(strategy)` | Extract `strategy_uid` from the Strategy object's JSON or the curated row data |
| `_fetch_dataset(dataset_id)` | `DatasetRepository.get_by_name()` or direct SQL — returns dict |
| `_fetch_validation(uid)` | Look up from `self.latest_validation_result` — return dict |
| `_resolve_dataset_snapshot_path(uid)` | Find `normalized_path` from dataset repository |

## 3. Success-Path UI Test Plan (Monkeypatch Seams)

| # | Test | Seam |
|---|---|---|
| 1 | Export button enabled when strategy + validation present | N/A (check UI state) |
| 2 | Clicking Export Archive calls `ArchiveExportService.export_strategy_archive()` | Monkeypatch `ArchiveExportService.export_strategy_archive` |
| 3 | Success path shows QMessageBox.information + log message | Assert QMessageBox.info called + log message |
| 4 | Failure path shows QMessageBox.critical + log error | Simulate `ArchiveExportServiceError` via monkeypatch |
| 5 | No PySide6 imports in service/adapter modules | Module-level import check |

## 4. Failure Handling

| Failure | Effect |
|---|---|
| Guard check fails (selection, validation) | WARN log + QMessageBox.warning, return early |
| Dataset snapshot file missing | `MissingDatasetSnapshotError` → Wrap in `ArchiveExportServiceError` → CRITICAL log + dialog |
| Strategy UID not found in repository | `MissingStrategyError` → CRITICAL log + dialog |
| Validation missing | `MissingValidationResultError` → CRITICAL log + dialog |
| File I/O during export | `ArchiveExporterError` → CRITICAL log + dialog |

## 5. Output Cleanup

If the export fails after partial file creation, the coordinator should NOT clean up the output folder — the user or operator can manually inspect and delete it. This matches the stager's repair-preservation policy from 060K.

## 6. Next Two-Task Batch

**Batch 060Y-Impl + 060Z-Design — Full UI Archive Export Wiring + Reproducibility Milestone Acceptance.**

- 060Y: Wire full `_handle_export_archive()` with `ProjectArchiveDataSource`, `ArchiveExportService`, snapshot path resolution, and log/dialog feedback.
- 060Z: Final reproducibility milestone acceptance signoff (no new functionality).

## 7. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
