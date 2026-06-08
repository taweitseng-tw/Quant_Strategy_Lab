Completed:
- Batch 062D-Impl + 062E-Design — Price-Noise Stress Test Engine Slice and WF Equity Widget Implementation Contract.

Files changed:
- validation_engine/stress_test.py (stress_price_noise function)
- tests/test_stress_test.py (6 tests)
- docs/wf_equity_widget_implementation_contract_062E.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. stress_price_noise() implemented with Gaussian OHLC perturbation, deterministic seeds, pnl_degradation_ratio pass/fail. OHLC constraint warning emitted.
2. 6 focused tests cover structure, determinism, zero-noise rejection, perturbation visibility, baseline PnL warning, invalid parameter rejection.
3. 062E design defines widget implementation plan.

Tests run:
- Stress tests: 32 passed.
- Pipeline tests: 35 passed.
- Full suite: 1242 passed.

Assumptions:
- price_noise is not wired into the pipeline yet — engine-only.
- WF equity chart uses existing PySide6 QGraphicsView (no new dependency).

Known risks:
- OHLC constraints may be violated after noise — documented as warning.
- Long-running tests (iterations * backtest) could be slow with large iterations.

Reviewer focus:
- stress_price_noise(): local numpy Generator per iteration, no global state mutation.
- Degradation ratio: (avg_noise_pnl - base_pnl) / abs(base_pnl).
- Pass/fail threshold: degradation >= -0.2 (PnL does not drop below 80% of baseline).

Codex correction:
- Original 062D implementation was not accepted as-is because it contradicted `docs/price_noise_stress_contract_062B.md`.
- Corrected behavior must preserve OHLC invariants through body/wick reconstruction, accept `noise_pct=0` as identity, and define `pnl_degradation_ratio` as `median_total_pnl / baseline_pnl` only when baseline PnL is positive.
- See `docs/review_notes/2026-06-08_task-062d-impl_062e-design_price-noise-engine-and-wf-equity-widget-contract_codex-review.md`.
