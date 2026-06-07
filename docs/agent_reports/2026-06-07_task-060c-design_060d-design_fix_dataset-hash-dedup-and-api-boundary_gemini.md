Completed:
- Batch 060C-Design + 060D-Design Fix — Dataset hash dedup key, API boundary cleanup, coordinator timing resolution.

Files changed:
- docs/dataset_import_adapter_insert_only_design_060D.md
- docs/strategy_import_adapter_transaction_boundary_design_060C.md
- docs/changelog.md

Behavior changed (design-only, no code changed):
1. Dataset adapter dedup key: (name, symbol, timeframe) → snapshot_hash (SHA-256 from manifest). Fallback (symbol, timeframe, source_path) for current schema. Schema prerequisite explicitly documented.
2. Dataset DTO now includes snapshot_hash field. Coordinator timing resolved to Option A (deterministic final path before DB insert, file move after commit). Section 8/9 contradiction removed.
3. Strategy adapter API cleaned: no commit=False parameter. Two distinct methods: insert_strategy() (auto-commit) and insert_strategy_no_commit() (coordinator-only, no commit). _insert_strategy_core() as shared private.

Tests run:
- Full suite: 1179 passed, 0 warnings (unchanged).

Assumptions:
- snapshot_hash requires a schema migration (add column) for strict dedup. The adapter will use fallback key until migration is done.
- Deterministic final path (data/imported/<exp>/ohlcv.csv) is known before any DB write, enabling the chosen coordinator timing.

Known risks:
- Without schema migration, fallback dedup by (symbol, timeframe, source_path) cannot detect content-identical datasets from different archives.
- Move-failure-after-commit gap (strategy + dataset row exists, file missing) is acknowledged MVP risk.

Reviewer focus:
- 060D section 4 (snapshot_hash dedup key + fallback + schema prerequisite).
- 060D section 8 (Option A coordinator timing — deterministic path before insert).
- 060C section 3 (Option B clean API — no commit=False parameter, three-method split).
- 060C section 5 (backward compatibility — only coordinator uses new method).
