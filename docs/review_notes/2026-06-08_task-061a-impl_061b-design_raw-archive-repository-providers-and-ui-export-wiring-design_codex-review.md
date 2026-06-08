# Codex Review - Batch 061A-Impl + 061B-Design

Decision: PASS

Score: 9.1/10 after Codex fixes

## Findings

- [P2] `docs/archive_full_ui_export_wiring_design_061B.md`: The original design snippet included an intentionally incorrect `dataset_rows_provider` placeholder. Codex rewrote the provider-shape section to avoid a copy-forward implementation bug.
- [P3] `app/services/archive_project_data_source.py`: The adapter docstring still described old provider expectations. Codex updated it to reference `StrategyRepository.list_all_raw()` and `DatasetRepository.get_raw_by_id()`.
- [P3] `tests/test_strategy_repo.py`: The raw-list ordering test asserted literal names but did not prove parity with `list_all()`. Codex strengthened it to compare raw ordering against model ordering.

## Required Fixes

- Completed by Codex in this review.

## Architecture Risk

- Repository additions are correctly contained inside `repository/`.
- UI was not modified in 061A/061B.
- Full UI export remains pending. The next implementation must not bypass service/repository boundaries; it should add service-layer accessors if needed rather than querying SQLite from `MainWindow`.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_repo.py tests\test_dataset_repo.py -q` - 32 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_roundtrip_acceptance.py -q` - 12 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` - 1251 passed.
- `git diff --check` - passed.

## Next Assignment

- Batch 061C-Impl + 061D-Design - Full UI Archive Export Wiring and Milestone Closure Design.
- 061C should add service-layer repository accessors as needed, then wire `_handle_export_archive()` through `ProjectArchiveDataSource` and `ArchiveExportService`.
- 061D should design final milestone closure criteria, not declare closure until Codex accepts the implemented UI export.
