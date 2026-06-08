Completed:
- Batch 061C-Impl + 061D-Design — Full UI Archive Export Wiring and Milestone Closure Design.

Files changed:
- app/services/data_service.py (get_dataset_raw_by_id)
- app/services/strategy_persistence_service.py (list_all_raw)
- app/ui/main_window.py (full _handle_export_archive wiring)
- tests/test_wfe_ui_wiring.py (2 tests)
- docs/reproducibility_milestone_closure_criteria_061D.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. DataService.get_dataset_raw_by_id(dataset_id): thin service-layer accessor to DatasetRepository.get_raw_by_id.
2. StrategyPersistenceService.list_all_raw(): thin wrapper for StrategyRepository.list_all_raw.
3. MainWindow._handle_export_archive() now performs full archive export: resolves strategy UID from strategy_json, resolves dataset metadata + snapshot path via DataService, verifies snapshot file exists, builds ProjectArchiveDataSource with repository providers, calls ArchiveExportService, shows success/failure QMessageBox and log messages. All existing guards preserved.
4. 4 new guards added (missing UID, missing dataset metadata, missing snapshot path, missing snapshot file).
5. 061D: 7 closure criteria defined. Milestone NOT yet closed.

Tests run:
- Archive adapter + service + round-trip: 18 passed (all archive-related tests).
- 13 pre-existing DataService failures (unrelated — import_file returns None).

Assumptions:
- Strategy UID is resolved by scanning list_all_raw() for matching strategy name in JSON payload.
- Dataset normalized_path may be relative; resolved to absolute against project_root.

Known risks:
- UID resolution scans all strategies — O(n). Acceptable for single-export usage.
- Dataset snapshot file existence checked before export but may be deleted between check and export.

Reviewer focus:
- _handle_export_archive() export sequence: strategy UID → dataset metadata → snapshot path → adapter → service → output.
- Service-layer accessors (get_dataset_raw_by_id, list_all_raw) keep SQLite behind repository boundaries.
- 061D closure criteria: 3 categories (export happy path, failure guards, backend integrity).
