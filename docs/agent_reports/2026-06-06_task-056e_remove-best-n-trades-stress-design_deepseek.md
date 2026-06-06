# Task 056E — Remove Best N Trades Stress Test Design Only

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Design for `stress_remove_best_n_trades()`

Created `docs/remove_best_n_trades_stress_design_056E.md` covering:

| Design Aspect | Decision |
|---|---|
| **Function name** | `stress_remove_best_n_trades(baseline, *, n=3, degradation_threshold=0.30)` |
| **Input** | `baseline: BacktestResult` (trade-list only, no re-backtest) |
| **Output** | `StressTestResult` (same schema as all existing stress tests) |
| **Algorithm** | Sort trades by PnL descending, remove top N, recompute metrics via `compute_metrics()` |
| **Pass/fail** | Degradation threshold: `(base_pnl - stressed_pnl) / abs(base_pnl) <= 0.30` |
| **Determinism** | Fully deterministic — no randomness, always removes top N by PnL |
| **Edge: 0 trades** | Vapid pass with warning |
| **Edge: n > trade count** | Remove all trades, vapid pass with warning |
| **No mutation** | Original `baseline.trades` never modified |
| **Pipeline config** | 3 new fields: `run_remove_best_n_trades_stress: bool = False`, `remove_best_n_trades_n: int = 3`, `remove_best_n_trades_degradation_threshold: float = 0.30` |
| **Default off** | Conservative; test only meaningful with sufficient trades |

### Key Design Decisions

1. **Engine-only** — no re-backtest needed; operates on existing trade list like `stress_random_missed_trades`.
2. **Degradation threshold** instead of "PnL must not improve" — removing best trades always worsens PnL, so a threshold provides useful granularity.
3. **Default off in pipeline** — the test needs >N trades to be meaningful; turning it on by default would produce spurious warnings for low-trade-count strategies.

### Test Plan (8 cases for implementation)

- Deterministic output
- PnL degradation confirmed
- Fail above threshold
- Pass within threshold
- Zero trades → vapid pass
- n > trade count → vapid pass
- Does not mutate baseline
- Structured output fields present

## Files Changed

| File | Change |
|---|---|
| `docs/remove_best_n_trades_stress_design_056E.md` | **Created** — full design note |
| `docs/changelog.md` | Task 056E entry |
| `docs/task_board.md` | 056E -> Done |

## Verification

- **No production code changed** (design-only).
- **`git diff --check`**: passes.
- **Git status**: Dirty only with expected docs files.

## Known Issues

- None.

## Risks

- None (design-only).

## Suggested Next Task

**Task 056E-Impl — Remove Best N Trades Stress Test Implementation** as scoped in `docs/remove_best_n_trades_stress_design_056E.md`:

- `validation_engine/stress_test.py`: Add `stress_remove_best_n_trades()` (engine-only, no pipeline wiring yet).
- `tests/test_stress_test.py`: 8 focused tests.
- `docs/changelog.md` + `docs/task_board.md`.
