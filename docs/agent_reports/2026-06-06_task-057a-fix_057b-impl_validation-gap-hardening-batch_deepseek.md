# Batch 057A-Fix + 057B-Impl — Validation Gap Hardening Batch

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057A-Fix — MC Bootstrap Design Hardening

3 corrections to `docs/monte_carlo_bootstrap_ci_design_057A.md`:

| Fix | Detail |
|---|---|
| Remove `worst_case_equity` from v0.2 schema | Deferred to v0.3; schema now has `confidence_intervals` only |
| Replace unsafe test claims | "Bootstrap always more conservative" → "metrics differ from baseline"; "95% of means in CI" → structural CI boundary check |
| Local RNG | `random.Random(base_seed + i)` per iteration, no global state mutation |

### 057B-Impl — Walk-Forward Equity Persistence

| Layer | Change |
|---|---|
| Engine | `WalkForwardWindow.equity_curve: list[float] \| None = None`; `store_equity` param (default `False`) |
| Pipeline | `PipelineConfig.wf_store_equity: bool = False`; passed to `walk_forward()`; `_wf_to_dict()` includes windows when equity present |
| Tests | 6 walk-forward + 3 pipeline config tests |

## Files Changed

| File | Change |
|---|---|
| `docs/monte_carlo_bootstrap_ci_design_057A.md` | 3 hardening fixes |
| `validation_engine/walk_forward.py` | equity_curve + store_equity |
| `app/services/validation_pipeline_service.py` | wf_store_equity config + wiring + serialization |
| `tests/test_walk_forward.py` | 6 tests |
| `tests/test_validation_pipeline_service.py` | 3 tests |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
walk_forward + pipeline: 69 passed
Full suite: 1047 passed, 1 warning
git diff --check -> passes
```

No Monte Carlo production code changed. No UI/report/chart/dependency changes.
