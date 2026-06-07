Completed:
- Batch 060E-Impl + 060F-Design — StrategyRepoAdapter Transaction Refactor and Dataset Snapshot Hash Schema Migration Design.

Files changed:
- repository/strategy_import_adapter.py (refactored)
- tests/test_strategy_import_adapter.py (4 new tests)
- docs/dataset_snapshot_hash_schema_migration_design_060F.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. StrategyRepoAdapter: extracted _insert_strategy_core() (shared private, no commit/rollback). insert_strategy() refactored to call core + explicit commit/rollback (backward-compatible).
2. Added insert_strategy_no_commit() — coordinator-facing, no commit/rollback. Caller owns transaction.
3. 4 new tests prove rollback, commit, duplicate-reject without commit, and boundary isolation for no_commit variant.

Tests run:
- tests/test_strategy_import_adapter.py: 16 passed (12 existing + 4 new).
- Full suite: 1183 passed, 0 warnings.

Assumptions:
- insert_strategy() backward compatibility preserved — all existing tests pass unchanged.
- insert_strategy_no_commit() is only used by future coordinator; direct callers use insert_strategy().

Known risks:
- No unified coordinator transaction yet — this is a prerequisite, not the coordinator itself.

Reviewer focus:
- _insert_strategy_core() in repository/strategy_import_adapter.py — no commit/rollback calls.
- insert_strategy() and insert_strategy_no_commit() — clean separation with no boolean parameter ambiguity.
- 060F design — idempotent ALTER TABLE with PRAGMA table_info probe, no index, rollback compatibility.
