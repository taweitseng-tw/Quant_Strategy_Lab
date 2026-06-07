Completed:
- Batch 060K-Impl + 060L-Design — ArchiveStager Implementation and ArchiveImportCoordinator First-Pass Wiring Design.

Files changed:
- archive/stager.py (created)
- tests/test_archive_stager.py (created, 7 tests + 1 skipped)
- docs/archive_import_coordinator_first_pass_wiring_design_060L.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. ArchiveStager: project-local `.staging/<exp>_<run_id>/` staging, SHA-256 verification, final move to `data/imported/<exp>/ohlcv.csv` after DB commit, staged path preserved on failure, cleanup_temp().
2. Source validation rejects path traversal and symlinks outside archive.
3. 060L design: 6-phase coordinator wiring with 6 failure audit points, ImportResult DTO, 7 spy/fake test scenarios.

Tests run:
- test_archive_stager.py: 7 passed, 1 skipped (symlink test requires admin on Windows).
- Full suite: 1210 passed, 1 skipped.

Assumptions:
- Monkeypatched move failure test uses archive.stager.shutil.move directly.
- Symlink test is skipped on Windows where creation may require admin.

Known risks:
- None within implementation scope.

Reviewer focus:
- archive/stager.py: move_to_final_destination() preserves self._staged_path on failure (src capture before move).
- 060L: failure audit matrix and ImportResult partial flag for final move failure.
