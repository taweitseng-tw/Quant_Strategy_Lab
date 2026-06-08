Completed:
- Batch 061A-Impl + 061B-Design — Raw Archive Repository Providers and Full UI Export Wiring Design.

Files changed:
- repository/strategy_repo.py (list_all_raw)
- repository/dataset_repo.py (get_raw_by_id)
- tests/test_strategy_repo.py (2 tests)
- tests/test_dataset_repo.py (2 tests)
- docs/archive_full_ui_export_wiring_design_061B.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. StrategyRepository.list_all_raw() returns raw dicts (id, project_id, name, strategy_json, created_at, updated_at). Existing list_all() unchanged.
2. DatasetRepository.get_raw_by_id(id) returns dict row or None. Includes normalized_path.
3. 061B design: exact MainWindow wiring steps, 8 user-facing errors, 5 UI wiring tests, open items.

Tests run:
- Repo tests: 32 passed.
- Archive adapter + round-trip: 12 passed.
- Full suite: 1251 passed.

Assumptions:
- list_all_raw() ordering matches list_all() (newest first by created_at DESC, id DESC).
- get_raw_by_id() has the same schema as the CREATE TABLE in db.py.

Known risks:
- Full UI export still requires MainWindow wiring (not implemented in this batch).
- DatasetRepository instance access from MainWindow not yet wired.

Reviewer focus:
- list_all_raw() SQL and return format (list of dicts, not sqlite3.Rows).
- get_raw_by_id() returns dict(row) for sqlite3.Row compatibility.
- 061B design: open items table (DatasetRepository access, validation per UID, path resolution).
