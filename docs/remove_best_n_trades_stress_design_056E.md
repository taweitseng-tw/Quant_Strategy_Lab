# Remove Best N Trades Stress Test Design — Task 056E

> Design-only. No production code changed.

## 1. Motivation

From PRD Section 12.3 (deferred stress tests):

> 移除最佳 N 筆交易 — surgically remove the strategy's best-performing trades and re-evaluate. If a strategy only passes because of 1-2 lucky outliers, this test should flag it.

This complements `stress_random_missed_trades` (which drops trades proportionally/randomly). The "remove best N" test is a **worst-case sensitivity check**: how much of the strategy's edge comes from its best trades?

## 2. Existing Stress Test Patterns

All stress tests in `validation_engine/stress_test.py` follow the same shape:

| Test | Input | Re-backtest? | Pass condition |
|---|---|---|---|
| `stress_commission_multiplier` | strategy, df, baseline | Yes | PnL doesn't improve |
| `stress_slippage_multiplier` | strategy, df, baseline | Yes | PnL doesn't improve |
| `stress_one_bar_delay` | strategy, df, baseline | Yes | PnL doesn't improve |
| `stress_random_missed_trades` | baseline | No (pure trade-list) | PnL doesn't improve |
| `stress_parameter_perturbation` | strategy, df, baseline | Yes (N variants) | PnL avg within threshold |

All return `StressTestResult(test_name, passed, baseline_metrics, stressed_metrics, degradation, assumptions, warnings, threshold)`.

Pipeline integration pattern (each stress test):
1. Call the stress function.
2. Convert to dict via `_stress_to_dict()`.
3. Append to `stress_results: list[dict]`.
4. Optional toggle in `PipelineConfig` (like `run_one_bar_delay_stress`).

## 3. Proposed Stress Test: `stress_remove_best_n_trades`

### 3.1 Function Signature

```python
def stress_remove_best_n_trades(
    baseline: BacktestResult,
    *,
    n: int = 3,
    degradation_threshold: float = 0.30,
) -> StressTestResult:
```

### 3.2 Input Shape

- `baseline: BacktestResult` — the IS backtest result with a non-empty trade list.
- `n: int = 3` — number of best trades (by PnL) to remove. Must be int >= 0.
- `degradation_threshold: float = 0.30` — max allowed PnL loss ratio before failing.

### 3.3 Input Validation

- `n` must be an int >= 0. Raise `ValueError` for negative or non-int values.
- `degradation_threshold` must be a float >= 0.0. Raise `ValueError` otherwise.

### 3.4 Algorithm

```
1. Validate inputs (n >= 0, int).
2. Guard: if baseline has 0 trades -> vacuously pass (warning).
3. Sort baseline.trades by PnL descending.
4. Remove top min(n, len(trades)) trades (the "best" trades).
5. Recompute metrics on surviving subset via compute_metrics(surviving).
6. Compute per-metric degradation using existing StressTestResult convention.
7. Compute pnl_loss_ratio for pass/fail (positive = worse, stored in assumptions).
8. Check pass/fail against degradation_threshold using pnl_loss_ratio.
```

### 3.5 Degradation Sign Convention (Corrected)

This design preserves the existing `StressTestResult.degradation` convention used by `_build_result()`:

```python
# Existing convention (same as _build_result):
degradation["total_pnl"] = (stressed_pnl - base_pnl) / abs(base_pnl)
# For profitable baselines, worse PnL is NEGATIVE here.
```

For pass/fail, a **separate** `pnl_loss_ratio` is computed (positive = worse) and stored in `assumptions`, not `degradation`:

```python
# Separate loss ratio for pass/fail (positive = worse):
pnl_loss_ratio = (base_pnl - stressed_pnl) / abs(base_pnl) if abs(base_pnl) > 1e-9 else 0.0
passed = pnl_loss_ratio <= degradation_threshold
```

This avoids confusing the existing degradation convention while keeping pass/fail logic readable.

### 3.6 Output Shape

Standard `StressTestResult`:

```python
StressTestResult(
    test_name="remove_best_n_trades",
    passed=True/False,
    baseline_metrics=baseline.metrics,
    stressed_metrics=compute_metrics(surviving),
    degradation={...},       # per-metric degradation dict (EXISTING convention)
    assumptions={
        "n": 3,
        "removed_count": 3,
        "surviving_count": 17,
        "total_baseline_count": 20,
        "pnl_loss_ratio": 0.15,  # positive = worse (separate from degradation)
    },
    warnings=[...],
    threshold={"max_pnl_loss": degradation_threshold},
)
```

### 3.7 Deterministic Behavior

This test has **no randomness** — it always removes the top N trades sorted by PnL descending. Results are fully deterministic for a given baseline trade list. No seed parameter needed.

### 3.8 Edge Cases (Corrected)

| Scenario | Behavior |
|---|---|
| `n < 0` or non-int | Raise `ValueError`: "n must be a non-negative integer." |
| `degradation_threshold < 0` | Raise `ValueError`: "degradation_threshold must be non-negative." |
| `baseline.trades` is empty | Vaporous pass with warning: "No trades to stress — baseline has zero trades." Consistent with `stress_random_missed_trades`. |
| `n == 0` | Pass (no trades removed). `removed_count=0`, `assumptions["n_zero"]=True`. |
| `0 < len(trades) <= n` | **Fail** (`passed=False`) with warning: "Insufficient trades for remove-best-n stress test (trades=X, n=Y)." Add `assumptions["insufficient_trades"]=True`. This is stricter than the original design and prevents low-trade-count strategies from receiving a free pass. |
| `abs(base_pnl) < 1e-9` | Vaporous pass (ratio is undefined). `pnl_loss_ratio=0.0` in assumptions. |

### 3.9 No Future Leak + No Mutation

- No future data is used — operates purely on the existing trade list.
- Original `baseline.trades` is **never mutated** — a new list `surviving` is constructed.

### 3.10 Pass/Fail Logic

```python
if len(surviving) == 0 and len(trades) > 0:
    # All trades were removed (0 < trades <= n).
    passed = False
elif abs(base_pnl) < 1e-9 or len(trades) == 0:
    # No meaningful PnL or no trades at all.
    passed = True
else:
    pnl_loss_ratio = (base_pnl - stressed_pnl) / abs(base_pnl)
    passed = pnl_loss_ratio <= degradation_threshold
```

## 4. Implementation Plan — Split Into Two Tasks

### 4.1 First Task: Engine-Only (Recommended Next: Task 056E-Impl)

| File | Change |
|---|---|
| `validation_engine/stress_test.py` | Add `stress_remove_best_n_trades()` function only |
| `tests/test_stress_test.py` | 9 new focused tests (see Section 5) |
| `docs/changelog.md` + `docs/task_board.md` | Standard update |

Pipeline config, pipeline wiring, and pipeline tests are deferred.

### 4.2 Later Task: Pipeline Integration (Future)

| File | Change |
|---|---|
| `app/services/validation_pipeline_service.py` | Add 3 config fields + wire into stress section |
| `tests/test_validation_pipeline_service.py` | 1-2 pipeline toggle tests |

### 4.3 Pipeline Configuration (Deferred)

```python
# Future PipelineConfig additions:
run_remove_best_n_trades_stress: bool = False  # default off
remove_best_n_trades_n: int = 3
remove_best_n_trades_degradation_threshold: float = 0.30
```

Default off because this test requires sufficient trades (> N) to be meaningful.

### 4.4 Pipeline Wiring (Deferred)

```python
# Future wiring in run_validation_pipeline():
if cfg.run_remove_best_n_trades_stress:
    n_trades_res = stress_remove_best_n_trades(
        baseline,
        n=cfg.remove_best_n_trades_n,
        degradation_threshold=cfg.remove_best_n_trades_degradation_threshold,
    )
    stress_results.append(_stress_to_dict(n_trades_res))
```

## 5. Test Plan (Task 056E-Impl)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_remove_best_n_trades_deterministic` | Same baseline produces identical results |
| 2 | `test_remove_best_n_trades_worsens_pnl` | PnL degrades (stressed_pnl <= base_pnl) |
| 3 | `test_remove_best_n_trades_fails_above_threshold` | `pnl_loss_ratio > threshold` -> `passed=False` |
| 4 | `test_remove_best_n_trades_passes_within_threshold` | `pnl_loss_ratio <= threshold` -> `passed=True` |
| 5 | `test_remove_best_n_trades_zero_trades` | Empty baseline -> vapid pass + warning |
| 6 | `test_remove_best_n_trades_insufficient_trades_fails` | `0 < trades <= n` -> `passed=False` + `insufficient_trades` in assumptions |
| 7 | `test_remove_best_n_trades_does_not_mutate_baseline` | Baseline trade list unchanged |
| 8 | `test_remove_best_n_trades_structured_output` | Result has all required fields |
| 9 | `test_remove_best_n_trades_negative_n_raises` | `n < 0` -> `ValueError` |

## 6. Design Decisions

1. **Engine-only first** — the immediate implementation covers only `stress_test.py` + tests + docs. Pipeline wiring is a separate later task.
2. **Operates on trade list only** (no re-backtest) — same pattern as `stress_random_missed_trades`, low computation cost.
3. **Separate `pnl_loss_ratio` for pass/fail** — stored in `assumptions`, not `degradation`, to avoid conflicting with the existing `_build_result()` sign convention where `degradation = (stressed - base) / abs(base)`.
4. **Conservative low-trade-count behavior** — `0 < trades <= n` fails instead of vacuously passing, preventing low-trade-count strategies from inflating their `min_stress_pass_rate`.
5. **Default off** in pipeline — the test needs enough trades to be meaningful; deferred to a later pipeline integration task.

## 7. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06 (revised 2026-06-06)
- **Dependencies**: None (standalone engine test)
- **Blocked by**: Nothing
