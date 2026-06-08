Completed:
- Batch 060Q-Impl + 060R-Design — Archive Export Service Boundary and UI/Round-Trip Contract Design.

Files changed:
- app/services/archive_export_service.py (created)
- tests/test_archive_export_service.py (created, 4 tests)
- docs/archive_export_ui_and_roundtrip_contract_060R.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. ArchiveExportService: dependency-injected wrapper around ArchiveBuilder + ArchiveExporter. No PySide6 imports. Single method export_strategy_archive() with built-in disclaimer.
2. 4 tests: success + verifier verification, missing strategy, missing validation, missing dataset.
3. 060R: UI trigger design on Results page, data flow, error handling, output path, 5-step round-trip acceptance test plan.

Tests run:
- Export service + builder + exporter: 22 passed.
- Full suite: 1230 passed.

Assumptions:
- The FAKE data source from tests mirrors the real ArchiveDataSource protocol.
- ArchiveVerifier.verify_all() calls ArchiveVerifier(ArchiveManifest.read_from_folder(folder), folder) inside the test.

Known risks:
- No UI button wired yet — design only for 060R.
- Round-trip acceptance test not implemented.

Reviewer focus:
- ArchiveExportService.export_strategy_archive() — thin wrapper, __cause__ chain preserved.
- 060R round-trip test plan: export → verify → import → assert → boundary.
