# UI Wiring Readiness Contract — Task 060T

> Design-only. No production code changed.

## 1. Data the UI Must Provide to ArchiveExportService

| Parameter | UI Source | How to obtain |
|---|---|---|
| `strategy_uid` | Selected Results row | `self.results_table.selectedStrategyUid()` or equivalent |
| `dataset_snapshot_path` | Dataset repository | `DatasetRepository.get_by_name() → meta.normalized_path` |
| `output_dir` | Project root | `<project_root>/exports/archives/<strategy_uid>/` |
| `experiment_name` | Selected strategy name | From Results row display name (or user dialog) |
| `disclaimer_text` | Not needed | Service uses built-in default |

## 2. How the UI Discovers Each Item

| Item | Discovery Method |
|---|---|
| Active project root | `self._project_repo` or `QFileDialog` / `getOpenFileName` — already wired in main_window.py |
| Selected strategy UID | Currently, Results page selection provides strategy name. Needs a strategy_uid column or a mapping from `StrategyRepository.list_all()` |
| Dataset snapshot path | Strategy holds `dataset_id` → `DatasetRepository.get_by_id()` or scan `datasets` table |
| Validation result presence | `PipelineResult` is already stored after Run in `self.latest_validation_result` |
| Destination folder | Pre-computed from `project_root + "/exports/archives/" + strategy_uid` |

## 3. Button Enable/Disable Rules

| State | Button |
|---|---|
| No project loaded | Disabled — "Open a project first" |
| Loading data | Disabled |
| No strategy selected | Enabled but shows "Select a validated strategy" if clicked |
| Strategy not validated | Disabled or shows "Strategy requires validation first" |
| Strategy validated + passed | **Enabled** |

## 4. Log Messages

| Event | Log Message |
|---|---|
| Export started | "INFO: Exporting archive for strategy '<name>'..." |
| Export success | "INFO: Archive exported to <path>" |
| Export failure | "ERROR: Failed to export archive: <error message>" |

## 5. UI Wiring Test Plan (Future, Not Implemented This Task)

| # | Test | Scope |
|---|---|---|
| 1 | Button disabled when no project loaded | UI state |
| 2 | Button calls `ArchiveExportService.export_strategy_archive()` | Service wiring |
| 3 | Success log written to log panel | UI feedback |
| 4 | Failure clears archive output directory (no partial folder) | Cleanup |
| 5 | No PySide6 in service module boundary | Isolation |

## 6. Recommended Next Two-Task Batch

**Batch 060U-Impl + 060V-Design — UI Export Archive Button Wiring + Final Reproducibility Signoff.**

- 060U: Wire "Export Archive" button on Results page → `ArchiveExportService`.
- 060V: Final reproducibility milestone signoff (all archive + export + import + round-trip).

## 7. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
