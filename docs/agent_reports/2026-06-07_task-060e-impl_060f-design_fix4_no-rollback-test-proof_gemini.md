Completed:
- Batch 060E-Impl + 060F-Design Fix4 — No-rollback test proof correction.

Files changed:
- tests/test_strategy_import_adapter.py

Behavior changed:
1. test_validation_error_does_not_rollback_caller_uncommitted:
   - Old: validation error → immediately caller rollback → assert cnt==0 (ambiguous: adapter OR caller could have done it).
   - New: stage prior → validation error → assert prior IS visible (cnt==1, proves adapter did NOT rollback) → caller rollback → assert cnt==0.
2. test_duplicate_uid_does_not_rollback_caller_uncommitted:
   - Old: no_commit prior → insert_strategy(auto-commit) → duplicate error → prior was already committed by step 2 (not provable).
   - New: commit source row → no_commit prior → duplicate error → assert prior IS visible (cnt==1) → caller rollback → assert prior gone (cnt==0), source row still exists (cnt==1).
3. SQLite failure rollback test unchanged.

Tests run:
- tests/test_strategy_import_adapter.py: 19 passed.
- Full suite: 1186 passed, 0 warnings.

Assumptions:
- In SQLite, an uncommitted INSERT is visible to the same connection.
- A validation error in _insert_strategy_core has no __cause__ (no sqlite3.Error), so the rollback guard is skipped.

Known risks:
- None. Tests now prove both positive (rollback happens when it should) and negative (no rollback when it shouldn't) behaviors.

Reviewer focus:
- Both tests: the key assertion is cnt==1 AFTER the error, BEFORE caller rollback — this is the proof the adapter did not interfere.
- Duplicate UID test: final assertion that committed source row still exists (cnt==1) after caller rollback.
