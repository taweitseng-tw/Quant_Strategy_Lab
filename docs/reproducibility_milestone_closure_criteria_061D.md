# Reproducibility Milestone Closure Criteria — Task 061D

> Design-only. No production code changed.  Milestone not yet closed.

## 1. Closure Criteria

Codex must verify ALL of the following before closing the reproducibility milestone:

### 1.1 UI Export Happy Path

| Criterion | Evidence |
|---|---|
| "Export Archive" button visible and enabled when strategy is selected + validated | UI inspection |
| Clicking button calls `ArchiveExportService.export_strategy_archive()` | Test or manual log inspection |
| Exported archive folder contains `manifest.json`, `strategy.json`, `dataset_meta.json`, `validation_result.json`, `ohlcv_snapshot.csv`, `disclaimer.txt` | Folder inspection |
| Exported archive passes `ArchiveVerifier.verify_all()` | Test or manual run |

### 1.2 Failure Guards

| Criterion | Evidence |
|---|---|
| No selection → warning message, no service call | Test or manual |
| No validation result → warning message, no service call | Test or manual |
| Strategy failed validation → warning message, no service call | Test or manual |
| No dataset metadata → warning message, no service call | Test or manual |
| Dataset snapshot file missing → warning message, no service call | Test or manual |

### 1.3 Backend Integrity

| Criterion | Evidence |
|---|---|
| Full suite passes | `pytest -q` exit 0 |
| `git diff --check` passes | No trailing whitespace |
| No PySide6 imports in archive/ or repository/ modules | Module-level check |
| No direct SQLite access from `main_window.py` | Code review |

## 2. Remaining Optional Items (After Closure)

| Item | Priority |
|---|---|
| Zip archive export | Low |
| Import UI | Low |
| Success audit log writes | Low |
| Batch/concurrent archive export | Low |

## 3. Next Batch

If 061C passes closure review: **Batch 061E — Reproducibility Milestone Closure and Final Changelog** (single task, signoff only).

If 061C still has gaps: **Batch 061C-Fix** — address Codex findings, then re-run closure criteria.

## 4. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
