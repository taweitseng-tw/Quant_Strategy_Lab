# Codex Review - Batch 061C-Impl + 061D-Design

Decision: PASS

Score: 9.0/10 after Codex fixes

## Findings

- [P1] `app/services/data_service.py`: `get_dataset_raw_by_id()` was inserted into the middle of `import_file()`, preventing `import_file()` from persisting metadata and returning its documented tuple. Codex restored the method structure.
- [P1] `app/ui/main_window.py`: The archive validation provider converted non-dict `PipelineResult` into `{"passed": True}`, losing validation details and causing archive export to miss real validation content. Codex now converts dataclasses with `asdict()`.
- [P2] `app/ui/main_window.py`: The validation provider ignored the requested UID and would return the same validation result for any UID. Codex added explicit UID mismatch blocking.
- [P2] `tests/test_wfe_ui_wiring.py`: The added tests did not prove export service invocation or critical failure guards. Codex added service-call, UID mismatch, and missing dataset metadata guard tests.

## Required Fixes

- Completed by Codex in this review.

## Architecture Risk

- UI still obtains the active project database only to construct service-layer objects; there is no direct SQL or raw connection query in `MainWindow`.
- Full archive export now calls `ArchiveExportService` on the valid path and blocks before service call on key invalid paths.
- Milestone is still not closed. 061E should be signoff-only and should verify closure criteria before marking the milestone complete.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_wfe_ui_wiring.py -q` - 19 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_csv_importer.py tests\test_dataset_repo.py tests\test_dataset_persistence_wiring.py -q` - 37 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_archive_project_data_source.py tests\test_archive_export_service.py tests\test_archive_roundtrip_acceptance.py -q` - 18 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` - 1256 passed.
- `git diff --check` - passed.

## Next Assignment

- Task 061E - Reproducibility Milestone Closure and Final Changelog.
- Signoff-only unless Codex review of 061E finds a concrete gap.
