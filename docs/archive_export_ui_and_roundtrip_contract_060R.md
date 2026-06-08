# Archive Export UI Trigger and Round-Trip Acceptance Contract — Task 060R

> Design-only. No production code changed.

## 1. UI Trigger Location

| Aspect | Detail |
|---|---|
| Page | **Results** page — where validated strategies are listed |
| Widget | A "Export Archive" button below or alongside the existing "Export Report" button |
| Activation | Enabled only when a validated strategy is selected and has a stored `strategy_uid` |

## 2. Data Flow

```
Results Page (UI)
  ↓  selected_strategy_uid, dataset_snapshot_path, output_dir
ArchiveExportService.export_strategy_archive()
  ↓  ArchiveBuilder.build() → validates inputs
  ↓  ArchiveExporter.export() → writes folder + manifest
  ↓  returns Path to archive folder
Log message: "Archive exported to <path>"
```

### What the UI passes to the service

| Parameter | Source |
|---|---|
| `strategy_uid` | Selected strategy row's `strategy_uid` from Results table |
| `dataset_snapshot_path` | Dataset's `normalized_path` from `dataset_repo` |
| `output_dir` | `<project_root>/exports/archives/<strategy_uid>/` |
| `disclaimer_text` | Default (service provides built-in disclaimer) |
| `experiment_name` | Strategy name or user-provided name from a dialog |

## 3. Error Handling

| Failure | UI Message |
|---|---|
| No strategy selected | "Please select a validated strategy first." |
| Strategy not validated | "This strategy has not been validated. Export requires a passed validation result." |
| Missing dataset | "Dataset not found for this strategy." |
| Export I/O error | "Failed to export archive: <error>" (log panel) |

## 4. Archive Output Location

```
<project_root>/exports/archives/<strategy_uid>/
  manifest.json
  disclaimer.txt
  strategy.json
  dataset_meta.json
  validation_result.json
  ohlcv_snapshot.csv
```

These files are already gitignored (`exports/` in `.gitignore`).

## 5. Round-Trip Acceptance Test Plan (Future)

```
TEST: Export → Verify → Import → Assert

1. EXPORT: ArchiveExportService.export_strategy_archive()
   → archive folder written to temp path
2. VERIFY: ArchiveManifest.read_from_folder() + ArchiveVerifier.verify_all()
   → all hashes match, disclaimer present
3. IMPORT: ArchiveImportCoordinator.import_archive()
   → new in-memory DB receives strategy + dataset rows
4. ASSERT:
   - Imported strategy has same strategy_uid as original
   - Imported dataset has same symbol/timeframe
   - No duplicate rejected (fresh DB)
   - ImportAuditLog has no FAILED rows
   - ImportResult.success is True
5. BOUNDARY: no PySide6/backtest_engine in coordinator namespace
```

## 6. UI Implementation Surface (Future)

| File | Change |
|---|---|
| `app/ui/main_window.py` | "Export Archive" button in Results page, signal wiring |
| `app/services/archive_export_service.py` | Already exists (060Q) |
| `tests/test_wfe_ui_wiring.py` or new | UI wiring test: button calls service, log panel gets success message |

## 7. Next Two-Task Batch

**Batch 060S-Impl + 060T-Design — UI "Export Archive" Button Wiring + Round-Trip Acceptance Test Implementation.**

- 060S: Wire button on Results page, passive/no-op safe, success/failure log messages.
- 060T: Implement round-trip acceptance test (export → verify → import → assert).

## 8. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
