# Task 056F — Remove Best N Trades Pipeline Integration

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Pipeline Wiring (`app/services/validation_pipeline_service.py`)

1. **Import**: Added `stress_remove_best_n_trades` to stress test imports.
2. **Config fields** (all default off):
   - `run_remove_best_n_trades_stress: bool = False`
   - `remove_best_n_trades_n: int = 3`
   - `remove_best_n_trades_degradation_threshold: float = 0.30`
3. **Wiring** (after parameter perturbation, before Monte Carlo):
   ```python
   if cfg.run_remove_best_n_trades_stress:
       n_trades_res = stress_remove_best_n_trades(
           baseline, n=cfg.remove_best_n_trades_n,
           degradation_threshold=cfg.remove_best_n_trades_degradation_threshold,
       )
       stress_results.append(_stress_to_dict(n_trades_res))
   ```

### Pipeline Tests (`tests/test_validation_pipeline_service.py`)

| Test | What it verifies |
|---|---|
| `test_remove_best_n_trades_not_included_by_default` | Default config omits the test; flag is `False` |
| `test_remove_best_n_trades_included_when_enabled` | Opt-in config appends the result with `test_name`, `passed`, `stressed_metrics` |
| `test_remove_best_n_trades_config_fields_in_snapshot` | Config snapshot records all 3 fields |

## Files Changed

| File | Change |
|---|---|
| `app/services/validation_pipeline_service.py` | Import + 3 config fields + stress wiring |
| `tests/test_validation_pipeline_service.py` | 3 pipeline integration tests |
| `docs/changelog.md` | Task 056F entry |
| `docs/task_board.md` | 056F → Done |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py tests/test_stress_test.py -v
-> 47 passed (21 pipeline + 26 stress)

.venv\Scripts\python.exe -m pytest -q
-> 1006 passed, 1 warning

git diff --check -> passes
```

Acceptance criteria:
1. ✅ Default pipeline output unchanged — no `remove_best_n_trades` unless opted in.
2. ✅ Opt-in appends exactly one `remove_best_n_trades` stress result.
3. ✅ Result serialized through existing `_stress_to_dict()`.
4. ✅ No UI/report/elimination changes.
5. ✅ Focused tests pass.
6. ✅ Full suite passes.
7. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Default off, opt-in only. Existing pipeline behavior completely unchanged.
