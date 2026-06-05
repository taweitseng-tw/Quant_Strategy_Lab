# Task 043A: Walk-forward Enhancements Design

## 1. Goal
Design safe v0.2 enhancements for the walk-forward validation layer. The enhancements must preserve existing deterministic behavior, remain compatible with the `WalkForwardResult` schema, and introduce zero future leaks.

## 2. Proposed Enhancements

### Enhancement A: Configurable Pass Criteria
**Current Behavior:** A window "passes" if `bt.metrics.get("total_pnl", 0.0) > 0`.
**Enhancement:** Allow users to pass a dictionary of minimum metric thresholds to `walk_forward`.
- **Implementation:** Add parameter `pass_criteria: dict[str, float] | None = None`.
- **Backward Compatibility:** If `None`, defaults to `{"total_pnl": 1e-9}` (effectively > 0).
- **Result Output:** Recorded in `WalkForwardResult.assumptions["pass_criteria"]`.

### Enhancement B: Stability Score across Windows
**Current Behavior:** Aggregates min/max/mean/median, but lacks a single cross-window stability metric.
**Enhancement:** Compute the signal-to-noise ratio of window PnLs.
- **Implementation:** Add `stability_score: float | None = None` to `WalkForwardResult`.
- **Calculation:** `mean(window_pnls) / std_dev(window_pnls)`. If `std_dev` is 0, return `None`.
- **Backward Compatibility:** Defaults to `None` if zero windows or std dev is 0.

### Enhancement C: Matrix Robustness Score
**Current Behavior:** `walk_forward_matrix` identifies the "best" and "worst" config based on pass rate, but doesn't score the overall matrix.
**Enhancement:** Add an overall matrix robustness score representing the percentage of configurations that passed a minimum threshold.
- **Implementation:** Add `matrix_robustness_score: float | None = None` to `WalkForwardMatrixSummary`. Add `robustness_pass_threshold: float = 0.5` parameter to `walk_forward_matrix`.
- **Calculation:** `sum(1 for cfg in tested if cfg.pass_rate >= robustness_pass_threshold) / len(tested)`.
- **Backward Compatibility:** Value defaults to `0.0` or `None` if `tested_count == 0`.

### Enhancement D: Walk-Forward Efficiency (WFE) Calculation
**Current Behavior:** Backtests are only run on the `test_seg`, keeping performance fast.
**Enhancement:** Add an optional flag to run the backtest on the `train_seg` to compute Walk-Forward Efficiency (bar-normalized out-of-sample PnL divided by bar-normalized in-sample PnL).
- **Implementation:** Add `calc_wfe: bool = False` to `walk_forward`.
- **Result Output:** 
  - Add `train_metrics: dict = field(default_factory=dict)` and `wfe: float | None = None` to `WalkForwardWindow`.
  - Add `average_wfe: float | None` to `WalkForwardResult.aggregate_metrics` (or directly onto result).
- **Backward Compatibility:** Default is `calc_wfe=False`, meaning no extra backtest runs, `train_metrics` remains empty, and performance is completely unaffected.

## 3. Exact New Fields
**WalkForwardWindow:**
- `train_metrics: dict = field(default_factory=dict)`
- `wfe: float | None = None`

**WalkForwardResult:**
- `stability_score: float | None = None`

**WalkForwardMatrixSummary:**
- `matrix_robustness_score: float | None = None`

## 4. No-Future-Leak Constraints
- The test segment bounds must remain strictly `start = train_end + 1` and `end = test_start + test_bars - 1`.
- The `calc_wfe` train segment backtest must be completely isolated and must not carry state forward to the test segment backtest. Both must start from clean states independently.

## 5. Performance Constraints
- If `calc_wfe=False` (the default), `walk_forward` must not perform any additional backtests. Time complexity remains identical.
- Mean/Std calculations for `stability_score` must use efficient native math on the already-collected metrics array (no re-runs).

## 6. Test Plan
- `test_wf_configurable_pass_criteria`: Verify passing `{"profit_factor": 1.5}` fails windows with PF < 1.5 even if PnL > 0.
- `test_wf_stability_score`: Verify correct calculation of mean/std on known PnL outputs. Verify `None` when std is 0.
- `test_wf_matrix_robustness_score`: Verify a matrix with 3 passed configs and 1 failed config yields `0.75`.
- `test_wf_calc_wfe_false`: Verify `run_backtest` is called `N` times (once per window) and `train_metrics` is empty.
- `test_wf_calc_wfe_true`: Verify `run_backtest` is called `2N` times (train + test per window), and `wfe` is correctly computed using bar-normalized PnL.
