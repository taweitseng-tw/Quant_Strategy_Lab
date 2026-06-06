# Batch 057A-Impl + 057C-Design — Monte Carlo Bootstrap Engine and Surface Design

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057A-Impl — Bootstrap Engine

`validation_engine/monte_carlo.py`:
- `run_bootstrap_monte_carlo()` — resamples trades with replacement, 200 iterations default, 95% CI, local `random.Random()` per iteration
- `MonteCarloResult.confidence_intervals: dict | None = None` — backward-compatible

### 057C-Design

`docs/bootstrap_pipeline_report_surface_design_057C.md` — pipeline config fields, result field shape, serialization strategy, display deferral.

### Tests

| File | Tests |
|---|---|
| `test_monte_carlo.py` | 11 new bootstrap tests (deterministic, structured, zero trades, single trade, no mutation, no global RNG, invalid inputs, CI bounds, existing MC unchanged) |

## Files Changed

| File | Change |
|---|---|
| `validation_engine/monte_carlo.py` | `run_bootstrap_monte_carlo()` + `confidence_intervals` field |
| `tests/test_monte_carlo.py` | 11 new tests |
| `docs/bootstrap_pipeline_report_surface_design_057C.md` | **Created** |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
MC tests: 49 passed (38 existing + 11 new)
Full suite: 1057 passed, 1 warning
git diff --check -> passes
```

Bootstrap not wired into pipeline. No UI/report/widget/dependency changes.
