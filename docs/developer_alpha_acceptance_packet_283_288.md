# Developer Alpha Acceptance Packet - Tasks 283-288

Acceptance recommendation for developer-alpha only.
Formal desktop release is not complete.
Generated: 2026-06-10

## Developer-Alpha Acceptance Evidence

| # | Capability | Evidence | Status |
|---|---|---|---|
| 1 | Desktop entrypoint imports and `main()` is callable | `test_app_main_imports_and_callable` | PASS |
| 2 | MainWindow imports without error | `test_main_window_imports` | PASS |
| 3 | Project root is available for local imports | `test_main_window_import_path` | PASS |
| 4 | Offscreen MainWindow constructs and closes | `test_offscreen_main_window_construct_and_close` | PASS |
| 5 | `app/main.py` subprocess launches and exits through `QSL_EXIT_AFTER_MS` | `test_subprocess_desktop_entrypoint_exits_cleanly` | PASS |
| 6 | Sample OHLCV CSV imports through DataService | `test_sample_ohlcv_import_produces_normalized_data` | PASS |
| 7 | Sample TXF CSV imports through DataService | `test_sample_txf_import_produces_normalized_data` | PASS |
| 8 | Sample data backtest produces trades, equity curve, metrics, and assumptions | `test_sample_ohlcv_backtest_produces_structured_output`, `test_sample_txf_backtest_produces_structured_output` | PASS |
| 9 | Sample workflow produces markdown report with key metrics | `test_sample_workflow_produces_markdown_report` | PASS |
| 10 | Archive import preview full contract is stable | `test_full_contract_acceptance` | PASS |
| 11 | Archive import preview no-config contract is stable | `test_no_config_preview_contract_acceptance` | PASS |
| 12 | Archive invalid input preserves service error cause | `test_invalid_archive_preserves_service_error_cause` | PASS |
| 13 | Unknown restore action is manual-review-required | `test_unknown_restore_action_is_manual_review_required` | PASS |
| 14 | Desktop evaluator walkthrough exists | `docs/desktop_evaluator_walkthrough_271_276.md` | PASS |
| 15 | Hold artifact decision exists | `docs/hold_artifact_decision_277_282.md` | PASS |

Verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Observed result: 16 passed.

## Recommendation

Developer-alpha recommendation: PASS.

Reasoning:
- The desktop startup path is covered in-process and through a real subprocess.
- Real sample data imports through existing DataService APIs.
- Sample data backtests produce structured output.
- A markdown report is generated from sample-data backtest output.
- Archive import preview has schema-versioned contract coverage.
- Hold artifacts are explicitly kept outside the developer-alpha release scope.

This recommendation is for a developer evaluator, not an end user. The evaluator
still needs a Python environment and should follow the desktop evaluator
walkthrough.

## Formal Desktop Release Status

Formal desktop release recommendation: NOT PASS.

Remaining formal-release gaps:

1. Installer or packaging path is not accepted yet.
2. CI pipeline is not accepted yet.
3. Visual/UI regression coverage is limited to offscreen startup smoke.
4. User-facing quickstart and troubleshooting docs are still thin.
5. Formal policy for optional developer tooling remains exclude-by-default.

## Next 3 Formal-Release Tasks

1. Tasks 289-294 - CI Smoke Pipeline Design
   Add or design a minimal CI workflow for Python 3.11+ dependency install and
   focused smoke tests.

2. Tasks 295-300 - Packaging Path Spike
   Create a small packaging decision document or spike for PyInstaller, Nuitka,
   or a pip-installable entrypoint.

3. Tasks 301-306 - User Quickstart And Troubleshooting
   Add a concise user-facing quickstart covering install, launch, sample data,
   report export, and common startup/import issues.

## Summary

| Metric | Value |
|---|---|
| Developer-alpha recommendation | PASS |
| Formal desktop release recommendation | NOT PASS |
| Startup smoke tests | 5 passing |
| Sample-data workflow smoke tests | 7 passing |
| Archive preview acceptance tests | 4 passing |
| Formal release gaps remaining | 5 |
| Next formal-release tasks proposed | 3 |
