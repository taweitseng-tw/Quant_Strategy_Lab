Completed:
- Batch 059Y-Impl + 059Z-Design Fix — Strategy UID Duplicate-Reject Guard and Staging/Commit/Move Ordering.

Files changed:
- repository/strategy_import_adapter.py
- tests/test_strategy_import_adapter.py
- docs/archive_import_filesystem_staging_design_059Z.md
- docs/changelog.md

Behavior changed:
1. ImportStrategyDTO.strategy_uid is now required (non-empty). Dedup scans existing strategy_json payloads for matching strategy_uid — no schema migration. Strategy_json must be valid JSON (dict), contain "strategy_uid", and payload_uid must match dto.strategy_uid.
2. Duplicate-reject now works by UID across different display names. Same UID, different name → DuplicateStrategyUIDError.
3. strategy_uid mismatch, malformed JSON, missing payload_uid all raise clear StrategyRepoAdapterError without inserting any row.
4. 059Z design corrected to Stage → DB Commit → Final Move ordering with two-zone cleanup.

Tests run:
- tests/test_strategy_import_adapter.py: 12 passed (5 new + 7 legacy updated).
- Audit tests: 11 passed.
- Full suite: 1179 passed, 0 warnings.

Assumptions:
- No schema migration needed — UID is stored inside strategy_json and scanned at insert time.
- Existing rows with unparseable JSON payloads are skipped during the scan (corner case).

Known risks:
- The UID scan is O(n) per insert. Acceptable for low-volume archive import but should be indexed if performance becomes an issue (future: add strategy_uid column + index).

Reviewer focus:
- _reject_duplicate_uid() scan loop in strategy_import_adapter.py.
- Payload validation chain: valid JSON → dict → has "strategy_uid" → matches dto.strategy_uid.
- 059Z design commitment to "Stage → DB Commit → Final Move" ordering and two-zone cleanup.
