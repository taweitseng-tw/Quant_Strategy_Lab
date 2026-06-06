# Monte Carlo Bootstrap + Confidence Interval Design — Task 057A

> Design-only. No production code changed.

## 1. Current State

### What Exists

`validation_engine/monte_carlo.py` has three functions:

| Function | Method | Output |
|---|---|---|
| `run_missed_trade_monte_carlo` | Per-iteration random missed-trade simulation (deterministic seeds) | `MonteCarloResult(percentile_summary, worst_case, stability_score)` |
| `run_slippage_monte_carlo` | Per-iteration random slippage perturbation | Same shape |
| `run_combined_monte_carlo` | Combines both per-iteration | Same shape |

All use the same pattern: run N iterations of a stress scenario, collect raw metrics, compute percentile summaries (p5, p25, p50, p75, p95), extract worst case, and produce a `stability_score` = `p05 / abs(p50)`.

### What's Missing (PRD §12.4 Alpha)

1. **Bootstrap resampling** — resample `baseline.trades` with replacement, not just randomly drop trades.
2. **Formal confidence intervals** — 95% CI for key metrics (total_pnl, profit_factor, max_drawdown).
3. **Worst-case equity curve** — project a worst-case cumulative equity path from the bootstrap distribution.

### Design Principle

The existing MC functions operate on `stress_random_missed_trades()` at each iteration. Bootstrap is a different class of simulation — it resamples trade sequences with replacement and recomputes metrics, rather than dropping trades at random.

To avoid scope creep, bootstrap should be a **separate function** in `monte_carlo.py`, not a modification of existing functions. It should reuse the existing `MonteCarloResult` schema where possible, and add fields where needed.

## 2. Proposed Function

### 2.1 Signature

```python
def run_bootstrap_monte_carlo(
    baseline: BacktestResult,
    *,
    iterations: int = 200,
    base_seed: int = 42,
    confidence_level: float = 0.95,
    percentiles: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0),
) -> MonteCarloResult:
```

### 2.2 Input Shape

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `baseline` | `BacktestResult` | Required | Source trade list |
| `iterations` | `int` | 200 | More than existing (100) — bootstrap needs higher N for stable CI |
| `base_seed` | `int` | 42 | Deterministic; iteration i uses `random.seed(base_seed + i)` |
| `confidence_level` | `float` | 0.95 | For CI computation |
| `percentiles` | `tuple[float, ...]` | (5, 25, 50, 75, 95) | Existing convention |

### 2.3 Algorithm

```
1. Validate inputs: baseline.trades must exist, iterations > 0, confidence_level in (0,1).
2. Guard: 0 trades -> return early with warning (same as existing MC).
3. For each iteration i in 0..N-1:
   a. Set random.seed(base_seed + i).
   b. Draw len(trades) samples WITH replacement from baseline.trades.
      (Bootstrap: each original trade can appear 0, 1, or multiple times.)
   c. Recompute metrics on resampled trade list via compute_metrics().
   d. Store raw metrics dict.
4. Compute percentile summaries for each metric key (existing _build_mc_result or similar).
5. Compute 95% confidence intervals:
   - For each metric, sort raw values.
   - CI lower = percentile((1 - confidence_level)/2 * 100)
   - CI upper = percentile((1 + confidence_level)/2 * 100)
6. Compute worst-case equity curve (optional, see Section 3).
7. Return MonteCarloResult with CI fields.
```

### 2.4 Deterministic Behavior

Same pattern as existing MC: each iteration uses `random.seed(base_seed + i)`. Results are reproducible for a given baseline + seed.

### 2.5 Edge Cases

| Scenario | Behavior |
|---|---|
| Zero trades | Return early with warning, empty result |
| 1 trade | Bootstrap still valid — all resamples have 1 element |
| `iterations <= 0` | `ValueError` |
| `confidence_level` outside (0,1) | `ValueError` |

## 3. Output Shape

### 3.1 Reuse Existing `MonteCarloResult`

Existing fields preserved:

```python
MonteCarloResult(
    test_name="bootstrap",
    iterations=200,
    baseline_metrics={...},
    percentile_summary={...},
    all_metrics=[...],
    worst_case={...},
    assumptions={...},
    warnings=[...],
    stability_score=...,
)
```

### 3.2 New Fields (Additive to MonteCarloResult)

```python
# Optional CI fields — None when bootstrap is not used.
confidence_intervals: dict[str, dict[str, float]] | None = None
# Example: {"total_pnl": {"ci_lower": 1000.0, "ci_upper": 5000.0, "ci_mean": 3000.0}}

worst_case_equity: list[float] | None = None
# Example: [100000.0, 99800.0, 99600.0, ...] — worst-case equity path.
# Only computed when `project_worst_case_equity=True` (opt-in).
```

### 3.3 CI Dict Shape

```python
confidence_intervals = {
    "total_pnl": {
        "ci_lower": 1020.0,
        "ci_upper": 9840.0,
        "ci_mean": 5430.0,
        "ci_level": 0.95,
    },
    "profit_factor": { ... },
    "max_drawdown_pnl": { ... },
    "avg_trade": { ... },
    "total_trades": { ... },
}
```

## 4. Worst-Case Equity Curve (Deferred to v0.3)

PRD §12.4 mentions "95% worst-case equity curve." This requires projecting a cumulative equity path from the bootstrap distribution, which is a non-trivial visualization feature.

**Recommendation**: Do NOT include in v0.2. Defer to a dedicated design task. The bootstrap CI is valuable standalone.

## 5. Integration Points

### 5.1 Pipeline Integration (later task)

In `run_validation_pipeline()`, after existing MC:

```python
if cfg.run_bootstrap_monte_carlo:  # default False
    bootstrap_result = run_bootstrap_monte_carlo(
        baseline, iterations=cfg.bootstrap_iterations,
        base_seed=cfg.mc_base_seed,
    )
```

Stored in a new `PipelineResult` field: `bootstrap_monte_carlo_result: dict | None`.

### 5.2 Report/Display (later task)

CI values can appear in the existing MC section or a separate Bootstrap section. Design deferred to a display task.

## 6. Test Plan

| # | Test | Verifies |
|---|---|---|
| 1 | `test_bootstrap_deterministic` | Same seed = same result |
| 2 | `test_bootstrap_does_not_mutate_trades` | Original trades unchanged |
| 3 | `test_bootstrap_reduces_stability` | Bootstrap PnL is more conservative |
| 4 | `test_bootstrap_ci_within_bounds` | CI lower < CI upper |
| 5 | `test_bootstrap_ci_level_respected` | ~95% of means fall within CI |
| 6 | `test_bootstrap_zero_trades` | Returns early with warning |
| 7 | `test_bootstrap_single_trade` | Handles single trade |
| 8 | `test_bootstrap_invalid_inputs` | Negative iterations -> ValueError |
| 9 | `test_bootstrap_structured_output` | All required fields present |

## 7. Design Decisions

1. **Separate function** — not a modification of existing MC. Bootstrap is a different method.
2. **Reuse MonteCarloResult** — adds CI fields, doesn't break existing schemas.
3. **Worst-case equity deferred** — complex visualization feature; CI is the core value.
4. **200 iterations default** — bootstrap needs more iterations than missed-trade MC for stable CI.
5. **Deterministic seeds** — same pattern as existing MC for reproducibility.

## 8. Non-Goals

- Not replacing existing MC functions.
- Not changing existing MonteCarloResult schema (additive only).
- Not implementing pipeline wiring or display in this design.
- Not implementing worst-case equity curve projection.

## 9. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: None (standalone engine test)
- **Blocked by**: Nothing
