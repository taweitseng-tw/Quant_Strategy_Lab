Completed:
- Batch 060E-Impl + 060F-Design Fix — Strategy rollback on core failure and next batch wording.

Files changed:
- repository/strategy_import_adapter.py
- tests/test_strategy_import_adapter.py
- docs/dataset_snapshot_hash_schema_migration_design_060F.md
- docs/changelog.md

Behavior changed:
1. insert_strategy() now wraps _insert_strategy_core() call in try/except that rolls back on ANY exception before re-raising. Previously only commit() failure was caught — core failures left the connection in a stale transaction state.
2. insert_strategy_no_commit() unchanged — no commit/rollback.
3. New regression test proves rollback on SQLite failure: duplicate UID → rollback → third insert succeeds on same connection.
4. 060F next batch wording corrected to "Post-Migration DatasetRepoAdapter Insert-Only Design (with Old-DB Fallback)" — not "Mode A implementation".

Tests run:
- tests/test_strategy_import_adapter.py: 17 passed (1 new regression test).
- Full suite: 1184 passed, 0 warnings.

Assumptions:
- The broad `except Exception` in insert_strategy() catches validation errors as well as SQLite errors. For validation errors the rollback is unnecessary but harmless (no SQL was executed).
- rollback() on a clean connection is a no-op in sqlite3.

Known risks:
- None within the fix scope. The no_commit path is unaffected.

Reviewer focus:
- insert_strategy() try/except Exception → rollback → raise pattern.
- Regression test: three-step sequence (insert → duplicate → insert succeeds after).
