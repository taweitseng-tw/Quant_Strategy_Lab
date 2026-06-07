Completed:
- Batch 060E-Impl + 060F-Design Fix2 — Narrow rollback scope, corrected tests, task alignment.

Files changed:
- repository/strategy_import_adapter.py
- tests/test_strategy_import_adapter.py
- docs/task_board.md
- docs/changelog.md

Behavior changed:
1. insert_strategy() rollback narrowed: only SQLite write failure (StrategyRepoAdapterError with __cause__ = sqlite3.Error) and commit() failure trigger rollback. Validation errors, JSON errors, DuplicateStrategyUIDError do NOT rollback caller's uncommitted data.
2. insert_strategy_no_commit() unchanged — no commit/rollback.
3. Tests: 3 new tests (real SQLite failure, validation no-rollback, duplicate-UID no-rollback). Old fake-SQLite-failure test removed.

Tests run:
- tests/test_strategy_import_adapter.py: 19 passed.
- Full suite: 1186 passed, 0 warnings.

Assumptions:
- The __cause__ chain (StrategyRepoAdapterError → sqlite3.Error) reliably distinguishes SQLite write failures from validation failures.
- Closing the connection forces a ProgrammingError during the UID scan, which is a real SQLite failure.

Known risks:
- None within the narrowed scope.

Reviewer focus:
- insert_strategy() except StrategyRepoAdapterError: isinstance(exc.__cause__, sqlite3.Error) → rollback, otherwise re-raise.
- Three new tests: SQLite failure, validation no-rollback, duplicate-UID no-rollback.
