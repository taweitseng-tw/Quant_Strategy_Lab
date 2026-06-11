# Fitness Multi-Metric Weighting Design - Tasks 427-432

Design document. No production code changed.

Generated: 2026-06-11

## Current Path

Fitness ranking already exists in the engine:

- `strategy_engine/ranking.py`
  - `DEFAULT_WEIGHTS`
  - `compute_fitness(metrics, weights=None)`
  - `rank_strategies(backtest_results, weights=None)`
- `app/services/strategy_service.py`
  - `StrategyService.get_ranked_strategies()`
  - currently calls `rank_strategies(backtest_results)` with no custom weights
- `strategy_engine/ga_fitness.py`
  - `GAFitnessConfig.fitness_weights`
  - already forwards custom weights into `compute_fitness`
- `app/services/ga_service.py` and `app/services/gp_service.py`
  - already carry optional `fitness_weights`

The gap is the regular strategy service path. It still always uses the
engine default weights, so the next implementation slice should add a small
service-layer configuration surface without changing ranking formulas.

## Proposed Contract

Use the existing `strategy_engine.ranking.DEFAULT_WEIGHTS` keys:

```python
{
    "total_pnl": 0.25,
    "profit_factor": 0.25,
    "max_drawdown_pnl": 0.20,
    "avg_trade": 0.15,
    "total_trades": 0.15,
}
```

Service rules:

- `StrategyService` owns a mutable copy of `DEFAULT_WEIGHTS`.
- `get_fitness_weights()` returns a copy, not the internal dict.
- `update_fitness_weights(weights: dict)` accepts partial updates.
- Unknown keys are ignored.
- Missing keys preserve the current value.
- Numeric values are clamped to `[0.0, 1.0]`.
- Non-numeric values are ignored.
- All-zero weights are allowed and should produce fitness `0.0`, matching
  the existing engine behavior when total weight is zero.

Ranking wiring:

```python
ranked = rank_strategies(backtest_results, weights=self.fitness_weights)
```

No UI controls are part of Tasks 433-438. This keeps the next slice small and
reviewable.

## Compatibility And Safety

- Default behavior remains unchanged because the service starts from a copy of
  `DEFAULT_WEIGHTS`.
- The default is not net-profit-only; `total_pnl` remains 25 percent of the
  default weighting.
- A user or later UI can intentionally set net-profit-only weights, but that is
  an explicit configuration choice, not the default.
- Missing metrics still follow current engine behavior:
  `compute_fitness()` uses `metrics.get(dim, 0.0)`.
- Engine code remains UI-free. The service passes a primitive dict into the
  existing engine API.
- GA and GP paths should not be changed in this slice because they already
  carry optional `fitness_weights`.

## Implementation Scope For Tasks 433-438

Modify:

- `app/services/strategy_service.py`
  - import `DEFAULT_WEIGHTS`
  - add `self.fitness_weights = dict(DEFAULT_WEIGHTS)`
  - add `update_fitness_weights()`
  - add `get_fitness_weights()`
  - pass `self.fitness_weights` into `rank_strategies()`
- `tests/test_strategy_service_fitness.py`
  - create focused service tests
- `tests/test_strategy_generator.py`
  - add focused engine ranking tests only if current coverage does not already
    prove the required behavior
- `docs/task_board.md`
- `docs/changelog.md`

Do not modify:

- ranking formulas in `strategy_engine/ranking.py`
- GA/GP services unless a test proves their existing behavior regressed
- UI controls
- report output
- validation or elimination formulas

## Required Tests For Tasks 433-438

1. New `StrategyService()` exposes default weights equal to `DEFAULT_WEIGHTS`.
2. `get_fitness_weights()` returns a copy; mutating the returned dict does not
   mutate service state.
3. `update_fitness_weights()` stores a valid partial update.
4. Values above `1.0` clamp to `1.0`.
5. Values below `0.0` clamp to `0.0`.
6. Unknown keys are ignored.
7. Non-numeric values are ignored.
8. Missing keys preserve existing values.
9. `get_ranked_strategies()` passes service weights into `rank_strategies()`.
10. All-zero weights produce deterministic zero fitness through the existing
    engine path.

## Acceptance Criteria For Tasks 433-438

- Default ranking output remains backward-compatible.
- Custom service weights can change deterministic ranking order or fitness
  values in a focused test.
- No formula changes are made in `strategy_engine/ranking.py`.
- No PySide6 imports are introduced into engine code.
- Focused tests pass.
- `git diff --check` passes.
