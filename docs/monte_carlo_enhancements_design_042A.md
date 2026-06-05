# Task 042A — Monte Carlo Enhancements Design

## 1. Overview
The current Monte Carlo engine (`validation_engine/monte_carlo.py`) provides foundational robustness checks via random missed trades and slippage perturbations. This design outlines safe enhancements that fit into the existing architecture without mutating the baseline `BacktestResult`, while maintaining strict determinism.

## 2. Proposed Enhancements

### Enhancement 1: Configurable Confidence Levels
Currently, the Monte Carlo module hardcodes percentiles to `("p5", "p25", "p50", "p75", "p95")`.
**Design:**
- Accept an optional `percentiles: tuple[float, ...]` parameter defaulting to `(5.0, 25.0, 50.0, 75.0, 95.0)`.
- The `percentile_summary` dictionary keys will be dynamically formatted as `f"p{int(p)}"` (e.g., `"p5"`).
- `worst_case` logic will dynamically select the minimum percentile for PnL/win rate and the maximum percentile for drawdown metrics.

### Enhancement 2: Combined Missed-Trade + Slippage Simulation (Noise Injection)
Currently, `run_missed_trade_monte_carlo` and `run_slippage_monte_carlo` are separate. Combining them subjects a strategy to both market execution noise and signal miss noise simultaneously.
**Design:**
- Add `run_combined_monte_carlo(strategy, df, baseline, ..., miss_probability, base_slippage_ticks, perturbation_pct)`.
- **Implementation:** In each iteration, first run `run_backtest(...)` with randomized slippage. Then pass the resulting `BacktestResult` to `stress_random_missed_trades(...)`. 
- **Determinism:** Seed the RNG with `base_seed + i` for both the slippage factor generation and the missed-trade stress test.

### Enhancement 3: Stability Score
A single scalar value summarizing the robustness of the strategy under Monte Carlo testing.
**Design:**
- Define `stability_score = p05_total_pnl / abs(p50_total_pnl)` (or similar conservative ratio). A score near 1.0 means high stability; near 0.0 or negative means the strategy collapses under worst-case noise.
- **Output:** Add `stability_score: float | None = None` to the `MonteCarloResult` dataclass.

## 3. Data Structures & Output Fields

The `MonteCarloResult` dataclass in `validation_engine/monte_carlo.py` will be extended as follows:
```python
@dataclass
class MonteCarloResult:
    # Existing fields...
    test_name: str
    iterations: int
    baseline_metrics: dict = field(default_factory=dict)
    percentile_summary: dict = field(default_factory=dict)
    all_metrics: list[dict] = field(default_factory=list)
    worst_case: dict = field(default_factory=dict)
    assumptions: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    
    # New fields:
    percentiles_used: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0)
    stability_score: float | None = None
```

## 4. Deterministic Seed Behavior
- All randomization must use standard library `random.Random(seed)` or `numpy.random.default_rng(seed)`.
- The seed for iteration `i` must always be `base_seed + i`.
- This ensures that re-running `run_combined_monte_carlo(..., base_seed=42)` yields the exact same metric distributions across runs.

## 5. Non-Mutation Guarantees
- The `baseline: BacktestResult` passed into the functions must never be modified. 
- The existing `run_backtest` generates a new `BacktestResult`.
- The existing `stress_random_missed_trades` creates a new `StressTestResult` by filtering a copy of the trades list, leaving the baseline trades untouched.

## 6. Performance Constraints
- Monte Carlo iterations will evaluate metrics on up to 1,000 backtest runs.
- `stress_random_missed_trades` is fast because it bypasses engine replay and simply filters existing trades and calls `compute_metrics()`.
- `run_combined_monte_carlo` requires full backtest replay for slippage perturbation. It must use the optimized `run_backtest` and is expected to take $O(iterations \times bars)$ time. Default iterations for combined MC should be kept conservative (e.g., 50 or 100) to maintain sub-second response times in the UI.

## 7. Test Plan
- `test_monte_carlo_configurable_percentiles`: Verify passing custom percentiles generates matching dict keys.
- `test_combined_monte_carlo_runs_correctly`: Verify `run_combined_monte_carlo` returns `iterations` metrics.
- `test_combined_monte_carlo_is_deterministic`: Verify exact match of `percentile_summary` when using the same `base_seed`.
- `test_combined_monte_carlo_does_not_mutate_baseline`: Verify `baseline.metrics` and `baseline.trades` remain completely unchanged.
- `test_stability_score_calculation`: Verify `stability_score` correctly computes the ratio of p5 to p50 PnL.
