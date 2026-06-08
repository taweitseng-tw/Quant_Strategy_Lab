Completed:
- Batch 062F-Impl + 062G-Design — Price-Noise Pipeline Integration and WF Equity Widget Test Contract.

Files changed:
- app/services/validation_pipeline_service.py (import + config + wiring)
- tests/test_validation_pipeline_service.py (5 tests)
- docs/wf_equity_widget_test_contract_062G.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. PipelineConfig now has 4 price-noise fields (all default off).
2. When `run_price_noise_stress=True`, price-noise stress result is appended after remove-best-N stress.
3. 5 pipeline tests: default off, opt-in includes, config snapshot, deterministic, explicit off.
4. 062G design: chart visibility rules, color/label expectations, 7 focused tests, next batch.

Tests run:
- Pipeline tests: 40 passed.
- Stress tests: 34 passed.

Assumptions:
- Price-noise stress uses `split.train` DataFrame (same as other stress tests).
- Determinism holds across same seed/config — verified by test.

Known risks:
- Price-noise iterations can be slow for large datasets — default is 50.
- No UI controls for price-noise yet.

Reviewer focus:
- PipelineConfig fields (default off).
- Wire position: after remove-best-N, before Monte Carlo.
- 062G chart visibility rules (when to show/hide).

Codex correction:
- Added missing assertions for `pnl_degradation_ratio`, `survival_rate`, and `research_only=True`.
- Added explicit-off coverage and tightened deterministic comparison to the full `price_noise` stress dict.
- Rewrote `docs/wf_equity_widget_test_contract_062G.md` visibility values from ambiguous symbols to explicit `Yes` / `No`.
