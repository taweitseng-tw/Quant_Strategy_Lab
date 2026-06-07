Completed:
- Batch 060C-Design + 060D-Design Fix — Snapshot hash schema boundary and next batch alignment.

Files changed:
- docs/dataset_import_adapter_insert_only_design_060D.md
- docs/strategy_import_adapter_transaction_boundary_design_060C.md
- docs/task_board.md
- docs/changelog.md

Behavior changed (design-only, no code changed):
1. Dataset adapter: strict two-mode separation. Mode A (current schema) never queries snapshot_hash column. Mode B (post-migration) requires column to exist. Test plan split into current-schema tests (implementable now) and post-migration tests (skip until migration).
2. Next batch unified across all docs to: 060E-Impl + 060F-Design - StrategyRepoAdapter Transaction Refactor Implementation + Dataset Snapshot Hash Schema Migration Design.
3. No coordinator implementation. No DatasetRepoAdapter implementation.

Tests run:
- Full suite: 1179 passed, 0 warnings (unchanged).

Assumptions:
- Mode A is implementable immediately with current schema. Mode B requires separate migration.
- The adapter probes schema at init time (self._has_snapshot_hash) to decide which mode.

Known risks:
- Fallback dedup by (symbol, timeframe, source_path) cannot detect content-identical datasets from different archives until schema migration is done.

Reviewer focus:
- 060D section 4 (Two-Mode Design — strict separation, no non-existent column queries).
- 060D section 10 (test split: Mode A vs Mode B).
- Next batch consistency across 060C, 060D, task_board, changelog.
