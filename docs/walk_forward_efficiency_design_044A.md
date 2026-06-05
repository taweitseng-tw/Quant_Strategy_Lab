# Task 044A: Walk-Forward Efficiency (WFE) Design

## 1. Goal
Design a safe, no-future-leak implementation plan for Walk-Forward Efficiency (WFE). WFE compares Out-of-Sample (OOS) performance against In-Sample (IS) performance per walk-forward window, providing a robustness metric indicating how well a strategy's historical performance holds up in unseen data. 
WFE is strictly a diagnostic tool; it does not indicate absolute live trading readiness, nor should it substitute holistic validation.

## 2. Definitions & Formula

**WFE Denominator Rule (Conservative - Option B):**
- **Formula:** `per_window_wfe = test_total_pnl / train_total_pnl`
- **Condition:** Calculated *only* when `train_total_pnl > 1e-9` (strictly positive and non-microscopic) and `test_total_pnl` is present.
- **Undefined WFE (`None`):** WFE is defined as `None` if any of the following are true:
  1. `train_total_pnl` is missing.
  2. `train_total_pnl <= 1e-9` (zero, negative, or near-zero floating point artifact).
  3. `test_total_pnl` is missing.
- **Justification for Option B:** A negative or zero IS PnL indicates the strategy failed on the training data. If it subsequently makes money in the OOS test data, calculating a ratio (e.g., using `abs(train_total_pnl)`) yields a mathematically positive WFE that gives a false sense of "robustness." In reality, the strategy behavior completely inverted between regimes. Treating WFE as `None` for failed IS windows prevents misleadingly "clean-looking" metrics for broken strategies, aligning with the project's strict anti-overfitting directives.

**Aggregate WFE Metrics (for all windows in a Walk-Forward run):**
- `average_wfe`: Arithmetic mean of all defined (`not None`) window WFEs. `None` if `defined_wfe_count == 0`.
- `median_wfe`: Median of all defined window WFEs. `None` if `defined_wfe_count == 0`.
- `defined_wfe_count`: Integer count of windows with a valid WFE.
- `undefined_wfe_count`: Integer count of windows with WFE = `None`.

*(Note: While some platforms bar-normalize PnL for WFE, the user's standard here is absolute total PnL. Bar-normalization might be added later if needed, but for MVP, we stick to the provided `test_total_pnl / train_total_pnl`).*

## 3. Data Structure Changes

No existing structures are mutated or removed. The following fields will be added:

**In `WalkForwardWindow` (dataclass in `walk_forward.py`):**
- `train_metrics: dict = field(default_factory=dict)` (Full metrics dict from the train backtest)
- `wfe: float | None = None`

**In `WalkForwardResult` (dataclass in `walk_forward.py`):**
- `average_wfe: float | None = None`
- `median_wfe: float | None = None`
- `defined_wfe_count: int = 0`
- `undefined_wfe_count: int = 0`

**In `walk_forward()` function signature:**
- `calc_wfe: bool = False` (Must default to `False`).

## 4. Execution & No-Future-Leak Guarantees

- **Opt-in Only:** `calc_wfe` defaults to `False`. If `False`, the train backtest is entirely skipped, maintaining byte-for-byte exact behavior and performance.
- **Strict Isolation:** When `calc_wfe=True`, the engine must run `run_backtest(strategy, train_seg)` and `run_backtest(strategy, test_seg)` independently as separate `BacktestResult` objects.
- **No State Carryover:** The two backtests share no engine state, portfolio state, or cache.
- **No Feedback Loop:** 
  - `test_seg` results cannot influence `train_metrics` because they run independently and temporally sequentially.
  - The `train_metrics` must **not** influence whether the test backtest is executed. The `test_seg` backtest is executed unconditionally for the window, ensuring unbiased test metrics regardless of IS performance.
- **No Side Effects on Core Logic:**
  - `train_metrics` and WFE must **never** affect the window's `passed` boolean flag or the overall `pass_rate`. Pass criteria must continue to operate exclusively on OOS `test_metrics`.
  - WFE must **never** affect `walk_forward_matrix` best/worst configuration selection. Selection remains tied strictly to OOS `pass_rate`.

## 5. Performance Risks & Mitigation

- **Risk:** Calculating WFE requires running a full backtest on the `train_seg`, effectively doubling the number of backtest calls per walk-forward matrix iteration if `test_bars` and `train_bars` are similar in size.
- **Mitigation:** `calc_wfe` is `False` by default. It is an opt-in calculation only utilized when a user explicitly requests WFE reporting. In the default `PipelineConfig` and matrix orchestrations, it remains disabled.

## 6. Future Compatibility Needs

- **`validation_pipeline_service.py`:** The `_wf_to_dict` function must be updated to serialize the new aggregate WFE fields (`average_wfe`, `median_wfe`, `defined_wfe_count`, `undefined_wfe_count`) to ensure they flow through to the UI and reports.
- **`reports/generator.py`:** While currently unaffected, WFE fields can eventually be rendered safely in the `_format_markdown_validation` and `_format_html_validation` logic, as long as it handles nullable types gracefully.

## 7. Implementation Test Plan

Future implementation (Task 044B) must satisfy these tests:

1. **Test Default Disabled Behavior (`test_wf_wfe_disabled`)**
   - Verify `calc_wfe=False` results in `wfe=None` and empty `train_metrics` for all windows.
   - Verify `run_backtest` is only called `N` times for `N` windows.
2. **Test Calculation Correctness (`test_wf_wfe_calculation`)**
   - Verify `wfe` correctly calculates `test_total_pnl / train_total_pnl`.
   - Verify `WalkForwardResult` correctly populates `average_wfe`, `median_wfe`, `defined_wfe_count`, and `undefined_wfe_count`.
3. **Test Zero/Missing/Negative IS PnL (`test_wf_wfe_undefined_conditions`)**
   - Verify if `train_total_pnl` is 0, negative, or `< 1e-9`, `wfe=None`.
   - Verify the `average_wfe` and `median_wfe` ignore `None` values and do not crash.
   - Verify `undefined_wfe_count` increments correctly.
4. **Test Complete Failure (`test_wf_wfe_all_none`)**
   - Verify `average_wfe=None` and `median_wfe=None` if every single window results in `wfe=None`.
5. **Test Matrix Independence (`test_wf_matrix_ignores_wfe`)**
   - Verify matrix `best_pass_rate_config` logic remains identical whether WFE is calculated or not.
