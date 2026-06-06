# Task 056E-Impl — Remove Best N Trades Stress Test Engine Implementation

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### `stress_remove_best_n_trades()` (`validation_engine/stress_test.py`)

Added engine-only stress test function:

```python
def stress_remove_best_n_trades(
    baseline: BacktestResult,
    *,
    n: int = 3,
    degradation_threshold: float = 0.30,
) -> StressTestResult:
```

**Algorithm**: Sort trades by PnL descending, remove top N, recompute metrics via `compute_metrics()`. No re-backtest. No randomness.

**Key design decisions implemented**:
1. **Degradation sign**: Preserves `(stressed - base) / abs(base)` convention from `_build_result()`.
2. **Pass/fail**: Uses separate `pnl_loss_ratio` in `assumptions` (positive = worse).
3. **No mutation**: `baseline.trades` never modified — new `surviving` list created.
4. **Edge cases**: Zero trades (vaporous pass), `0 < trades <= n` (`passed=False` + `assumptions["insufficient_trades"]=True`), `n == 0` (pass + `assumptions["n_zero"]=True`), non-positive base PnL (vaporous pass).
5. **Input validation**: `ValueError` for negative/non-int `n`, negative `degradation_threshold`, bool `n`.

### Tests (`tests/test_stress_test.py`)

10 new focused tests:

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_remove_best_n_trades_deterministic` | Same baseline produces identical results |
| 2 | `test_remove_best_n_trades_worsens_pnl` | stressed PnL <= baseline PnL |
| 3 | `test_remove_best_n_trades_fails_above_threshold` | tight threshold causes fail |
| 4 | `test_remove_best_n_trades_passes_within_threshold` | lenient threshold passes |
| 5 | `test_remove_best_n_trades_zero_trades` | empty baseline -> vapid pass |
| 6 | `test_remove_best_n_trades_insufficient_trades_fails` | 0 < trades <= n -> fail |
| 7 | `test_remove_best_n_trades_does_not_mutate_baseline` | baseline unchanged |
| 8 | `test_remove_best_n_trades_structured_output` | all fields present |
| 9 | `test_remove_best_n_trades_negative_n_raises` | n < 0 -> ValueError |
| 10 | `test_remove_best_n_trades_negative_threshold_raises` | threshold < 0 -> ValueError |

## Files Changed

| File | Change |
|---|---|
| `validation_engine/stress_test.py` | Added `stress_remove_best_n_trades()` function |
| `tests/test_stress_test.py` | Added 10 focused tests |
| `docs/changelog.md` | Task 056E-Impl entry |
| `docs/task_board.md` | 056E-Impl -> Done |
| `docs/agent_reports/2026-06-06_task-056e-impl_remove-best-n-trades-stress-engine-implementation_deepseek.md` | **Created** |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_stress_test.py -v
-> 25 passed (15 existing + 10 new)

.venv\Scripts\python.exe -m pytest -q
-> 1002 passed, 1 warning

git diff --check -> passes
```

Acceptance criteria:
1. ✅ `stress_remove_best_n_trades()` exists and returns `StressTestResult`.
2. ✅ Does not mutate `baseline.trades`.
3. ✅ Preserves existing `degradation` sign convention.
4. ✅ `pnl_loss_ratio` in `assumptions`, not in `degradation["total_pnl"]`.
5. ✅ Low-trade-count behavior matches accepted design.
6. ✅ No pipeline, UI, report, or elimination changes.
7. ✅ Focused tests pass.
8. ✅ Full suite passes.
9. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Engine-only function, no pipeline wiring.

## Suggested Next Task

**Pipeline integration deferred task**: Wire `stress_remove_best_n_trades()` into `app/services/validation_pipeline_service.py` with `PipelineConfig` fields and toggle tests.
