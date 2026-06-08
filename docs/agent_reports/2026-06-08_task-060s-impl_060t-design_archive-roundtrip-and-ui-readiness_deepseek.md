Completed:
- Batch 060S-Impl + 060T-Design — Export/Import Round-Trip Acceptance and UI Wiring Readiness.

Files changed:
- tests/test_archive_roundtrip_acceptance.py (created, 1 round-trip test)
- docs/archive_ui_wiring_readiness_contract_060T.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. Round-trip test: FakeDataSource → ArchiveExportService → ArchiveVerifier → ArchiveImportCoordinator (real adapters) → assert strategy/dataset rows exist, 0 failure audit, no UI/engine boundary.
2. 060T: Button enable/disable rules, data discovery methods, log messages, 5-test UI wiring plan.

Tests run:
- Round-trip: 1 passed.
- Export service + import acceptance + round-trip: 13 passed.
- Full suite: 1233 passed.

Assumptions:
- The exported archive manifest's content_hashes are used directly by the stager during import.
- The round-trip test constructs import DTOs from exported JSON files (strategy.json, dataset_meta.json).

Known risks:
- No UI button wired yet.
- The round-trip test does not yet test the full coordinator → UI feedback loop.

Reviewer focus:
- test_export_verify_import_roundtrip: 4-phase assertion (export, verify, import, assert DB state).
- 060T: enable/disable rules table + data discovery methods.
