Completed:
- Batch 060C-Design + 060D-Design — StrategyRepoAdapter Transaction Boundary Refactor Design and DatasetRepoAdapter Insert-Only Slice Design.

Files changed:
- docs/strategy_import_adapter_transaction_boundary_design_060C.md (created)
- docs/dataset_import_adapter_insert_only_design_060D.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
- No production code changed (design-only batch).
- 060C: StrategyRepoAdapter auto-commit removed via Option B (no-commit split). Backward-compatible. Migration path defined.
- 060D: DatasetRepoAdapter defined with ImportDatasetDTO, duplicate-reject by (name, symbol, timeframe), no-overwrite semantics.

Tests run:
- Full suite: 1179 passed, 0 warnings (unchanged).

Assumptions:
- Option B (no-commit split) preserves backward compatibility for existing UI callers.
- Dataset dedup key (name, symbol, timeframe) is available from archive manifest at import time.
- Coordinator first pass will use no-commit variant and manage transaction externally.

Known risks:
- Existing StrategyRepository UI callers are unchanged by the refactor — no risk.
- Dataset normalized_path may reference a nonexistent file if final move fails after DB commit (already acknowledged MVP gap).

Reviewer focus:
- 060C section 4 (Option B recommendation) and section 5 (backward compatibility).
- 060D section 4 (dedup key comparison and recommendation).
- 060D section 9 (coordinator integration — normalized_path timing).
