Completed:
- Batch 060M-Impl + 060N-Design — ArchiveImportCoordinator First-Pass Implementation and Coordinator Acceptance Tests Design.

Files changed:
- archive/import_coordinator.py (created)
- tests/test_archive_import_coordinator.py (created, 8 tests)
- docs/archive_import_coordinator_acceptance_tests_design_060N.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. ArchiveImportCoordinator: dependency-injected orchestrator. 6-phase sequence. ImportResult dataclass with partial/skipped/audit_failed flags.
2. Failure paths: duplicate → skip, stage failure → cleanup + audit, DB failure → rollback + cleanup + audit, move failure → partial (no rollback), audit failure → non-crashing.
3. 060N: 6 integration-style acceptance scenarios for future hardening.

Tests run:
- test_archive_import_coordinator.py: 8 passed.
- Full suite: 1219 passed.

Assumptions:
- Preflight duplicate check uses insert_strategy_no_commit + rollback as a probe.
- Audit adapter is optional — failure is non-crashing.

Known risks:
- Preflight insert + rollback leaves a used ID in the auto-increment sequence (cosmetic gap).

Reviewer focus:
- _import_archive_impl() sequence: verify → preflight probe + rollback → stage → DB writes → commit → move → cleanup.
- ImportResult.partial = True on move failure — DB rows kept, staging preserved.
- _write_failure_audit() best-effort with passed pass on failure.
