# Task 056E-Fix — Remove Best N Trades Stress Test Design Hardening

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### P1 Fixes: Degradation Sign + Implementation Scope

**Degradation sign conflict**: The original design used `(base_pnl - stressed_pnl) / abs(base_pnl)` for pass/fail — a positive-means-worse ratio. The existing `_build_result()` convention is `degradation = (stressed - base) / abs(base)` where worse PnL is negative. Mixing the two would confuse reports, tests, and elimination.

**Fix**: Pass/fail now uses a separate `pnl_loss_ratio` stored in `assumptions` (positive = worse). The `degradation` dict preserves the existing `(stressed - base) / abs(base)` convention.

**Implementation scope**: The original design listed pipeline wiring in the same implementation surface while claiming "engine-only first."

**Fix**: Section 4 now explicitly splits into two tasks:
- Task 056E-Impl (engine-only): `stress_test.py` + `tests/test_stress_test.py` + docs
- Future pipeline integration: `validation_pipeline_service.py` + config + tests

### P2 Fix: `0 < trades <= n` Now Fails

- Before: vapid pass with warning.
- After: explicit fail (`passed=False`) with `assumptions["insufficient_trades"]=True` and warning. Prevents low-trade-count strategies from receiving a free pass in `min_stress_pass_rate`.

### P3 Fix: Typo

Removed `degration_threshold` in deferred pipeline wiring example — corrected to `degradation_threshold`.

### Additional Hardening

- Added `ValueError` for `n < 0` or non-int.
- Added `ValueError` for `degradation_threshold < 0`.
- Added `n == 0` edge case: pass with `assumptions["n_zero"]=True`.
- Updated test plan from 8 to 9 cases (added `test_remove_best_n_trades_negative_n_raises`).

## Files Changed

| File | Change |
|---|---|
| `docs/remove_best_n_trades_stress_design_056E.md` | **Revised** — degradation sign, scope split, edge cases, typo fix, input validation |
| `docs/changelog.md` | Task 056E-Fix entry |
| `docs/task_board.md` | 056E-Fix -> Done |
| `docs/agent_reports/2026-06-06_task-056e-fix_remove-best-n-trades-stress-design-hardening_deepseek.md` | **Created** |

## Verification

- **No production code changed** (design-only hardening).
- **`git diff --check`**: passes.
- **Engine/UI separation preserved**: corrected design uses separate `pnl_loss_ratio` for pass/fail, preserving existing `degradation` convention.
- **Git status**: Dirty only with expected docs files.

## Known Issues

- None.

## Risks

- None (design-only task).

## Suggested Next Task

**Task 056E-Impl — Remove Best N Trades Stress Test Implementation (engine-only)**:

```
validation_engine/stress_test.py: Add stress_remove_best_n_trades()
tests/test_stress_test.py: 9 focused tests
docs/changelog.md + docs/task_board.md: Standard update
```

Full corrected design in `docs/remove_best_n_trades_stress_design_056E.md`.
