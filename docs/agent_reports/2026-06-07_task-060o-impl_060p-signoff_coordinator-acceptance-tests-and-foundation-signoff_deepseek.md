Completed:
- Batch 060O-Impl + 060P-Signoff — Coordinator Acceptance Tests and Reproducibility Foundation Signoff.

Files changed:
- tests/test_archive_import_coordinator_acceptance.py (created, 6 tests)
- docs/reproducibility_foundation_signoff_060P.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. 6 acceptance tests: manifest failure → no DB; duplicate UID → skipped; duplicate dataset → rollback strategy; move failure → partial (DB kept); audit failure → audit_failed=True; no UI/engine boundary.
2. Coordinator uses read-only preflight — no insert-and-rollback probe.
3. Signoff: 14 archive components status table, risks assessed, verdict: reproducibility foundation functionally complete.

Tests run:
- Coordinator (unit + acceptance): 15 passed.
- Full suite: 1226 passed.

Assumptions:
- All acceptance tests use real SQLite + repository adapters (no mock DB).
- Move failure test uses monkeypatch on ArchiveStager.move_to_final_destination.

Known risks:
- No UI trigger for archive export/import yet.
- No zip archive support (folder-only).

Reviewer focus:
- Acceptance tests: each covers a specific coordinator failure path with real DB assertions.
- Signoff: coverage table, remaining risks, recommended next batch.
