# Task 056E-Impl-Fix — Remove Best N Trades Deterministic Test Hardening

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### P1 Fix: Synthetic Baseline Replaces Weak Conditional-Guarded Tests

**Problem**: Core threshold tests used `_make_baseline_with_trades(200)` which produced only 1 trade. Assertions were guarded by `if baseline.metrics["total_trades"] >= 3:` and could silently pass without testing the intended behavior.

**Fix**: Replaced with `_make_synthetic_baseline(pnls)` using explicit `Trade` objects and `compute_metrics()`:

```python
def _make_synthetic_baseline(pnls: list[float]) -> BacktestResult:
    trades = [Trade(..., pnl=pnl) for pnl in pnls]
    return BacktestResult(trades=trades, metrics=compute_metrics(trades), ...)
```

### Test Changes

| Test | Before | After |
|---|---|---|
| `test_remove_best_n_trades_worsens_pnl` | `if trades >= 3:` guarded | Exact: `stressed_pnl == 20.0` |
| `test_remove_best_n_trades_exact_metrics` | *did not exist* | **New**: `degradation == -0.833333`, `pnl_loss_ratio == 0.833333` |
| `test_remove_best_n_trades_fails_above_threshold` | `if trades >= 3:` + `if pnl_loss > 0.01:` guarded | Deterministic: threshold 0.30 vs pnl_loss 0.833 → `not result.passed` |
| `test_remove_best_n_trades_passes_within_threshold` | `if trades >= 3:` guarded | Deterministic: threshold 0.99 vs pnl_loss 0.833 → `result.passed` |
| `test_remove_best_n_trades_insufficient_trades_fails` | `if trade_count > 0:` guarded | Deterministic: 2 trades, n=5 → `not result.passed` |
| All other tests | Used generated baseline | Use `_make_synthetic_baseline(...)` with known PnL values |

**No implementation changes were needed** — the engine code was already correct and produced the expected exact values.

## Files Changed

| File | Change |
|---|---|
| `tests/test_stress_test.py` | Added `Trade`/`BacktestResult`/`compute_metrics` imports, added `_make_synthetic_baseline()` helper, rewrote 10 tests with exact assertions |
| `docs/changelog.md` | Task 056E-Impl-Fix entry |
| `docs/task_board.md` | 056E-Impl-Fix → Done |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_stress_test.py -v
-> 26 passed (15 existing + 11 new)

.venv\Scripts\python.exe -m pytest -q
-> 1003 passed, 1 warning

git diff --check -> passes
```

Acceptance criteria:
1. ✅ No conditional guards that skip core assertions.
2. ✅ Deterministic synthetic baseline with known PnL values.
3. ✅ Exact assertions for `degradation["total_pnl"]` and `pnl_loss_ratio`.
4. ✅ Tight threshold fails and lenient threshold passes deterministically.
5. ✅ No pipeline, UI, report, or elimination changes.
6. ✅ Focused tests pass.
7. ✅ Full suite passes.
8. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Engine code unchanged — only test hardening.

## Suggested Next Task

Pipeline integration: Wire `stress_remove_best_n_trades()` into `app/services/validation_pipeline_service.py`.
