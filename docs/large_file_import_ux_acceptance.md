# Large-File Import UX Acceptance Summary

## Completed Rounds 1-6

### Round 1 - Background Worker Progress Signals
- Added `ImportWorker.progress_updated` stages for reading, importing/normalizing/checking quality, and finalizing.
- Wired progress to `MainWindow._on_import_progress()` so the import button, tooltip, and log panel update from Qt signals.
- Added `test_import_worker_progress_signals_emitted`.

### Round 2 - Import Completion Summary
- Import success now reports row count, symbol, timeframe, date range, quality state, warning count, and chart subset note when applicable.
- The data status label remains compact and color-coded.

### Round 3 - Quality Warning Detail Extraction
- `DataService.extract_warning_details()` reports structured large-jump and time-gap samples when available.
- Falls back to warning text when structured samples or a DataFrame are unavailable.
- Added tests for no warnings, large jumps, time gaps, and fallback behavior.

### Round 4 - Data Page Quality Report Surface
- The data status tooltip includes compact quality evidence plus actionable warning details.
- Existing UI tests cover clean imports, warning imports, failed-quality imports, and import failures.

### Round 5 - Session-Aware Gap Classification
- `check_quality()` now accepts optional `session_start` and `session_end` parameters.
- Expected overnight or weekend session breaks can be classified separately from intraday missing-bar gaps.
- Default behavior is unchanged when session parameters are omitted or blank.

### Round 6 - TXF Smoke Verification
- Existing TXF and sample-data smoke tests continue through `DataService`.
- UI import acceptance tests run the `ImportWorker` path synchronously for deterministic verification.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_data_page_wiring.py tests/test_candlestick_chart.py tests/test_sample_data_workflow_smoke.py tests/test_quality_checker.py tests/test_dataset_persistence_wiring.py tests/test_txf_import.py tests/test_export_persistence_acceptance.py tests/test_active_dataset.py -q
# Result: 115 passed
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Worker-local `DataService` | Avoids sharing project SQLite connections with the UI thread. |
| Progress as Qt signal | Keeps long imports off the UI thread while updating UI state safely. |
| Optional session-aware filtering | Preserves legacy quality-check behavior unless session bounds are provided. |
| Structured quality issues | Lets UI details use checker-approved samples instead of recalculating loosely. |
| Best-effort metadata persistence | Keeps import usable in memory even if project persistence fails. |
