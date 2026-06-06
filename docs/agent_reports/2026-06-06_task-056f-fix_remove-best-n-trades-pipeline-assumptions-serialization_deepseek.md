# Task 056F-Fix — Remove Best N Trades Pipeline Assumptions Serialization

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### `_stress_to_dict()` Extended (`app/services/validation_pipeline_service.py`)

Before:
```python
def _stress_to_dict(sr) -> dict:
    return {"test_name", "passed", "degradation", "stressed_metrics"}
```

After:
```python
def _stress_to_dict(sr) -> dict:
    result = {"test_name", "passed", "degradation", "stressed_metrics"}
    if hasattr(sr, "assumptions"): result["assumptions"] = sr.assumptions
    if hasattr(sr, "warnings"):    result["warnings"] = sr.warnings
    if hasattr(sr, "threshold"):   result["threshold"] = sr.threshold
    return result
```

All existing keys (`test_name`, `passed`, `degradation`, `stressed_metrics`) remain unchanged. New keys are additive and use `hasattr` guards for safety.

### Test Updated

`test_remove_best_n_trades_included_when_enabled` now asserts:
- `assert "assumptions" in n_trades`
- `assert n_trades["assumptions"]["n"] == 2`
- `assert isinstance(n_trades["assumptions"]["removed_count"], int)`
- `assert isinstance(n_trades["assumptions"]["pnl_loss_ratio"], float)`
- `assert "warnings" in n_trades`

## Files Changed

| File | Change |
|---|---|
| `app/services/validation_pipeline_service.py` | Extended `_stress_to_dict()` to include `assumptions`, `warnings`, `threshold` |
| `tests/test_validation_pipeline_service.py` | Updated opt-in test with `assumptions` assertions |
| `docs/changelog.md` | Task 056F-Fix entry |
| `docs/task_board.md` | 056F-Fix → Done |

## Verification

```
.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py tests/test_stress_test.py -v
-> 47 passed

.venv\Scripts\python.exe -m pytest -q
-> 1006 passed, 1 warning

git diff --check → passes
```

Acceptance criteria:
1. ✅ Pipeline stress result dicts include `assumptions`.
2. ✅ Opt-in remove-best-N result exposes `n`, `removed_count`, `pnl_loss_ratio`.
3. ✅ Default pipeline still omits `remove_best_n_trades`.
4. ✅ Remove-best-N stress remains opt-in only.
5. ✅ No UI/report/elimination changes.
6. ✅ Focused tests pass.
7. ✅ Full suite passes.
8. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. Backward-compatible: existing keys unchanged, new keys are additive with `hasattr` guards.
