Completed:
- Task 063D-Impl — MC Worst-Case Equity Engine and Serialization Slice.

Files changed:
- validation_engine/monte_carlo.py (worst_case_equity_curve field, collect_worst_case_equity parameter)
- app/services/validation_pipeline_service.py (_mc_to_dict serialization)
- tests/test_monte_carlo.py (5 new tests)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
1. MonteCarloResult.worst_case_equity_curve defaults to None (backward-compatible).
2. run_missed_trade_monte_carlo(collect_worst_case_equity=True) captures a trade-step equity curve for the worst iteration.
3. Worst iteration selection: lowest total_pnl → highest abs max_drawdown_pnl → lowest index.
4. Pipeline serialization includes worst_case_equity_curve only when present.

Tests run:
- MC tests: 54 passed.
- Pipeline tests: 40 passed.
- Widget + report tests: 85 passed.

Assumptions:
- Trade-step equity curve starts at initial_capital (from baseline.assumptions, default 100000).
- Surviving trades are reconstructed deterministically from the same seed used by stress_random_missed_trades.

Known risks:
- Trade-step equity curve is not a true bar-by-bar equity curve — it shows step changes at each surviving trade.
- Only run_missed_trade_monte_carlo supports collect_worst_case_equity; other MC runners do not.

Reviewer focus:
- Worst iteration selection tie-break logic.
- Trade-step equity curve computation in run_missed_trade_monte_carlo.
- Pipeline serialization conditional on None.
