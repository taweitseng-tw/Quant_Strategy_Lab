Completed:
- Batch 060W-Impl + 060X-Design — ProjectArchiveDataSource Adapter Slice and Full UI Export Delegation Design.

Files changed:
- app/services/archive_project_data_source.py (created)
- tests/test_archive_project_data_source.py (created, 8 tests)
- docs/archive_full_ui_export_delegation_design_060X.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. ProjectArchiveDataSource: scans strategy rows for UID in strategy_json, returns dict or None. Dependency-injected providers for strategies, datasets, validations. No PySide6/UI imports.
2. 060X: full delegation wiring from MainWindow to ProjectArchiveDataSource to ArchiveExportService, helper method table, monkeypatch UI test plan, failure handling table.

Tests run:
- Adapter + export service: 15 passed.
- Full suite: 1245 passed.

Assumptions:
- Strategy UID is stored inside strategy_json payload (not in a dedicated SQL column).
- Providers are zero-argument (strategies) or single-argument (dataset, validation) callables.
- ProjectArchiveDataSource wraps providers registered after MainWindow construction.

Known risks:
- The UID scan is O(n) across all stored strategies. Acceptable for archive export frequency.

Reviewer focus:
- get_strategy() parser loop: handles both string and dict strategy_json, skips malformed rows gracefully.
- 060X delegation pattern: guard → adapter → service → output → feedback.
